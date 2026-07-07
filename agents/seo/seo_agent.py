"""
seo_agent.py

Fully parameterized via config.json (no hardcoded site details) so this can
be reused for other businesses/clients later — just swap the config file
and the GSC_SERVICE_ACCOUNT_JSON secret.

Does three things:
  1. Pulls Search Console performance data (queries, pages, positions, CTR)
  2. Crawls the live site itself and audits on-page SEO basics
     (titles, meta descriptions, headings, image alt text)
  3. Combines both into a prioritized, plain-English list of suggestions —
     not just raw tables you have to interpret yourself

Outputs:
  - seo_report.md   — human-readable report with a "Recommended Actions" section
  - seo_data.json   — structured data for future agents (e.g. Content Agent) to consume
"""
import json
import os
import hashlib
import requests
from datetime import date, timedelta
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.environ.get("SEO_CONFIG_PATH", os.path.join(SCRIPT_DIR, "config.json"))
CREDENTIALS_PATH = os.environ.get("GSC_CREDENTIALS_PATH", "gsc_credentials.json")
REPORT_PATH = os.path.join(SCRIPT_DIR, "seo_report.md")
DATA_PATH = os.path.join(SCRIPT_DIR, "seo_data.json")

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}
TIMEOUT_SECONDS = 10


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    # API keys should never be committed to the repo — allow environment
    # variables to override whatever placeholder is in config.json.
    pagespeed_key = os.environ.get("PAGESPEED_API_KEY")
    if pagespeed_key:
        cfg["pagespeed_api_key"] = pagespeed_key
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        cfg["openai_api_key"] = openai_key
    return cfg


# ── Search Console data ──────────────────────────────────────────────

def get_gsc_service():
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH, scopes=SCOPES
    )
    return build("searchconsole", "v1", credentials=creds)


def query_search_analytics(service, site_url, start_date, end_date, dimensions, row_limit=1000):
    body = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "dimensions": dimensions,
        "rowLimit": row_limit,
    }
    response = service.searchanalytics().query(siteUrl=site_url, body=body).execute()
    return response.get("rows", [])


def draft_with_llm(cfg, prompt, max_length, max_attempts=3):
    """Calls OpenAI to draft text that must fit within max_length characters.
    This is a bounded agentic loop, not an open-ended one: generate, check
    the hard constraint, and if it fails, regenerate with specific feedback
    about exactly how much to cut. Stops after max_attempts either way —
    never loops indefinitely. Returns None if it never succeeds, so callers
    can fall back gracefully rather than publish something broken."""
    api_key = cfg.get("openai_api_key")
    if not api_key:
        return None

    current_prompt = prompt
    for attempt in range(max_attempts):
        try:
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": cfg.get("openai_model", "gpt-4o-mini"),
                    "messages": [{"role": "user", "content": current_prompt}],
                    "max_tokens": 150,
                    "temperature": 0.7,
                },
                timeout=30,
            )
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"].strip().strip('"')

            if len(text) <= max_length:
                return text

            # Failed the constraint — regenerate with specific, actionable feedback
            over_by = len(text) - max_length
            current_prompt = (
                f"{prompt}\n\nYour previous attempt was {len(text)} characters, "
                f"which is {over_by} characters too long. Try again, strictly under "
                f"{max_length} characters this time. Previous attempt: \"{text}\""
            )
        except requests.exceptions.RequestException as e:
            print(f"WARNING: LLM draft call failed (attempt {attempt + 1}): {e}")
            return None

    print(f"WARNING: LLM draft never fit within {max_length} chars after {max_attempts} attempts")
    return None


def draft_title(cfg, page_title, page_desc, keywords, max_length):
    keyword_hint = f" Naturally include this keyword if it fits well: \"{keywords[0]['query']}\"." if keywords else ""
    prompt = (
        f"Write an SEO-friendly page title for a page currently titled \"{page_title}\" "
        f"(about: {page_desc}).{keyword_hint} Strictly under {max_length} characters. "
        f"Return ONLY the title text, nothing else."
    )
    return draft_with_llm(cfg, prompt, max_length)


def draft_meta_description(cfg, page_title, page_desc, keywords, max_length):
    keyword_hint = f" Naturally include this keyword if it fits well: \"{keywords[0]['query']}\"." if keywords else ""
    prompt = (
        f"Write an SEO meta description for a page titled \"{page_title}\" (about: {page_desc})."
        f"{keyword_hint} Make it compelling enough to encourage clicks from search results. "
        f"Strictly under {max_length} characters. Return ONLY the meta description text, nothing else."
    )
    return draft_with_llm(cfg, prompt, max_length)


def check_indexing_status(service, site_url, page_url):
    """Uses Search Console's URL Inspection API to check whether Google has
    actually indexed this specific page — a different question from ranking
    performance. A perfectly optimized page that isn't indexed gets zero
    search traffic regardless of title/meta/schema quality."""
    try:
        body = {"inspectionUrl": page_url, "siteUrl": site_url}
        result = service.urlInspection().index().inspect(body=body).execute()
        index_result = result.get("inspectionResult", {}).get("indexStatusResult", {})
        return {
            "verdict": index_result.get("verdict"),  # PASS, FAIL, NEUTRAL, PARTIAL, VERDICT_UNSPECIFIED
            "coverage_state": index_result.get("coverageState"),
            "robots_txt_state": index_result.get("robotsTxtState"),
            "indexing_state": index_result.get("indexingState"),
            "page_fetch_state": index_result.get("pageFetchState"),
            "last_crawl_time": index_result.get("lastCrawlTime"),
        }
    except Exception as e:
        print(f"WARNING: could not check indexing status for {page_url} ({e})")
        return None


