#!/usr/bin/env python3
"""
Outreach Agent — non-monetary track (backlink requests / "you're listed" notices)

What it does, per run:
  1. Loads active tools from tools.json (source of truth, same as Directory Freshness Agent)
  2. Skips anything already contacted (outreach_log.json) or already queued (outreach_pending.json)
  3. Picks up to `max_per_run` new candidates (config.json), oldest-added-to-directory first
  4. For each candidate: best-effort finds a contact point on their own site (mailto: link or
     a /contact, /about, /contact-us page), then drafts an outreach message
  5. Writes everything to outreach_pending.json in AGENT_CONTRACT.md shape for your review
  6. NEVER sends anything itself. Sending only happens after you approve, and even then
     apply_outreach.py currently just marks it ready-to-send (see that file's docstring).

Also runs a second, separate sponsorship-pitch track (see build_sponsorship_item / config's
sponsorship_tiers) — kept as its own log namespace and rate limit so it can be tuned or paused
independently of backlink outreach.
"""

import json
import re
import hashlib
import datetime
import os
import sys
from urllib.parse import urljoin, urlparse

import requests

ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(ROOT, "config.json")
TOOLS_PATH = os.path.join(ROOT, "..", "directory-freshness", "tools.json")
PENDING_PATH = os.path.join(ROOT, "outreach_pending.json")
LOG_PATH = os.path.join(ROOT, "outreach_log.json")

