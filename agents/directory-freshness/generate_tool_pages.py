#!/usr/bin/env python3
"""
Per-Tool Page Generator — programmatic SEO pages from tools.json.

Reads agents/directory-freshness/tools.json and generates one substantial
page per ACTIVE tool at tools/<id>.html, plus regenerates sitemap.xml to
include them all.

Design decisions:
- Fully deterministic — no LLM calls. Every sentence is templated from real
  tools.json data (pricing, category, alternatives), so pages can regenerate
  daily with zero cost and zero hallucination risk.
- Substance over thinness: each page gets an overview, pricing detail,
  best-for section, 3 alternatives from the same category (real internal
  links), a category guide link, an FAQ block, and SoftwareApplication
  schema. This is what keeps these on the right side of Google's
  scaled-content policies — every section is real data, not filler.
- Archived tools get their page REMOVED (and dropped from the sitemap), so
  dead tools never leave stale pages behind.

Run from repo root:  python3 agents/directory-freshness/generate_tool_pages.py
"""

import json
import os
import re
import shutil
from datetime import date

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS_JSON = os.path.join(REPO_ROOT, "agents", "directory-freshness", "tools.json")
OUT_DIR = os.path.join(REPO_ROOT, "tools")
SITEMAP = os.path.join(REPO_ROOT, "sitemap.xml")
SITE = "https://www.allaidunia.com"
TODAY = date.today().isoformat()

# Category -> 3-step quickstart shown on every tool page in that category
CATEGORY_QUICKSTART = {
    "Video": ["Describe your scene in one or two sentences — subject, motion, and mood.",
              "Add camera language ('slow pan', 'aerial shot') — video models respond strongly to it.",
              "Generate a short clip first, refine the prompt, then extend to full length."],
    "Image": ["Start with the subject, then style ('photorealistic', 'illustration'), then lighting.",
              "Iterate: generate, spot what's off, add one correcting detail, regenerate.",
              "Save prompts that work — small wording changes produce very different images."],
    "Audio": ["Write your script or describe the sound first — the text drives everything.",
              "Specify tone and pacing ('warm, conversational', 'energetic') explicitly.",
              "Generate a short sample before committing to the full-length version."],
    "Chat": ["Give it a role first ('You are a...') — context dramatically improves answers.",
             "State your goal and constraints in the first message, not spread across many.",
             "Ask it to show reasoning or sources when accuracy matters."],
    "Writing": ["Give it audience, tone, and length before asking for a draft.",
                "Treat the first output as a draft — ask for specific revisions, not 'make it better'.",
                "Paste in an example of writing you like and ask it to match the style."],
    "Code": ["Describe what the code should do AND the language/framework up front.",
             "Paste error messages verbatim — they're the fastest path to a fix.",
             "Ask it to explain the code it wrote; you'll catch issues and learn faster."],
}

# Category -> (guide URL, guide label, "best for" blurb)
CATEGORY_INFO = {
    "Video": ("/guides/video-generation.html", "AI video generation guide",
              "creating videos from text or images — marketing clips, social content, and cinematic shots"),
    "Image": ("/guides/3d-image-generation.html", "AI image generation guide",
              "generating images and artwork from text descriptions — illustrations, photos, and 3D-style renders"),
    "Audio": ("/guides/voice-audio.html", "AI voice & audio guide",
              "generating voiceovers, music, and audio — narration, songs, and sound design"),
    "Chat": ("/guides/chatbots-agents.html", "AI chatbot setup guide",
             "conversational AI — answering questions, brainstorming, and automating support"),
    "Writing": ("/guides/writing-content.html", "AI writing guide",
                "writing and editing content — blog posts, marketing copy, and long-form text"),
    "Code": ("/", "AI tools directory",
             "writing, reviewing, and debugging code with AI assistance"),
    "Design": ("/", "AI tools directory",
               "design work — interfaces, graphics, and creative assets"),
    "Productivity": ("/", "AI tools directory",
                     "getting more done — organizing, summarizing, and automating everyday tasks"),
    "Marketing": ("/", "AI tools directory",
                  "marketing work — campaigns, copy, and audience insights"),
    "Research": ("/", "AI tools directory",
                 "research — finding, summarizing, and organizing information"),
    "Search": ("/", "AI tools directory",
               "AI-powered search — finding answers with sources instead of link lists"),
    "Uncategorized": ("/", "AI tools directory", "a range of AI-assisted tasks"),
}


