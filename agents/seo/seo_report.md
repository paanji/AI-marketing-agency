# SEO Report — AllAIDunia
_2026-07-07_

Data window: 2026-06-06 to 2026-07-04 (vs. prior 2026-05-09 to 2026-06-05)

## Recommended Actions
Prioritized suggestions combining Search Console data and a live site audit. Items tagged for `content_agent` will be actioned automatically once that agent exists — items tagged `manual` need a person for now.

### High Priority
- [technical] Critical content may be invisible to crawlers: the container `#tools-grid` has only 0 item(s) in the raw HTML (expected at least 10). This strongly suggests this page's main content is filled in by JavaScript after load. Many AI crawlers (GPTBot, ClaudeBot, PerplexityBot) and Googlebot under some conditions do not execute JavaScript, meaning they may see an empty page here even though a human visitor sees full content. This is a likely explanation for unusually low search visibility despite otherwise reasonable on-page SEO — the fix is to render this content directly into the HTML at build time, in addition to keeping the JavaScript for interactive features. _(page: https://www.allaidunia.com/video-ai-tools.html)_ — *suggested owner: manual*
- [technical] Not indexed by Google: verdict is 'NEUTRAL' — URL is unknown to Google. A page that isn't indexed gets zero search traffic no matter how well it's optimized otherwise. Use Search Console's URL Inspection tool to request indexing directly. _(page: https://www.allaidunia.com/video-ai-tools.html)_ — *suggested owner: manual*
- [technical] Not indexed by Google: verdict is 'NEUTRAL' — URL is unknown to Google. A page that isn't indexed gets zero search traffic no matter how well it's optimized otherwise. Use Search Console's URL Inspection tool to request indexing directly. _(page: https://www.allaidunia.com/best-free-ai-video-editing-tools.html)_ — *suggested owner: manual*