CONTACT_PAGE_GUESSES = ["/contact", "/contact-us", "/about", "/about-us"]
CONTACT_LINK_KEYWORDS = ["contact", "support", "get in touch", "reach us", "reach out", "help"]
MAILTO_RE = re.compile(r'mailto:([^\s"\'<>?]+)', re.IGNORECASE)
LINK_RE = re.compile(r'<a\s[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r'<[^>]+>')
TITLE_RE = re.compile(r'<title[^>]*>(.*?)</title>', re.IGNORECASE | re.DOTALL)
REQUEST_TIMEOUT = 10
USER_AGENT = "Mozilla/5.0 (compatible; AllAIDuniaOutreachBot/1.0; +https://www.allaidunia.com/)"


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_config():
    return load_json(CONFIG_PATH, {
        "site_name": "AllAIDunia",
        "site_url": "https://www.allaidunia.com/",
        "from_name": "AllAIDunia Team",
        "max_per_run": 5,
        "min_days_since_added": 0,
        "excluded_domains": []
    })


def domain_of(url):
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return url


def strip_tags(html_fragment):
    return TAG_RE.sub("", html_fragment).strip()


def get_title(html):
    match = TITLE_RE.search(html)
    return strip_tags(match.group(1)) if match else ""


def fetch(url, headers):
    """Thin wrapper — returns Response or None, never raises."""
    try:
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        return resp if resp.status_code < 400 else None
    except requests.RequestException:
        return None


def find_contact_links(html, base_url):
    """
    Parses real <a> tags from the page and returns any whose href or visible text
    matches a contact-ish keyword. These are links the site itself put there —
    far more trustworthy than a guessed path that happens to return 200.
    """
    matches = []
    for href, text in LINK_RE.findall(html):
        text_clean = strip_tags(text).lower()
        href_lower = href.lower()
        if any(kw in href_lower or kw in text_clean for kw in CONTACT_LINK_KEYWORDS):
            matches.append(urljoin(base_url, href))
    return matches


def looks_like_same_shell(homepage_html, candidate_html):
    """
    Heuristic for JS-rendered SPAs that return 200 + the same app shell for every route
    (a real risk here — this project's own site had the mirror-image bug: real content that
    crawlers couldn't see). If a guessed path's <title> matches the homepage's, or its content
    length is within 10% of the homepage's, it's likely the same shell, not a distinct page.
    """
    home_title = get_title(homepage_html)
    cand_title = get_title(candidate_html)
    if home_title and cand_title and home_title == cand_title:
        return True
    home_len, cand_len = len(homepage_html), len(candidate_html)
    if home_len and abs(cand_len - home_len) / home_len < 0.10:
        return True
    return False


def find_contact(tool_url, excluded_domains):
    """
    Layered, best-effort contact discovery. Returns:
      {"method": "email"|"contact_form"|"help_center"|"unknown",
       "value": <email or url or None>,
       "confidence": "verified"|"guessed"|"unknown"}

    Order of trust, highest first:
      1. mailto: link anywhere on the homepage
      2. a real on-site link whose href/text says "contact"/"support"/etc — confidence: verified
      3. a help./support. subdomain that resolves — flagged separately, since a ticket queue
         isn't a great fit for a casual outreach ask
      4. guessed common paths (/contact, /about, ...) — confidence: verified only if the content
         looks meaningfully different from the homepage; guessed (low-trust) if it looks like
         the same SPA shell answering every route
    Never raises — network/parse errors just fall through to the next layer or "unknown".
    """
    domain = domain_of(tool_url)
    if domain in excluded_domains:
        return {"method": "unknown", "value": None, "confidence": "unknown"}

    headers = {"User-Agent": USER_AGENT}
    home_resp = fetch(tool_url, headers)
    home_html = home_resp.text if home_resp else ""

    # Layer 1: mailto anywhere on the homepage
    if home_html:
        match = MAILTO_RE.search(home_html)
        if match:
            return {"method": "email", "value": match.group(1), "confidence": "verified"}

    # Layer 2: a real on-site link to something contact-like
    if home_html:
        for link in find_contact_links(home_html, tool_url):
            link_resp = fetch(link, headers)
            if not link_resp:
                continue
            match = MAILTO_RE.search(link_resp.text)
            if match:
                return {"method": "email", "value": match.group(1), "confidence": "verified"}
            return {"method": "contact_form", "value": link, "confidence": "verified"}

    # Layer 3: help/support subdomain
    parsed = urlparse(tool_url)
    for prefix in ("help", "support"):
        candidate = f"{parsed.scheme}://{prefix}.{domain}"
        if fetch(candidate, headers):
            return {"method": "help_center", "value": candidate, "confidence": "verified"}

    # Layer 4: guessed common paths, with SPA-shell detection
    for path in CONTACT_PAGE_GUESSES:
        candidate_url = urljoin(tool_url, path)
        resp = fetch(candidate_url, headers)
        if not resp:
            continue
        match = MAILTO_RE.search(resp.text)
        if match:
            return {"method": "email", "value": match.group(1), "confidence": "verified"}
        if home_html and looks_like_same_shell(home_html, resp.text):
            continue  # almost certainly the same app shell, not a real distinct page — keep looking
        return {"method": "contact_form", "value": candidate_url, "confidence": "verified"}

    # Nothing verified — fall back to the single lowest-trust guess so there's still
    # something for a human to try, but mark it clearly unverified
    if home_html:
        fallback_url = urljoin(tool_url, CONTACT_PAGE_GUESSES[0])
        return {"method": "contact_form", "value": fallback_url, "confidence": "guessed"}

    return {"method": "unknown", "value": None, "confidence": "unknown"}


def deterministic_message(tool, config, contact):
    """Template-based draft. Always available, zero cost, zero hallucination risk."""
    tool_name = tool.get("name", "your tool")
    our_page = f"{config['site_url'].rstrip('/')}/#{tool.get('id', '')}"
    subject = f"You're listed on {config['site_name']} — quick backlink ask"
    body = (
        f"Hi {tool_name} team,\n\n"
        f"Just a heads up — {tool_name} is featured on {config['site_name']} "
        f"({config['site_url']}), a free directory of AI tools. You can see your listing here: "
        f"{our_page}\n\n"
        f"If you're open to it, we'd really appreciate a link back to us from your site "
        f"(e.g. a \"featured on\" or resources page) — happy to reciprocate with a link from "
        f"our listing to any page of yours you'd prefer (docs, blog, etc.).\n\n"
        f"No pressure either way, and thanks for building {tool_name} — it's a genuinely useful "
        f"addition to the directory.\n\n"
        f"Best,\n{config['from_name']}"
    )
    return {"subject": subject, "body": body}


def format_tiers(tiers):
    lines = []
    for tier in tiers:
        includes = ", ".join(tier["includes"])
        lines.append(f"- {tier['name']} — ${tier['price_usd_month']}/mo: {includes}")
    return "\n".join(lines)


def deterministic_sponsorship_message(tool, config):
    """
    Template-based sponsorship pitch. Deliberately does NOT cite specific traffic numbers —
    leans on curation, category count, and the AI-search/GEO optimization angle instead, since
    those are concretely true regardless of current traffic level. See config.json's
    sponsorship_pitch_note for the reasoning.
    """
    tool_name = tool.get("name", "your tool")
    our_page = f"{config['site_url'].rstrip('/')}/#{tool.get('id', '')}"
    tiers_text = format_tiers(config.get("sponsorship_tiers", []))
    subject = f"{tool_name} on {config['site_name']} — featured placement option"
    body = (
        f"Hi {tool_name} team,\n\n"
        f"{tool_name} is already listed on {config['site_name']} ({our_page}), a curated "
        f"directory of AI tools organized into 12 categories, built specifically to be easy for "
        f"both people and AI answer engines (ChatGPT, Perplexity, etc.) to find and cite tools "
        f"from.\n\n"
        f"We're opening up a few featured-placement options for tools that want more visibility "
        f"than a standard listing:\n\n"
        f"{tiers_text}\n\n"
        f"We're early and keeping this to a small founding group at these rates before they go "
        f"up — happy to send more detail or just hear if this isn't a fit right now, no worries "
        f"either way.\n\n"
        f"Best,\n{config['from_name']}"
    )
    return {"subject": subject, "body": body}


def polish_with_llm(draft, tool, config):
    """
    Optional LLM pass to make the deterministic draft read less templated.
    Only runs if OPENAI_API_KEY is set. Falls back silently to the deterministic
    draft on any error — this is a polish step, never a required step.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return draft

    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        prompt = (
            "Rewrite this outreach email to sound warmer and less templated, "
            "while keeping it short, honest, and low-pressure. Keep the same ask "
            "(backlink, reciprocal link offer) and keep all URLs exactly as given. "
            "Return ONLY JSON: {\"subject\": \"...\", \"body\": \"...\"}\n\n"
            f"Tool name: {tool.get('name')}\n"
            f"Original subject: {draft['subject']}\n"
            f"Original body:\n{draft['body']}"
        )
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        text = resp.choices[0].message.content.strip()
        text = re.sub(r"^```json|```$", "", text).strip()
        parsed = json.loads(text)
        if parsed.get("subject") and parsed.get("body"):
            return parsed
    except Exception:
        pass
    return draft


def make_id(category, tool_domain):
    """Deterministic ID per AGENT_CONTRACT.md — same tool+category always gets the same id."""
    return hashlib.sha256(f"outreach:{category}:{tool_domain}".encode()).hexdigest()[:10]


def classify_pricing_tier(pricing_text: str) -> str:
    """
    Same classifier as agents/directory-freshness/regenerate_html.py's classify_pricing_tier,
    duplicated here rather than imported (the two agents' folders aren't set up as a shared
    package). tools.json's `pricing` field is free text ("PAID only", "FREE tier available",
    "", etc), not a clean enum — this derives free / freemium / paid / unknown from it.
    Keep this in sync with regenerate_html.py's version if that logic ever changes.
    """
    text = (pricing_text or "").lower()
    if not text or "see site" in text:
        return "unknown"
    if "completely free" in text:
        return "free"
    if "paid only" in text or "requires" in text:
        return "paid"
    if "trial" in text and "credits" not in text and "tier" not in text:
        return "paid"
    if "free" in text:
        return "freemium"
    return "unknown"


def select_candidates(tool_list, log_key, log, already_used_domains, config, limit,
                       pricing_filter=None):
    candidates = []
    for tool in tool_list:
        if tool.get("status") != "active":
            continue
        url = tool.get("url")
        if not url:
            continue
        domain = domain_of(url)
        if domain in log.get(log_key, {}):
            continue
        if domain in already_used_domains:
            continue
        if domain in config.get("excluded_domains", []):
            continue
        if pricing_filter and classify_pricing_tier(tool.get("pricing")) not in pricing_filter:
            continue
        candidates.append(tool)
        if len(candidates) >= limit:
            break
    return candidates


def build_backlink_item(tool, config):
    domain = domain_of(tool["url"])
    contact = find_contact(tool["url"], config.get("excluded_domains", []))
    draft = deterministic_message(tool, config, contact)
    draft = polish_with_llm(draft, tool, config)
    return domain, {
        "id": make_id("backlink_outreach", domain),
        "description": f"Backlink outreach draft for {tool.get('name', domain)}",
        "priority": "low",
        "category": "backlink_outreach",
        "suggested_agent": "manual",
        "page": None,
        "tool_name": tool.get("name"),
        "tool_domain": domain,
        "tool_url": tool.get("url"),
        "contact_method": contact["method"],
        "contact_value": contact["value"],
        "contact_confidence": contact["confidence"],
        "proposed_message": draft,
        "approved": None,
    }


def build_sponsorship_item(tool, config):
    domain = domain_of(tool["url"])
    contact = find_contact(tool["url"], config.get("excluded_domains", []))
    draft = deterministic_sponsorship_message(tool, config)
    draft = polish_with_llm(draft, tool, config)
    return domain, {
        "id": make_id("sponsorship_pitch", domain),
        "description": f"Sponsorship pitch draft for {tool.get('name', domain)}",
        "priority": "low",
        "category": "sponsorship_pitch",
        "suggested_agent": "manual",
        "page": None,
        "tool_name": tool.get("name"),
        "tool_domain": domain,
        "tool_url": tool.get("url"),
        "contact_method": contact["method"],
        "contact_value": contact["value"],
        "contact_confidence": contact["confidence"],
        "proposed_message": draft,
        "approved": None,
    }


def main():
    config = load_config()
    tools = load_json(TOOLS_PATH, [])
    tool_list = tools if isinstance(tools, list) else tools.get("tools", [])

    log = load_json(LOG_PATH, {"contacted": {}, "sponsorship_contacted": {}})
    pending = load_json(PENDING_PATH, {"agent_meta": {}, "action_items": []})
    already_queued_domains = {
        item.get("tool_domain") for item in pending.get("action_items", [])
    }

    new_items = []
    errors = []
    used_this_run = set()  # dedupe: never draft two messages to the same domain in one run

    backlink_candidates = select_candidates(
        tool_list, "contacted", log,
        already_queued_domains | used_this_run, config,
        config.get("max_per_run", 5),
    )
    for tool in backlink_candidates:
        try:
            domain, item = build_backlink_item(tool, config)
            new_items.append(item)
            used_this_run.add(domain)
        except Exception as e:
            errors.append(f"[backlink] {tool.get('name', 'unknown')}: {e}")

    if config.get("enable_sponsorship_outreach"):
        sponsorship_candidates = select_candidates(
            tool_list, "sponsorship_contacted", log,
            already_queued_domains | used_this_run, config,
            config.get("max_sponsorship_per_run", 3),
            pricing_filter=config.get("sponsorship_eligible_pricing"),
        )
        for tool in sponsorship_candidates:
            try:
                domain, item = build_sponsorship_item(tool, config)
                new_items.append(item)
                used_this_run.add(domain)
            except Exception as e:
                errors.append(f"[sponsorship] {tool.get('name', 'unknown')}: {e}")

    pending.setdefault("action_items", [])
    pending["action_items"].extend(new_items)
    backlink_count = sum(1 for i in new_items if i["category"] == "backlink_outreach")
    sponsorship_count = sum(1 for i in new_items if i["category"] == "sponsorship_pitch")
    pending["agent_meta"] = {
        "agent_name": "outreach_agent",
        "schema_version": "1.0",
        "run_date": datetime.date.today().isoformat(),
        "status": "success" if not errors else "success_with_errors",
        "summary": (
            f"{backlink_count} backlink draft(s), {sponsorship_count} sponsorship draft(s) "
            f"queued for review" + (f"; {len(errors)} error(s)" if errors else "")
        ),
    }
    if errors:
        pending["agent_meta"]["errors"] = errors

    save_json(PENDING_PATH, pending)
    save_json(LOG_PATH, log)
    print(pending["agent_meta"]["summary"])


if __name__ == "__main__":
    sys.exit(main())
