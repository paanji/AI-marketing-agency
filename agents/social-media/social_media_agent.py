"""
Social Media Agent
-------------------
Reads content ideas from configured sources and drafts platform-native posts
for every enabled platform, for human review. Never posts anything itself,
on any platform, in v1 -- see config.json's `auto_publish_supported` /
`auto_publish_notes` per platform for the reasoning.

Built to be business-agnostic:
  - `business_profile` in config.json controls the words used (offering
    type, what to call the catalog) so the same code works for a tools
    directory, an e-commerce shop, a restaurant, or a service business.
  - `new_catalog_items` / `catalog_milestones` sources are schema-agnostic:
    they read whatever field names config.json's `field_mapping` points at,
    never assuming any one client's exact JSON shape.
  - `manual_announcements` is the source for businesses with NO
    programmatic catalog at all (a plumber, a consultant, a salon) -- the
    owner just adds a plain text entry, no schema required.

Outputs:
  - social_data.json     (AGENT_CONTRACT.md-compliant: agent_meta + action_items)
  - social_pending.json  (human review queue, "approved": null until reviewed)
  - social_rejected.json (blocklist -- content angles you've said no to, never resurface)
"""

import json
import hashlib
import os
from datetime import datetime, timedelta, timezone

from video_generator import VIDEO_PROVIDERS, VideoGenerationError

AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(AGENT_DIR))  # agents/social-media -> agents -> repo root


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(path, default=None):
    if not os.path.exists(path):
        return default if default is not None else {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def resolve_path(relative_path):
    """content_sources.*.source_file paths in config are given relative to
    the repo root (e.g. 'agents/directory-freshness/tools.json'), matching
    how they're written in config.json for readability."""
    return os.path.join(REPO_ROOT, relative_path)


def deterministic_id(*parts):
    """Same underlying content angle + platform always produces the same ID,
    per AGENT_CONTRACT.md, so re-runs don't duplicate queue entries."""
    raw = "|".join(str(p) for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:10]


def apply_hashtags(draft, platform_cfg, extra_tags=None):
    if platform_cfg.get("hashtags"):
        pool = (extra_tags or []) + ["#SmallBusiness"]
        draft["hashtags"] = pool[: platform_cfg.get("hashtag_count", 3)]


def check_length(draft, platform, platform_cfg):
    limit = platform_cfg.get("char_limit")
    if limit and len(draft.get("body", "")) > limit:
        draft["truncation_warning"] = (
            f"Draft body is {len(draft['body'])} chars, over the {limit} char "
            f"limit for {platform}. Needs manual trimming before use."
        )


def try_generate_video(media_folder_name, item_id, caption_text, voiceover_text, video_cfg, config):
    """Attempts real video generation if a client media folder exists for
    this content idea. Returns (video_path, review_url) on success, or
    (None, None) if there's no media folder yet -- the normal, expected
    case for a client who hasn't uploaded photos -- and must never raise
    up into the caller."""
    if not media_folder_name:
        return None, None

    media_dir = os.path.join(
        resolve_path(video_cfg.get("media_assets_dir", "agents/social-media/media_assets")),
        media_folder_name,
    )
    if not os.path.isdir(media_dir):
        return None, None

    output_dir = resolve_path(video_cfg.get("output_dir", "agents/social-media/generated_media"))
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{item_id}.mp4")

    provider_name = video_cfg.get("provider", "slideshow")
    provider_fn = VIDEO_PROVIDERS.get(provider_name)
    if provider_fn is None:
        return None, None

    try:
        provider_fn(media_dir, output_path, caption_text, voiceover_text, video_cfg, config)
    except Exception:
        # Video generation is a bonus, not a requirement -- any failure
        # here (bad images, ffmpeg error, unimplemented provider) falls
        # back to the text-only draft + media_brief instead of blocking
        # the item entirely.
        return None, None

    repo = os.environ.get("GITHUB_REPOSITORY")
    run_id = os.environ.get("GITHUB_RUN_ID")
    review_url = f"https://github.com/{repo}/actions/runs/{run_id}" if repo and run_id else None
    return output_path, review_url


# ---------------------------------------------------------------------------
# Source 1: new_catalog_items (schema-agnostic via field_mapping)
# ---------------------------------------------------------------------------

def get_recent_catalog_items(source_cfg):
    fm = source_cfg["field_mapping"]
    data = load_json(resolve_path(source_cfg["source_file"]), default={})
    items = data.get(fm["list_key"], [])

    cutoff = datetime.now(timezone.utc) - timedelta(days=source_cfg.get("lookback_days", 7))
    results = []
    for item in items:
        if fm.get("status_field") and item.get(fm["status_field"]) != fm.get("status_active_value"):
            continue
        date_field = fm.get("date_added_field")
        if date_field and item.get(date_field):
            try:
                added_dt = datetime.fromisoformat(item[date_field]).replace(tzinfo=timezone.utc)
                if added_dt < cutoff:
                    continue
            except ValueError:
                pass  # malformed date -- fall through, still consider it
        media_field = fm.get("media_folder_field")
        results.append({
            "name": item.get(fm.get("name_field", "name"), "This item"),
            "desc": item.get(fm.get("description_field", "desc"), ""),
            "url": item.get(fm.get("url_field", "url"), ""),
            "media_folder": item.get(media_field) if media_field else None,
        })
    return results


def get_catalog_milestone(source_cfg):
    """Deterministic, no LLM. Fires only when the active-item count exactly
    matches a configured interval."""
    fm = source_cfg["field_mapping"]
    data = load_json(resolve_path(source_cfg["source_file"]), default={})
    items = data.get(fm["list_key"], [])
    active_count = sum(1 for i in items if i.get(fm.get("status_field")) == fm.get("status_active_value"))
    if active_count in source_cfg.get("milestone_intervals", []):
        return active_count
    return None


# ---------------------------------------------------------------------------
# Source 2: manual_announcements (no schema -- any business)
# ---------------------------------------------------------------------------

def get_new_announcements(source_cfg, already_seen_texts):
    """Reads a plain list the owner maintains directly:
    [{"text": "...", "cta_url": "https://...", "date": "2026-07-01"}, ...]
    Only `text` is required. No other structure assumed."""
    data = load_json(resolve_path(source_cfg["source_file"]), default={"announcements": []})
    results = []
    for entry in data.get("announcements", []):
        text = entry.get("text", "").strip()
        if not text or text in already_seen_texts:
            continue
        results.append(entry)
    return results


# ---------------------------------------------------------------------------
# Draft generation (deterministic-first; facts only ever come from the
# catalog file or the owner's own announcement text, never invented)
# ---------------------------------------------------------------------------

def draft_catalog_item_post(item, platform, platform_cfg, profile):
    name, desc, url = item["name"], item["desc"], item["url"]
    catalog_label = profile.get("catalog_label", "our lineup")
    content_type = platform_cfg["content_type"]

    if content_type == "text_post":
        if platform == "reddit":
            body = f"Came across {name} recently -- {desc} Worth a look: {url}".strip()
        elif platform == "twitter":
            body = f"New: {name}\n{desc}\n{url}".strip()
        else:
            body = f"Just added {name} to {catalog_label}.\n\n{desc}\n\nCheck it out: {url}".strip()
    elif content_type == "caption_plus_media_brief":
        body = f"{name} 👀\n\n{desc}\n\nLink in bio."
    elif content_type == "shorts_script":
        body = (
            f"[HOOK - 0:00-0:02] \"Check out {name}...\"\n"
            f"[0:02-0:15] Show {name}, voiceover explaining: {desc}\n"
            f"[0:15-0:25] Quick example / demo\n"
            f"[0:25-0:30] \"Link in bio / description\" -- on-screen text: '{name}'"
        )
    else:
        body = f"{name}: {desc} {url}".strip()

    draft = {"platform": platform, "content_type": content_type, "body": body}
    if content_type == "caption_plus_media_brief":
        draft["media_brief"] = (
            f"Need: 1 clean, authentic photo or short clip related to {name}. "
            f"No stock photos -- authenticity matters more than polish here."
        )
    if content_type == "shorts_script":
        draft["title"] = f"{name}"
        draft["description"] = f"{desc} Learn more via the link below."

    apply_hashtags(draft, platform_cfg, extra_tags=["#New"])
    check_length(draft, platform, platform_cfg)
    return draft


def draft_milestone_post(count, milestone_label, platform, platform_cfg, client_name):
    content_type = platform_cfg["content_type"]
    if content_type == "text_post":
        body = f"{client_name} just hit {count} {milestone_label}. Thanks for following along."
    elif content_type == "caption_plus_media_brief":
        body = f"🎉 {count} {milestone_label}.\n\n{client_name} just hit a milestone."
    elif content_type == "shorts_script":
        body = (
            f"[HOOK] \"We just hit {count} {milestone_label}.\"\n"
            f"[BODY] Quick montage/graphic celebrating the number.\n"
            f"[CTA] \"Link in bio to learn more.\""
        )
    else:
        body = f"{client_name}: {count} {milestone_label}."

    draft = {"platform": platform, "content_type": content_type, "body": body}
    if content_type == "caption_plus_media_brief":
        draft["media_brief"] = f"Need: a simple graphic showing '{count} {milestone_label}'."
    apply_hashtags(draft, platform_cfg, extra_tags=["#Milestone"])
    check_length(draft, platform, platform_cfg)
    return draft


def draft_announcement_post(entry, platform, platform_cfg):
    """Passes the owner's own text through with light platform shaping.
    Never rewrites the substance -- only adds platform-appropriate framing
    (link, hashtags, script structure)."""
    text = entry["text"].strip()
    cta_url = entry.get("cta_url", "")
    content_type = platform_cfg["content_type"]

    if content_type == "text_post":
        body = f"{text}\n{cta_url}".strip()
    elif content_type == "caption_plus_media_brief":
        body = f"{text}\n\n{'Link in bio.' if cta_url else ''}".strip()
    elif content_type == "shorts_script":
        body = (
            f"[HOOK] \"{text}\"\n"
            f"[BODY] Show relevant footage/photos while restating the key point.\n"
            f"[CTA] \"{'Link in bio / description' if cta_url else 'Reach out to learn more'}\""
        )
    else:
        body = text

    draft = {"platform": platform, "content_type": content_type, "body": body}
    if content_type == "caption_plus_media_brief":
        draft["media_brief"] = "Need: a photo/clip that genuinely matches this announcement -- no stock imagery."
    if content_type == "shorts_script":
        draft["title"] = text[:80]
        draft["description"] = text

    apply_hashtags(draft, platform_cfg)
    check_length(draft, platform, platform_cfg)
    return draft


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(config_path=None):
    config_path = config_path or os.path.join(AGENT_DIR, "config.json")
    config = load_json(config_path)

    client_name = config.get("client_name", "the business")
    profile = config.get("business_profile", {})
    sources_cfg = config.get("content_sources", {})
    platforms_cfg = config.get("platforms", {})

    pending_path = os.path.join(AGENT_DIR, "social_pending.json")
    rejected_path = os.path.join(AGENT_DIR, "social_rejected.json")
    data_path = os.path.join(AGENT_DIR, "social_data.json")

    pending = load_json(pending_path, default={"items": []})
    rejected = load_json(rejected_path, default={"blocked_ids": []})

    existing_ids = {item["id"] for item in pending.get("items", [])}
    blocked_ids = set(rejected.get("blocked_ids", []))
    already_seen_texts = {
        item["announcement_text"] for item in pending.get("items", [])
        if item.get("source") == "manual_announcement"
    }

    action_items = []
    new_pending_items = []
    video_cfg = config.get("video", {})
    source_errors = []

    enabled_platforms = {p: c for p, c in platforms_cfg.items() if c.get("enabled")}

    # --- Source 1: new catalog items ---
    nc_cfg = sources_cfg.get("new_catalog_items", {})
    if nc_cfg.get("enabled"):
        try:
            for item in get_recent_catalog_items(nc_cfg):
                for platform, platform_cfg in enabled_platforms.items():
                    item_id = deterministic_id("catalog_item", item["name"], platform)
                    if item_id in existing_ids or item_id in blocked_ids:
                        continue
                    draft = draft_catalog_item_post(item, platform, platform_cfg, profile)
                    if platform_cfg.get("requires_media"):
                        video_path, review_url = try_generate_video(
                            item.get("media_folder"), item_id,
                            caption_text=draft["body"], voiceover_text=item["desc"],
                            video_cfg=video_cfg, config=config,
                        )
                        if video_path:
                            draft["video_generated"] = True
                            draft["video_path"] = os.path.relpath(video_path, REPO_ROOT)
                            if review_url:
                                draft["video_review_url"] = review_url
                    new_pending_items.append({
                        "id": item_id, "source": "new_catalog_item",
                        "item_name": item["name"], "draft": draft, "approved": None,
                    })
                    action_items.append({
                        "id": item_id,
                        "description": f"Draft {platform} post announcing '{item['name']}'",
                        "priority": "low", "category": "social_content",
                        "suggested_agent": "manual", "page": item["url"],
                    })
        except Exception as e:
            source_errors.append(f"new_catalog_items: {e}")

    # --- Source 2: catalog milestones ---
    cm_cfg = sources_cfg.get("catalog_milestones", {})
    if cm_cfg.get("enabled"):
        try:
            milestone = get_catalog_milestone(cm_cfg)
            if milestone:
                label = cm_cfg.get("milestone_label", "items")
                for platform, platform_cfg in enabled_platforms.items():
                    item_id = deterministic_id("milestone", milestone, label, platform)
                    if item_id in existing_ids or item_id in blocked_ids:
                        continue
                    draft = draft_milestone_post(milestone, label, platform, platform_cfg, client_name)
                    new_pending_items.append({
                        "id": item_id, "source": "catalog_milestone",
                        "milestone_count": milestone, "draft": draft, "approved": None,
                    })
                    action_items.append({
                        "id": item_id,
                        "description": f"Draft {platform} post celebrating {milestone} {label}",
                        "priority": "low", "category": "social_content",
                        "suggested_agent": "manual", "page": None,
                    })
        except Exception as e:
            source_errors.append(f"catalog_milestones: {e}")

    # --- Source 3: manual announcements (any business, no schema) ---
    ma_cfg = sources_cfg.get("manual_announcements", {})
    if ma_cfg.get("enabled"):
        try:
            for entry in get_new_announcements(ma_cfg, already_seen_texts):
                text = entry["text"].strip()
                for platform, platform_cfg in enabled_platforms.items():
                    item_id = deterministic_id("announcement", text, platform)
                    if item_id in existing_ids or item_id in blocked_ids:
                        continue
                    draft = draft_announcement_post(entry, platform, platform_cfg)
                    if platform_cfg.get("requires_media"):
                        video_path, review_url = try_generate_video(
                            entry.get("media_folder"), item_id,
                            caption_text=draft["body"], voiceover_text=text,
                            video_cfg=video_cfg, config=config,
                        )
                        if video_path:
                            draft["video_generated"] = True
                            draft["video_path"] = os.path.relpath(video_path, REPO_ROOT)
                            if review_url:
                                draft["video_review_url"] = review_url
                    new_pending_items.append({
                        "id": item_id, "source": "manual_announcement",
                        "announcement_text": text, "draft": draft, "approved": None,
                    })
                    action_items.append({
                        "id": item_id,
                        "description": f"Draft {platform} post for announcement: \"{text[:60]}\"",
                        "priority": "low", "category": "social_content",
                        "suggested_agent": "manual", "page": entry.get("cta_url"),
                    })
        except Exception as e:
            source_errors.append(f"manual_announcements: {e}")

    # Always write the pending/data files, no matter what happened above --
    # a broken source should never prevent the git commit step from having
    # something to commit, and should never silently vanish either.
    pending["items"] = pending.get("items", []) + new_pending_items
    save_json(pending_path, pending)

    if source_errors:
        status = "success" if new_pending_items or pending.get("items") else "failed"
        summary = (
            f"{len(new_pending_items)} new draft(s) queued. "
            f"{len(source_errors)} source(s) had errors and were skipped: {'; '.join(source_errors)}"
        )
    else:
        status = "success"
        summary = f"{len(new_pending_items)} new draft(s) queued for review across enabled platforms."

    output = {
        "agent_meta": {
            "agent_name": "social_media_agent",
            "schema_version": "1.1",
            "run_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "status": status,
            "summary": summary,
        },
        "action_items": action_items,
    }
    save_json(data_path, output)
    print(summary)
    return output


if __name__ == "__main__":
    run()