### Medium Priority
- [on_page_seo] Title ("AllAIDunia â Find the Right AI Tool for Any Task | 60+ Free AI Tools") is 70 characters — Google truncates over ~ 30-60. _(page: https://www.allaidunia.com/)_ — *suggested owner: content_agent*
  **Proposed fix:** "AllAIDunia â Find the Right AI Tool for Any Task | 60+"
- [ai_search_geo] No schema.org markup — adding ItemList/SoftwareApplication schema helps AI systems understand and cite this page correctly. _(page: https://www.allaidunia.com/)_ — *suggested owner: content_agent*
  ```
  {
  "@context": "https://schema.org",
  "@type": "ItemList",
  "name": "AllAIDunia — AI Tools Directory",
  "url": "https://www.allaidunia.com/",
  "numberOfItems": 60,
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "item": {
        "@type": "SoftwareApplication",
        "name": "ChatGPT",
        "url": "https://chat.openai.com",
        "description": "OpenAI's flagship AI assistant for everything",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 2,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Claude",
        "url": "https://claude.ai",
        "description": "Anthropic's thoughtful and safe AI assistant",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 3,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Gemini",
        "url": "https://gemini.google.com",
        "description": "Google's powerful multimodal AI model",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 4,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Grok",
        "url": "https://grok.com",
        "description": "xAI's witty real-time AI by Elon Musk",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 5,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Mistral",
        "url": "https://chat.mistral.ai",
        "description": "Open-weight European AI models",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 6,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Meta AI",
        "url": "https://meta.ai",
        "description": "Meta's AI across apps and the web",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 7,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Copilot",
        "url": "https://copilot.microsoft.com",
        "description": "Microsoft's AI assistant powered by GPT-4",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 8,
      "item": {
        "@type": "SoftwareApplication",
        "name": "DeepSeek",
        "url": "https://chat.deepseek.com",
        "description": "Powerful open-source reasoning model",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 9,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Le Chat",
        "url": "https://chat.mistral.ai",
        "description": "Mistral's fast conversational AI",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 10,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Pi AI",
        "url": "https://pi.ai",
        "description": "Your personal AI that listens and learns",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 11,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Perplexity",
        "url": "https://perplexity.ai",
        "description": "AI-powered answer engine with citations",
        "applicationCategory": "Search"
      }
    },
    {
      "@type": "ListItem",
      "position": 12,
      "item": {
        "@type": "SoftwareApplication",
        "name": "You.com",
        "url": "https://you.com",
        "description": "AI search with cited answers",
        "applicationCategory": "Search"
      }
    },
    {
      "@type": "ListItem",
      "position": 13,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Exa AI",
        "url": "https://exa.ai",
        "description": "Neural search for developers and researchers",
        "applicationCategory": "Search"
      }
    },
    {
      "@type": "ListItem",
      "position": 14,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Midjourney",
        "url": "https://midjourney.com",
        "description": "Stunning AI image generation",
        "applicationCategory": "Image"
      }
    },
    {
      "@type": "ListItem",
      "position": 15,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Stable Diff.",
        "url": "https://stability.ai",
        "description": "Open-source image generation model",
        "applicationCategory": "Image"
      }
    },
    {
      "@type": "ListItem",
      "position": 16,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Adobe Firefly",
        "url": "https://firefly.adobe.com",
        "description": "Adobe's generative AI for creatives",
        "applicationCategory": "Image"
      }
    },
    {
      "@type": "ListItem",
      "position": 17,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Krea",
        "url": "https://krea.ai",
        "description": "Real-time AI image creation tool",
        "applicationCategory": "Image"
      }
    },
    {
      "@type": "ListItem",
      "position": 18,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Ideogram",
        "url": "https://ideogram.ai",
        "description": "AI image gen with great text typography",
        "applicationCategory": "Image"
      }
    },
    {
      "@type": "ListItem",
      "position": 19,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Leonardo AI",
        "url": "https://leonardo.ai",
        "description": "AI images for games and creative work",
        "applicationCategory": "Image"
      }
    },
    {
      "@type": "ListItem",
      "position": 20,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Flux",
        "url": "https://blackforestlabs.ai",
        "description": "State of the art image generation model",
        "applicationCategory": "Image"
      }
    },
    {
      "@type": "ListItem",
      "position": 21,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Canva AI",
        "url": "https://canva.com/ai-image-generator",
        "description": "AI image generation inside Canva",
        "applicationCategory": "Image"
      }
    },
    {
      "@type": "ListItem",
      "position": 22,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Runway",
        "url": "https://runwayml.com",
        "description": "AI video generation and editing suite",
        "applicationCategory": "Video"
      }
    },
    {
      "@type": "ListItem",
      "position": 23,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Sora",
        "url": "https://sora.com",
        "description": "OpenAI's text-to-video model",
        "applicationCategory": "Video"
      }
    },
    {
      "@type": "ListItem",
      "position": 24,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Kling AI",
        "url": "https://klingai.com",
        "description": "Realistic AI video generation",
        "applicationCategory": "Video"
      }
    },
    {
      "@type": "ListItem",
      "position": 25,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Pika",
        "url": "https://pika.art",
        "description": "AI video from text or images",
        "applicationCategory": "Video"
      }
    },
    {
      "@type": "ListItem",
      "position": 26,
      "item": {
        "@type": "SoftwareApplication",
        "name": "HeyGen",
        "url": "https://heygen.com",
        "description": "AI avatar video creator for business",
        "applicationCategory": "Video"
      }
    },
    {
      "@type": "ListItem",
      "position": 27,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Synthesia",
        "url": "https://synthesia.io",
        "description": "AI video with realistic avatars",
        "applicationCategory": "Video"
      }
    },
    {
      "@type": "ListItem",
      "position": 28,
      "item": {
        "@type": "SoftwareApplication",
        "name": "ElevenLabs",
        "url": "https://elevenlabs.io",
        "description": "Ultra-realistic AI voice cloning",
        "applicationCategory": "Audio"
      }
    },
    {
      "@type": "ListItem",
      "position": 29,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Suno",
        "url": "https://suno.com",
        "description": "Generate full songs with AI",
        "applicationCategory": "Audio"
      }
    },
    {
      "@type": "ListItem",
      "position": 30,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Udio",
        "url": "https://udio.com",
        "description": "AI music creation and generation",
        "applicationCategory": "Audio"
      }
    },
    {
      "@type": "ListItem",
      "position": 31,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Murf AI",
        "url": "https://murf.ai",
        "description": "AI voiceover and text-to-speech",
        "applicationCategory": "Audio"
      }
    },
    {
      "@type": "ListItem",
      "position": 32,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Descript",
        "url": "https://descript.com",
        "description": "Edit audio and video like a document",
        "applicationCategory": "Audio"
      }
    },
    {
      "@type": "ListItem",
      "position": 33,
      "item": {
        "@type": "SoftwareApplication",
        "name": "GitHub Copilot",
        "url": "https://github.com/features/copilot",
        "description": "AI pair programmer inside your IDE",
        "applicationCategory": "Code"
      }
    },
    {
      "@type": "ListItem",
      "position": 34,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Cursor",
        "url": "https://cursor.sh",
        "description": "The AI-first code editor",
        "applicationCategory": "Code"
      }
    },
    {
      "@type": "ListItem",
      "position": 35,
      "item": {
        "@type": "SoftwareApplication",
        "name": "v0",
        "url": "https://v0.dev",
        "description": "Generate UI components with AI by Vercel",
        "applicationCategory": "Code"
      }
    },
    {
      "@type": "ListItem",
      "position": 36,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Bolt",
        "url": "https://bolt.new",
        "description": "Full-stack AI app builder in browser",
        "applicationCategory": "Code"
      }
    },
    {
      "@type": "ListItem",
      "position": 37,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Lovable",
        "url": "https://lovable.dev",
        "description": "AI that builds full web apps from prompts",
        "applicationCategory": "Code"
      }
    },
    {
      "@type": "ListItem",
      "position": 38,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Replit AI",
        "url": "https://replit.com",
        "description": "AI-powered coding in the browser",
        "applicationCategory": "Code"
      }
    },
    {
      "@type": "ListItem",
      "position": 39,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Windsurf",
        "url": "https://codeium.com/windsurf",
        "description": "AI code editor by Codeium",
        "applicationCategory": "Code"
      }
    },
    {
      "@type": "ListItem",
      "position": 40,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Tabnine",
        "url": "https://tabnine.com",
        "description": "AI code completion for all IDEs",
        "applicationCategory": "Code"
      }
    },
    {
      "@type": "ListItem",
      "position": 41,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Jasper",
        "url": "https://jasper.ai",
        "description": "AI for marketing content and copywriting",
        "applicationCategory": "Writing"
      }
    },
    {
      "@type": "ListItem",
      "position": 42,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Copy.ai",
        "url": "https://copy.ai",
        "description": "AI writing and workflow automation",
        "applicationCategory": "Writing"
      }
    },
    {
      "@type": "ListItem",
      "position": 43,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Grammarly",
        "url": "https://grammarly.com",
        "description": "AI grammar and writing assistant",
        "applicationCategory": "Writing"
      }
    },
    {
      "@type": "ListItem",
      "position": 44,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Quillbot",
        "url": "https://quillbot.com",
        "description": "AI paraphrasing and summarisation",
        "applicationCategory": "Writing"
      }
    },
    {
      "@type": "ListItem",
      "position": 45,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Writesonic",
        "url": "https://writesonic.com",
        "description": "AI writing platform for marketers",
        "applicationCategory": "Writing"
      }
    },
    {
      "@type": "ListItem",
      "position": 46,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Notion AI",
        "url": "https://notion.so/ai",
        "description": "AI inside your notes and documents",
        "applicationCategory": "Productivity"
      }
    },
    {
      "@type": "ListItem",
      "position": 47,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Otter.ai",
        "url": "https://otter.ai",
        "description": "AI meeting notes and transcription",
        "applicationCategory": "Productivity"
      }
    },
    {
      "@type": "ListItem",
      "position": 48,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Mem.ai",
        "url": "https://mem.ai",
        "description": "AI-powered notes that self-organise",
        "applicationCategory": "Productivity"
      }
    },
    {
      "@type": "ListItem",
      "position": 49,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Reclaim AI",
        "url": "https://reclaim.ai",
        "description": "AI calendar and time management",
        "applicationCategory": "Productivity"
      }
    },
    {
      "@type": "ListItem",
      "position": 50,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Motion",
        "url": "https://usemotion.com",
        "description": "AI task and project scheduling",
        "applicationCategory": "Productivity"
      }
    },
    {
      "@type": "ListItem",
      "position": 51,
      "item": {
        "@type": "SoftwareApplication",
        "name": "HuggingFace",
        "url": "https://huggingface.co",
        "description": "The GitHub of AI models and datasets",
        "applicationCategory": "Research"
      }
    },
    {
      "@type": "ListItem",
      "position": 52,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Replicate",
        "url": "https://replicate.com",
        "description": "Run open-source AI models via API",
        "applicationCategory": "Research"
      }
    },
    {
      "@type": "ListItem",
      "position": 53,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Together AI",
        "url": "https://together.ai",
        "description": "Fast inference for open-source models",
        "applicationCategory": "Research"
      }
    },
    {
      "@type": "ListItem",
      "position": 54,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Arxiv + AI",
        "url": "https://arxiv.org",
        "description": "Latest AI research papers",
        "applicationCategory": "Research"
      }
    },
    {
      "@type": "ListItem",
      "position": 55,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Figma AI",
        "url": "https://figma.com",
        "description": "AI-powered design features in Figma",
        "applicationCategory": "Design"
      }
    },
    {
      "@type": "ListItem",
      "position": 56,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Framer AI",
        "url": "https://framer.com",
        "description": "AI website builder with animations",
        "applicationCategory": "Design"
      }
    },
    {
      "@type": "ListItem",
      "position": 57,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Looka",
        "url": "https://looka.com",
        "description": "AI logo and brand design maker",
        "applicationCategory": "Design"
      }
    },
    {
      "@type": "ListItem",
      "position": 58,
      "item": {
        "@type": "SoftwareApplication",
        "name": "AdCreative",
        "url": "https://adcreative.ai",
        "description": "AI-generated ad creatives that convert",
        "applicationCategory": "Marketing"
      }
    },
    {
      "@type": "ListItem",
      "position": 59,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Surfer SEO",
        "url": "https://surferseo.com",
        "description": "AI SEO writing and optimisation",
        "applicationCategory": "Marketing"
      }
    },
    {
      "@type": "ListItem",
      "position": 60,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Lately AI",
        "url": "https://lately.ai",
        "description": "AI social media content repurposing",
        "applicationCategory": "Marketing"
      }
    }
  ]
}
  ```
- [technical] Page speed could be better (Lighthouse performance score: 85/100, mobile). LCP: 3.5 s, CLS: 0.07. _(page: https://www.allaidunia.com/)_ — *suggested owner: manual*
- [on_page_seo] Title ("Best AI Video Tools 2026 â Free & Paid Video AI | AllAIDunia") is 62 characters — Google truncates over ~ 30-60. _(page: https://www.allaidunia.com/video-ai-tools.html)_ — *suggested owner: content_agent*
  **Proposed fix:** "Best AI Video Tools 2026 â Free & Paid Video AI |"
- [ai_search_geo] No schema.org markup — adding ItemList/SoftwareApplication schema helps AI systems understand and cite this page correctly. _(page: https://www.allaidunia.com/video-ai-tools.html)_ — *suggested owner: content_agent*
  ```
  {
  "@context": "https://schema.org",
  "@type": "ItemList",
  "name": "AllAIDunia — AI Tools Directory",
  "url": "https://www.allaidunia.com/",
  "numberOfItems": 60,
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "item": {
        "@type": "SoftwareApplication",
        "name": "ChatGPT",
        "url": "https://chat.openai.com",
        "description": "OpenAI's flagship AI assistant for everything",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 2,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Claude",
        "url": "https://claude.ai",
        "description": "Anthropic's thoughtful and safe AI assistant",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 3,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Gemini",
        "url": "https://gemini.google.com",
        "description": "Google's powerful multimodal AI model",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 4,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Grok",
        "url": "https://grok.com",
        "description": "xAI's witty real-time AI by Elon Musk",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 5,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Mistral",
        "url": "https://chat.mistral.ai",
        "description": "Open-weight European AI models",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 6,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Meta AI",
        "url": "https://meta.ai",
        "description": "Meta's AI across apps and the web",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 7,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Copilot",
        "url": "https://copilot.microsoft.com",
        "description": "Microsoft's AI assistant powered by GPT-4",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 8,
      "item": {
        "@type": "SoftwareApplication",
        "name": "DeepSeek",
        "url": "https://chat.deepseek.com",
        "description": "Powerful open-source reasoning model",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 9,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Le Chat",
        "url": "https://chat.mistral.ai",
        "description": "Mistral's fast conversational AI",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 10,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Pi AI",
        "url": "https://pi.ai",
        "description": "Your personal AI that listens and learns",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 11,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Perplexity",
        "url": "https://perplexity.ai",
        "description": "AI-powered answer engine with citations",
        "applicationCategory": "Search"
      }
    },
    {
      "@type": "ListItem",
      "position": 12,
      "item": {
        "@type": "SoftwareApplication",
        "name": "You.com",
        "url": "https://you.com",
        "description": "AI search with cited answers",
        "applicationCategory": "Search"
      }
    },
    {
      "@type": "ListItem",
      "position": 13,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Exa AI",
        "url": "https://exa.ai",
        "description": "Neural search for developers and researchers",
        "applicationCategory": "Search"
      }
    },
    {
      "@type": "ListItem",
      "position": 14,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Midjourney",
        "url": "https://midjourney.com",
        "description": "Stunning AI image generation",
        "applicationCategory": "Image"
      }
    },
    {
      "@type": "ListItem",
      "position": 15,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Stable Diff.",
        "url": "https://stability.ai",
        "description": "Open-source image generation model",
        "applicationCategory": "Image"
      }
    },
    {
      "@type": "ListItem",
      "position": 16,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Adobe Firefly",
        "url": "https://firefly.adobe.com",
        "description": "Adobe's generative AI for creatives",
        "applicationCategory": "Image"
      }
    },
    {
      "@type": "ListItem",
      "position": 17,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Krea",
        "url": "https://krea.ai",
        "description": "Real-time AI image creation tool",
        "applicationCategory": "Image"
      }
    },
    {
      "@type": "ListItem",
      "position": 18,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Ideogram",
        "url": "https://ideogram.ai",
        "description": "AI image gen with great text typography",
        "applicationCategory": "Image"
      }
    },
    {
      "@type": "ListItem",
      "position": 19,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Leonardo AI",
        "url": "https://leonardo.ai",
        "description": "AI images for games and creative work",
        "applicationCategory": "Image"
      }
    },
    {
      "@type": "ListItem",
      "position": 20,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Flux",
        "url": "https://blackforestlabs.ai",
        "description": "State of the art image generation model",
        "applicationCategory": "Image"
      }
    },
    {
      "@type": "ListItem",
      "position": 21,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Canva AI",
        "url": "https://canva.com/ai-image-generator",
        "description": "AI image generation inside Canva",
        "applicationCategory": "Image"
      }
    },
    {
      "@type": "ListItem",
      "position": 22,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Runway",
        "url": "https://runwayml.com",
        "description": "AI video generation and editing suite",
        "applicationCategory": "Video"
      }
    },
    {
      "@type": "ListItem",
      "position": 23,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Sora",
        "url": "https://sora.com",
        "description": "OpenAI's text-to-video model",
        "applicationCategory": "Video"
      }
    },
    {
      "@type": "ListItem",
      "position": 24,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Kling AI",
        "url": "https://klingai.com",
        "description": "Realistic AI video generation",
        "applicationCategory": "Video"
      }
    },
    {
      "@type": "ListItem",
      "position": 25,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Pika",
        "url": "https://pika.art",
        "description": "AI video from text or images",
        "applicationCategory": "Video"
      }
    },
    {
      "@type": "ListItem",
      "position": 26,
      "item": {
        "@type": "SoftwareApplication",
        "name": "HeyGen",
        "url": "https://heygen.com",
        "description": "AI avatar video creator for business",
        "applicationCategory": "Video"
      }
    },
    {
      "@type": "ListItem",
      "position": 27,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Synthesia",
        "url": "https://synthesia.io",
        "description": "AI video with realistic avatars",
        "applicationCategory": "Video"
      }
    },
    {
      "@type": "ListItem",
      "position": 28,
      "item": {
        "@type": "SoftwareApplication",
        "name": "ElevenLabs",
        "url": "https://elevenlabs.io",
        "description": "Ultra-realistic AI voice cloning",
        "applicationCategory": "Audio"
      }
    },
    {
      "@type": "ListItem",
      "position": 29,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Suno",
        "url": "https://suno.com",
        "description": "Generate full songs with AI",
        "applicationCategory": "Audio"
      }
    },
    {
      "@type": "ListItem",
      "position": 30,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Udio",
        "url": "https://udio.com",
        "description": "AI music creation and generation",
        "applicationCategory": "Audio"
      }
    },
    {
      "@type": "ListItem",
      "position": 31,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Murf AI",
        "url": "https://murf.ai",
        "description": "AI voiceover and text-to-speech",
        "applicationCategory": "Audio"
      }
    },
    {
      "@type": "ListItem",
      "position": 32,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Descript",
        "url": "https://descript.com",
        "description": "Edit audio and video like a document",
        "applicationCategory": "Audio"
      }
    },
    {
      "@type": "ListItem",
      "position": 33,
      "item": {
        "@type": "SoftwareApplication",
        "name": "GitHub Copilot",
        "url": "https://github.com/features/copilot",
        "description": "AI pair programmer inside your IDE",
        "applicationCategory": "Code"
      }
    },
    {
      "@type": "ListItem",
      "position": 34,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Cursor",
        "url": "https://cursor.sh",
        "description": "The AI-first code editor",
        "applicationCategory": "Code"
      }
    },
    {
      "@type": "ListItem",
      "position": 35,
      "item": {
        "@type": "SoftwareApplication",
        "name": "v0",
        "url": "https://v0.dev",
        "description": "Generate UI components with AI by Vercel",
        "applicationCategory": "Code"
      }
    },
    {
      "@type": "ListItem",
      "position": 36,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Bolt",
        "url": "https://bolt.new",
        "description": "Full-stack AI app builder in browser",
        "applicationCategory": "Code"
      }
    },
    {
      "@type": "ListItem",
      "position": 37,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Lovable",
        "url": "https://lovable.dev",
        "description": "AI that builds full web apps from prompts",
        "applicationCategory": "Code"
      }
    },
    {
      "@type": "ListItem",
      "position": 38,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Replit AI",
        "url": "https://replit.com",
        "description": "AI-powered coding in the browser",
        "applicationCategory": "Code"
      }
    },
    {
      "@type": "ListItem",
      "position": 39,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Windsurf",
        "url": "https://codeium.com/windsurf",
        "description": "AI code editor by Codeium",
        "applicationCategory": "Code"
      }
    },
    {
      "@type": "ListItem",
      "position": 40,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Tabnine",
        "url": "https://tabnine.com",
        "description": "AI code completion for all IDEs",
        "applicationCategory": "Code"
      }
    },
    {
      "@type": "ListItem",
      "position": 41,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Jasper",
        "url": "https://jasper.ai",
        "description": "AI for marketing content and copywriting",
        "applicationCategory": "Writing"
      }
    },
    {
      "@type": "ListItem",
      "position": 42,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Copy.ai",
        "url": "https://copy.ai",
        "description": "AI writing and workflow automation",
        "applicationCategory": "Writing"
      }
    },
    {
      "@type": "ListItem",
      "position": 43,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Grammarly",
        "url": "https://grammarly.com",
        "description": "AI grammar and writing assistant",
        "applicationCategory": "Writing"
      }
    },
    {
      "@type": "ListItem",
      "position": 44,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Quillbot",
        "url": "https://quillbot.com",
        "description": "AI paraphrasing and summarisation",
        "applicationCategory": "Writing"
      }
    },
    {
      "@type": "ListItem",
      "position": 45,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Writesonic",
        "url": "https://writesonic.com",
        "description": "AI writing platform for marketers",
        "applicationCategory": "Writing"
      }
    },
    {
      "@type": "ListItem",
      "position": 46,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Notion AI",
        "url": "https://notion.so/ai",
        "description": "AI inside your notes and documents",
        "applicationCategory": "Productivity"
      }
    },
    {
      "@type": "ListItem",
      "position": 47,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Otter.ai",
        "url": "https://otter.ai",
        "description": "AI meeting notes and transcription",
        "applicationCategory": "Productivity"
      }
    },
    {
      "@type": "ListItem",
      "position": 48,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Mem.ai",
        "url": "https://mem.ai",
        "description": "AI-powered notes that self-organise",
        "applicationCategory": "Productivity"
      }
    },
    {
      "@type": "ListItem",
      "position": 49,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Reclaim AI",
        "url": "https://reclaim.ai",
        "description": "AI calendar and time management",
        "applicationCategory": "Productivity"
      }
    },
    {
      "@type": "ListItem",
      "position": 50,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Motion",
        "url": "https://usemotion.com",
        "description": "AI task and project scheduling",
        "applicationCategory": "Productivity"
      }
    },
    {
      "@type": "ListItem",
      "position": 51,
      "item": {
        "@type": "SoftwareApplication",
        "name": "HuggingFace",
        "url": "https://huggingface.co",
        "description": "The GitHub of AI models and datasets",
        "applicationCategory": "Research"
      }
    },
    {
      "@type": "ListItem",
      "position": 52,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Replicate",
        "url": "https://replicate.com",
        "description": "Run open-source AI models via API",
        "applicationCategory": "Research"
      }
    },
    {
      "@type": "ListItem",
      "position": 53,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Together AI",
        "url": "https://together.ai",
        "description": "Fast inference for open-source models",
        "applicationCategory": "Research"
      }
    },
    {
      "@type": "ListItem",
      "position": 54,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Arxiv + AI",
        "url": "https://arxiv.org",
        "description": "Latest AI research papers",
        "applicationCategory": "Research"
      }
    },
    {
      "@type": "ListItem",
      "position": 55,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Figma AI",
        "url": "https://figma.com",
        "description": "AI-powered design features in Figma",
        "applicationCategory": "Design"
      }
    },
    {
      "@type": "ListItem",
      "position": 56,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Framer AI",
        "url": "https://framer.com",
        "description": "AI website builder with animations",
        "applicationCategory": "Design"
      }
    },
    {
      "@type": "ListItem",
      "position": 57,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Looka",
        "url": "https://looka.com",
        "description": "AI logo and brand design maker",
        "applicationCategory": "Design"
      }
    },
    {
      "@type": "ListItem",
      "position": 58,
      "item": {
        "@type": "SoftwareApplication",
        "name": "AdCreative",
        "url": "https://adcreative.ai",
        "description": "AI-generated ad creatives that convert",
        "applicationCategory": "Marketing"
      }
    },
    {
      "@type": "ListItem",
      "position": 59,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Surfer SEO",
        "url": "https://surferseo.com",
        "description": "AI SEO writing and optimisation",
        "applicationCategory": "Marketing"
      }
    },
    {
      "@type": "ListItem",
      "position": 60,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Lately AI",
        "url": "https://lately.ai",
        "description": "AI social media content repurposing",
        "applicationCategory": "Marketing"
      }
    }
  ]
}
  ```
- [technical] Page speed could be better (Lighthouse performance score: 71/100, mobile). LCP: 3.2 s, CLS: 0.38. _(page: https://www.allaidunia.com/video-ai-tools.html)_ — *suggested owner: manual*
- [ai_search_geo] No schema.org markup — adding ItemList/SoftwareApplication schema helps AI systems understand and cite this page correctly. _(page: https://www.allaidunia.com/best-free-ai-video-editing-tools.html)_ — *suggested owner: content_agent*
  ```
  {
  "@context": "https://schema.org",
  "@type": "ItemList",
  "name": "AllAIDunia — AI Tools Directory",
  "url": "https://www.allaidunia.com/",
  "numberOfItems": 60,
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "item": {
        "@type": "SoftwareApplication",
        "name": "ChatGPT",
        "url": "https://chat.openai.com",
        "description": "OpenAI's flagship AI assistant for everything",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 2,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Claude",
        "url": "https://claude.ai",
        "description": "Anthropic's thoughtful and safe AI assistant",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 3,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Gemini",
        "url": "https://gemini.google.com",
        "description": "Google's powerful multimodal AI model",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 4,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Grok",
        "url": "https://grok.com",
        "description": "xAI's witty real-time AI by Elon Musk",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 5,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Mistral",
        "url": "https://chat.mistral.ai",
        "description": "Open-weight European AI models",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 6,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Meta AI",
        "url": "https://meta.ai",
        "description": "Meta's AI across apps and the web",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 7,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Copilot",
        "url": "https://copilot.microsoft.com",
        "description": "Microsoft's AI assistant powered by GPT-4",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 8,
      "item": {
        "@type": "SoftwareApplication",
        "name": "DeepSeek",
        "url": "https://chat.deepseek.com",
        "description": "Powerful open-source reasoning model",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 9,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Le Chat",
        "url": "https://chat.mistral.ai",
        "description": "Mistral's fast conversational AI",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 10,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Pi AI",
        "url": "https://pi.ai",
        "description": "Your personal AI that listens and learns",
        "applicationCategory": "Chat"
      }
    },
    {
      "@type": "ListItem",
      "position": 11,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Perplexity",
        "url": "https://perplexity.ai",
        "description": "AI-powered answer engine with citations",
        "applicationCategory": "Search"
      }
    },
    {
      "@type": "ListItem",
      "position": 12,
      "item": {
        "@type": "SoftwareApplication",
        "name": "You.com",
        "url": "https://you.com",
        "description": "AI search with cited answers",
        "applicationCategory": "Search"
      }
    },
    {
      "@type": "ListItem",
      "position": 13,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Exa AI",
        "url": "https://exa.ai",
        "description": "Neural search for developers and researchers",
        "applicationCategory": "Search"
      }
    },
    {
      "@type": "ListItem",
      "position": 14,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Midjourney",
        "url": "https://midjourney.com",
        "description": "Stunning AI image generation",
        "applicationCategory": "Image"
      }
    },
    {
      "@type": "ListItem",
      "position": 15,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Stable Diff.",
        "url": "https://stability.ai",
        "description": "Open-source image generation model",
        "applicationCategory": "Image"
      }
    },
    {
      "@type": "ListItem",
      "position": 16,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Adobe Firefly",
        "url": "https://firefly.adobe.com",
        "description": "Adobe's generative AI for creatives",
        "applicationCategory": "Image"
      }
    },
    {
      "@type": "ListItem",
      "position": 17,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Krea",
        "url": "https://krea.ai",
        "description": "Real-time AI image creation tool",
        "applicationCategory": "Image"
      }
    },
    {
      "@type": "ListItem",
      "position": 18,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Ideogram",
        "url": "https://ideogram.ai",
        "description": "AI image gen with great text typography",
        "applicationCategory": "Image"
      }
    },
    {
      "@type": "ListItem",
      "position": 19,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Leonardo AI",
        "url": "https://leonardo.ai",
        "description": "AI images for games and creative work",
        "applicationCategory": "Image"
      }
    },
    {
      "@type": "ListItem",
      "position": 20,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Flux",
        "url": "https://blackforestlabs.ai",
        "description": "State of the art image generation model",
        "applicationCategory": "Image"
      }
    },
    {
      "@type": "ListItem",
      "position": 21,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Canva AI",
        "url": "https://canva.com/ai-image-generator",
        "description": "AI image generation inside Canva",
        "applicationCategory": "Image"
      }
    },
    {
      "@type": "ListItem",
      "position": 22,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Runway",
        "url": "https://runwayml.com",
        "description": "AI video generation and editing suite",
        "applicationCategory": "Video"
      }
    },
    {
      "@type": "ListItem",
      "position": 23,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Sora",
        "url": "https://sora.com",
        "description": "OpenAI's text-to-video model",
        "applicationCategory": "Video"
      }
    },
    {
      "@type": "ListItem",
      "position": 24,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Kling AI",
        "url": "https://klingai.com",
        "description": "Realistic AI video generation",
        "applicationCategory": "Video"
      }
    },
    {
      "@type": "ListItem",
      "position": 25,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Pika",
        "url": "https://pika.art",
        "description": "AI video from text or images",
        "applicationCategory": "Video"
      }
    },
    {
      "@type": "ListItem",
      "position": 26,
      "item": {
        "@type": "SoftwareApplication",
        "name": "HeyGen",
        "url": "https://heygen.com",
        "description": "AI avatar video creator for business",
        "applicationCategory": "Video"
      }
    },
    {
      "@type": "ListItem",
      "position": 27,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Synthesia",
        "url": "https://synthesia.io",
        "description": "AI video with realistic avatars",
        "applicationCategory": "Video"
      }
    },
    {
      "@type": "ListItem",
      "position": 28,
      "item": {
        "@type": "SoftwareApplication",
        "name": "ElevenLabs",
        "url": "https://elevenlabs.io",
        "description": "Ultra-realistic AI voice cloning",
        "applicationCategory": "Audio"
      }
    },
    {
      "@type": "ListItem",
      "position": 29,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Suno",
        "url": "https://suno.com",
        "description": "Generate full songs with AI",
        "applicationCategory": "Audio"
      }
    },
    {
      "@type": "ListItem",
      "position": 30,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Udio",
        "url": "https://udio.com",
        "description": "AI music creation and generation",
        "applicationCategory": "Audio"
      }
    },
    {
      "@type": "ListItem",
      "position": 31,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Murf AI",
        "url": "https://murf.ai",
        "description": "AI voiceover and text-to-speech",
        "applicationCategory": "Audio"
      }
    },
    {
      "@type": "ListItem",
      "position": 32,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Descript",
        "url": "https://descript.com",
        "description": "Edit audio and video like a document",
        "applicationCategory": "Audio"
      }
    },
    {
      "@type": "ListItem",
      "position": 33,
      "item": {
        "@type": "SoftwareApplication",
        "name": "GitHub Copilot",
        "url": "https://github.com/features/copilot",
        "description": "AI pair programmer inside your IDE",
        "applicationCategory": "Code"
      }
    },
    {
      "@type": "ListItem",
      "position": 34,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Cursor",
        "url": "https://cursor.sh",
        "description": "The AI-first code editor",
        "applicationCategory": "Code"
      }
    },
    {
      "@type": "ListItem",
      "position": 35,
      "item": {
        "@type": "SoftwareApplication",
        "name": "v0",
        "url": "https://v0.dev",
        "description": "Generate UI components with AI by Vercel",
        "applicationCategory": "Code"
      }
    },
    {
      "@type": "ListItem",
      "position": 36,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Bolt",
        "url": "https://bolt.new",
        "description": "Full-stack AI app builder in browser",
        "applicationCategory": "Code"
      }
    },
    {
      "@type": "ListItem",
      "position": 37,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Lovable",
        "url": "https://lovable.dev",
        "description": "AI that builds full web apps from prompts",
        "applicationCategory": "Code"
      }
    },
    {
      "@type": "ListItem",
      "position": 38,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Replit AI",
        "url": "https://replit.com",
        "description": "AI-powered coding in the browser",
        "applicationCategory": "Code"
      }
    },
    {
      "@type": "ListItem",
      "position": 39,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Windsurf",
        "url": "https://codeium.com/windsurf",
        "description": "AI code editor by Codeium",
        "applicationCategory": "Code"
      }
    },
    {
      "@type": "ListItem",
      "position": 40,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Tabnine",
        "url": "https://tabnine.com",
        "description": "AI code completion for all IDEs",
        "applicationCategory": "Code"
      }
    },
    {
      "@type": "ListItem",
      "position": 41,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Jasper",
        "url": "https://jasper.ai",
        "description": "AI for marketing content and copywriting",
        "applicationCategory": "Writing"
      }
    },
    {
      "@type": "ListItem",
      "position": 42,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Copy.ai",
        "url": "https://copy.ai",
        "description": "AI writing and workflow automation",
        "applicationCategory": "Writing"
      }
    },
    {
      "@type": "ListItem",
      "position": 43,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Grammarly",
        "url": "https://grammarly.com",
        "description": "AI grammar and writing assistant",
        "applicationCategory": "Writing"
      }
    },
    {
      "@type": "ListItem",
      "position": 44,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Quillbot",
        "url": "https://quillbot.com",
        "description": "AI paraphrasing and summarisation",
        "applicationCategory": "Writing"
      }
    },
    {
      "@type": "ListItem",
      "position": 45,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Writesonic",
        "url": "https://writesonic.com",
        "description": "AI writing platform for marketers",
        "applicationCategory": "Writing"
      }
    },
    {
      "@type": "ListItem",
      "position": 46,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Notion AI",
        "url": "https://notion.so/ai",
        "description": "AI inside your notes and documents",
        "applicationCategory": "Productivity"
      }
    },
    {
      "@type": "ListItem",
      "position": 47,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Otter.ai",
        "url": "https://otter.ai",
        "description": "AI meeting notes and transcription",
        "applicationCategory": "Productivity"
      }
    },
    {
      "@type": "ListItem",
      "position": 48,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Mem.ai",
        "url": "https://mem.ai",
        "description": "AI-powered notes that self-organise",
        "applicationCategory": "Productivity"
      }
    },
    {
      "@type": "ListItem",
      "position": 49,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Reclaim AI",
        "url": "https://reclaim.ai",
        "description": "AI calendar and time management",
        "applicationCategory": "Productivity"
      }
    },
    {
      "@type": "ListItem",
      "position": 50,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Motion",
        "url": "https://usemotion.com",
        "description": "AI task and project scheduling",
        "applicationCategory": "Productivity"
      }
    },
    {
      "@type": "ListItem",
      "position": 51,
      "item": {
        "@type": "SoftwareApplication",
        "name": "HuggingFace",
        "url": "https://huggingface.co",
        "description": "The GitHub of AI models and datasets",
        "applicationCategory": "Research"
      }
    },
    {
      "@type": "ListItem",
      "position": 52,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Replicate",
        "url": "https://replicate.com",
        "description": "Run open-source AI models via API",
        "applicationCategory": "Research"
      }
    },
    {
      "@type": "ListItem",
      "position": 53,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Together AI",
        "url": "https://together.ai",
        "description": "Fast inference for open-source models",
        "applicationCategory": "Research"
      }
    },
    {
      "@type": "ListItem",
      "position": 54,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Arxiv + AI",
        "url": "https://arxiv.org",
        "description": "Latest AI research papers",
        "applicationCategory": "Research"
      }
    },
    {
      "@type": "ListItem",
      "position": 55,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Figma AI",
        "url": "https://figma.com",
        "description": "AI-powered design features in Figma",
        "applicationCategory": "Design"
      }
    },
    {
      "@type": "ListItem",
      "position": 56,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Framer AI",
        "url": "https://framer.com",
        "description": "AI website builder with animations",
        "applicationCategory": "Design"
      }
    },
    {
      "@type": "ListItem",
      "position": 57,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Looka",
        "url": "https://looka.com",
        "description": "AI logo and brand design maker",
        "applicationCategory": "Design"
      }
    },
    {
      "@type": "ListItem",
      "position": 58,
      "item": {
        "@type": "SoftwareApplication",
        "name": "AdCreative",
        "url": "https://adcreative.ai",
        "description": "AI-generated ad creatives that convert",
        "applicationCategory": "Marketing"
      }
    },
    {
      "@type": "ListItem",
      "position": 59,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Surfer SEO",
        "url": "https://surferseo.com",
        "description": "AI SEO writing and optimisation",
        "applicationCategory": "Marketing"
      }
    },
    {
      "@type": "ListItem",
      "position": 60,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Lately AI",
        "url": "https://lately.ai",
        "description": "AI social media content repurposing",
        "applicationCategory": "Marketing"
      }
    }
  ]
}
  ```

### Low Priority
- [ai_search_geo] No llms.txt file — an emerging standard giving AI systems a clean, structured summary of your site. Not yet universal, but cheap to add and forward-looking. — *suggested owner: content_agent*
  ```
  # AllAIDunia

> A free directory of 60+ AI tools, organized by category.

## Audio
- [ElevenLabs](https://elevenlabs.io): Ultra-realistic AI voice cloning
- [Suno](https://suno.com): Generate full songs with AI
- [Udio](https://udio.com): AI music creation and generation
- [Murf AI](https://murf.ai): AI voiceover and text-to-speech
- [Descript](https://descript.com): Edit audio and video like a document

## Chat
- [ChatGPT](https://chat.openai.com): OpenAI's flagship AI assistant for everything
- [Claude](https://claude.ai): Anthropic's thoughtful and safe AI assistant
- [Gemini](https://gemini.google.com): Google's powerful multimodal AI model
- [Grok](https://grok.com): xAI's witty real-time AI by Elon Musk
- [Mistral](https://chat.mistral.ai): Open-weight European AI models
- [Meta AI](https://meta.ai): Meta's AI across apps and the web
- [Copilot](https://copilot.microsoft.com): Microsoft's AI assistant powered by GPT-4
- [DeepSeek](https://chat.deepseek.com): Powerful open-source reasoning model
- [Le Chat](https://chat.mistral.ai): Mistral's fast conversational AI
- [Pi AI](https://pi.ai): Your personal AI that listens and learns

## Code
- [GitHub Copilot](https://github.com/features/copilot): AI pair programmer inside your IDE
- [Cursor](https://cursor.sh): The AI-first code editor
- [v0](https://v0.dev): Generate UI components with AI by Vercel
- [Bolt](https://bolt.new): Full-stack AI app builder in browser
- [Lovable](https://lovable.dev): AI that builds full web apps from prompts
- [Replit AI](https://replit.com): AI-powered coding in the browser
- [Windsurf](https://codeium.com/windsurf): AI code editor by Codeium
- [Tabnine](https://tabnine.com): AI code completion for all IDEs

## Design
- [Figma AI](https://figma.com): AI-powered design features in Figma
- [Framer AI](https://framer.com): AI website builder with animations
- [Looka](https://looka.com): AI logo and brand design maker

## Image
- [Midjourney](https://midjourney.com): Stunning AI image generation
- [Stable Diff.](https://stability.ai): Open-source image generation model
- [Adobe Firefly](https://firefly.adobe.com): Adobe's generative AI for creatives
- [Krea](https://krea.ai): Real-time AI image creation tool
- [Ideogram](https://ideogram.ai): AI image gen with great text typography
- [Leonardo AI](https://leonardo.ai): AI images for games and creative work
- [Flux](https://blackforestlabs.ai): State of the art image generation model
- [Canva AI](https://canva.com/ai-image-generator): AI image generation inside Canva

## Marketing
- [AdCreative](https://adcreative.ai): AI-generated ad creatives that convert
- [Surfer SEO](https://surferseo.com): AI SEO writing and optimisation
- [Lately AI](https://lately.ai): AI social media content repurposing

## Productivity
- [Notion AI](https://notion.so/ai): AI inside your notes and documents
- [Otter.ai](https://otter.ai): AI meeting notes and transcription
- [Mem.ai](https://mem.ai): AI-powered notes that self-organise
- [Reclaim AI](https://reclaim.ai): AI calendar and time management
- [Motion](https://usemotion.com): AI task and project scheduling

## Research
- [HuggingFace](https://huggingface.co): The GitHub of AI models and datasets
- [Replicate](https://replicate.com): Run open-source AI models via API
- [Together AI](https://together.ai): Fast inference for open-source models
- [Arxiv + AI](https://arxiv.org): Latest AI research papers

## Search
- [Perplexity](https://perplexity.ai): AI-powered answer engine with citations
- [You.com](https://you.com): AI search with cited answers
- [Exa AI](https://exa.ai): Neural search for developers and researchers

## Video
- [Runway](https://runwayml.com): AI video generation and editing suite
- [Sora](https://sora.com): OpenAI's text-to-video model
- [Kling AI](https://klingai.com): Realistic AI video generation
- [Pika](https://pika.art): AI video from text or images
- [HeyGen](https://heygen.com): AI avatar video creator for business
- [Synthesia](https://synthesia.io): AI video with realistic avatars

## Writing
- [Jasper](https://jasper.ai): AI for marketing content and copywriting
- [Copy.ai](https://copy.ai): AI writing and workflow automation
- [Grammarly](https://grammarly.com): AI grammar and writing assistant
- [Quillbot](https://quillbot.com): AI paraphrasing and summarisation
- [Writesonic](https://writesonic.com): AI writing platform for marketers

  ```
- [on_page_seo] Meta description is 179 characters — will get truncated. _(page: https://www.allaidunia.com/)_ — *suggested owner: content_agent*
  **Proposed fix:** "Looking for an AI tool? AllAIDunia organizes 60+ AI tools by category â document writing, video editing, image generation, coding, and more. Free…"
- [on_page_seo] Missing Open Graph tags (og:image) — affects how this page's links look when shared on social media, Slack, or WhatsApp. _(page: https://www.allaidunia.com/)_ — *suggested owner: content_agent*
- [ai_search_geo] No lists or tables — AI answer engines strongly prefer content structured for easy extraction and citation. _(page: https://www.allaidunia.com/)_ — *suggested owner: content_agent*
- [on_page_seo] Missing Open Graph tags (og:image) — affects how this page's links look when shared on social media, Slack, or WhatsApp. _(page: https://www.allaidunia.com/video-ai-tools.html)_ — *suggested owner: content_agent*
- [ai_search_geo] No lists or tables — AI answer engines strongly prefer content structured for easy extraction and citation. _(page: https://www.allaidunia.com/video-ai-tools.html)_ — *suggested owner: content_agent*
- [on_page_seo] Meta description is 164 characters — will get truncated. _(page: https://www.allaidunia.com/best-free-ai-video-editing-tools.html)_ — *suggested owner: content_agent*
  **Proposed fix:** "Editing video the old way takes hours. Here are the best free AI tools for video editing in 2026 â from text-to-video generation to AI avatars, compared…"
- [on_page_seo] Missing Open Graph tags (og:image) — affects how this page's links look when shared on social media, Slack, or WhatsApp. _(page: https://www.allaidunia.com/best-free-ai-video-editing-tools.html)_ — *suggested owner: content_agent*
- [ai_search_geo] No lists or tables — AI answer engines strongly prefer content structured for easy extraction and citation. _(page: https://www.allaidunia.com/best-free-ai-video-editing-tools.html)_ — *suggested owner: content_agent*


## Overview
| Metric | Value |
|---|---|
| Total queries seen | 1 |
| Total clicks | 0 |
| Total impressions | 4 |
| Average position | 8.8 |
| Overall CTR | 0.0% |

## AI Search Readiness (GEO/AEO)
Whether AI answer engines (ChatGPT, Perplexity, Gemini, Google AI Overviews) can find, understand, and cite this site.

- AI crawler access: all checked crawlers allowed
- llms.txt present: No
- Schema types found across site: **none**

## On-Page Audit
3 page(s) checked from the sitemap.

| Page | Indexed | Title Length | Meta Desc | H1s | Images Missing Alt | Word Count |
|---|---|---|---|---|---|---|
| https://www.allaidunia.com/ | Yes | 70 | Yes | 1 | 0 | 881 |
| https://www.allaidunia.com/video-ai-tools.html | **NO** (NEUTRAL) | 62 | Yes | 1 | 0 | 246 |
| https://www.allaidunia.com/best-free-ai-video-editing-tools.html | **NO** (NEUTRAL) | 57 | Yes | 1 | 0 | 571 |

## Top Queries by Visibility

| Query | Position | Impressions | Clicks | CTR |
|---|---|---|---|---|
| ai dunia | 8.8 | 4 | 0 | 0% |