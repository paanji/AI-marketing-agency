# SEO Report — AllAIDunia
_2026-07-06_

Data window: 2026-06-05 to 2026-07-03 (vs. prior 2026-05-08 to 2026-06-04)

## Recommended Actions
Prioritized suggestions combining Search Console data and a live site audit. Items tagged for `content_agent` will be actioned automatically once that agent exists — items tagged `manual` need a person for now.

### High Priority
- [technical] Critical content may be invisible to crawlers: the container `#tools-grid` has only 0 item(s) in the raw HTML (expected at least 10). This strongly suggests this page's main content is filled in by JavaScript after load. Many AI crawlers (GPTBot, ClaudeBot, PerplexityBot) and Googlebot under some conditions do not execute JavaScript, meaning they may see an empty page here even though a human visitor sees full content. This is a likely explanation for unusually low search visibility despite otherwise reasonable on-page SEO — the fix is to render this content directly into the HTML at build time, in addition to keeping the JavaScript for interactive features. _(page: https://www.allaidunia.com/)_ — *suggested owner: manual*
- [technical] Critical content may be invisible to crawlers: the container `#tools-grid` has only 0 item(s) in the raw HTML (expected at least 10). This strongly suggests this page's main content is filled in by JavaScript after load. Many AI crawlers (GPTBot, ClaudeBot, PerplexityBot) and Googlebot under some conditions do not execute JavaScript, meaning they may see an empty page here even though a human visitor sees full content. This is a likely explanation for unusually low search visibility despite otherwise reasonable on-page SEO — the fix is to render this content directly into the HTML at build time, in addition to keeping the JavaScript for interactive features. _(page: https://www.allaidunia.com/video-ai-tools.html)_ — *suggested owner: manual*

### Medium Priority
- [on_page_seo] Title is 70 characters — Google truncates over ~60. _(page: https://www.allaidunia.com/)_ — *suggested owner: content_agent*
- [ai_search_geo] No schema.org markup — adding ItemList/SoftwareApplication schema helps AI systems understand and cite this page correctly. _(page: https://www.allaidunia.com/)_ — *suggested owner: content_agent*
- [on_page_seo] Title is 62 characters — Google truncates over ~60. _(page: https://www.allaidunia.com/video-ai-tools.html)_ — *suggested owner: content_agent*
- [ai_search_geo] No schema.org markup — adding ItemList/SoftwareApplication schema helps AI systems understand and cite this page correctly. _(page: https://www.allaidunia.com/video-ai-tools.html)_ — *suggested owner: content_agent*
- [ai_search_geo] No schema.org markup — adding ItemList/SoftwareApplication schema helps AI systems understand and cite this page correctly. _(page: https://www.allaidunia.com/best-free-ai-video-editing-tools.html)_ — *suggested owner: content_agent*

### Low Priority
- [ai_search_geo] No llms.txt file — an emerging standard giving AI systems a clean, structured summary of your site. Not yet universal, but cheap to add and forward-looking. — *suggested owner: content_agent*
- [on_page_seo] Meta description is 179 characters — will get truncated. _(page: https://www.allaidunia.com/)_ — *suggested owner: content_agent*
- [ai_search_geo] No lists or tables — AI answer engines strongly prefer content structured for easy extraction and citation. _(page: https://www.allaidunia.com/)_ — *suggested owner: content_agent*
- [ai_search_geo] No lists or tables — AI answer engines strongly prefer content structured for easy extraction and citation. _(page: https://www.allaidunia.com/video-ai-tools.html)_ — *suggested owner: content_agent*
- [on_page_seo] Meta description is 164 characters — will get truncated. _(page: https://www.allaidunia.com/best-free-ai-video-editing-tools.html)_ — *suggested owner: content_agent*
- [ai_search_geo] No lists or tables — AI answer engines strongly prefer content structured for easy extraction and citation. _(page: https://www.allaidunia.com/best-free-ai-video-editing-tools.html)_ — *suggested owner: content_agent*


## Overview
| Metric | Value |
|---|---|
| Total queries seen | 1 |
| Total clicks | 0 |
| Total impressions | 2 |
| Average position | 8.5 |
| Overall CTR | 0.0% |

## AI Search Readiness (GEO/AEO)
Whether AI answer engines (ChatGPT, Perplexity, Gemini, Google AI Overviews) can find, understand, and cite this site.

- AI crawler access: all checked crawlers allowed
- llms.txt present: No
- Schema types found across site: **none**

## On-Page Audit
3 page(s) checked from the sitemap.

| Page | Title Length | Meta Desc | H1s | Images Missing Alt | Word Count |
|---|---|---|---|---|---|
| https://www.allaidunia.com/ | 70 | Yes | 1 | 0 | 335 |
| https://www.allaidunia.com/video-ai-tools.html | 62 | Yes | 1 | 0 | 246 |
| https://www.allaidunia.com/best-free-ai-video-editing-tools.html | 57 | Yes | 1 | 0 | 571 |

## Top Queries by Visibility

| Query | Position | Impressions | Clicks | CTR |
|---|---|---|---|---|
| ai dunia | 8.5 | 2 | 0 | 0% |