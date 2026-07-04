# AllAIDunia Directory Freshness Agent — Full Documentation

**Repo:** `AI-marketing-agency` (GitHub, private)
**Purpose:** Keep allaidunia.com's tool directory accurate automatically — removing dead tools, discovering new ones, and publishing changes to the live site — with human approval required before anything new goes live.

---

## 1. The Big Picture

Before this system, your tool data lived hardcoded inside `index.html` in three separate places, and any update meant manually editing HTML and re-uploading it to Hostinger.

Now, `tools.json` is the **single source of truth**. Everything else — your live site's grid, your chatbot's knowledge, your chatbot's pricing info — is *generated* from it automatically. You (or the automation) only ever edit `tools.json` indirectly, through the scripts below. **`index.html` should never be hand-edited again** — any manual change will get overwritten the next time automation runs.

```
tools.json  (source of truth)
     │
     ├──▶ check_links.py       (keeps it accurate — archives dead, revives recovered)
     ├──▶ discover_tools.py    (adds new candidates to pending.json for your review)
     ├──▶ apply_approvals.py   (moves your approved picks from pending.json into tools.json)
     │
     └──▶ regenerate_html.py   (rewrites index.html to match tools.json)
                │
                └──▶ FTP deploy step (pushes index.html to Hostinger — your live site)
```

---

## 2. The Files, and What Each One Does

| File | Type | What it does | Runs |
|---|---|---|---|
| `tools.json` | Data | The source of truth — all tools, their status, strikes, pricing | Updated by scripts, never by hand |
| `pending.json` | Data | New tool candidates awaiting your yes/no decision | Updated by discovery, edited by you |
| `rejected.json` | Data | Permanent blocklist — domains you've said no to, never resurface | Updated automatically on rejection |
| `check_links.py` | Script | Tests every tool's URL, applies the 3-strike archive/revive logic | Daily, automatic |
| `discover_tools.py` | Script | Searches Hacker News "Show HN" for new AI tools, filters and scores them | Every 3 days, automatic |
| `apply_approvals.py` | Script | Reads your decisions in `pending.json`, publishes approved tools | Whenever you commit a review |
| `regenerate_html.py` | Script | Rewrites `index.html`'s 3 data blocks from `tools.json` | After every `tools.json` change |
| `extract_tools.py` | Script | One-time setup tool that built the original `tools.json` | Already used, not needed again |
| `backfill_pricing.py` | Script | One-time tool that recovered pricing info into `tools.json` | Already used, not needed again |
| `check-links.yml` | Workflow | Schedules and runs the daily link check → regenerate → deploy chain | Daily, 3 AM UTC |
| `discover-tools.yml` | Workflow | Schedules the discovery run | Every 3 days |
| `apply-approvals.yml` | Workflow | Triggers the moment you commit changes to `pending.json` | On your commit |

---

## 3. How Each Automated Flow Works, Step by Step

### A. Daily Link Health Check (`check-links.yml`)

1. Runs automatically every day at 3 AM UTC (or manually via Actions → "Check Tool Links" → Run workflow)
2. `check_links.py` tests every tool's URL
3. Classifies each result:
   - **Alive** → resets strikes to 0, tool stays/returns to `active`
   - **Dead** (404, DNS failure, connection refused) → strike +1
   - **Inconclusive** (403/429/503/timeout — likely bot-blocking, not real failure) → **no action taken at all**, since we can't tell if it's really down
4. A tool hits **3 strikes** → moved to `archived` (removed from live site, never deleted from the data)
5. Archived tools are re-checked weekly — if back online, they auto-revive to `active`
6. `regenerate_html.py` rewrites `index.html` to match the updated `tools.json`
7. The new `index.html` is deployed to Hostinger via FTP
8. Both `tools.json` and `index.html` are committed back to GitHub

### B. Discovery (`discover-tools.yml`)