def find_quick_wins(query_rows, cfg):
    wins = []
    for row in query_rows:
        position = row["position"]
        impressions = row["impressions"]
        if (cfg["quick_win_min_position"] <= position <= cfg["quick_win_max_position"]
                and impressions >= cfg["quick_win_min_impressions"]):
            wins.append({
                "query": row["keys"][0], "position": round(position, 1),
                "impressions": impressions, "clicks": row["clicks"],
                "ctr": round(row["ctr"] * 100, 1),
            })
    wins.sort(key=lambda w: w["impressions"], reverse=True)
    return wins


def find_declining_pages(recent_rows, prior_rows, cfg):
    recent_by_page = {r["keys"][0]: r["clicks"] for r in recent_rows}
    prior_by_page = {r["keys"][0]: r["clicks"] for r in prior_rows}
    declines = []
    for page, prior_clicks in prior_by_page.items():
        if prior_clicks < 5:
            continue
        recent_clicks = recent_by_page.get(page, 0)
        drop_pct = ((prior_clicks - recent_clicks) / prior_clicks) * 100
        if drop_pct >= cfg["decline_threshold_pct"]:
            declines.append({
                "page": page, "prior_clicks": prior_clicks,
                "recent_clicks": recent_clicks, "drop_pct": round(drop_pct, 1),
            })
    declines.sort(key=lambda d: d["drop_pct"], reverse=True)
    return declines


def find_low_ctr_queries(query_rows, cfg):
    flagged = []
    for row in query_rows:
        impressions = row["impressions"]
        ctr = row["ctr"] * 100
        if impressions >= cfg["low_ctr_min_impressions"] and ctr < cfg["low_ctr_threshold_pct"]:
            flagged.append({
                "query": row["keys"][0], "position": round(row["position"], 1),
                "impressions": impressions, "clicks": row["clicks"], "ctr": round(ctr, 2),
            })
    flagged.sort(key=lambda w: w["impressions"], reverse=True)
    return flagged


def compute_overview(query_rows):
    total_clicks = sum(r["clicks"] for r in query_rows)
    total_impressions = sum(r["impressions"] for r in query_rows)
    avg_position = (
        sum(r["position"] * r["impressions"] for r in query_rows) / total_impressions
        if total_impressions else 0
    )
    return {
        "total_queries": len(query_rows), "total_clicks": total_clicks,
        "total_impressions": total_impressions, "avg_position": round(avg_position, 1),
        "overall_ctr": round((total_clicks / total_impressions * 100) if total_impressions else 0, 2),
    }


def top_queries_by_impressions(query_rows, n):
    rows = sorted(query_rows, key=lambda r: r["impressions"], reverse=True)[:n]
    return [{
        "query": r["keys"][0], "position": round(r["position"], 1),
        "impressions": r["impressions"], "clicks": r["clicks"], "ctr": round(r["ctr"] * 100, 1),
    } for r in rows]


# ── GEO/AEO: AI Search Readiness checks ──────────────────────────────

def check_ai_crawler_access(site_url, ai_crawlers):
    """Checks whether robots.txt blocks any AI crawlers. Returns a list of
    bot names that are BLOCKED (empty list = all good)."""
    parsed = urlparse(site_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    blocked = []
    try:
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        for bot in ai_crawlers:
            if not rp.can_fetch(bot, site_url):
                blocked.append(bot)
    except Exception as e:
        print(f"WARNING: could not read robots.txt ({e}) — skipping AI crawler check")
        return None  # distinguish "couldn't check" from "checked, none blocked"
    return blocked


def check_llms_txt(site_url):
    parsed = urlparse(site_url)
    llms_url = f"{parsed.scheme}://{parsed.netloc}/llms.txt"
    try:
        resp = requests.get(llms_url, headers=HEADERS, timeout=TIMEOUT_SECONDS)
        return resp.status_code == 200
    except requests.exceptions.RequestException:
        return False


def extract_schema_types(soup):
    """Finds JSON-LD structured data blocks and returns the @type values found."""
    types_found = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(script.string or "{}")
        except (json.JSONDecodeError, TypeError):
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict):
                graph = item.get("@graph")
                if graph:
                    for g in graph:
                        if isinstance(g, dict) and "@type" in g:
                            types_found.append(g["@type"])
                elif "@type" in item:
                    types_found.append(item["@type"])
    return types_found


def check_content_extractability(soup):
    """Rough heuristic for how 'liftable' the content is for an AI answer
    engine: presence of lists/tables (easy to extract as discrete facts)
    and reasonably short paragraphs (easier to quote as standalone answers)."""
    lists_and_tables = len(soup.find_all(["ul", "ol", "table"]))
    paragraphs = soup.find_all("p")
    if paragraphs:
        avg_paragraph_words = sum(len(p.get_text().split()) for p in paragraphs) / len(paragraphs)
    else:
        avg_paragraph_words = 0
    headings_h2_plus = len(soup.find_all(["h2", "h3"]))
    return {
        "lists_and_tables_count": lists_and_tables,
        "avg_paragraph_words": round(avg_paragraph_words, 1),
        "subheading_count": headings_h2_plus,
    }


