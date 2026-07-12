# Social Media Agent — Full Documentation

**Location in repo:** `agents/social-media/`
**Purpose:** Draft platform-native social posts (Reddit, LinkedIn, Twitter/X, Instagram, Facebook, YouTube Shorts scripts) for human review and manual posting. Built to work for **any business** — a tools directory, an e-commerce shop, a restaurant, or a service business with no product catalog at all — not just AllAIDunia.

---

## 1. Why this generalizes beyond AllAIDunia

Two design choices make this reusable across completely different businesses:

1. **`business_profile` in config.json** controls the *words* the agent uses (what to call a single item, what to call the catalog) so phrasing adapts without touching code. A directory says "added to the directory"; a shop could say "added to the shop"; a service business skips this entirely (see #2).
2. **Three independent content sources**, and a business only needs to enable the ones that fit it:
   - **`new_catalog_items`** — for a business *with* a programmatic product/tool/menu file. Schema-agnostic: `field_mapping` in config tells the agent which JSON keys mean "name," "description," "URL," "status" — it never assumes any one client's exact field names.
   - **`catalog_milestones`** — celebrates the active-item count crossing a round number. Also catalog-driven.
   - **`manual_announcements`** — the **general-purpose source that works for literally any business**, including ones with zero catalog file. The owner just adds a plain `{"text": "...", "cta_url": "..."}` entry to `announcements.json` — a promo, a new service, an award, a milestone that isn't catalog-derived ("500 happy customers," "10 years in business"). No schema, no code change, no catalog file required.

**Tested:** a service business with `new_catalog_items` and `catalog_milestones` both disabled, running on `manual_announcements` alone, produces correct platform-native drafts with no code changes — only a config swap.

---

## 2. Video generation (new)

For platforms that need media (Instagram, Facebook, YouTube Shorts), the agent can now generate an actual short video automatically -- not just a `media_brief` describing what's needed.

**How it works:** if a content idea (a new catalog item, or a `manual_announcements` entry) points at a folder of the client's own photos, the agent stitches them into a Ken Burns-style pan/zoom slideshow, bakes in a short caption, and adds an AI voiceover (OpenAI TTS) reading the description/announcement text. If no photos exist yet for that item, video generation is silently skipped and the platform falls back to its `media_brief` (a text description of what to shoot) -- exactly like before. **Nothing ever blocks on missing media.**

**Tested end-to-end:** a "face wash launch" scenario -- a `manual_announcements` entry with two product photos in `media_assets/glow-fresh-launch/` -- correctly generated real .mp4 videos for Instagram, Facebook, and YouTube, while Reddit/LinkedIn/Twitter correctly stayed text-only (they don't require media).

**This is a pluggable provider**, not a hardcoded pipeline:
- `video_generator.py` exposes a `VIDEO_PROVIDERS` registry. `slideshow` (ffmpeg-based, client's own photos) is implemented now.
- An `ai_generated` provider (Runway/Pika/Kling/Sora/Veo -- true text-to-video) is scaffolded as a clear stub. Swapping to it later, for a client who wants it and is willing to pay per-second API costs, means implementing one function with the same signature and registering it -- **zero changes anywhere else in the pipeline.**
- Which provider is active is a single line in `config.json` (`video.provider`), so different clients could even run different providers simultaneously if you're managing multiple client configs.

**Where client photos go:** `agents/social-media/media_assets/<folder-name>/` -- one subfolder per item/announcement, containing jpg/png/webp files. Point a catalog item's `media_folder_field` (in `field_mapping`) or an announcement's `media_folder` key at that subfolder name.

**Where generated videos go:** `agents/social-media/generated_media/*.mp4` locally during a run. In GitHub Actions, these are uploaded as a workflow **artifact** (not committed to the repo, to avoid bloating it with binary files) -- `social_pending.json` includes a `video_review_url` linking straight to that run's Actions page when available.

**Cost:** effectively free. ffmpeg runs as ordinary GitHub Actions compute; OpenAI TTS is roughly $0.015/minute of audio -- for a weekly cadence across even several platforms, this is well under $1/month per client. See the cost discussion earlier in this project for the full breakdown, including what upgrading to true AI-generated footage would cost per client.

---

## 3. Why draft-only, on every platform, in v1

| Platform | Why it's draft-only for now |
|---|---|
| Reddit | Auto-posting risks account/shadow bans even with a real API — the human-review step matters *more* here, not less. |
| LinkedIn | Comparatively low-risk API. Most plausible candidate for an opt-in auto-publish phase later. |
| Twitter/X | Paid-tier gated, rate-limited; also a plausible later auto-publish candidate. |
| Instagram | Requires Meta Business verification, Graph API, and **an actual image/video asset** this agent doesn't generate. |
| Facebook | Same Meta Graph API + media-asset requirement as Instagram. |
| YouTube | There's no video file. Output is a Shorts *script* only — a human records/edits it. Not a "not yet," structurally impossible for a text-only agent. |

Every draft lands in `social_pending.json` with `"approved": null`. Nothing posts anywhere until you say so.

---

## 4. The Files

| File | What it is |
|---|---|
| `social_media_agent.py` | Core script — pulls content ideas from all enabled sources, drafts posts per enabled platform |
| `video_generator.py` | Generates slideshow videos from client photos (pluggable — `ai_generated` provider stubbed for later) |
| `apply_social_review.py` | Reads your `approved: true/false/null` decisions, sorts them |
| `media_assets/` | Client-supplied photos, organized in one subfolder per item/announcement |
| `generated_media/` | Output videos (not committed to the repo — uploaded as a GitHub Actions artifact instead) |
| `config.json` | **The reusability lever.** `business_profile` (words used), `content_sources` (which sources are on, and their field mappings), `platforms` (which platforms + their style rules) |
| `announcements.json` | Plain-text input for `manual_announcements` — the source usable by any business, including ones with no catalog file |
| `social_data.json` | Machine-readable output — `agent_meta` + `action_items`, per `AGENT_CONTRACT.md` |
| `social_pending.json` | Review queue — one entry per (content idea × enabled platform), `"approved": null` until you decide |
| `social_rejected.json` | Permanent blocklist — content angles you've said no to, keyed by deterministic ID |
| `ready_to_post.json` | Where approved drafts land — ready for you (or a future auto-publish step) to use |
| `.github/workflows/social-drafts.yml` | Schedules draft generation (weekly by default) |
| `.github/workflows/apply-social-review.yml` | Triggers the instant you commit a change to `social_pending.json` |

---

## 5. How It Works, Step by Step

### A. Draft generation (`social-drafts.yml`, weekly or manual)

1. Loads `config.json` — `business_profile`, enabled `content_sources`, enabled `platforms`
2. Pulls content ideas:
   - **New catalog items** — active items in the mapped catalog file added within `lookback_days` (if enabled)
   - **Catalog milestones** — active item count crossing a configured round number (if enabled)
   - **Manual announcements** — any new entry in `announcements.json` not already drafted (if enabled)
3. Drafts a post per idea × enabled platform, following that platform's `style`/`char_limit`/`hashtags` rules
4. Facts always come from the catalog file's mapped fields or the owner's own announcement text — **never invented by an LLM**
5. Each draft gets a deterministic ID (same idea + same platform = same ID every run), so re-runs never duplicate the queue
6. Writes `social_pending.json` and `social_data.json`

### B. Your review (manual — the only human step)

1. Open `social_pending.json`, read each draft, tweak wording if you like
2. Set `"approved": true` / `false` / leave `null`
3. Commit to `main`

### C. Applying decisions (`apply-social-review.yml`, on commit)

1. `true` → moved into `ready_to_post.json` with an `approved_date` stamp
2. `false` → discarded, ID added to `social_rejected.json`
3. `null` → left untouched
4. You (or, later, a trusted per-platform auto-publish step) post manually from `ready_to_post.json`

---

## 6. Onboarding a New Client — Two Scenarios

### Scenario A: client has a programmatic catalog (shop, directory, menu system)
1. Set `business_profile` (offering words, catalog label)
2. Point `content_sources.new_catalog_items.source_file` at their catalog JSON
3. Fill in `field_mapping` to match their actual field names — no code changes
4. Optionally enable `catalog_milestones` with a relevant `milestone_label`
5. Toggle `platforms` to what they actually use

### Scenario B: client has no catalog file at all (most service businesses)
1. Set `business_profile`
2. Disable `new_catalog_items` and `catalog_milestones`
3. Keep `manual_announcements` enabled — this is now their *only* content source
4. They (or you, on their behalf) maintain `announcements.json` directly — a line of plain text per thing worth announcing

Both scenarios use the exact same `social_media_agent.py` — zero code forking per client.

---

## 7. Known Limitations

**(Video-specific, in addition to the general limitations below)**
- **Images only, no video clips yet.** The slideshow provider reads jpg/png/webp from a media folder; if a client supplies short video clips instead of photos, those aren't stitched in yet.
- **Caption overlay is plain text, no custom fonts/branding yet.** Fine for a first pass; a client wanting on-brand fonts/colors would need a small enhancement to the `drawtext` filter in `video_generator.py`.
- **Voiceover uses a single fixed voice (`alloy`).** Config doesn't yet expose per-client voice selection, though OpenAI's TTS API supports several.
- **No music library shipped.** `background_music_path` defaults to `null`; add a royalty-free track path per client if background music is wanted.
- **`ai_generated` provider is a stub, not implemented.** Calling it raises a clear "not implemented yet" error rather than silently failing, so it's obvious this needs a deliberate build step (vendor choice, API key, cost sign-off) before use.



- **`date_added` isn't yet a guaranteed field on AllAIDunia's `tools.json`.** If missing, the "new catalog items" source can't filter by recency and relies on the pending/rejected files to avoid re-announcing. Recommended fix: add it to `apply_approvals.py`'s insertion step.
- **Instagram/Facebook drafts include a `media_brief`, not an actual image.** No media generation in this agent. Natural integration point if that's added upstream later.
- **YouTube output is a script, not a video** — no auto-publish path exists here structurally.
- **Hashtags are a small deterministic pool**, not LLM-generated or trend-aware — intentionally minimal to avoid spammy tag-stuffing.
- **`manual_announcements` passes the owner's text through with only light platform framing** — it does not rewrite substance or verify factual claims. Whatever the owner writes is what gets drafted; review still matters.
- **LLM phrasing variation is scaffolded in `config.json`'s `llm` block but not yet wired in** — v1 is fully deterministic templates, keeping it free and hallucination-free. Add the LLM call only if template repetition becomes a real problem.
- **No per-subreddit rule-checking** — `target_subreddits` in config is a reference list only; check each subreddit's self-promotion rules manually before posting.

---

## 8. What You Actually Need to Do

- **Review `social_pending.json`** whenever it runs
- **Post approved items from `ready_to_post.json`** yourself, respecting each platform's norms
- **For AllAIDunia specifically:** add `date_added` to the Directory Freshness Agent's insertion step when convenient
- **For a new client with no catalog:** just maintain `announcements.json` — nothing else needed

---

*This document reflects the Social Media Agent as of July 2026, generalized for multi-client reuse across both catalog-driven and announcement-only businesses. Update it if content sources or the auto-publish stance change.*
