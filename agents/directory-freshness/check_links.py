"""
check_links.py

Reads tools.json, tests every tool's URL, and updates lifecycle state:

  active  --(fails)-->  flagged (strike 1, 2)  --(3rd fail)-->  archived
  flagged --(works)-->  active (strikes reset to 0)
  archived --(works, checked ~weekly)--> active (auto-revived)

Rules:
- active/flagged tools are checked EVERY run (these are live on the site,
  we want to catch problems fast).
- archived tools are only re-checked if it's been >= REVIVAL_CHECK_DAYS
  since their last check (no urgency, they're already off the site).
- Nothing is ever deleted. archived just means "not shown on the site."
- A single successful check fully resets consecutive_failures to 0.

Run this from GitHub Actions on a schedule (e.g. daily).
"""
import json
import requests
from datetime import date, datetime, timedelta

TOOLS_PATH = "agents/directory-freshness/tools.json"
STRIKES_TO_ARCHIVE = 3
REVIVAL_CHECK_DAYS = 7
TIMEOUT_SECONDS = 10
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

today = date.today()
today_str = today.isoformat()


# Status codes that mean "a bot got blocked", NOT "the site is dead".
# Cloudflare/WAF-protected sites (Claude, Midjourney, Meta, etc.) routinely
# return these to datacenter IPs like GitHub Actions runners, even though
# the site is perfectly alive for real visitors. We must NOT strike on these.
INCONCLUSIVE_CODES = {403, 429, 503}


def check_url(url: str) -> tuple[str, str]:
    """Returns (result, reason) where result is one of:
       'alive'        - confirmed working
       'dead'         - confirmed broken (404, DNS failure, connection refused)
       'inconclusive' - blocked/rate-limited, can't tell if real (403/429/503, timeout)
    Tries HEAD first, falls back to GET, with one retry."""
    for attempt in range(2):
        try:
            resp = requests.head(
                url, headers=HEADERS, timeout=TIMEOUT_SECONDS,
                allow_redirects=True
            )
            if resp.status_code >= 400 or resp.status_code == 405:
                # HEAD not allowed / error -> try GET before giving up
                resp = requests.get(
                    url, headers=HEADERS, timeout=TIMEOUT_SECONDS,
                    allow_redirects=True, stream=True
                )
            if resp.status_code < 400:
                return "alive", f"OK ({resp.status_code})"
            if resp.status_code in INCONCLUSIVE_CODES:
                return "inconclusive", f"HTTP {resp.status_code} (likely bot-blocked, not dead)"
            return "dead", f"HTTP {resp.status_code}"
        except requests.exceptions.Timeout:
            if attempt == 0:
                continue
            return "inconclusive", "Timeout"
        except requests.exceptions.SSLError:
            return "dead", "SSL error"
        except requests.exceptions.ConnectionError:
            if attempt == 0:
                continue
            return "dead", "Connection failed"
        except requests.exceptions.RequestException as e:
            return "inconclusive", f"Error: {e}"
    return "inconclusive", "Failed after retry"


def days_since(date_str: str) -> int:
    try:
        last = datetime.fromisoformat(date_str).date()
    except ValueError:
        return 999
    return (today - last).days


def main():
    with open(TOOLS_PATH, "r", encoding="utf-8") as f:
        tools = json.load(f)

    summary = {"checked": 0, "skipped": 0, "revived": 0,
               "newly_flagged": 0, "newly_archived": 0, "still_broken": 0,
               "inconclusive": 0}

    for t in tools:
        status = t.get("status", "active")

        # Archived tools: only re-check occasionally
        if status == "archived":
            if days_since(t.get("last_checked", today_str)) < REVIVAL_CHECK_DAYS:
                summary["skipped"] += 1
                continue

        result, reason = check_url(t["url"])
        summary["checked"] += 1
        t["last_checked"] = today_str

        if result == "alive":
            t["last_working"] = today_str
            t["consecutive_failures"] = 0
            if status == "archived":
                t["status"] = "active"
                t["archived_date"] = None
                summary["revived"] += 1
                print(f"REVIVED  : {t['name']} ({t['url']})")
            elif status == "flagged":
                t["status"] = "active"
                print(f"RECOVERED: {t['name']} ({t['url']})")
            # else: was already active and stayed active — no log needed

        elif result == "inconclusive":
            # Bot-blocked or timed out — don't touch strikes or status at all.
            # We genuinely don't know if the site is up; guessing wrong in
            # either direction is worse than just waiting for a clearer signal.
            summary["inconclusive"] += 1
            print(f"UNCLEAR  : {t['name']} ({t['url']}) — {reason}, no action taken")

        else:  # result == "dead"
            t["consecutive_failures"] = t.get("consecutive_failures", 0) + 1
            if t["consecutive_failures"] >= STRIKES_TO_ARCHIVE:
                if status != "archived":
                    t["status"] = "archived"
                    t["archived_date"] = today_str
                    summary["newly_archived"] += 1
                    print(f"ARCHIVED : {t['name']} ({t['url']}) — {reason}")
                else:
                    summary["still_broken"] += 1
            else:
                t["status"] = "flagged"
                summary["newly_flagged"] += 1
                print(f"FLAGGED  : {t['name']} ({t['url']}) — {reason} "
                      f"(strike {t['consecutive_failures']}/{STRIKES_TO_ARCHIVE})")

    with open(TOOLS_PATH, "w", encoding="utf-8") as f:
        json.dump(tools, f, indent=2, ensure_ascii=False)

    print("\n── Summary ──")
    for k, v in summary.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
