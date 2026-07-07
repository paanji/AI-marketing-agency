# SEO Agent — Full Documentation

**Location in repo:** `agents/seo/`
**Purpose:** Automatically checks AllAIDunia's search visibility — both traditional Google ranking and readiness for AI answer engines (ChatGPT, Perplexity, Gemini) — and turns findings into a prioritized, plain-English list of fixes.

---

## 1. The Files

| File | What it is |
|---|---|
| `seo_agent.py` | The script itself — all the logic lives here |
| `config.json` | Every threshold and setting, parameterized so this agent can be reused for a different site/client by editing this file alone — no code changes needed |
| `seo_report.md` | Human-readable output — **this is the one you actually read** |
| `seo_data.json` | Machine-readable output — for future agents (e.g. Content Agent) to consume programmatically |
| `seo_history.json` | Running log of key metrics per run — one entry per day, never overwritten. Powers the "Historical Trend" section once 2+ snapshots exist. |
| `.github/workflows/seo-report.yml` | Schedules the agent to run weekly (Tuesdays) and can be triggered manually |

---

## 2. What Happens When It Runs — Step by Step

1. **Authenticates** with Google Search Console using a service account credential (stored as the `GSC_SERVICE_ACCOUNT_JSON` GitHub secret)
2. **Pulls performance data** — the last 28 days of search queries and page-level clicks/impressions, compared against the prior 28 days
3. **Fetches the sitemap** (`sitemap_url` in config) and gets the list of real pages to audit
4. **For each page, runs a full audit** (see section 3 below for every individual check)
5. **Checks site-wide signals once** — `robots.txt` (AI crawler access) and `llms.txt` presence
6. **Combines everything into prioritized action items** — each tagged with a priority (high/medium/low), a category, and which agent should act on it
7. **Writes two output files** — `seo_report.md` for you, `seo_data.json` for future automation
8. **Commits both files back to the repo** automatically

Total runtime: roughly 1-3 minutes, depending on how many pages need PageSpeed checks (the slowest part).

---

## 3. Every Check It Performs, and Why

### Search performance (from Search Console data)
- **Quick-win queries** — queries ranking positions 5-15: close to page 1, worth a small push
- **Low CTR queries** — getting real impressions but rarely clicked: usually a weak title/meta description
- **Declining pages** — lost 25%+ of clicks compared to the prior period
- **Top queries by visibility** — a baseline snapshot, useful even before anything qualifies as a "quick win"

### On-page SEO (per page)
- **Title length** (30-60 characters) — too short is vague, too long gets truncated by Google
- **Meta description length** (70-160 characters) — same idea
- **H1 heading** — flags zero or multiple H1 tags
- **Image alt text** — flags any image with none
- **Thin content** — flags pages under ~150 words

### AI Search Readiness (GEO/AEO)
- **AI crawler access** — checks `robots.txt` isn't blocking GPTBot, ClaudeBot, PerplexityBot, Google-Extended, and others
- **Schema.org structured data** — flags pages with no structured data at all; ideal types for a directory are `ItemList`/`SoftwareApplication`
- **Content extractability** — flags pages with no lists/tables, or paragraphs averaging over 150 words (harder for AI systems to quote cleanly)
- **`llms.txt`** — flags if this emerging AI-focused standard file is missing

### Technical / crawlability
- **JS-rendering blindspot** — checks whether a critical content container (e.g. `#tools-grid`) actually has content in the *raw* HTML, or is empty and only filled in by JavaScript afterward. This was the single biggest real finding so far — crawlers that don't execute JavaScript were seeing an empty page. **Fixed** in `regenerate_html.py` for the homepage (bakes real content in at build time, keeps the JS for interactivity), and via a one-off manual fix for `video-ai-tools.html` (which has its own separate embedded tool data, not yet part of the automated pipeline).
- **Google indexing status** — uses the URL Inspection API to check whether a page is *actually indexed*, not just how it ranks. A page can be perfectly optimized and still get zero traffic if it isn't indexed at all.
- **`noindex` meta tag** — checks if the page is explicitly telling Google not to index it
- **Canonical tag** — checks it exists and points to the correct domain (this specifically caught the www/non-www mismatch this site actually had)
- **Page speed / Core Web Vitals** — via Google's PageSpeed Insights API (mobile), checks the Lighthouse performance score, LCP, and CLS. Limited to the first few pages (`max_pages_for_pagespeed` in config) since each check takes 10-30+ seconds. Uses a 60s timeout with one retry, since real Lighthouse audits often exceed 30 seconds.
- **Open Graph tags** — checks `og:title`, `og:description`, `og:image` are present, affecting how links look when shared on social/messaging apps

