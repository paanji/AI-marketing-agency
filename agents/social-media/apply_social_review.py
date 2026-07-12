"""
Applies your review decisions from social_pending.json.

Mirrors directory-freshness/apply_approvals.py's pattern exactly:
  - "approved": true  -> moved into ready_to_post.json (final, human-readable,
                         ready for you or a future auto-publish step to use)
  - "approved": false -> discarded from the queue, its id added to
                         social_rejected.json so the same content angle
                         never resurfaces
  - "approved": null  -> left untouched, still waiting

This script never posts to any platform. It only reorganizes files.
"""

import json
import os
from datetime import datetime, timezone

AGENT_DIR = os.path.dirname(os.path.abspath(__file__))


def load_json(path, default=None):
    if not os.path.exists(path):
        return default if default is not None else {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def run():
    pending_path = os.path.join(AGENT_DIR, "social_pending.json")
    rejected_path = os.path.join(AGENT_DIR, "social_rejected.json")
    ready_path = os.path.join(AGENT_DIR, "ready_to_post.json")

    pending = load_json(pending_path, default={"items": []})
    rejected = load_json(rejected_path, default={"blocked_ids": []})
    ready = load_json(ready_path, default={"items": []})

    still_pending = []
    approved_count = 0
    rejected_count = 0

    for item in pending.get("items", []):
        decision = item.get("approved")
        if decision is True:
            item["approved_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            ready["items"].append(item)
            approved_count += 1
        elif decision is False:
            rejected["blocked_ids"].append(item["id"])
            rejected_count += 1
        else:
            still_pending.append(item)

    pending["items"] = still_pending

    save_json(pending_path, pending)
    save_json(rejected_path, rejected)
    save_json(ready_path, ready)

    summary = (
        f"{approved_count} draft(s) moved to ready_to_post.json, "
        f"{rejected_count} rejected and blocklisted, "
        f"{len(still_pending)} still awaiting your decision."
    )
    print(summary)
    return summary


if __name__ == "__main__":
    run()
