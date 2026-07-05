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
        return json.load(f)


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


def audit_page(url):
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

    return {
        "url": url,
        "status_code": status,
        "fetch_error": False,
        "title": title_text,
        "title_length": len(title_text),
        "has_meta_description": bool(meta_desc),
        "meta_description_length": len(meta_desc),
        "h1_count": len(h1_tags),
        "images_total": len(images),
        "images_missing_alt": len(images_missing_alt),
        "word_count": word_count,
        "schema_types": schema_types,
        "extractability": extractability,
    }


def audit_site(cfg):
    urls = get_sitemap_urls(cfg["sitemap_url"], cfg["max_pages_to_crawl"])
    if not urls:
        urls = [cfg["site_url"]]
    print(f"Auditing {len(urls)} page(s) from sitemap...")
    page_audits = [audit_page(url) for url in urls]

    blocked_ai_crawlers = check_ai_crawler_access(cfg["site_url"], cfg["ai_crawlers_to_check"])
    has_llms_txt = check_llms_txt(cfg["site_url"]) if cfg.get("check_llms_txt") else None

    return page_audits, {
        "blocked_ai_crawlers": blocked_ai_crawlers,
        "has_llms_txt": has_llms_txt,
    }


# ── Suggestions engine — combines GSC + on-page data into plain English ──

def generate_suggestions(cfg, overview, quick_wins, low_ctr, declines, page_audits, geo_checks):
    """Returns a list of structured action items, not plain strings, so future
    agents (e.g. Content Agent) can filter and act on them programmatically
    rather than needing to parse English sentences.

    Each item: {description, priority, category, suggested_agent, page}
      priority: 'high' | 'medium' | 'low'
      category: 'technical' | 'on_page_seo' | 'ai_search_geo' | 'content_opportunity' | 'accessibility'
      suggested_agent: 'content_agent' | 'manual' — which agent should pick this up.
        'manual' means no agent exists yet to handle it; you do it by hand for now.
    """
    items = []

    def add(description, priority, category, suggested_agent, page=None):
        items.append({
            "description": description, "priority": priority, "category": category,
            "suggested_agent": suggested_agent, "page": page,
        })

    # ── GEO/AEO: AI Search Readiness (site-wide) ──
    blocked = geo_checks.get("blocked_ai_crawlers")
    if blocked:
        add(f"robots.txt is blocking {', '.join(blocked)} — these crawlers are how ChatGPT, Claude, "
            f"Perplexity, and Google's AI systems discover and cite content. Blocking them means you "
            f"can't appear in AI-generated answers.",
            "high", "ai_search_geo", "manual")

    if geo_checks.get("has_llms_txt") is False:
        add("No llms.txt file — an emerging standard giving AI systems a clean, structured summary of "
            "your site. Not yet universal, but cheap to add and forward-looking.",
            "low", "ai_search_geo", "content_agent")

    # ── Per-page checks ──
    for page in page_audits:
        url = page["url"]
        if page.get("fetch_error"):
            add(f"Page could not be loaded (status: {page.get('status_code', 'no response')}). "
                f"Search engines can't index a page they can't fetch.",
                "high", "technical", "manual", url)
            continue

        if not page["title"]:
            add("No `<title>` tag at all — one of the most important on-page SEO elements.",
                "high", "on_page_seo", "content_agent", url)
        elif page["title_length"] < cfg["title_min_length"]:
            add(f"Title (\"{page['title']}\") is only {page['title_length']} characters — aim for "
                f"{cfg['title_min_length']}-{cfg['title_max_length']}.",
                "medium", "on_page_seo", "content_agent", url)
        elif page["title_length"] > cfg["title_max_length"]:
            add(f"Title is {page['title_length']} characters — Google truncates over ~{cfg['title_max_length']}.",
                "medium", "on_page_seo", "content_agent", url)

        if not page["has_meta_description"]:
            add("No meta description — directly affects click-through rate from search results.",
                "medium", "on_page_seo", "content_agent", url)
        elif page["meta_description_length"] < cfg["meta_description_min_length"]:
            add(f"Meta description is only {page['meta_description_length']} characters — aim for "
                f"{cfg['meta_description_min_length']}-{cfg['meta_description_max_length']}.",
                "medium", "on_page_seo", "content_agent", url)
        elif page["meta_description_length"] > cfg["meta_description_max_length"]:
            add(f"Meta description is {page['meta_description_length']} characters — will get truncated.",
                "low", "on_page_seo", "content_agent", url)

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
            add(f"No schema.org markup — adding {'/'.join(cfg['ideal_schema_types'][:2])} schema helps "
                f"AI systems understand and cite this page correctly.",
                "medium", "ai_search_geo", "content_agent", url)

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
    recent_page_rows = query_search_analytics(service, site_url, recent_start, end_date, ["page"])
    prior_page_rows = query_search_analytics(service, site_url, prior_start, prior_end, ["page"])

    quick_wins = find_quick_wins(query_rows, cfg)
    declines = find_declining_pages(recent_page_rows, prior_page_rows, cfg)
    low_ctr = find_low_ctr_queries(query_rows, cfg)
    overview = compute_overview(query_rows)
    top_queries = top_queries_by_impressions(query_rows, cfg["top_queries_count"])

    page_audits, geo_checks = audit_site(cfg)

    suggestions = generate_suggestions(cfg, overview, quick_wins, low_ctr, declines, page_audits, geo_checks)

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
              "| Page | Title Length | Meta Desc | H1s | Images Missing Alt | Word Count |",
              "|---|---|---|---|---|---|"]
    for p in page_audits:
        if p.get("fetch_error"):
            lines.append(f"| {p['url']} | — | — | — | — | **COULD NOT LOAD** |")
        else:
            lines.append(f"| {p['url']} | {p['title_length']} | {'Yes' if p['has_meta_description'] else 'MISSING'} | "
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
