# Agent Output Contract

This defines the standard shape every agent in this system writes its structured
output in. The goal: any future agent (Content Agent, Outreach Agent, a manager/CEO
agent) can read another agent's output file and know exactly what to expect,
without reading that agent's source code first.

**Every agent's `*_data.json` output must follow this shape.** If you build a new
agent, follow this contract — don't invent a new one-off shape per agent.

---

## Top-level envelope: `agent_meta`

Every agent's output file must include this block, unchanged in structure:

```json
"agent_meta": {
  "agent_name": "seo_agent",
  "schema_version": "1.0",
  "run_date": "2026-07-05",
  "status": "success",
  "summary": "12 action items found (3 high priority)"
}
```

- **agent_name**: stable identifier for the agent (snake_case)
- **schema_version**: bump this if you change the shape of this agent's output in a
  way that could break a consumer (e.g. renaming a field, changing a type).
  Consumers should check this before assuming a shape.
- **status**: `"success"` or `"failed"`. On failure, an agent should still write
  this envelope (with whatever else it can) rather than just crashing silently —
  a consumer or future manager agent needs to be able to see "X agent failed"
  rather than finding a stale or missing file with no explanation.
- **summary**: one human-readable sentence, for quick display in a future
  aggregated dashboard without needing to parse the rest of the file.

## Action items: `action_items`

Any agent that produces actionable suggestions (not just raw data) should output
them as a list under this key, each item shaped like:

```json
{
  "id": "f41d6d992f",
  "description": "Meta description is 179 characters — will get truncated.",
  "priority": "medium",
  "category": "on_page_seo",
  "suggested_agent": "content_agent",
  "page": "https://www.allaidunia.com/",
  "proposed_fix": "AllAIDunia — free directory of 60+ AI tools, covering chat, image, video, and code assistants. Updated weekly."
}
```

- **id**: a short, **deterministic** hash derived from the issue's own content
  (not random, not run-dependent). The same underlying issue must produce the
  same ID every run, so a consuming agent (or a human) can track "have I already
  handled this one?" across runs without needing a database. If the underlying
  issue changes or resolves, its ID naturally changes or disappears.
- **priority**: `"high"` | `"medium"` | `"low"`
- **category**: free-text but should be consistent within an agent (e.g. this
  agent uses: `technical`, `on_page_seo`, `ai_search_geo`, `content_opportunity`,
  `accessibility`)
- **suggested_agent**: which agent should act on this. Use `"manual"` if no
  agent capable of handling it exists yet — this is an honest signal, not a
  placeholder to hide. A future agent should filter for its own name here
  before acting on anything.
- **page**: the specific URL this relates to, or `null` if it's site-wide.
- **proposed_fix**: the ACTUAL drafted replacement content where one could be
  produced — a real new title, a real meta description, real schema.org JSON,
  real llms.txt content — not just a description of the problem. `null` if no
  concrete fix could be confidently produced (e.g. the issue genuinely needs
  human judgment, like adding an image, or an LLM call failed). **Prefer
  deterministic generation over LLM calls wherever the fix has a clear,
  reliable rule** (e.g. truncating an overlong title at a word boundary) —
  only fall back to an LLM when real judgment/creativity is required and no
  deterministic rule can produce a confident answer. This keeps costs down
  and avoids hallucination risk on the cases that don't need it.

## Everything else in the file is agent-specific

Beyond `agent_meta` and `action_items`, an agent can include whatever other data
is useful to it or future consumers (e.g. `seo_agent`'s `overview`, `top_queries`,
`page_audits`, `geo_checks`). There's no need to force unrelated data into a
common shape — only the envelope and action items need to be standardized.

## Current agents following this contract

| Agent | Output file | Status |
|---|---|---|
| seo_agent | `agents/seo/seo_data.json` | ✅ follows contract (v1.0) |
| directory-freshness (check_links, discover_tools, apply_approvals) | `agents/directory-freshness/*.json` | ⚠️ predates this contract — does not yet emit `agent_meta`/`action_items` |

When directory-freshness or any future agent is next revisited, bring it in line
with this contract rather than leaving it as a one-off shape.
