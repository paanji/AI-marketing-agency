# Outreach Agent — Local Citation Extension (Design Sketch)

**Status:** design only, not yet built into `outreach_agent.py`. Hold actual coding until the
AllAIDunia backlink version has run for a few weeks and we know the discovery/drafting logic
is solid — same discipline used for the SEO Agent (proven on AllAIDunia before generalizing to
`local_service_business`).

This covers what changes for a local-service client (e.g. the laptop repair/computer sales client)
once `config.json` sets `"outreach_type": "local_citation"`.

---

## 1. Why this isn't just "backlinks, but for a different client"

Backlink outreach has one shape: find a company, find a person, ask for a link. Local citation
work has **two different shapes**, and the queue needs to keep them visibly separate:

| | Self-serve platforms | Directory/partnership applications |
|---|---|---|
| Example | Google Business Profile, Bing Places, Apple Business Connect, Yelp | Manufacturer authorized-repair programs, chamber of commerce, niche directories |
| Who does the work | You, logging into a dashboard | Us, drafting to a real contact — same engine as backlink outreach |
| What the agent produces | A pre-filled NAP checklist + submission link | A drafted message, discovery + draft as before |
| `suggested_agent` | `"manual"` — no agent can click through a Google verification flow | `"manual"` (send is still human-approved) but agent-draftable |

Treating a Google Business Profile submission as an "email to send" would be nonsense — there's
no one to email. Treating a manufacturer partner application as a copy-paste checklist item would
undersell what's actually a relationship-building outreach message. Keeping them as two item types
in the same queue means you can scan `outreach_pending.json` and immediately know whether an item
needs you to log into a dashboard or to review a drafted message.

## 2. Priority tiers (from `citation_platforms[].tier` / `directory_partnership_targets[].tier`)

- **Tier 1 — do first, always**: Google Business Profile, Bing Places, Apple Business Connect.
  These carry the most local-search ranking weight and Google's verification alone takes days,
  so starting late costs real calendar time regardless of anything else in the queue.
- **Tier 2 — do once Tier 1 is submitted**: Yelp, Facebook, manufacturer partner programs.
- **Tier 3 — background/opportunistic**: chamber of commerce, small local directories. Real but
  marginal ranking value; fine to batch these into slower runs.

The agent should always surface Tier 1 gaps first, even out of alphabetical/discovery order —
this is the single highest-leverage thing the citation queue can do.

## 3. NAP consistency is the actual point

The entire value of citation building collapses if the business name, address, and phone number
don't match *exactly* across every platform (abbreviations, suite numbers, old phone numbers all
count as inconsistent). That's why `business_profile` is a single block reused verbatim everywhere,
not re-typed per platform — the agent's checklist items should quote it character-for-character,
and a future "citation audit" pass (checking what's already live and flagging mismatches) is a
natural next feature once the initial round of citations exists to audit.

## 4. How `outreach_agent.py` would branch (pseudocode, not yet implemented)

```python
if config.get("outreach_type") == "local_citation":
    for platform in sorted(config["citation_platforms"], key=lambda p: p["tier"]):
        if platform["name"] in log["citations_done"]:
            continue
        item = build_citation_checklist_item(platform, config["business_profile"])
        # item.category = "local_citation", item.suggested_agent = "manual"
        # item.proposed_fix = pre-filled NAP block + submission_url, NOT a message

    for target in sorted(config["directory_partnership_targets"], key=lambda t: t["tier"]):
        if target["name"] in log["contacted"]:
            continue
        contact = find_contact(...)   # same discovery logic as backlink track
        draft = draft_partnership_message(target, config["business_profile"])
        # item.category = "partnership_outreach" — same shape as existing backlink items
else:
    # existing backlink_outreach logic, unchanged
    ...
```

The discovery and drafting functions already built for backlinks are reused as-is for
`directory_partnership_targets` — only the target list and message framing change (asking to be
listed/partnered, not asking for a backlink to an existing listing).

## 5. The guardrail that matters most here: review requests

Review-request outreach ("ask happy customers to leave a Google review") is the natural next
extension for a local service business, and it's deliberately **not included** in this sketch.
Google's guidelines prohibit review-gating — soliciting reviews only from customers you expect
to be satisfied, or filtering who gets asked based on predicted sentiment — and prohibit
incentivizing reviews. If this gets built later, "ask every customer, unconditionally, no
incentive" needs to be a hardcoded rule in the code, not a configurable option a client could ask
us to loosen. A client request to "only send it to our best customers" is a request to violate
platform policy, and that's a place to push back rather than accommodate.

## 6. What we'd actually need before building this for real

- Real `business_profile` data for the laptop repair client (exact legal name, address, phone,
  hours, service list) — the example config has placeholders only.
- A decision on whether manufacturer partner applications (Dell, HP) are worth pursuing now, given
  they mentioned technician certification — that's a business decision for the client, not
  something to default into the queue.
- Confirmation the client wants us submitting Google Business Profile / Bing Places ourselves
  (needs their login) vs. us handing them the checklist to submit themselves.