def check_js_rendering_blindspot(soup, cfg):
    """Checks whether a critical content container (e.g. the tools grid) is
    empty in the raw HTML — meaning it's only populated by JavaScript after
    load. Crawlers that don't execute JS (many AI bots, and Googlebot under
    some conditions) would see an empty page here, even though a human
    visitor sees full content. This is often the real explanation behind
    sparse Search Console data on an otherwise well-built site."""
    selector = cfg.get("critical_content_selector")
    if not selector:
        return None  # not configured for this site — skip
    container = soup.select_one(selector)
    if container is None:
        return None  # this page doesn't have that container — not applicable
    real_children = [c for c in container.find_all(recursive=False)]
    expected_min = cfg.get("min_expected_child_elements", 1)
    return {
        "selector": selector,
        "children_found": len(real_children),
        "expected_min": expected_min,
        "likely_invisible_to_crawlers": len(real_children) < expected_min,
    }


def check_pagespeed(url, cfg):
    """Uses Google's free PageSpeed Insights API to check Core Web Vitals —
    a confirmed ranking factor. Works without an API key at low volume;
    set pagespeed_api_key in config if you hit rate limits at scale.
    Real Lighthouse audits can take 30-60+ seconds, so this uses a longer
    timeout than other checks, plus one retry for transient failures."""
    params = {"url": url, "strategy": "mobile", "category": "performance"}
    if cfg.get("pagespeed_api_key"):
        params["key"] = cfg["pagespeed_api_key"]

    for attempt in range(2):
        try:
            resp = requests.get(
                "https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
                params=params, timeout=60
            )
            resp.raise_for_status()
            data = resp.json()
            lighthouse = data.get("lighthouseResult", {})
            perf_score = lighthouse.get("categories", {}).get("performance", {}).get("score")
            audits = lighthouse.get("audits", {})
            return {
                "performance_score": perf_score,  # 0.0-1.0, or None if unavailable
                "lcp_display": audits.get("largest-contentful-paint", {}).get("displayValue"),
                "cls_display": audits.get("cumulative-layout-shift", {}).get("displayValue"),
                "tbt_display": audits.get("total-blocking-time", {}).get("displayValue"),
            }
        except requests.exceptions.RequestException as e:
            if attempt == 0:
                print(f"PageSpeed check failed for {url}, retrying once ({e})")
                continue
            print(f"WARNING: PageSpeed check failed for {url} after retry ({e})")
            return None


def check_meta_robots_noindex(soup):
    """A page can be technically live and well-optimized but explicitly tell
    Google not to index it via a meta tag — independent of anything else
    checked so far. Returns True if noindex is present."""
    tag = soup.find("meta", attrs={"name": "robots"})
    if tag is None:
        return False
    content = tag.get("content", "").lower()
    return "noindex" in content


def check_canonical_tag(soup, expected_domain):
    """Checks for a canonical tag and whether it points to the expected
    domain. Directly relevant given the www/non-www redirect issue this
    site already had — a proper canonical tag makes that class of problem
    self-diagnosing instead of requiring manual investigation."""
    tag = soup.find("link", attrs={"rel": "canonical"})
    if tag is None or not tag.get("href"):
        return {"has_canonical": False, "canonical_url": None, "domain_mismatch": False}
    canonical_url = tag["href"].strip()
    canonical_domain = urlparse(canonical_url).netloc
    return {
        "has_canonical": True,
        "canonical_url": canonical_url,
        "domain_mismatch": bool(canonical_domain) and canonical_domain != expected_domain,
    }


def check_open_graph_tags(soup):
    """Affects how links look when shared on social media/Slack/WhatsApp.
    Low priority compared to indexing/speed issues, but cheap to check."""
    og_title = soup.find("meta", attrs={"property": "og:title"})
    og_desc = soup.find("meta", attrs={"property": "og:description"})
    og_image = soup.find("meta", attrs={"property": "og:image"})
    return {
        "has_og_title": og_title is not None,
        "has_og_description": og_desc is not None,
        "has_og_image": og_image is not None,
    }


def truncate_at_word_boundary(text: str, max_length: int) -> str:
    """Truncates text to fit within max_length without cutting mid-word."""
    if len(text) <= max_length:
        return text
    truncated = text[:max_length].rsplit(" ", 1)[0]
    return truncated.rstrip(" -–—,.")


def suggest_title_fix(current_title: str, cfg: dict, page_queries: list, business_name: str):
    """Proposes an actual replacement title, not just a diagnosis.
    - Too long: truncate cleanly at a word boundary.
    - Too short: only proposed if we have real keyword data to build from —
      otherwise returns None rather than guessing at content we can't verify."""
    max_len = cfg["title_max_length"]
    min_len = cfg["title_min_length"]

    if len(current_title) > max_len:
        return truncate_at_word_boundary(current_title, max_len)

    if len(current_title) < min_len:
        if page_queries:
            top_query = page_queries[0]["query"]
            candidate = f"{top_query.title()} | {business_name}"
            if min_len <= len(candidate) <= max_len:
                return candidate
        return None  # no real data to build a confident suggestion from

    return None  # already within bounds, nothing to suggest


