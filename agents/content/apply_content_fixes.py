"""
Content Agent — Step 2: Apply approved fixes.

Triggered automatically the moment you commit a change to content_pending.json
(same pattern as apply_approvals.py for the Directory Freshness Agent).

For each item in content_pending.json:
  - approved: true  -> apply the fix to the real file, then remove from queue
                       and log it in content_applied_log.json
  - approved: false -> remove from queue, add its ID to content_rejected.json
                       so it never resurfaces just because the SEO Agent still
                       technically detects the same underlying issue
  - approved: null  -> left untouched, still waiting on your decision

This script only ever touches files listed via file_path in content_pending.json
(html files at the site root, or llms.txt). It never touches tools.json,
pending.json, or anything owned by the Directory Freshness Agent.
"""

import json
import os
import re
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


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def apply_title(html, current_value, proposed_fix):
    if current_value not in html:
        return html, False
    return html.replace(current_value, proposed_fix, 1), True


def apply_meta_description(html, current_value, proposed_fix):
    if current_value not in html:
        return html, False
    return html.replace(current_value, proposed_fix, 1), True


def apply_schema_org(html, item_id, proposed_fix, marker_prefix):
    """
    Injects (or replaces) a marked JSON-LD <script> block just before </head>.
    Any existing block for this SAME file, regardless of which id created it,
    is removed first — a file should only carry one current schema block.
    """
    block_pattern = re.compile(
        rf"<!-- {re.escape(marker_prefix)}:.*? -->.*?<!-- /{re.escape(marker_prefix)}:.*? -->\n?",
        re.DOTALL,
    )
    html = block_pattern.sub("", html)

    new_block = (
        f"<!-- {marker_prefix}:{item_id} -->\n"
        f'<script type="application/ld+json">\n{proposed_fix}\n</script>\n'
        f"<!-- /{marker_prefix}:{item_id} -->\n"
    )

    if "</head>" not in html:
        return html, False

    html = html.replace("</head>", new_block + "</head>", 1)
    return html, True


def main():
    config = load_json(CONFIG_PATH, {})
    pending_path = config.get("content_pending_path", "agents/content/content_pending.json")
    rejected_path = config.get("content_rejected_path", "agents/content/content_rejected.json")
    applied_log_path = config.get("content_applied_log_path", "agents/content/content_applied_log.json")
    marker_prefix = config.get("schema_marker_prefix", "CONTENT-AGENT:SCHEMA")

    pending = load_json(pending_path, [])
    if not pending:
        print("No content_pending.json items found — nothing to do.")
        return

    rejected_ids = set(load_json(rejected_path, []))
    applied_log = load_json(applied_log_path, [])

    still_pending = []
    applied_count = 0
    rejected_count = 0
    error_count = 0

    for item in pending:
        approved = item.get("approved")

        if approved is None:
            still_pending.append(item)
            continue

        if approved is False:
            rejected_ids.add(item["id"])
            rejected_count += 1
            print(f"[{item['id']}] rejected — added to blocklist, removed from queue.")
            continue

        # approved is True — apply it.
        file_path = item.get("file_path")
        fix_type = item.get("fix_type")

        if fix_type == "llms_txt":
            try:
                write_file(file_path, item["proposed_fix"])
                applied_log.append(item)
                applied_count += 1
                print(f"[{item['id']}] wrote {file_path}")
            except Exception as e:
                print(f"[{item['id']}] ERROR writing {file_path}: {e}")
                still_pending.append(item)
                error_count += 1
            continue

        if not file_path or not os.path.exists(file_path):
            print(f"[{item['id']}] ERROR: file not found: {file_path} — leaving in queue.")
            still_pending.append(item)
            error_count += 1
            continue

        html = read_file(file_path)

        if fix_type == "title":
            new_html, ok = apply_title(html, item["current_value"], item["proposed_fix"])
        elif fix_type == "meta_description":
            new_html, ok = apply_meta_description(html, item["current_value"], item["proposed_fix"])
        elif fix_type == "schema_org":
            new_html, ok = apply_schema_org(html, item["id"], item["proposed_fix"], marker_prefix)
        else:
            print(f"[{item['id']}] ERROR: unknown fix_type '{fix_type}' — leaving in queue.")
            still_pending.append(item)
            error_count += 1
            continue

        if not ok:
            print(
                f"[{item['id']}] ERROR: expected content not found in {file_path} "
                f"(file may have changed since the SEO Agent last ran) — leaving in queue "
                f"for manual attention."
            )
            still_pending.append(item)
            error_count += 1
            continue

        write_file(file_path, new_html)
        applied_log.append(item)
        applied_count += 1
        print(f"[{item['id']}] applied {fix_type} fix to {file_path}")

    save_json(pending_path, still_pending)
    save_json(rejected_path, sorted(rejected_ids))
    save_json(applied_log_path, applied_log)

    print(
        f"\nDone. {applied_count} applied, {rejected_count} rejected, "
        f"{error_count} errors, {len(still_pending)} still awaiting review."
    )

    if error_count > 0:
        # Non-zero exit so the workflow surfaces a visible failure in the Actions tab,
        # even though some items may have applied successfully.
        sys.exit(1)


if __name__ == "__main__":
    main()
