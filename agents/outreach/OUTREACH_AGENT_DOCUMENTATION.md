# Outreach Agent — Documentation (Non-Monetary Track)

**Repo location:** `agents/outreach/`
**Purpose:** Build real backlinks by letting AI tool companies know they're listed on AllAIDunia and asking for a link back — with a human approval step before anything is sent, same as every other publish-facing action in this system.

**Scope note:** this is the non-monetary track only. Per `PROJECT_OVERVIEW.md`, paid sponsorship outreach is intentionally deferred until Analytics Agent shows real traffic growth to back the pitch — pitching for money with near-zero visible traffic would undermine itself. `config.json` has a placeholder comment marking where that track plugs in later.

---

## 1. The Files

| File | What it does |
|---|---|
| `outreach_agent.py` | Finds new candidates from `tools.json`, best-effort discovers a contact point on the tool's own site, drafts a message, writes to `outreach_pending.json` |
| `apply_outreach.py` | Reads your approve/reject decisions, moves them into `outreach_log.json` (permanent — nothing gets contacted twice) |
| `config.json` | Site identity, rate limit (`max_per_run`), excluded domains |
| `outreach_pending.json` | Your review queue — same `approved: true/false/null` pattern as `pending.json` |
| `outreach_log.json` | Permanent record of every domain ever contacted/declined — the do-not-recontact list |
| `.github/workflows/outreach-agent.yml` | Weekly scheduled run + triggers `apply_outreach.py` on your commit |

## 2. How It Works

1. Loads active tools from `tools.json` (same source of truth as the Directory Freshness Agent)
2. Skips anything already in `outreach_log.json` (already contacted or declined) or already sitting in `outreach_pending.json`
3. Takes up to `max_per_run` candidates (default 5) — deliberately small, since simultaneous mass outreach reads as spam and some sites rate-limit or block bulk contact-form hits
4. For each candidate, checks the tool's own homepage and a few common paths (`/contact`, `/about`) for a `mailto:` link or a real contact page
5. Drafts a short, low-pressure message: "you're listed, here's the link, would you consider linking back, happy to reciprocate" — template-based by default, optionally polished by `gpt-4o-mini` if `OPENAI_API_KEY` is set (falls back silently to the template on any LLM error)
6. Writes everything to `outreach_pending.json`, following `AGENT_CONTRACT.md`'s `agent_meta` + `action_items` shape

## 3. Your Review Step (the only human step)

Same pattern as `pending.json`:
1. Open `outreach_pending.json`, look at each drafted item's `proposed_message`
2. Set `"approved": true` to send it, `"approved": false` to skip it permanently, or leave `null` to decide later
3. Commit — `apply_outreach.py` runs automatically

## 4. Important: Nothing Is Auto-Sent

There's no email-sending credential configured. Approving an item marks it `"approved_ready_to_send"` in `outreach_log.json` with the full drafted message — you copy it and send it yourself for now. This matches the project's standing rule that anything publishing or sending externally needs a human checkpoint, and specifically avoids scripting contact-form submissions, which risks violating individual sites' terms of service.

If you later want real auto-send for the `contact_method: "email"` items: add an SMTP or transactional-email API secret (e.g. Resend, Postmark) and a send step in `apply_outreach.py`. Contact-form-method items should probably always stay manual.

## 5. Known Limitations

- **Contact discovery is best-effort and will often come back `"unknown"`** — no email, no contact page found. Those items still get drafted (so you have the message ready) but you'll need to track the contact down yourself, e.g. via their social/LinkedIn.
- **No verification the backlink was actually added** — this agent doesn't check tool sites afterward for a returned link. Worth a manual spot-check occasionally; a future Analytics Agent extension could check referral traffic instead of scraping every site.
- **No monetization track yet** — see scope note above.
- **Rate limit is a flat number per run, not adaptive** — if you want faster throughput, raise `max_per_run` in `config.json`, but keep it modest to avoid pattern-matching as spam across many sites' contact forms/inboxes in a short window.

---

*Add this file to the project knowledge base alongside `AGENT_CONTRACT.md` and `PROJECT_OVERVIEW.md` once the agent is live, and update `PROJECT_OVERVIEW.md`'s Outreach Agent section to reflect BUILT status.*