1. Runs every 3 days automatically (or manually via Actions → "Discover New Tools" → Run workflow)
2. `discover_tools.py` searches Hacker News "Show HN" posts from the last ~8 days
3. Filters for AI-related titles (word-boundary matched, so "email" or "quality" won't false-match on "ai")
4. Skips anything already in `tools.json`, already in `pending.json`, or on the `rejected.json` blocklist
5. Checks each candidate's link is alive
6. Survivors are added to `pending.json` with `"approved": null` — **nothing here ever touches the live site**

### C. Your Review (manual — the only human step)

1. Open `pending.json` in your GitHub repo, click the pencil/edit icon
2. For each candidate:
   - Set the correct `cat` (category) — the script can't know this
   - Rewrite `desc` into a clean one-liner — the script just captures the raw HN post title
   - Set `"approved": true` (publish it) or `"approved": false` (discard it)
   - Leave `"approved": null` if you're not ready to decide yet — it stays queued
3. Commit the change to `main`

### D. Applying Your Decisions (`apply-approvals.yml`)

1. Triggers automatically the instant you commit a change to `pending.json` — you never run this manually
2. `apply_approvals.py`:
   - `true` → tool moves into `tools.json` as `active`, removed from `pending.json`
   - `false` → discarded from `pending.json`, its domain permanently added to `rejected.json` so it never resurfaces
   - `null` → left untouched, still waiting
3. `regenerate_html.py` rewrites `index.html`
4. Deployed to Hostinger via FTP
5. `tools.json`, `pending.json`, `rejected.json`, and `index.html` all committed back to GitHub

---

## 4. What You Actually Need to Do (Ongoing)

This is the part that matters day-to-day — everything else runs itself.

| Task | Frequency | Where |
|---|---|---|
| **Review `pending.json`** — approve/reject new candidates | Whenever convenient — no urgency, nothing breaks if you wait weeks | GitHub → `pending.json` → edit → commit |
| Glance at flagged tools (optional) | Occasionally | `tools.json` → look for `"status": "flagged"` |
| Check Actions tab for failed runs (optional) | Occasionally | GitHub → Actions tab → look for red ❌ |

That's genuinely it. You do not need to:
- Manually check links
- Manually search for new tools
- Manually edit `index.html`
- Manually upload anything to Hostinger

---

## 5. GitHub Secrets in Use

Stored securely under **Settings → Secrets and variables → Actions** — never visible in code or chat:

| Secret | Purpose |
|---|---|
| `FTP_SERVER` | Hostinger FTP host |
| `FTP_USERNAME` | Hostinger FTP username |
| `FTP_PASSWORD` | Hostinger FTP password |

---

## 6. Known Limitations & Things to Keep an Eye On

- **Bot-blocked sites (403/429/503)** are never auto-archived, by design — this avoids falsely removing real tools like Claude or Midjourney that block automated checks. Occasionally this means a genuinely dead tool sitting behind such a block could go undetected. Low risk, but not zero.
- **DALL·E 3 and Phind** were sitting at strike 1/3 as of the last check — worth a glance if they hit 3. `labs.openai.com` in particular may be a stale URL since OpenAI has shifted DALL·E access into ChatGPT directly.
- **Discovery only covers Hacker News "Show HN"** — Product Hunt was deliberately excluded due to their commercial-use terms. This means some tools that launch elsewhere first won't be caught.
- **New tool descriptions and categories are never auto-filled well** — the script only has the raw HN post title to work with. Always review/rewrite these before approving.
- **`extract_tools.py` and `backfill_pricing.py`** were one-time setup tools — safe to ignore going forward, but keep them in the repo for reference/history.

---

## 7. If Something Breaks

1. **Go to the Actions tab** — a red ❌ tells you which workflow failed and on which step
2. Expand the failed step's log for the error message
3. Common past issues and fixes:
   - *"Push rejected"* — usually resolves itself via the built-in retry logic; if not, another run may be overlapping
   - *FileNotFoundError for index.html* — means `index.html` is missing from the repo root; re-upload it
   - *A real tool showing as FLAGGED for a bot-blocked reason* — check `check_links.py`'s `INCONCLUSIVE_CODES` list is still `{403, 429, 503}` and hasn't been accidentally changed

---

*This document reflects the system as of July 2026. If you add new workflows or scripts later, update this file to keep it accurate.*
