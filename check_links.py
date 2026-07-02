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

TOOLS_PATH = "tools.json"
STRIKES_TO_ARCHIVE = 3
REVIVAL_CHECK_DAYS = 7
TIMEOUT_SECONDS = 10
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AllAIDuniaLinkChecker/1.0; "
                  "+https://www.allaidunia.com)"
}

today = date.today()
today_str = today.isoformat()


def check_url(url: str) -> tuple[bool, str]:
    """Returns (is_alive, reason). Tries HEAD first, falls back to GET
    (some servers block HEAD requests but allow GET), with one retry."""
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
                return True, f"OK ({resp.status_code})"
            return False, f"HTTP {resp.status_code}"
        except requests.exceptions.Timeout:
            if attempt == 0:
                continue
            return False, "Timeout"
        except requests.exceptions.SSLError:
            return False, "SSL error"
        except requests.exceptions.ConnectionError:
            if attempt == 0:
                continue
            return False, "Connection failed"
        except requests.exceptions.RequestException as e:
            return False, f"Error: {e}"
    return False, "Failed after retry"


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
               "newly_flagged": 0, "newly_archived": 0, "still_broken": 0}

    for t in tools:
        status = t.get("status", "active")

        # Archived tools: only re-check occasionally
        if status == "archived":
            if days_since(t.get("last_checked", today_str)) < REVIVAL_CHECK_DAYS:
                summary["skipped"] += 1
                continue

        alive, reason = check_url(t["url"])
        summary["checked"] += 1
        t["last_checked"] = today_str

        if alive:
            t["last_working"] = today_str
            was_broken = t.get("consecutive_failures", 0) > 0 or status != "active"
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

        else:
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
