"""
Shared utilities for the Outreach Agent's two scripts (outreach_agent.py and
apply_outreach.py) — kept in one place so the review report and confidence-sort logic
can't drift out of sync between drafting and applying.
"""

import json
import os
import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
PENDING_PATH = os.path.join(ROOT, "outreach_pending.json")
LOG_PATH = os.path.join(ROOT, "outreach_log.json")
REVIEW_REPORT_PATH = os.path.join(ROOT, "outreach_review.md")

CONFIDENCE_RANK = {"verified": 0, "guessed": 1, "unknown": 2}
CONFIDENCE_BADGE = {"verified": "✅ verified", "guessed": "⚠️ guessed", "unknown": "❓ unknown"}


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def sort_by_confidence(items):
    """
    Undecided items only ever sit in outreach_pending.json (apply_outreach.py removes
    decided ones), so it's always safe to reorder the full list. Puts verified contacts
    first so the most trustworthy items to approve are the first thing you see.
    """
    return sorted(
        items,
        key=lambda i: CONFIDENCE_RANK.get(i.get("contact_confidence", "unknown"), 2),
    )


def write_review_report(pending):
    """
    Human-readable companion to outreach_pending.json — same pattern as seo_report.md
    alongside seo_data.json. This is what you actually read; outreach_pending.json stays
    the source of truth you edit (set approved: true/false) to make decisions.

    Called from both scripts: outreach_agent.py after drafting new items, and
    apply_outreach.py after removing decided ones — so it never goes stale either way.
    """
    lines = [
        "# Outreach Review",
        "",
        f"_Generated {datetime.date.today().isoformat()} — "
        f"{pending['agent_meta']['summary']}_",
        "",
        "To act on any item: edit `outreach_pending.json`, set that item's `\"approved\"` "
        "to `true` or `false`, and commit. Leave it `null` to keep it queued.",
        "",
        "| Confidence | Category | Tool | Method | Contact |",
        "|---|---|---|---|---|",
    ]
    for item in pending.get("action_items", []):
        if item.get("approved") is not None:
            continue  # already decided, not yet applied — don't clutter the review view
        confidence = item.get("contact_confidence", "unknown")
        badge = CONFIDENCE_BADGE.get(confidence, confidence)
        contact = item.get("contact_value") or "—"
        lines.append(
            f"| {badge} | {item['category']} | {item['tool_name']} | "
            f"{item['contact_method']} | {contact} |"
        )
    if not pending.get("action_items"):
        lines.append("| _(queue is empty)_ | | | | |")
    lines += [
        "",
        "**Recommended order:** approve ✅ verified items first — those are confirmed real "
        "contact points, not guesses. Give ⚠️ guessed items a manual check before approving. "
        "❓ unknown items have no discovered contact at all; you'll need to track one down "
        "yourself if you want to proceed with those.",
    ]
    with open(REVIEW_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
