"""
Content Agent — Step 1: Build the review queue.

Reads agents/seo/seo_data.json (following AGENT_CONTRACT.md's action_items shape),
filters for items tagged suggested_agent == "content_agent" that already have a
proposed_fix drafted by the SEO Agent, and writes/updates content_pending.json —
a human review queue in the same spirit as the Directory Freshness Agent's
pending.json.

This script NEVER touches the live site. It only ever writes content_pending.json.
Human decisions (approved: true/false) made in a previous run are preserved by ID
across re-runs, so re-running this doesn't wipe out review progress.

Items without a proposed_fix (e.g. "missing OG image", "no lists/tables") are
skipped for now — the SEO Agent didn't draft a fix for these, and the Content
Agent's job (per PROJECT_OVERVIEW.md) is to apply drafted fixes, not generate new
creative work from scratch. They remain visible in seo_report.md as manual items.
"""

import json
import os
import sys

CONFIG_PATH = "agents/content/config.json"


def load_json(path, default=None):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def url_to_file_path(page_url, site_url, site_root_dir):
    """Map a page URL from seo_data.json to its file on disk in the repo."""
    if page_url is None:
        return None
    relative = page_url.replace(site_url.rstrip("/"), "").lstrip("/")
    if relative == "":
        relative = "index.html"
    return relative if site_root_dir in (".", "") else os.path.join(site_root_dir, relative)


def classify_fix_type(item):
    """
    field_type distinguishes title/meta cleanly. Schema.org and llms.txt both
    come through with field_type: null, so we disambiguate by shape:
    - llms.txt is always site-wide (page is null)
    - schema.org proposed_fix is always JSON (starts with '{')
    """
    field_type = item.get("field_type")
    if field_type == "title":
        return "title"
    if field_type == "meta description":
        return "meta_description"
    if item.get("page") is None:
        return "llms_txt"
    fix_text = (item.get("proposed_fix") or "").strip()
    if fix_text.startswith("{"):
        return "schema_org"
    return "other"  # no known application strategy yet — skip


def main():
    config = load_json(CONFIG_PATH, {})
    seo_data_path = config.get("seo_data_path", "agents/seo/seo_data.json")
    pending_path = config.get("content_pending_path", "agents/content/content_pending.json")
    rejected_path = config.get("content_rejected_path", "agents/content/content_rejected.json")
    site_url = config.get("site_url", "https://www.allaidunia.com/")
    site_root_dir = config.get("site_root_dir", ".")

    seo_data = load_json(seo_data_path)
    if not seo_data:
        print(f"ERROR: could not read {seo_data_path}")
        sys.exit(1)

    existing_pending = load_json(pending_path, [])
    existing_by_id = {entry["id"]: entry for entry in existing_pending}

    rejected_ids = set(load_json(rejected_path, []))

    action_items = seo_data.get("action_items", [])
    new_pending = []
    skipped_no_fix = 0
    skipped_rejected = 0
    skipped_unknown_shape = 0

    for item in action_items:
        if item.get("suggested_agent") != "content_agent":
            continue

        if item["id"] in rejected_ids:
            # Human already said no to this exact issue previously — don't re-ask.
            skipped_rejected += 1
            continue

        if item.get("proposed_fix") is None:
            skipped_no_fix += 1
            continue

        fix_type = classify_fix_type(item)
        if fix_type == "other":
            skipped_unknown_shape += 1
            continue

        if fix_type == "llms_txt":
            file_path = "llms.txt" if site_root_dir in (".", "") else os.path.join(site_root_dir, "llms.txt")
        else:
            file_path = url_to_file_path(item.get("page"), site_url, site_root_dir)

        # Preserve a prior human decision on this exact ID if one exists.
        prior = existing_by_id.get(item["id"], {})

        entry = {
            "id": item["id"],
            "fix_type": fix_type,
            "page": item.get("page"),
            "file_path": file_path,
            "description": item.get("description"),
            "current_value": item.get("current_value"),
            "proposed_fix": item.get("proposed_fix"),
            "target_range": item.get("target_range"),
            "approved": prior.get("approved", None),
        }
        new_pending.append(entry)

    save_json(pending_path, new_pending)

    print(
        f"Content Agent queue updated: {len(new_pending)} actionable item(s) "
        f"awaiting review in {pending_path}."
    )
    print(
        f"Skipped — {skipped_no_fix} with no drafted fix yet, "
        f"{skipped_rejected} previously rejected, "
        f"{skipped_unknown_shape} unrecognized shape."
    )


if __name__ == "__main__":
    main()