### Actually drafting fixes, not just diagnosing (the biggest capability upgrade)
For title and meta description issues, the agent now produces a real, ready-to-use replacement — not just a description of the problem:
- **Deterministic first** — word-boundary truncation for overlong text, or a keyword-template fix when real Search Console query data exists for that page (via a page+query correlated Search Console call). Free, instant, no hallucination risk.
- **LLM fallback only when needed** — if deterministic logic can't confidently produce a fix (e.g. a title is completely missing, or too short with no keyword data available), it calls OpenAI (`gpt-4o-mini` by default) with a bounded generate-check-retry loop: draft, check it actually fits the character limit, and if not, regenerate with specific feedback about exactly how much to cut. Stops after a fixed number of attempts either way — never loops indefinitely, and returns nothing rather than publishing something broken if it never fits.
- **Schema.org markup and `llms.txt` are always deterministic** — generated directly from `tools.json`'s real data, never via LLM, since there's no reason to risk hallucination on structured data we already have accurately.

The actual fix content is stored in each action item's `proposed_fix` field (see `AGENT_CONTRACT.md`). Long content (full schema JSON, full `llms.txt`) is kept out of the human-readable `seo_report.md` — it only shows a short pointer to `seo_data.json`, where the future Content Agent will read it from directly.

---

## 4. Understanding the Report

`seo_report.md` is organized as:

1. **Recommended Actions** — grouped by High / Medium / Low priority, this is the main section to read
2. **Overview** — total clicks, impressions, average position, overall CTR for the period
3. **AI Search Readiness (GEO/AEO)** — site-wide crawler/schema/llms.txt findings
4. **On-Page Audit** — a table, one row per page, showing indexing status and the raw numbers
5. **Top Queries by Visibility** — your top queries by impressions, regardless of ranking position

Each recommendation includes a **suggested owner**:
- **`content_agent`** — will be actioned automatically once that agent is built (titles, meta descriptions, schema markup, `llms.txt`)
- **`manual`** — no agent handles this yet; requires a person. This includes things like fixing `robots.txt`, `.htaccess` redirects, page speed optimization, and canonical tag fixes — architecture-level changes that carry real risk if automated carelessly.

---

## 5. The Data Contract (for future agents)

`seo_data.json` follows the standard shape defined in `AGENT_CONTRACT.md` at the repo root:
- An `agent_meta` envelope (agent name, schema version, run status, one-line summary)
- An `action_items` list, where each item has a **stable, deterministic ID** — the same underlying issue produces the same ID every run, so a future agent (or a human) can track "have I already handled this one?" without needing a separate database.

---

## 6. Secrets Used

| Secret | Purpose |
|---|---|
| `GSC_SERVICE_ACCOUNT_JSON` | Authenticates with Search Console (analytics + URL Inspection) |
| `PAGESPEED_API_KEY` | Gives page speed checks their own quota instead of sharing Google's tiny anonymous rate limit |
| `OPENAI_API_KEY` | Powers title/meta description drafting when deterministic logic can't confidently produce a fix. Reuses the same key as the site's chatbot, added separately here since Cloudflare and GitHub Actions secrets don't share storage. |

Used only within the workflow run and never committed to the repo.

---

## 7. Known Limitations

- **Thresholds are fixed defaults, not self-tuning** — e.g. "title should be 30-60 characters" is a reasonable industry convention, not something the agent learns and adjusts based on this specific site's actual results over time.
- **No competitor analysis** — deliberately skipped; real competitor tools (Ahrefs, Moz) require paid APIs costing hundreds/month.
- **No actual AI-citation testing** — the agent checks whether AI crawlers *can* access the site, but doesn't test whether ChatGPT/Perplexity actually mention AllAIDunia in real answers (that would need separate paid API calls per test query).
- **PageSpeed checks are capped** — only the first few pages (config-controlled) get checked per run, to keep runtime reasonable as the site grows.
- **`video-ai-tools.html` is outside the automated pipeline** — it has its own separate embedded tool array, fixed manually once for the JS-rendering issue. If its tool list changes, it won't update automatically the way the homepage does.
- **Deterministic title/meta fixes can read awkwardly** — word-boundary truncation guarantees the length fits, but doesn't understand when a cut lands mid-thought (e.g. "...60+ Free" instead of finishing "AI Tools"). Still valid and under the limit, just occasionally less polished than an LLM rewrite would be.

---

## 8. What You Actually Need to Do

- **Read `seo_report.md`** whenever it runs (weekly, or trigger manually from the Actions tab)
- **Act on `manual`-tagged items yourself** for now — these are the technical/architecture fixes with no agent to hand them to yet
- **`content_agent`-tagged items** will start resolving automatically once that agent is built

---

*This document reflects the SEO Agent as of July 2026. Update it if the agent's checks or output shape change.*