def pricing_class(pricing_text):
    """Mirror of the classification used for grid badges."""
    p = (pricing_text or "").upper()
    if "COMPLETELY FREE" in p or p == "FREE":
        return "Free"
    if "FREE" in p and ("PAID" in p or "$" in p or "TIER" in p or "PLAN" in p or "PLUS" in p or "PRO" in p):
        return "Freemium"
    if "$" in p or "PAID" in p or "SUBSCRIPTION" in p:
        return "Paid"
    return "Pricing varies"


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def build_page(tool, all_tools):
    name = tool["name"]
    cat = tool.get("cat", "Uncategorized")
    guide_url, guide_label, best_for = CATEGORY_INFO.get(cat, CATEGORY_INFO["Uncategorized"])
    pricing_text = tool.get("pricing", "Pricing varies")
    pclass = pricing_class(pricing_text)
    desc = tool.get("desc", "")
    color = tool.get("color", "#7c6cfa")
    letter = tool.get("letter", name[:1].upper())
    ext_url = tool["url"]

    alternatives = [t for t in all_tools
                    if t.get("cat") == cat and t["id"] != tool["id"] and t.get("status") == "active"][:4]

    title_variants = [
        f"{name} Review 2026 — Pricing & Alternatives | AllAIDunia",
        f"{name} Review 2026 — Pricing & Alternatives",
        f"{name} — Pricing & Alternatives 2026",
        f"{name} Review 2026 | AllAIDunia",
        f"{name} Review 2026",
    ]
    title = next((t for t in title_variants if len(t) <= 60), title_variants[-1])

    meta_desc = (f"Is {name} worth it in 2026? {desc}. See pricing ({pclass.lower()}), "
                 f"what it's best for, and the top {cat.lower()} alternatives.")
    if len(meta_desc) > 158:
        meta_desc = meta_desc[:155].rsplit(" ", 1)[0] + "…"

    schema = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": name,
        "url": ext_url,
        "description": desc,
        "applicationCategory": cat,
        "offers": {"@type": "Offer",
                   "price": "0" if pclass == "Free" else None,
                   "priceCurrency": "USD"} if pclass == "Free" else None,
    }
    schema = {k: v for k, v in schema.items() if v is not None}
    if "offers" in schema and schema["offers"] is None:
        del schema["offers"]

    alt_cards = "\n".join(
        f'''      <a class="alt-card" href="/tools/{t["id"]}.html">
        <span class="alt-letter" style="background:{t.get("color", "#7c6cfa")};color:{t.get("text", "#fff")}">{esc(t.get("letter", t["name"][:1]))}</span>
        <span>
          <strong>{esc(t["name"])}</strong>
          <small>{esc((t.get("desc") or "")[:70])}</small>
        </span>
      </a>''' for t in alternatives) or '      <p class="muted">No other tools in this category yet.</p>'

    pricing_faq = {
        "Free": f"Yes — {name} is completely free to use.",
        "Freemium": f"{name} has a free tier to start with; paid plans unlock more. Current pricing: {pricing_text}.",
        "Paid": f"{name} is a paid tool. Current pricing: {pricing_text}.",
        "Pricing varies": f"{name}'s pricing varies — check their site for current plans.",
    }[pclass]

    steps = CATEGORY_QUICKSTART.get(cat)
    if steps:
        step_items = "\n".join(f"    <li>{esc(s)}</li>" for s in steps)
        quickstart_html = (f"\n  <h2>How to get good results with {esc(name)}</h2>\n"
                           f"  <ol style=\"margin:0 0 12px 20px; color:var(--text);\">\n{step_items}\n  </ol>\n"
                           f"  <p class=\"muted\">Want a head start? <a href=\"/prompt-guru.html\">Prompt Guru</a> "
                           f"writes a tailored prompt for you — free.</p>")
    else:
        quickstart_html = ""

    return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(meta_desc)}">
