"""
discover_tools.py

Finds candidate new AI tools from Hacker News "Show HN" posts and writes
qualifying ones into pending.json for manual review. NOTHING here ever
touches tools.json directly or goes live automatically — see apply_approvals.py
for the step that actually publishes anything, which only runs on your
explicit approval.

Source: HN Algolia Search API (https://hn.algolia.com/api) — free, public,
no API key or account required, no commercial-use restriction.
"""
import json
import re
import requests
from datetime import date, datetime, timedelta
from urllib.parse import urlparse

TOOLS_PATH = "tools.json"
PENDING_PATH = "pending.json"
REJECTED_PATH = "rejected.json"

HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date"
LOOKBACK_DAYS = 8          # slightly over a week so a weekly run doesn't miss any
MIN_POINTS = 15            # quality gate — filters out low-traction posts
AI_KEYWORDS = [
    "ai", "gpt", "llm", "chatbot", "machine learning", "neural",
    "generative", "artificial intelligence", "claude", "openai",
    "diffusion", "copilot", "agent"
]
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}
TIMEOUT_SECONDS = 10


import re as _re
_AI_KEYWORD_PATTERNS = []
for _kw in AI_KEYWORDS:
    if _kw == "ai":
        # Kept strict — no plural, this is the one prone to false substring matches
        _pattern = r"\bai\b"
    else:
        _pattern = r"\b" + _re.escape(_kw) + r"s?\b"  # allow simple plurals
    _AI_KEYWORD_PATTERNS.append(_re.compile(_pattern, _re.IGNORECASE))


def is_ai_related(title: str) -> bool:
    return any(pattern.search(title) for pattern in _AI_KEYWORD_PATTERNS)


def clean_domain(url: str) -> str:
    """Normalizes a URL down to its bare domain for de-duplication,
    e.g. 'https://www.midjourney.com/app' -> 'midjourney.com'"""
    try:
        netloc = urlparse(url).netloc.lower()
        return netloc[4:] if netloc.startswith("www.") else netloc
    except Exception:
        return url.lower()


def extract_tool_name(hn_title: str) -> str:
    """'Show HN: Midjourney – AI art in seconds' -> 'Midjourney'"""
    title = re.sub(r"^show hn:\s*", "", hn_title, flags=re.IGNORECASE).strip()
    # Titles are often "Name – description" or "Name: description"
    for sep in [" – ", " — ", " - ", ": "]:
        if sep in title:
            return title.split(sep)[0].strip()
    return title[:60].strip()


def check_url_alive(url: str) -> bool:
    """Simple alive check — reuses the same tolerant logic as check_links.py.
    Treats bot-blocks (403/429/503) as 'assume alive' since we can't
    disprove it, and would rather a human reviewer filter it out than
    silently drop a legitimate tool."""
    try:
        resp = requests.head(url, headers=HEADERS, timeout=TIMEOUT_SECONDS,
                              allow_redirects=True)
        if resp.status_code >= 400 and resp.status_code not in (403, 405, 429, 503):
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT_SECONDS,
                                 allow_redirects=True, stream=True)
        return resp.status_code < 400 or resp.status_code in (403, 429, 503)
    except requests.exceptions.RequestException:
        return False


def main():
    with open(TOOLS_PATH, "r", encoding="utf-8") as f:
        existing_tools = json.load(f)
    existing_domains = {clean_domain(t["url"]) for t in existing_tools}

    try:
        with open(PENDING_PATH, "r", encoding="utf-8") as f:
            pending = json.load(f)
    except FileNotFoundError:
        pending = []
    pending_domains = {clean_domain(p["url"]) for p in pending}

    try:
        with open(REJECTED_PATH, "r", encoding="utf-8") as f:
            rejected_domains = set(json.load(f))
    except FileNotFoundError:
        rejected_domains = set()

    since_timestamp = int((datetime.utcnow() - timedelta(days=LOOKBACK_DAYS)).timestamp())

    params = {
        "tags": "show_hn",
        "numericFilters": f"created_at_i>{since_timestamp},points>={MIN_POINTS}",
        "hitsPerPage": 100,
    }
    resp = requests.get(HN_SEARCH_URL, params=params, timeout=TIMEOUT_SECONDS)
    resp.raise_for_status()
    hits = resp.json().get("hits", [])

    today_str = date.today().isoformat()
    added = 0
    skipped_duplicate = 0
    skipped_not_ai = 0
    skipped_dead = 0

    for hit in hits:
        title = hit.get("title") or ""
        url = hit.get("url")
        points = hit.get("points", 0)

        if not url or not title:
            continue
        if not is_ai_related(title):
            skipped_not_ai += 1
            continue

        domain = clean_domain(url)
        if domain in existing_domains or domain in pending_domains:
            skipped_duplicate += 1
            continue
        if domain in rejected_domains:
            skipped_duplicate += 1
            continue

        if not check_url_alive(url):
            skipped_dead += 1
            continue

        name = extract_tool_name(title)
        pending.append({
            "id": re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"),
            "name": name,
            "cat": "Uncategorized",   # you'll set this during review
            "url": url,
            "color": "#7c6cfa",
            "text": "#fff",
            "letter": name[0].upper() if name else "?",
            "desc": title,            # HN title as a starting point — edit freely
            "isNew": True,
            "featured": False,
            "source": "discovered",
            "discovery_source": "Show HN",
            "discovery_points": points,
            "discovered_date": today_str,
            "approved": None          # null = awaiting your review. true = approve, false = reject
        })
        pending_domains.add(domain)
        added += 1
        print(f"CANDIDATE: {name} ({url}) — {points} HN points")

    with open(PENDING_PATH, "w", encoding="utf-8") as f:
        json.dump(pending, f, indent=2, ensure_ascii=False)

    print("\n── Summary ──")
    print(f"  new candidates added: {added}")
    print(f"  skipped (duplicate): {skipped_duplicate}")
    print(f"  skipped (not AI-related): {skipped_not_ai}")
    print(f"  skipped (link dead): {skipped_dead}")
    print(f"  total pending review: {len(pending)}")


if __name__ == "__main__":
    main()
