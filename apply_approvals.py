"""
apply_approvals.py

Reads pending.json (which you've reviewed and marked up) and:
  - approved: true   -> moves the tool into tools.json as an active listing
  - approved: false  -> discards it, removed from pending.json
  - approved: null   -> leaves it untouched, still awaiting your decision

This is the ONLY script that adds new tools to the live-facing tools.json.
Nothing gets published without an explicit `true` from you.
"""
import json
from datetime import date

TOOLS_PATH = "tools.json"
PENDING_PATH = "pending.json"

today_str = date.today().isoformat()


def main():
    with open(TOOLS_PATH, "r", encoding="utf-8") as f:
        tools = json.load(f)

    try:
        with open(PENDING_PATH, "r", encoding="utf-8") as f:
            pending = json.load(f)
    except FileNotFoundError:
        print("No pending.json found — nothing to do.")
        return

    still_pending = []
    approved_count = 0
    rejected_count = 0

    for candidate in pending:
        decision = candidate.get("approved")

        if decision is True:
            tools.append({
                "id": candidate["id"],
                "name": candidate["name"],
                "cat": candidate.get("cat", "Uncategorized"),
                "url": candidate["url"],
                "color": candidate.get("color", "#7c6cfa"),
                "text": candidate.get("text", "#fff"),
                "letter": candidate.get("letter", candidate["name"][0].upper()),
                "desc": candidate.get("desc", ""),
                "isNew": True,
                "featured": False,
                "status": "active",
                "consecutive_failures": 0,
                "last_checked": today_str,
                "last_working": today_str,
                "archived_date": None,
                "source": candidate.get("source", "discovered")
            })
            approved_count += 1
            print(f"APPROVED : {candidate['name']} -> added to tools.json")

        elif decision is False:
            rejected_count += 1
            print(f"REJECTED : {candidate['name']} -> discarded")

        else:
            still_pending.append(candidate)

    with open(TOOLS_PATH, "w", encoding="utf-8") as f:
        json.dump(tools, f, indent=2, ensure_ascii=False)

    with open(PENDING_PATH, "w", encoding="utf-8") as f:
        json.dump(still_pending, f, indent=2, ensure_ascii=False)

    print("\n── Summary ──")
    print(f"  approved (now live in tools.json): {approved_count}")
    print(f"  rejected (discarded): {rejected_count}")
    print(f"  still awaiting review: {len(still_pending)}")


if __name__ == "__main__":
    main()