def suggest_meta_description_fix(current_desc: str, cfg: dict, page_queries: list, page_title: str):
    """Proposes an actual replacement meta description.
    - Too long: truncate cleanly at a word boundary.
    - Too short/missing: only proposed if we have keyword data to incorporate."""
    max_len = cfg["meta_description_max_length"]
    min_len = cfg["meta_description_min_length"]

    if current_desc and len(current_desc) > max_len:
        return truncate_at_word_boundary(current_desc, max_len - 1) + "…"

    if not current_desc or len(current_desc) < min_len:
        if page_queries:
            top_queries = ", ".join(q["query"] for q in page_queries[:3])
            candidate = f"{page_title} — covering {top_queries} and more. Free to browse, updated regularly."
            if len(candidate) > max_len:
                candidate = truncate_at_word_boundary(candidate, max_len - 1) + "…"
            if len(candidate) >= min_len:
                return candidate
        return None

    return None


def generate_homepage_schema(tools: list, business_name: str, site_url: str) -> str:
    """Generates real, ready-to-insert ItemList JSON-LD from tools.json data
    — deterministic, not AI-generated, so there's no hallucination risk in
    something as structurally important as schema markup."""
    items = []
    for i, t in enumerate(tools[:100], 1):  # ItemList practical cap
        items.append({
            "@type": "ListItem",
            "position": i,
            "item": {
                "@type": "SoftwareApplication",
                "name": t["name"],
                "url": t["url"],
                "description": t.get("desc", ""),
                "applicationCategory": t.get("cat", ""),
            }
        })
    schema = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"{business_name} — AI Tools Directory",
        "url": site_url,
        "numberOfItems": len(tools),
        "itemListElement": items,
    }
    return json.dumps(schema, indent=2, ensure_ascii=False)


def generate_llms_txt_content(tools: list, business_name: str, site_url: str) -> str:
    """Generates real, complete llms.txt content from tools.json — not a
    suggestion to add one, the actual file ready to publish."""
    lines = [f"# {business_name}", "", f"> A free directory of {len(tools)}+ AI tools, organized by category.", ""]
    by_cat = {}
    for t in tools:
        by_cat.setdefault(t["cat"], []).append(t)
    for cat, cat_tools in sorted(by_cat.items()):
        lines.append(f"## {cat}")
        for t in cat_tools:
            lines.append(f"- [{t['name']}]({t['url']}): {t.get('desc', '')}")
        lines.append("")
    return "\n".join(lines)


def get_sitemap_urls(sitemap_url, max_pages):
    try:
        resp = requests.get(sitemap_url, headers=HEADERS, timeout=TIMEOUT_SECONDS)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "xml")
        urls = [loc.text.strip() for loc in soup.find_all("loc")]
        return urls[:max_pages]
    except requests.exceptions.RequestException as e:
        print(f"WARNING: could not fetch sitemap ({e}) — falling back to homepage only")
        return []


