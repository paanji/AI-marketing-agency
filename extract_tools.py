"""
Extracts the `tools` array from index.html into tools.json,
adding lifecycle-tracking fields (status, strikes, timestamps).

This tools.json becomes the single source of truth. Going forward,
index.html is GENERATED from tools.json — never hand-edited.
"""
import re
import json
import json5
from datetime import date

HTML_PATH = "index.html"
OUT_PATH = "tools.json"

with open(HTML_PATH, "r", encoding="utf-8") as f:
    html = f.read()

# Grab everything between "const tools = [" and the matching "];"
match = re.search(r"const tools = (\[.*?\]);", html, re.DOTALL)
if not match:
    raise SystemExit("Could not find `const tools = [...]` array in index.html")

raw_array_text = match.group(1)

# json5 handles unquoted keys, single quotes, comments, trailing commas —
# all the JS-object-literal quirks that break strict JSON.parse
tools_raw = json5.loads(raw_array_text)

today = date.today().isoformat()

tools_out = []
for t in tools_raw:
    tools_out.append({
        "id": re.sub(r"[^a-z0-9]+", "-", t["name"].lower()).strip("-"),
        "name": t["name"],
        "cat": t["cat"],
        "url": t["url"],
        "color": t.get("color", "#333"),
        "text": t.get("text", "#fff"),
        "letter": t.get("letter", t["name"][0].upper()),
        "desc": t.get("desc", ""),
        "isNew": t.get("isNew", False),
        "featured": t.get("featured", False),
        # ── lifecycle fields (new) ──
        "status": "active",
        "consecutive_failures": 0,
        "last_checked": today,
        "last_working": today,
        "archived_date": None,
        "source": "manual"
    })

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(tools_out, f, indent=2, ensure_ascii=False)

print(f"Extracted {len(tools_out)} tools -> {OUT_PATH}")

# Quick sanity check: category breakdown
from collections import Counter
cats = Counter(t["cat"] for t in tools_out)
for c, n in sorted(cats.items()):
    print(f"  {c}: {n}")
