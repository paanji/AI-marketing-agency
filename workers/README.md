# Cloudflare Workers

Source code for every Cloudflare Worker this project runs. Deploys happen via
`wrangler deploy` from each Worker's own directory (or by pasting into the
Cloudflare dashboard) — GitHub Actions does NOT deploy these automatically.

**Why this directory exists:** Worker code that only lives in the Cloudflare
dashboard has no version control and no backup. Every Worker's source belongs
here, even if editing/deploying still happens elsewhere.

| Directory | Worker | Status |
|---|---|---|
| `prompt-guru/` | Prompt Guru question + synthesis API | Active |
| `chatbot/` | The site chatbot (GPT-4o-mini) | ⚠️ NOT YET COMMITTED — paste the dashboard source into `chatbot/worker.js` as backup |

Secrets (`OPENAI_API_KEY`, etc.) are set per-Worker via `wrangler secret put`
— they live in Cloudflare's secret store, never in this repo. `wrangler.toml`
files here contain only non-secret config (names, KV bindings, dates).
