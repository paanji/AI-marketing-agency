/**
 * AllAIDunia — Prompt Guru Worker (v2)
 * ----------------------------------------------------------------------------
 * Endpoints:
 *   POST /api/prompt-guru/questions   { request, category }
 *       -> { category, questions: [ { q, examples: [...] } ] }
 *   POST /api/prompt-guru/synthesize  { original_request, qa, tool, category }
 *       -> { prompt, tool_label, tool_url }
 *
 * v2 changes:
 *   - All categories supported (image, video, website, writing, code,
 *     voiceover, music, logo). Client sends the category chosen on the
 *     start screen; "auto" lets the model infer.
 *   - Questions now come with 3-4 tappable example answers each.
 *   - logo reuses image format rules (CATEGORY_ALIAS).
 *   - Tools without curated rules fall back to the model's own knowledge.
 *
 * Bindings required: GURU_KV (KV), OPENAI_API_KEY (secret).
 */

const ALLOWED_ORIGINS = [
  "https://www.allaidunia.com",
  "https://allaidunia.com"
];

const FORMATS_URL = "https://www.allaidunia.com/prompt_formats.json";
const OPENAI_MODEL = "gpt-4o-mini";
const DAILY_LIMIT_PER_IP = 20;

const VALID_CATEGORIES = ["image", "video", "website", "writing", "code", "voiceover", "music", "logo"];
// Categories whose curated format rules live under a different key
const CATEGORY_ALIAS = { logo: "image" };

function corsHeaders(origin) {
  const allow = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];
  return {
    "Access-Control-Allow-Origin": allow,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json"
  };
}

function json(data, status, origin) {
  return new Response(JSON.stringify(data), { status: status || 200, headers: corsHeaders(origin) });
}

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

async function checkRateLimit(env, ip) {
  const key = "rl:" + ip + ":" + todayStr();
  const current = parseInt((await env.GURU_KV.get(key)) || "0", 10);
  if (current >= DAILY_LIMIT_PER_IP) return false;
  await env.GURU_KV.put(key, String(current + 1), { expirationTtl: 90000 });
  return true;
}

async function callOpenAI(env, systemPrompt, userContent, jsonMode) {
  const body = {
    model: OPENAI_MODEL,
    messages: [
      { role: "system", content: systemPrompt },
      { role: "user", content: userContent }
    ],
    max_tokens: 800,
    temperature: 0.7
  };
  if (jsonMode) body.response_format = { type: "json_object" };

  const resp = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer " + env.OPENAI_API_KEY
    },
    body: JSON.stringify(body)
  });

  if (!resp.ok) {
    const errText = await resp.text();
    throw new Error("OpenAI error " + resp.status + ": " + errText.slice(0, 200));
  }
  const data = await resp.json();
  return data.choices?.[0]?.message?.content || "";
}

/* ---------------- Endpoint 1: tailored questions with example answers ---------------- */

async function handleQuestions(request, env, origin) {
  let body;
  try { body = await request.json(); } catch { return json({ error: "Malformed request" }, 400, origin); }

  const userRequest = (body.request || "").trim();
  let category = String(body.category || "auto").toLowerCase();
  if (category !== "auto" && !VALID_CATEGORIES.includes(category)) category = "auto";

  if (!userRequest || userRequest.length < 5) {
    return json({ error: "Please describe what you want to create." }, 400, origin);
  }
  if (userRequest.length > 1000) {
    return json({ error: "Description too long — keep it under 1000 characters." }, 400, origin);
  }

  const categoryLine = category === "auto"
    ? 'First decide the best-fitting category from this list: ' + VALID_CATEGORIES.join(", ") + "."
    : 'The user has already chosen the category: "' + category + '". Do not change it.';

  const systemPrompt = [
    "You are a senior prompt engineer helping a user craft the perfect prompt for an AI tool.",
    categoryLine,
    "Read their request and respond ONLY with a JSON object of this exact shape:",
    '{ "category": "<category>", "questions": [ { "q": "...", "examples": ["...", "...", "..."] } ] }',
    "Rules:",
    "- Ask 3 or 4 SHORT clarifying questions SPECIFIC to their exact request — never generic form questions.",
    "- Never ask something their request already answers.",
    "- Each question gets 3-4 SHORT example answers (2-5 words each) that a beginner could tap to answer — realistic, varied options for THEIR request, not abstract labels.",
    "- Questions should cover what most affects prompt quality for this category (style, mood, composition/camera for visuals; structure, tone, audience for writing; pages, features, look for websites; genre, tempo, vocals for music; voice character, pacing for voiceovers; language/framework, constraints for code).",
    "- Do NOT ask which tool they'll use — handled separately."
  ].join("\n");

  const raw = await callOpenAI(env, systemPrompt, userRequest, true);

  let parsed;
  try { parsed = JSON.parse(raw); } catch { return json({ error: "Could not generate questions — try rephrasing your request." }, 502, origin); }

  let outCategory = String(parsed.category || "").toLowerCase();
  if (!VALID_CATEGORIES.includes(outCategory)) {
    outCategory = category === "auto" ? "image" : category;
  }

  const rawQs = Array.isArray(parsed.questions) ? parsed.questions.slice(0, 4) : [];
  const questions = rawQs.map(item => {
    if (typeof item === "string") return { q: item, examples: [] };
    return {
      q: String(item.q || "").slice(0, 300),
      examples: Array.isArray(item.examples) ? item.examples.slice(0, 4).map(e => String(e).slice(0, 60)) : []
    };
  }).filter(item => item.q);

  if (questions.length < 2) {
    return json({ error: "Could not generate questions — try rephrasing your request." }, 502, origin);
  }

  return json({ category: outCategory, questions }, 200, origin);
}

