"""
regenerate_html.py

Rewrites the three data blocks inside index.html so the LIVE SITE matches
tools.json:
  1. `const tools = [...]`      — the visible directory grid (all non-archived)
  2. `const toolsDB = [...]`    — chatbot's lookup table
  3. systemPrompt's tool list   — chatbot's knowledge of what's available + pricing

Archived tools are excluded from all three (removed from the live site).
Flagged tools ARE still included (per design: one grace period shouldn't
hide a tool from visitors).

index.html should never be hand-edited for tool changes — this script is
the only thing that writes to it. Run this after check_links.py or
apply_approvals.py change tools.json.
"""
import json
import re
from urllib.parse import urlparse

HTML_PATH = "index.html"
TOOLS_PATH = "agents/directory-freshness/tools.json"


def js_string(s: str) -> str:
    """Escapes a string for safe embedding inside a JS template/string literal."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def domain_of(url: str) -> str:
    try:
        netloc = urlparse(url).netloc
        return netloc[4:] if netloc.startswith("www.") else netloc
    except Exception:
        return url


def build_tools_array(tools: list) -> str:
    lines = ["const tools = ["]
    current_cat = None
    for t in tools:
        if t["cat"] != current_cat:
            current_cat = t["cat"]
            lines.append(f"  // {current_cat}")
        lines.append(
            "  { name:\"%s\", cat:\"%s\", url:\"%s\", color:\"%s\", text:\"%s\", "
            "letter:\"%s\", desc:\"%s\", isNew:%s, featured:%s },"
            % (
                js_string(t["name"]), js_string(t["cat"]), js_string(t["url"]),
                t.get("color", "#333"), t.get("text", "#fff"), js_string(t.get("letter", "?")),
                js_string(t.get("desc", "")),
                "true" if t.get("isNew") else "false",
                "true" if t.get("featured") else "false",
            )
        )
    lines.append("];")
    return "\n".join(lines)


def build_toolsdb_array(tools: list) -> str:
    lines = ["const toolsDB = ["]
    for t in tools:
        lines.append(
            "  { name:\"%s\", url:\"%s\", color:\"%s\", letter:\"%s\" },"
            % (js_string(t["name"]), js_string(t["url"]), t.get("color", "#333"),
               js_string(t.get("letter", "?")))
        )
    lines.append("];")
    return "\n".join(lines)


def build_pricing_lines(tools: list) -> str:
    lines = []
    for t in tools:
        pricing = t.get("pricing") or "see site for pricing"
        lines.append(f"{t['name']} ({domain_of(t['url'])}) - {t.get('desc', '')} - {pricing}")
    return "\n".join(lines)


def main():
    with open(TOOLS_PATH, "r", encoding="utf-8") as f:
        all_tools = json.load(f)

    # Archived tools are hidden from the live site everywhere.
    # Flagged tools still show (grace period, per design).
    live_tools = [t for t in all_tools if t.get("status") != "archived"]

    with open(HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. Replace `const tools = [...]`
    new_tools_block = build_tools_array(live_tools)
    html, n1 = re.subn(
        r"const tools = \[.*?\];", new_tools_block, html, count=1, flags=re.DOTALL
    )

    # 2. Replace `const toolsDB = [...]`
    new_toolsdb_block = build_toolsdb_array(live_tools)
    html, n2 = re.subn(
        r"const toolsDB = \[.*?\];", new_toolsdb_block, html, count=1, flags=re.DOTALL
    )

    # 3. Replace the pricing list inside systemPrompt
    new_pricing_block = build_pricing_lines(live_tools)
    html, n3 = re.subn(
        r"(Available tools and their free status:\n).*?(\n\nRULES:)",
        lambda m: m.group(1) + new_pricing_block + m.group(2),
        html, count=1, flags=re.DOTALL
    )

    if not (n1 and n2 and n3):
        raise SystemExit(
            f"ERROR: expected to replace all 3 blocks, but got "
            f"tools={n1} toolsDB={n2} systemPrompt={n3}. "
            f"Aborting without writing — check index.html structure hasn't changed."
        )

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    archived_count = len(all_tools) - len(live_tools)
    print(f"Regenerated index.html: {len(live_tools)} live tools "
          f"({archived_count} archived tools hidden)")


if __name__ == "__main__":
    main()