def audit_page(url, cfg, service=None, page_index=0):
    """Checks one page for common on-page SEO basics. Returns a dict with
    fetch_error=True if the page couldn't be fetched at all."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT_SECONDS)
        status = resp.status_code
        if status >= 400:
            return {"url": url, "status_code": status, "fetch_error": True}
        soup = BeautifulSoup(resp.text, "html.parser")
    except requests.exceptions.RequestException as e:
        return {"url": url, "status_code": None, "fetch_error": True, "error": str(e)}

    title_tag = soup.find("title")
    title_text = title_tag.get_text(strip=True) if title_tag else ""

    meta_desc_tag = soup.find("meta", attrs={"name": "description"})
    meta_desc = meta_desc_tag.get("content", "").strip() if meta_desc_tag else ""

    h1_tags = soup.find_all("h1")

    images = soup.find_all("img")
    images_missing_alt = [img for img in images if not img.get("alt", "").strip()]

    word_count = len(soup.get_text(separator=" ", strip=True).split())

    schema_types = extract_schema_types(soup)
    extractability = check_content_extractability(soup)
    js_blindspot = check_js_rendering_blindspot(soup, cfg)
    indexing = check_indexing_status(service, cfg["site_url"], url) if service else None
    noindex = check_meta_robots_noindex(soup)
    canonical = check_canonical_tag(soup, urlparse(cfg["site_url"]).netloc)
    open_graph = check_open_graph_tags(soup)

    # Page speed calls are slow (~10-20s each) and rate-limited without an API
    # key, so only check the first N pages (config-controlled) rather than
    # every page on a larger site.
    pagespeed = None
    if page_index < cfg.get("max_pages_for_pagespeed", 5):
        pagespeed = check_pagespeed(url, cfg)

    return {
        "url": url,
        "status_code": status,
        "fetch_error": False,
        "title": title_text,
        "title_length": len(title_text),
        "has_meta_description": bool(meta_desc),
        "meta_description": meta_desc,
        "meta_description_length": len(meta_desc),
        "h1_count": len(h1_tags),
        "images_total": len(images),
        "images_missing_alt": len(images_missing_alt),
        "word_count": word_count,
        "schema_types": schema_types,
        "extractability": extractability,
        "js_blindspot": js_blindspot,
        "indexing": indexing,
        "noindex": noindex,
        "canonical": canonical,
        "open_graph": open_graph,
        "pagespeed": pagespeed,
    }


def audit_site(cfg, service=None):
    urls = get_sitemap_urls(cfg["sitemap_url"], cfg["max_pages_to_crawl"])
    if not urls:
        urls = [cfg["site_url"]]
    print(f"Auditing {len(urls)} page(s) from sitemap...")
    page_audits = [audit_page(url, cfg, service, i) for i, url in enumerate(urls)]

    blocked_ai_crawlers = check_ai_crawler_access(cfg["site_url"], cfg["ai_crawlers_to_check"])
    has_llms_txt = check_llms_txt(cfg["site_url"]) if cfg.get("check_llms_txt") else None

    return page_audits, {
        "blocked_ai_crawlers": blocked_ai_crawlers,
        "has_llms_txt": has_llms_txt,
    }


# ── Suggestions engine — combines GSC + on-page data into plain English ──

def generate_suggestions(cfg, overview, quick_wins, low_ctr, declines, page_audits, geo_checks,
                          page_query_map=None, all_tools=None):
    """Returns a list of structured action items, not plain strings, so future
    agents (e.g. Content Agent) can filter and act on them programmatically
    rather than needing to parse English sentences.

    Each item: {description, priority, category, suggested_agent, page, proposed_fix}
      priority: 'high' | 'medium' | 'low'
      category: 'technical' | 'on_page_seo' | 'ai_search_geo' | 'content_opportunity' | 'accessibility'
      suggested_agent: 'content_agent' | 'manual' — which agent should pick this up.
        'manual' means no agent exists yet to handle it; you do it by hand for now.
      proposed_fix: the ACTUAL drafted replacement content where possible
        (a new title, a new meta description, real schema JSON, real llms.txt
        content) — not just a description of the problem. None if no concrete
        fix could be drafted (e.g. LLM call failed, or the fix genuinely
        needs human judgment like adding an image).
    """
    page_query_map = page_query_map or {}
    all_tools = all_tools or []
    items = []

    def add(description, priority, category, suggested_agent, page=None, proposed_fix=None):
        # Deterministic ID from the content itself — same issue on the same
        # page always gets the same ID across runs, so a consuming agent
        # (or a human) can track "have I already handled this one?" without
        # needing a database. Changes only if the underlying issue changes.
        id_source = f"{category}|{page or ''}|{description}"
        item_id = hashlib.sha1(id_source.encode("utf-8")).hexdigest()[:10]
        items.append({
            "id": item_id,
            "description": description, "priority": priority, "category": category,
            "suggested_agent": suggested_agent, "page": page,
            "proposed_fix": proposed_fix,
        })

    # ── GEO/AEO: AI Search Readiness (site-wide) ──
    blocked = geo_checks.get("blocked_ai_crawlers")
    if blocked:
        add(f"robots.txt is blocking {', '.join(blocked)} — these crawlers are how ChatGPT, Claude, "
            f"Perplexity, and Google's AI systems discover and cite content. Blocking them means you "
            f"can't appear in AI-generated answers.",
            "high", "ai_search_geo", "manual")

    if geo_checks.get("has_llms_txt") is False:
        proposed_llms_txt = generate_llms_txt_content(all_tools, cfg.get("business_name", ""), cfg.get("site_url", "")) if all_tools else None
        add("No llms.txt file — an emerging standard giving AI systems a clean, structured summary of "
            "your site. Not yet universal, but cheap to add and forward-looking.",
            "low", "ai_search_geo", "content_agent", proposed_fix=proposed_llms_txt)

    # ── Per-page checks ──
    for page in page_audits:
        url = page["url"]
        if page.get("fetch_error"):
            add(f"Page could not be loaded (status: {page.get('status_code', 'no response')}). "
                f"Search engines can't index a page they can't fetch.",
                "high", "technical", "manual", url)
            continue

        page_keywords = page_query_map.get(url, [])
        business_name = cfg.get("business_name", "")

        if not page["title"]:
            proposed = draft_title(cfg, "(no title)", url, page_keywords, cfg["title_max_length"])
            add("No `<title>` tag at all — one of the most important on-page SEO elements.",
                "high", "on_page_seo", "content_agent", url, proposed_fix=proposed)
        elif page["title_length"] < cfg["title_min_length"] or page["title_length"] > cfg["title_max_length"]:
            # Deterministic first (free, instant, reliable for truncation and
            # clear keyword-template cases); only call the LLM if that can't
            # confidently produce a fix (e.g. too short with no keyword data).
            proposed = suggest_title_fix(page["title"], cfg, page_keywords, business_name)
            if proposed is None:
                proposed = draft_title(cfg, page["title"], url, page_keywords, cfg["title_max_length"])
            direction = "aim for" if page["title_length"] < cfg["title_min_length"] else "Google truncates over ~"
            add(f"Title (\"{page['title']}\") is {page['title_length']} characters — "
                f"{direction} {cfg['title_min_length']}-{cfg['title_max_length']}.",
                "medium", "on_page_seo", "content_agent", url, proposed_fix=proposed)

        current_meta = page.get("meta_description", "")
        if not page["has_meta_description"]:
            proposed = draft_meta_description(cfg, page["title"], url, page_keywords,
                                               cfg["meta_description_max_length"])
            add("No meta description — directly affects click-through rate from search results.",
                "medium", "on_page_seo", "content_agent", url, proposed_fix=proposed)
        elif (page["meta_description_length"] < cfg["meta_description_min_length"]
              or page["meta_description_length"] > cfg["meta_description_max_length"]):
            proposed = suggest_meta_description_fix(current_meta, cfg, page_keywords, page["title"])
            if proposed is None:
                proposed = draft_meta_description(cfg, page["title"], url, page_keywords,
                                                   cfg["meta_description_max_length"])
            too_short = page["meta_description_length"] < cfg["meta_description_min_length"]
            note = (f"only {page['meta_description_length']} characters — aim for "
                    f"{cfg['meta_description_min_length']}-{cfg['meta_description_max_length']}"
                    if too_short else
                    f"{page['meta_description_length']} characters — will get truncated")
            add(f"Meta description is {note}.",
                "medium" if too_short else "low", "on_page_seo", "content_agent", url, proposed_fix=proposed)

        if page["h1_count"] == 0:
            add("No H1 tag — helps both users and search engines understand the page's main topic.",
                "low", "on_page_seo", "content_agent", url)
        elif page["h1_count"] > 1:
            add(f"{page['h1_count']} H1 tags found — best practice is exactly one per page.",
                "low", "on_page_seo", "content_agent", url)

        if page["images_missing_alt"] > 0:
            add(f"{page['images_missing_alt']} image(s) missing alt text — affects accessibility and "
                f"image search visibility.", "low", "accessibility", "content_agent", url)

        if page["word_count"] < 150:
            add(f"Only ~{page['word_count']} words — more substantive content tends to rank better.",
                "medium", "content_opportunity", "content_agent", url)

        if not page.get("schema_types"):
            proposed_schema = generate_homepage_schema(all_tools, cfg.get("business_name", ""), cfg.get("site_url", "")) if all_tools else None
            add(f"No schema.org markup — adding {'/'.join(cfg['ideal_schema_types'][:2])} schema helps "
                f"AI systems understand and cite this page correctly.",
                "medium", "ai_search_geo", "content_agent", url, proposed_fix=proposed_schema)

        js_blindspot = page.get("js_blindspot")
        if js_blindspot and js_blindspot["likely_invisible_to_crawlers"]:
            add(f"Critical content may be invisible to crawlers: the container `{js_blindspot['selector']}` "
                f"has only {js_blindspot['children_found']} item(s) in the raw HTML (expected at least "
                f"{js_blindspot['expected_min']}). This strongly suggests this page's main content is filled "
                f"in by JavaScript after load. Many AI crawlers (GPTBot, ClaudeBot, PerplexityBot) and "
                f"Googlebot under some conditions do not execute JavaScript, meaning they may see an empty "
                f"page here even though a human visitor sees full content. This is a likely explanation for "
                f"unusually low search visibility despite otherwise reasonable on-page SEO — the fix is to "
                f"render this content directly into the HTML at build time, in addition to keeping the "
                f"JavaScript for interactive features.",
                "high", "technical", "manual", url)

        indexing = page.get("indexing")
        if indexing and indexing.get("verdict") not in ("PASS", None):
            coverage = indexing.get("coverage_state", "unknown reason")
            add(f"Not indexed by Google: verdict is '{indexing.get('verdict')}' — {coverage}. "
                f"A page that isn't indexed gets zero search traffic no matter how well it's optimized "
                f"otherwise. Use Search Console's URL Inspection tool to request indexing directly.",
                "high", "technical", "manual", url)

        if page.get("noindex"):
            add("This page has a `noindex` meta tag — explicitly telling Google not to index it, "
                "regardless of anything else. If this wasn't intentional, it fully explains poor "
                "search visibility on its own.",
                "high", "technical", "manual", url)

        canonical = page.get("canonical", {})
        if not canonical.get("has_canonical"):
            add("No canonical tag — recommended so search engines know the definitive URL for this "
                "page, especially relevant given this site previously had a www/non-www duplication issue.",
                "medium", "technical", "manual", url)
        elif canonical.get("domain_mismatch"):
            add(f"Canonical tag points to a different domain ({canonical.get('canonical_url')}) than "
                f"expected — this can accidentally tell Google to credit a different host for this page's "
                f"content, similar to the earlier www/non-www redirect issue.",
                "high", "technical", "manual", url)

        og = page.get("open_graph", {})
        missing_og = [k.replace("has_og_", "og:") for k, v in og.items() if not v]
        if missing_og:
            add(f"Missing Open Graph tags ({', '.join(missing_og)}) — affects how this page's links "
                f"look when shared on social media, Slack, or WhatsApp.",
                "low", "on_page_seo", "content_agent", url)

        pagespeed = page.get("pagespeed")
        if pagespeed and pagespeed.get("performance_score") is not None:
            score = pagespeed["performance_score"]
            if score < cfg.get("performance_score_poor_threshold", 0.5):
                add(f"Poor page speed (Lighthouse performance score: {round(score * 100)}/100, mobile). "
                    f"LCP: {pagespeed.get('lcp_display', 'n/a')}, CLS: {pagespeed.get('cls_display', 'n/a')}. "
                    f"Core Web Vitals are a confirmed Google ranking factor.",
                    "high", "technical", "manual", url)
            elif score < cfg.get("performance_score_good_threshold", 0.9):
                add(f"Page speed could be better (Lighthouse performance score: {round(score * 100)}/100, mobile). "
                    f"LCP: {pagespeed.get('lcp_display', 'n/a')}, CLS: {pagespeed.get('cls_display', 'n/a')}.",
                    "medium", "technical", "manual", url)

        extractability = page.get("extractability", {})
        if extractability.get("lists_and_tables_count", 0) == 0 and page["word_count"] > 150:
            add("No lists or tables — AI answer engines strongly prefer content structured for easy "
                "extraction and citation.", "low", "ai_search_geo", "content_agent", url)
        if extractability.get("avg_paragraph_words", 0) > 150:
            add(f"Paragraphs average {extractability['avg_paragraph_words']} words — shorter, "
                f"self-contained paragraphs are easier for AI systems to quote as standalone answers.",
                "low", "ai_search_geo", "content_agent", url)

    # ── Search performance-driven opportunities ──
    for w in low_ctr[:5]:
        add(f"Query \"{w['query']}\" gets {w['impressions']} impressions but only {w['ctr']}% CTR at "
            f"position {w['position']} — likely needs a more compelling title/meta description.",
            "medium", "content_opportunity", "content_agent")

    for w in quick_wins[:5]:
        add(f"\"{w['query']}\" ranks position {w['position']} with {w['impressions']} impressions — a "
            f"supporting blog post or added internal links could push this onto page 1.",
            "high", "content_opportunity", "content_agent")

    for d in declines[:5]:
        add(f"{d['page']} lost {d['drop_pct']}% of its clicks ({d['prior_clicks']} to {d['recent_clicks']}) "
            f"— check for recent changes, broken elements, or content going stale.",
            "high", "technical", "manual", d["page"])

    if not items:
        add("No specific issues found this run — site looks healthy on the checks performed.",
            "low", "technical", "manual")

    return items


def main():
    cfg = load_config()
    business_name = cfg["business_name"]
    site_url = cfg["site_url"]

    print(f"Running SEO agent for: {business_name} ({site_url})")

    service = get_gsc_service()
    today = date.today()
    end_date = today - timedelta(days=3)  # GSC data has a ~2-3 day lag
    recent_start = end_date - timedelta(days=28)
    prior_start = recent_start - timedelta(days=28)
    prior_end = recent_start - timedelta(days=1)

    query_rows = query_search_analytics(service, site_url, recent_start, end_date, ["query"])
    page_query_rows = query_search_analytics(service, site_url, recent_start, end_date, ["page", "query"])
    recent_page_rows = query_search_analytics(service, site_url, recent_start, end_date, ["page"])
    prior_page_rows = query_search_analytics(service, site_url, prior_start, prior_end, ["page"])

    # Group real query performance by the specific page it belongs to —
    # this is what lets us suggest actual keyword-backed titles, not guesses.
    page_queries_map = {}
    for row in page_query_rows:
        page_url, query = row["keys"]
        page_queries_map.setdefault(page_url, []).append({
            "query": query, "impressions": row["impressions"],
            "clicks": row["clicks"], "position": row["position"],
        })
    for page_url in page_queries_map:
        page_queries_map[page_url].sort(key=lambda q: q["impressions"], reverse=True)

    quick_wins = find_quick_wins(query_rows, cfg)
    declines = find_declining_pages(recent_page_rows, prior_page_rows, cfg)
    low_ctr = find_low_ctr_queries(query_rows, cfg)
    overview = compute_overview(query_rows)
    top_queries = top_queries_by_impressions(query_rows, cfg["top_queries_count"])

    page_audits, geo_checks = audit_site(cfg, service)

    # Load the Directory Freshness Agent's tools.json — used for deterministic
    # schema.org and llms.txt generation (structured data we already have
    # accurately, no LLM/hallucination risk needed for these two).
    all_tools = []
    tools_json_path = cfg.get("tools_json_path", "agents/directory-freshness/tools.json")
    try:
        with open(tools_json_path, "r", encoding="utf-8") as f:
            all_tools_raw = json.load(f)
        all_tools = [t for t in all_tools_raw if t.get("status") != "archived"]
    except FileNotFoundError:
        print(f"WARNING: could not find {tools_json_path} — schema/llms.txt suggestions will be skipped")

    suggestions = generate_suggestions(cfg, overview, quick_wins, low_ctr, declines, page_audits, geo_checks,
                                        page_query_map=page_queries_map, all_tools=all_tools)

    # ── Build the human-readable report ──
    lines = [
        f"# SEO Report — {business_name}",
        f"_{today.isoformat()}_",
        "",
        f"Data window: {recent_start} to {end_date} (vs. prior {prior_start} to {prior_end})",
        "",
        "## Recommended Actions",
        "Prioritized suggestions combining Search Console data and a live site audit. "
        "Items tagged for `content_agent` will be actioned automatically once that agent exists — "
        "items tagged `manual` need a person for now.",
        "",
    ]
    for priority in ["high", "medium", "low"]:
        tier_items = [s for s in suggestions if s["priority"] == priority]
        if not tier_items:
            continue
        lines.append(f"### {priority.title()} Priority")
        for item in tier_items:
            page_note = f" _(page: {item['page']})_" if item.get("page") else ""
            lines.append(f"- [{item['category']}] {item['description']}{page_note} "
                         f"— *suggested owner: {item['suggested_agent']}*")
            if item.get("proposed_fix"):
                fix_display = item["proposed_fix"]
                if len(fix_display) > 300:  # collapse long content (schema JSON, llms.txt) into a code block
                    lines.append(f"  ```\n  {fix_display}\n  ```")
                else:
                    lines.append(f"  **Proposed fix:** \"{fix_display}\"")
        lines.append("")

    lines += ["", "## Overview", "| Metric | Value |", "|---|---|",
              f"| Total queries seen | {overview['total_queries']} |",
              f"| Total clicks | {overview['total_clicks']} |",
              f"| Total impressions | {overview['total_impressions']} |",
              f"| Average position | {overview['avg_position']} |",
              f"| Overall CTR | {overview['overall_ctr']}% |"]

    lines += ["", "## AI Search Readiness (GEO/AEO)",
              "Whether AI answer engines (ChatGPT, Perplexity, Gemini, Google AI Overviews) can find, "
              "understand, and cite this site.", ""]
    blocked = geo_checks.get("blocked_ai_crawlers")
    if blocked is None:
        lines.append("- AI crawler access: **could not check** (robots.txt unreachable)")
    elif blocked:
        lines.append(f"- AI crawler access: **BLOCKING** {', '.join(blocked)}")
    else:
        lines.append("- AI crawler access: all checked crawlers allowed")
    lines.append(f"- llms.txt present: {'Yes' if geo_checks.get('has_llms_txt') else 'No'}")
    schema_summary = {}
    for p in page_audits:
        for t in p.get("schema_types", []) or []:
            schema_summary[t] = schema_summary.get(t, 0) + 1
    if schema_summary:
        lines.append(f"- Schema types found across site: {', '.join(f'{k} ({v})' for k, v in schema_summary.items())}")
    else:
        lines.append("- Schema types found across site: **none**")

    lines += ["", "## On-Page Audit", f"{len(page_audits)} page(s) checked from the sitemap.", "",
              "| Page | Indexed | Title Length | Meta Desc | H1s | Images Missing Alt | Word Count |",
              "|---|---|---|---|---|---|---|"]
    for p in page_audits:
        if p.get("fetch_error"):
            lines.append(f"| {p['url']} | — | — | — | — | — | **COULD NOT LOAD** |")
        else:
            indexing = p.get("indexing")
            if indexing is None:
                index_display = "unknown"
            elif indexing.get("verdict") == "PASS":
                index_display = "Yes"
            else:
                index_display = f"**NO** ({indexing.get('verdict')})"
            lines.append(f"| {p['url']} | {index_display} | {p['title_length']} | {'Yes' if p['has_meta_description'] else 'MISSING'} | "
                          f"{p['h1_count']} | {p['images_missing_alt']} | {p['word_count']} |")

    lines += ["", "## Top Queries by Visibility", "", "| Query | Position | Impressions | Clicks | CTR |", "|---|---|---|---|---|"]
    for q in top_queries:
        lines.append(f"| {q['query']} | {q['position']} | {q['impressions']} | {q['clicks']} | {q['ctr']}% |")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # ── Machine-readable version for future agents ──
    # "agent_meta" is a standard envelope every agent in this system should use,
    # so a future manager/CEO agent can aggregate status across all of them
    # without needing custom logic per agent.
    high_priority_count = len([s for s in suggestions if s["priority"] == "high"])
    structured_data = {
        "agent_meta": {
            "agent_name": "seo_agent",
            "schema_version": "1.0",
            "run_date": today.isoformat(),
            "status": "success",
            "summary": f"{len(suggestions)} action items found ({high_priority_count} high priority)",
        },
        "business_name": business_name, "site_url": site_url,
        "generated_date": today.isoformat(),
        "window": {"start": recent_start.isoformat(), "end": end_date.isoformat()},
        "overview": overview, "top_queries": top_queries, "quick_wins": quick_wins,
        "low_ctr_queries": low_ctr, "declining_pages": declines,
        "page_audits": page_audits, "geo_checks": geo_checks,
        "action_items": suggestions,
    }
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(structured_data, f, indent=2, ensure_ascii=False)

    print(f"\n{len(suggestions)} suggestions generated")
    print(f"Report written to {REPORT_PATH}")
    print(f"Structured data written to {DATA_PATH}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Even on failure, write a minimal status record — a future manager
        # agent needs to be able to see "SEO agent failed" rather than just
        # finding a stale or missing file with no explanation.
        failure_record = {
            "agent_meta": {
                "agent_name": "seo_agent",
                "schema_version": "1.0",
                "run_date": date.today().isoformat(),
                "status": "failed",
                "summary": f"Run failed: {e}",
            }
        }
        try:
            with open(DATA_PATH, "w", encoding="utf-8") as f:
                json.dump(failure_record, f, indent=2)
        except Exception:
            pass  # don't let a secondary failure mask the original error
        raise  # re-raise so the GitHub Actions workflow still shows red/failed