/* ---------------- Endpoint 2: synthesize the final prompt ---------------- */

async function handleSynthesize(request, env, origin) {
  let body;
  try { body = await request.json(); } catch { return json({ error: "Malformed request" }, 400, origin); }

  const { original_request, qa, tool, category } = body || {};
  if (!original_request || !Array.isArray(qa) || !tool || !category) {
    return json({ error: "Missing required fields." }, 400, origin);
  }

  let formats;
  try {
    const fResp = await fetch(FORMATS_URL, { cf: { cacheTtl: 600, cacheEverything: true } });
    formats = await fResp.json();
  } catch {
    return json({ error: "Could not load tool format rules — try again shortly." }, 502, origin);
  }

  const cat = String(category).toLowerCase();
  const formatKey = CATEGORY_ALIAS[cat] || cat;
  const toolSpec = formats?.[formatKey]?.[tool];

  const qaText = qa
    .slice(0, 6)
    .map(p => "Q: " + String(p.q).slice(0, 200) + "\nA: " + String(p.a).slice(0, 300))
    .join("\n");

  var systemPrompt;
  var toolLabel;
  var toolUrl = null;

  const categoryHint = cat === "logo"
    ? "The user is creating a LOGO — favor clean, iconic, brand-appropriate design language in the prompt."
    : "";

  if (toolSpec) {
    toolLabel = toolSpec.label;
    toolUrl = toolSpec.directory_url;
    systemPrompt = [
      "You are a senior prompt engineer. Compose the single best prompt for the tool: " + toolSpec.label + ".",
      categoryHint,
      "Strictly follow these format rules for this tool:",
      ...toolSpec.rules.map(r => "- " + r),
      "Here is an example of a well-formatted prompt for this tool (match its FORMAT, not its content):",
      toolSpec.example,
      "Output ONLY the final prompt. No explanation, no preamble, no quotes around it."
    ].filter(Boolean).join("\n");
  } else {
    const customToolName = String(tool).slice(0, 80);
    toolLabel = customToolName;
    systemPrompt = [
      "You are a senior prompt engineer. Compose the single best prompt for the AI tool: \"" + customToolName + "\".",
      categoryHint,
      "Use your own knowledge of that specific tool's known prompting conventions and syntax if you have it.",
      "If you are not confident about this tool's exact syntax, default to clean, natural-language descriptive prose — do not invent fake flags or syntax you are not sure is real.",
      "Output ONLY the final prompt. No explanation, no preamble, no quotes around it, and do not mention that you were unsure."
    ].filter(Boolean).join("\n");
  }

  const userContent =
    "The user's original request: " + String(original_request).slice(0, 1000) +
    "\n\nClarifying answers gathered:\n" + qaText;

  const prompt = (await callOpenAI(env, systemPrompt, userContent, false)).trim();
  if (!prompt) return json({ error: "Could not generate a prompt — please try again." }, 502, origin);

  return json({ prompt, tool_label: toolLabel, tool_url: toolUrl }, 200, origin);
}

/* ---------------- Router ---------------- */

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders(origin) });
    }
    if (request.method !== "POST") {
      return json({ error: "Not found" }, 404, origin);
    }

    try {
      const ip = request.headers.get("CF-Connecting-IP") || "unknown";
      const allowed = await checkRateLimit(env, ip);
      if (!allowed) {
        return json({ error: "Daily limit reached — come back tomorrow!" }, 429, origin);
      }

      if (url.pathname === "/api/prompt-guru/questions") {
        return await handleQuestions(request, env, origin);
      }
      if (url.pathname === "/api/prompt-guru/synthesize") {
        return await handleSynthesize(request, env, origin);
      }
    } catch (err) {
      return json({ error: "Something went wrong: " + err.message }, 500, origin);
    }

    return json({ error: "Not found" }, 404, origin);
  }
};
