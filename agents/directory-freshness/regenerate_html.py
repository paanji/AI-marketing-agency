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
import html as html_lib
from urllib.parse import urlparse

HTML_PATH = "index.html"
TOOLS_PATH = "agents/directory-freshness/tools.json"


def classify_pricing_tier(pricing_text: str) -> str:
    """Derives a simple badge category (free / freemium / paid / unknown) from
    the existing free-text pricing field, computed fresh every time — not
    stored separately, so it can never drift out of sync with tools.json."""
    text = (pricing_text or "").lower()
    if not text or "see site" in text:
        return "unknown"
    if "completely free" in text:
        return "free"
    if "paid only" in text or "requires" in text:
        return "paid"
    if "trial" in text and "credits" not in text and "tier" not in text:
        return "paid"  # a time-limited trial means the underlying product is paid
    if "free" in text:
        return "freemium"
    return "unknown"


def js_string(s: str) -> str:
    """Escapes a string for safe embedding inside a JS template/string literal."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def domain_of(url: str) -> str:
    try:
        netloc = urlparse(url).netloc
        return netloc[4:] if netloc.startswith("www.") else netloc
    except Exception:
        return url


def build_static_grid_html(tools: list) -> str:
    """Server-side rendering of the same tool cards the page's JS render()
    function produces client-side. This is the actual fix for the
    JS-rendering blindspot the SEO agent identified: crawlers that don't
    execute JavaScript (many AI bots, and Googlebot under some conditions)
    now see the full tool grid immediately in the raw HTML, instead of an
    empty container. The JS render() function still runs for real visitors
    and still powers interactive search/filtering — this just ensures
    there's real content present before any JavaScript runs at all."""
    if not tools:
        return '<div class="no-results">No tools found 🤔</div>'
    TIER_LABELS = {"free": "Free", "freemium": "Freemium", "paid": "Paid", "unknown": "Pricing varies"}
    cards = []
    for i, t in enumerate(tools):
        if t.get("featured"):
            badge = '<span class="featured-pill">Featured</span>'
        elif t.get("isNew"):
            badge = '<span class="new-pill">New</span>'
        else:
            badge = ""
        name = html_lib.escape(t["name"])
        desc = html_lib.escape(t.get("desc", ""))
        cat = html_lib.escape(t["cat"])
        letter = html_lib.escape(t.get("letter", "?"))
        url = html_lib.escape(t["url"], quote=True)
        color = html_lib.escape(t.get("color", "#333"), quote=True)
        text_color = html_lib.escape(t.get("text", "#fff"), quote=True)
        tier = classify_pricing_tier(t.get("pricing", ""))
        tier_label = TIER_LABELS[tier]
        cards.append(
            f'<a class="tool-card" href="{url}" target="_blank" rel="noopener noreferrer" '
            f'data-pricing="{tier}" style="animation-delay:{i * 0.025}s">'
            f'<div class="card-top">'
            f'<div class="tool-icon" style="background:{color}; color:{text_color}">{letter}</div>'
            f'{badge}'
            f'</div>'
            f'<div>'
            f'<div class="tool-name">{name}</div>'
            f'<div class="tool-desc">{desc}</div>'
            f'</div>'
            f'<div class="card-foot">'
            f'<span class="tool-cat">{cat}</span>'
            f'<span class="tool-price tool-price-{tier}">{tier_label}</span>'
            f'</div>'
            f'</a>'
        )
    return "\n".join(cards)


def build_tools_array(tools: list) -> str:
    lines = ["const tools = ["]
    current_cat = None
    for t in tools:
        if t["cat"] != current_cat:
            current_cat = t["cat"]
            lines.append(f"  // {current_cat}")
        lines.append(
            "  { name:\"%s\", cat:\"%s\", url:\"%s\", color:\"%s\", text:\"%s\", "
            "letter:\"%s\", desc:\"%s\", isNew:%s, featured:%s, pricing:\"%s\" },"
            % (
                js_string(t["name"]), js_string(t["cat"]), js_string(t["url"]),
                t.get("color", "#333"), t.get("text", "#fff"), js_string(t.get("letter", "?")),
                js_string(t.get("desc", "")),
                "true" if t.get("isNew") else "false",
                "true" if t.get("featured") else "false",
                js_string(t.get("pricing", "")),
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

    # 4. Replace the grid section (count-bar + tools-grid) with real, static
    #    HTML cards baked in at build time — fixes the JS-rendering blindspot.
    #    Uses a non-greedy match anchored to a unique fixed comment further
    #    down the page, rather than trying to match the closing </div> of
    #    the grid itself — the cards contain their own nested </div> tags,
    #    which would make naive regex matching stop at the wrong place.
    static_cards = build_static_grid_html(live_tools)
    count_text = f"Showing <span>{len(live_tools)}</span> of <span>{len(live_tools)}</span> tools"
    new_grid_section = (
        '<div class="container grid-section">\n'
        f'  <div class="count-bar" id="count-bar">{count_text}</div>\n'
        f'  <div class="tools-grid" id="tools-grid">\n{static_cards}\n  </div>\n'
        '</div>'
    )
    html, n4 = re.subn(
        r'<div class="container grid-section">.*?(?=\n<!-- CATEGORY PAGES \+ BLOG LINKS -->)',
        lambda m: new_grid_section,
        html, count=1, flags=re.DOTALL
    )

    if not (n1 and n2 and n3 and n4):
        raise SystemExit(
            f"ERROR: expected to replace all 4 blocks, but got "
            f"tools={n1} toolsDB={n2} systemPrompt={n3} grid={n4}. "
            f"Aborting without writing — check index.html structure hasn't changed."
        )

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    archived_count = len(all_tools) - len(live_tools)
    print(f"Regenerated index.html: {len(live_tools)} live tools "
          f"({archived_count} archived tools hidden)")


if __name__ == "__main__":
    main()