<link rel="canonical" href="{SITE}/tools/{tool["id"]}.html">
<link rel="icon" href="/favicon.ico">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(meta_desc)}">
<meta property="og:url" content="{SITE}/tools/{tool["id"]}.html">
<meta property="og:type" content="website">
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet" />
<script type="application/ld+json">
{json.dumps(schema, indent=2, ensure_ascii=False)}
</script>
<style>
  [data-theme="dark"] {{ --bg:#0a0a0f; --bg2:#111118; --bg3:#18181f; --border:rgba(255,255,255,0.08);
    --border2:rgba(255,255,255,0.14); --text:#f0eff5; --muted:#8b8a96; --card-bg:#111118; }}
  :root {{ --accent:#7c6cfa; --accent2:#fa6c9f; --gold:#f0c060;
    --font-head:'Syne',sans-serif; --font-body:'DM Sans',sans-serif; --radius:14px; }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:var(--font-body); background:var(--bg); color:var(--text); line-height:1.55; }}
  a {{ color:var(--accent); }}
  .nav {{ display:flex; align-items:center; justify-content:space-between;
    padding:18px clamp(16px,4vw,48px); border-bottom:1px solid var(--border); }}
  .nav a.home {{ font-family:var(--font-head); font-weight:800; font-size:18px; color:var(--accent); text-decoration:none; }}
  .nav a.home span {{ color:var(--gold); }}
  .nav a.back {{ font-size:13px; color:var(--muted); text-decoration:none; }}
  .wrap {{ max-width:760px; margin:0 auto; padding:40px 16px 90px; }}
  .tool-head {{ display:flex; align-items:center; gap:16px; margin-bottom:8px; }}
  .tool-letter {{ width:56px; height:56px; border-radius:14px; display:flex; align-items:center;
    justify-content:center; font-family:var(--font-head); font-weight:700; font-size:24px; flex-shrink:0; }}
  h1 {{ font-family:var(--font-head); font-size:clamp(26px,5vw,38px); font-weight:800; line-height:1.15; }}
  .badges {{ display:flex; gap:8px; margin:14px 0 26px; flex-wrap:wrap; }}
  .badge {{ font-size:12px; padding:5px 12px; border-radius:999px; border:1px solid var(--border2); color:var(--muted); }}
  .badge.price {{ border-color:var(--accent); color:var(--accent); }}
  h2 {{ font-family:var(--font-head); font-size:20px; margin:34px 0 10px; }}
  p {{ margin-bottom:12px; color:var(--text); }}
  .muted {{ color:var(--muted); }}
  .cta {{ display:inline-block; background:var(--accent); color:#fff; text-decoration:none;
    padding:12px 22px; border-radius:10px; font-weight:500; margin-top:6px; }}
  .alt-grid {{ display:grid; gap:10px; margin-top:10px; }}
  .alt-card {{ display:flex; gap:12px; align-items:center; background:var(--card-bg);
    border:1px solid var(--border); border-radius:var(--radius); padding:14px; text-decoration:none; color:var(--text); }}
  .alt-card:hover {{ border-color:var(--accent); }}
  .alt-letter {{ width:38px; height:38px; border-radius:9px; display:flex; align-items:center;
    justify-content:center; font-family:var(--font-head); font-weight:700; flex-shrink:0; }}
  .alt-card small {{ display:block; color:var(--muted); font-size:12.5px; }}
  .faq-item {{ border-top:1px solid var(--border); padding:14px 0; }}
  .faq-item strong {{ display:block; margin-bottom:6px; }}
  .foot {{ margin-top:56px; text-align:center; font-size:12.5px; color:var(--muted); }}
</style>
</head>
<body>
<nav class="nav">
  <a class="home" href="/">AllAI<span>Dunia</span></a>
  <a class="back" href="/">&larr; All AI tools</a>
</nav>
<div class="wrap">
  <div class="tool-head">
    <div class="tool-letter" style="background:{color};color:{tool.get("text", "#fff")}">{esc(letter)}</div>
    <h1>{esc(name)}</h1>
  </div>
  <div class="badges">
    <span class="badge">{esc(cat)}</span>
    <span class="badge price">{esc(pclass)}</span>
  </div>

  <p>{esc(desc)}. {esc(name)} is one of the {esc(cat.lower())} AI tools we list in the
  <a href="/">AllAIDunia directory</a>, where every tool is checked daily so dead links never linger.</p>

  <h2>What is {esc(name)} best for?</h2>
  <p>{esc(name)} is best suited for {best_for}. If you're new to this category, our
  <a href="{guide_url}">{esc(guide_label)}</a> walks through the workflow step by step, with a
  copy-paste starter prompt.</p>

{quickstart_html}
  <h2>{esc(name)} pricing</h2>
  <p>{esc(pricing_faq)}</p>

  <p><a class="cta" href="{ext_url}" target="_blank" rel="noopener">Visit {esc(name)} &rarr;</a></p>

  <h2>{esc(name)} alternatives</h2>
  <p class="muted">Other {esc(cat.lower())} tools from our directory worth comparing:</p>
  <div class="alt-grid">
{alt_cards}
  </div>

  <h2>Frequently asked questions</h2>
  <div class="faq-item">
    <strong>Is {esc(name)} free?</strong>
    <span class="muted">{esc(pricing_faq)}</span>
  </div>
  <div class="faq-item">
    <strong>What category is {esc(name)} in?</strong>
    <span class="muted">{esc(name)} is a {esc(cat.lower())} AI tool. Browse all {esc(cat.lower())} tools in
    <a href="/">our directory</a>.</span>
  </div>
  <div class="faq-item">
    <strong>How do I get better results from {esc(name)}?</strong>
    <span class="muted">Better prompts = better output. Try our free
    <a href="/prompt-guru.html">Prompt Guru</a> — answer a few questions and get a prompt
    crafted for your exact task.</span>
  </div>

  <div class="foot">Part of the <a href="/">AllAIDunia</a> AI tools directory · Link checked {TODAY}</div>
</div>
</body>
</html>
"""


def build_sitemap(tool_ids):
    core = [
        ("/", "1.0", "weekly"),
        ("/about.html", "0.6", "monthly"),
        ("/contact.html", "0.5", "monthly"),
        ("/prompt-guru.html", "0.8", "monthly"),
        ("/guides/websites.html", "0.8", "monthly"),
        ("/guides/video-generation.html", "0.8", "monthly"),
        ("/guides/3d-image-generation.html", "0.8", "monthly"),
        ("/guides/voice-audio.html", "0.8", "monthly"),
        ("/guides/chatbots-agents.html", "0.8", "monthly"),
        ("/guides/writing-content.html", "0.8", "monthly"),
        ("/video-ai-tools.html", "0.8", "monthly"),
        ("/best-free-ai-video-editing-tools.html", "0.8", "monthly"),
    ]
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, pri, freq in core:
        lines += ["<url>", f"<loc>{SITE}{path}</loc>", f"<lastmod>{TODAY}</lastmod>",
                  f"<changefreq>{freq}</changefreq>", f"<priority>{pri}</priority>", "</url>"]
    for tid in sorted(tool_ids):
        lines += ["<url>", f"<loc>{SITE}/tools/{tid}.html</loc>", f"<lastmod>{TODAY}</lastmod>",
                  "<changefreq>weekly</changefreq>", "<priority>0.7</priority>", "</url>"]
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def main():
    with open(TOOLS_JSON, encoding="utf-8") as f:
        tools = json.load(f)

    active = [t for t in tools if t.get("status") == "active"]
    active_ids = {t["id"] for t in active}

    os.makedirs(OUT_DIR, exist_ok=True)

    # Remove pages for tools that are no longer active (archived/removed)
    removed = 0
    for fname in os.listdir(OUT_DIR):
        if fname.endswith(".html") and fname[:-5] not in active_ids:
            os.remove(os.path.join(OUT_DIR, fname))
            removed += 1

    written = 0
    for tool in active:
        page = build_page(tool, active)
        out_path = os.path.join(OUT_DIR, f"{tool['id']}.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(page)
        written += 1

    with open(SITEMAP, "w", encoding="utf-8") as f:
        f.write(build_sitemap(active_ids))

    print(f"Generated {written} tool pages, removed {removed} stale pages, "
          f"sitemap now has {12 + len(active_ids)} URLs.")


if __name__ == "__main__":
    main()
