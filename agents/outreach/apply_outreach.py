#!/usr/bin/env python3
"""
apply_outreach.py — processes your approve/reject decisions in outreach_pending.json

Triggers the same way apply_approvals.py does for the Directory Freshness Agent:
on your commit to outreach_pending.json.

For each action item:
  approved == true  -> moved to outreach_log.json as "approved_ready_to_send"
                        (contact info + message stay there so you can copy/send it),
                        removed from outreach_pending.json, domain permanently marked
                        contacted so it's never queued again.
  approved == false -> discarded, domain permanently marked contacted (declined) so
                        it's never queued again either.
  approved == null  -> left untouched, still waiting.

NOTE ON SENDING: this script does not send email. There's no SMTP/email-API credential
configured yet, and auto-sending is exactly the kind of "publishes/sends something
externally" action that should stay behind human approval per the project's automation
principles. Once you're ready to trust auto-send for the email-method items, add an
SMTP secret and a send step here — contact_form-method items will still need a human
either way, since most contact forms aren't scriptable without hitting ToS issues.
"""

import json
import os
import sys
import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
PENDING_PATH = os.path.join(ROOT, "outreach_pending.json")
LOG_PATH = os.path.join(ROOT, "outreach_log.json")


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


LOG_KEY_BY_CATEGORY = {
    "backlink_outreach": "contacted",
    "sponsorship_pitch": "sponsorship_contacted",
}


def main():
    pending = load_json(PENDING_PATH, {"agent_meta": {}, "action_items": []})
    log = load_json(LOG_PATH, {"contacted": {}, "sponsorship_contacted": {}})

    remaining = []
    approved_count = 0
    rejected_count = 0

    for item in pending.get("action_items", []):
        decision = item.get("approved")
        if decision is None:
            remaining.append(item)
            continue

        domain = item.get("tool_domain")
        log_key = LOG_KEY_BY_CATEGORY.get(item.get("category"), "contacted")

        if decision is True:
            log.setdefault(log_key, {})[domain] = {
                "status": "approved_ready_to_send",
                "category": item.get("category"),
                "tool_name": item.get("tool_name"),
                "contact_method": item.get("contact_method"),
                "contact_value": item.get("contact_value"),
                "proposed_message": item.get("proposed_message"),
                "decided_date": datetime.date.today().isoformat(),
            }
            approved_count += 1
        else:
            log.setdefault(log_key, {})[domain] = {
                "status": "declined",
                "category": item.get("category"),
                "tool_name": item.get("tool_name"),
                "decided_date": datetime.date.today().isoformat(),
            }
            rejected_count += 1

    pending["action_items"] = remaining
    pending["agent_meta"] = {
        "agent_name": "outreach_agent",
        "schema_version": "1.0",
        "run_date": datetime.date.today().isoformat(),
        "status": "success",
        "summary": (
            f"{approved_count} approved (ready to send), "
            f"{rejected_count} declined, {len(remaining)} still awaiting review"
        ),
    }

    save_json(PENDING_PATH, pending)
    save_json(LOG_PATH, log)
    print(pending["agent_meta"]["summary"])
    if approved_count:
        print(
            "Approved drafts are in outreach_log.json under \"approved_ready_to_send\" "
            "— copy the proposed_message and send it yourself for now."
        )


if __name__ == "__main__":
    sys.exit(main())
