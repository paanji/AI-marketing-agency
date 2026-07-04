"""
backfill_pricing.py (one-time use)

The chatbot's systemPrompt in index.html contains pricing info (free/paid
status) for 35 tools that doesn't exist anywhere in tools.json. Running
this once pulls that data into tools.json as a proper "pricing" field,
so it's captured before the HTML regenerator overwrites systemPrompt.
"""
import json
import re

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

with open("tools.json", "r", encoding="utf-8") as f:
    tools = json.load(f)

match = re.search(
    r"Available tools and their free status:\n(.*?)\n\nRULES:",
    html, re.DOTALL
)
if not match:
    raise SystemExit("Could not find the pricing list in systemPrompt")

lines = [l.strip() for l in match.group(1).split("\n") if l.strip()]

# Each line looks like:
# "ChatGPT (chat.openai.com) - writing, emails, resume, brainstorm - FREE tier available"
pricing_map = {}
for line in lines:
    m = re.match(r"^(.+?)\s*\([^)]+\)\s*-\s*.+?\s*-\s*(.+)$", line)
    if m:
        name, pricing = m.group(1).strip(), m.group(2).strip()
        pricing_map[name.lower()] = pricing

matched = 0
for t in tools:
    key = t["name"].lower()
    if key in pricing_map:
        t["pricing"] = pricing_map[key]
        matched += 1
    else:
        t.setdefault("pricing", "")  # unknown — fill in manually later if useful

with open("tools.json", "w", encoding="utf-8") as f:
    json.dump(tools, f, indent=2, ensure_ascii=False)

print(f"Matched pricing for {matched} tools out of {len(pricing_map)} found in systemPrompt")
unmatched = set(pricing_map) - {t["name"].lower() for t in tools}
if unmatched:
    print("Names in systemPrompt but not found in tools.json (check spelling):")
    for n in unmatched:
        print(f"  - {n}")
