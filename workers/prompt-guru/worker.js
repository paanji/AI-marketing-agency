/**
 * AllAIDunia — Prompt Guru Worker
 * ----------------------------------------------------------------------------
 * Two endpoints:
 *   POST /api/prompt-guru/questions   { request }                    -> { category, questions: [...] }
 *   POST /api/prompt-guru/synthesize  { original_request, qa, tool, category } -> { prompt }
 *
 * Design decisions (mirroring the rest of the agent system):
 *   - Tool syntax rules live in /prompt_formats.json ON THE LIVE SITE, not in
 *     this code — editing that file changes output format with no redeploy.
 *   - Exactly 2 LLM calls per completed session (1 per endpoint).
 *   - KV-based per-IP daily rate limit protects the OpenAI budget.
 *
 * Setup:
 *   1. wrangler kv:namespace create GURU_KV       -> bind as GURU_KV
 *   2. wrangler secret put OPENAI_API_KEY         -> same key value as chatbot
 *   3. wrangler deploy
 *   (Or merge both handlers into the existing chatbot Worker and reuse its
 *    env.OPENAI_API_KEY — the code below is self-contained either way.)
 */

const ALLOWED_ORIGINS = [
  "https://www.allaidunia.com",
  "https://allaidunia.com"
];

const FORMATS_URL = "https://www.allaidunia.com/prompt_formats.json";
const OPENAI_MODEL = "gpt-4o-mini";
const DAILY_LIMIT_PER_IP = 20; // completed sessions cost 2 calls; 20 calls ≈ 10 sessions/day/IP

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
  // 90000s TTL (~25h) auto-expires old counters, keeping KV clean
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
    max_tokens: 600,
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

/* ---------------- Endpoint 1: generate tailored questions ---------------- */

async function handleQuestions(request, env, origin) {
  let body;
  try { body = await request.json(); } catch { return json({ error: "Malformed request" }, 400, origin); }

  const userRequest = (body.request || "").trim();
  if (!userRequest || userRequest.length < 5) {
    return json({ error: "Please describe what you want to create." }, 400, origin);
  }
  if (userRequest.length > 1000) {
    return json({ error: "Description too long — keep it under 1000 characters." }, 400, origin);
  }

  const systemPrompt = [
    "You are a senior prompt engineer helping a user craft the perfect prompt for an AI image or video generation tool.",
    "Read their request and respond ONLY with a JSON object of this exact shape:",
    '{ "category": "image" | "video", "questions": ["...", "...", "..."] }',
    "Rules for the questions:",
    "- Ask 3 or 4 SHORT clarifying questions SPECIFIC to their exact request — never generic form questions.",
    "- Never ask something their request already answers.",
    "- Each question must be answerable in a few words.",
    "- Questions should cover the details that most affect prompt quality: style, mood/lighting, composition/camera, and anything ambiguous in their request.",
    "- If the request could be either image or video, pick the more likely one from their wording.",
    "- Do NOT ask which tool they'll use — that is handled separately."
  ].join("\n");

  const raw = await callOpenAI(env, systemPrompt, userRequest, true);

  let parsed;
  try { parsed = JSON.parse(raw); } catch { return json({ error: "Could not generate questions — try rephrasing your request." }, 502, origin); }

  const category = parsed.category === "video" ? "video" : "image";
  const questions = Array.isArray(parsed.questions) ? parsed.questions.slice(0, 4).map(String) : [];
  if (questions.length < 2) {
    return json({ error: "Could not generate questions — try rephrasing your request." }, 502, origin);
  }

  return json({ category, questions }, 200, origin);
}

/* ---------------- Endpoint 2: synthesize the final prompt ---------------- */

async function handleSynthesize(request, env, origin) {
  let body;
  try { body = await request.json(); } catch { return json({ error: "Malformed request" }, 400, origin); }

  const { original_request, qa, tool, category } = body || {};
  if (!original_request || !Array.isArray(qa) || !tool || !category) {
    return json({ error: "Missing required fields." }, 400, origin);
  }

  // Fetch tool syntax rules from the live site's config (cached 10 min at the edge)
  let formats;
  try {
    const fResp = await fetch(FORMATS_URL, { cf: { cacheTtl: 600, cacheEverything: true } });
    formats = await fResp.json();
  } catch {
    return json({ error: "Could not load tool format rules — try again shortly." }, 502, origin);
  }

  const toolSpec = formats?.[category]?.[tool];
  if (!toolSpec) {
    return json({ error: "Unknown tool: " + tool }, 400, origin);
  }

  const qaText = qa
    .slice(0, 6)
    .map(p => "Q: " + String(p.q).slice(0, 200) + "\nA: " + String(p.a).slice(0, 300))
    .join("\n");

  const systemPrompt = [
    "You are a senior prompt engineer. Compose the single best prompt for the tool: " + toolSpec.label + ".",
    "Strictly follow these format rules for this tool:",
    ...toolSpec.rules.map(r => "- " + r),
    "Here is an example of a well-formatted prompt for this tool (match its FORMAT, not its content):",
    toolSpec.example,
    "Output ONLY the final prompt. No explanation, no preamble, no quotes around it."
  ].join("\n");

  const userContent =
    "The user's original request: " + String(original_request).slice(0, 1000) +
    "\n\nClarifying answers gathered:\n" + qaText;

  const prompt = (await callOpenAI(env, systemPrompt, userContent, false)).trim();
  if (!prompt) return json({ error: "Could not generate a prompt — please try again." }, 502, origin);

  return json({ prompt, tool_label: toolSpec.label, tool_url: toolSpec.directory_url }, 200, origin);
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
      // Rate limit both endpoints per IP
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
