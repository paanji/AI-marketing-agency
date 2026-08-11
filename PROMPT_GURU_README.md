# Prompt Guru — Setup Guide

## Repo layout (what goes where)

```
/prompt-guru.html                      ← site page (root, like other pages)
/prompt_formats.json                   ← served config the Worker reads at runtime
/workers/prompt-guru/worker.js         ← Worker source
/workers/prompt-guru/wrangler.toml     ← Worker deploy config
/workers/README.md                     ← explains the workers/ convention
```

Site files stay at root because they must be deployed to Hostinger and served
publicly. Worker code gets its own directory because it deploys via wrangler,
not FTPS — a completely separate pipeline.

## Deploy order

### 1. Commit everything
Upload all 5 files to the repo in the layout above (GitHub → Add file →
Upload files preserves folder structure if you drag the `workers` folder in).

### 2. Whitelist the two site files
In `.github/workflows/deploy-site.yml`, add to the exclude block:

```
            !prompt-guru.html
            !prompt_formats.json
```

Run **Deploy Site (Full)** from the Actions tab, then confirm
`https://www.allaidunia.com/prompt_formats.json` loads in a browser —
the Worker depends on it.

### 3. Deploy the Worker
From `workers/prompt-guru/` locally (needs wrangler CLI):

```bash
wrangler kv:namespace create GURU_KV      # paste the printed id into wrangler.toml
wrangler secret put OPENAI_API_KEY        # same key value as the chatbot
wrangler deploy
```

Copy the deployed URL (e.g. `https://prompt-guru.YOUR-SUBDOMAIN.workers.dev`).

### 4. Point the page at the Worker
In `prompt-guru.html`, one line near the top of the script:

```js
var API_BASE = "https://prompt-guru.YOUR-SUBDOMAIN.workers.dev";
```

Replace, commit, re-run Deploy Site (Full).

### 5. Add it to the directory inventory
Add this entry to `agents/directory-freshness/tools.json` (NOT index.html —
let `regenerate_html.py` bake the grid on its next run):

```json
{
  "id": "prompt-guru",
  "name": "Prompt Guru",
  "cat": "Productivity",
  "url": "https://www.allaidunia.com/prompt-guru.html",
  "color": "#7c6cfa",
  "text": "#fff",
  "letter": "P",
  "desc": "Built by AllAIDunia — answers a few questions, then writes the perfect prompt for your AI tool",
  "isNew": true,
  "featured": true,
  "status": "active",
  "consecutive_failures": 0,
  "last_checked": "2026-08-10",
  "last_working": "2026-08-10",
  "archived_date": null,
  "source": "manual",
  "pricing": "FREE"
}
```

### 6. (Recommended) Back up the chatbot Worker
Paste the existing chatbot Worker's source from the Cloudflare dashboard into
`workers/chatbot/worker.js` — it currently has no version control at all.

## Costs & limits
- 2 gpt-4o-mini calls per completed session
- Rate limit: 20 calls/IP/day via KV (tune `DAILY_LIMIT_PER_IP` in worker.js)
- `prompt_formats.json` edits take up to 10 min to reach the Worker (edge cache)

## Known limitations (v1)
- Image + Video categories only — expand after usage proves demand
- No session persistence across refresh (deliberate — keeps it fast/cheap)
- Adding a new tool = edit `prompt_formats.json` (rules) + the `TOOLS` object
  in `prompt-guru.html` (picker chip)
- Once in tools.json, `check_links.py` will link-check the page daily like
  any other tool — fine, just know it's on the strike path if the page 404s
