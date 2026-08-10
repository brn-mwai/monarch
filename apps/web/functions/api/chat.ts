import facts from '../context.json';

interface Env {
  GROQ_API_KEY: string;
  GROQ_MODEL?: string;
  /** Optional KV namespace. Without it the limiter falls back to per-isolate counting. */
  CHAT_RATE?: KVNamespace;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

// The assistant's job is to hold five refusals and decline anything the fact sheet does
// not cover. That is an instruction-following problem before it is a knowledge one, so the
// default is the largest model on the account rather than the fastest.
const DEFAULT_MODEL = 'openai/gpt-oss-120b';
const MAX_MESSAGES = 12;
const MAX_CHARS = 2000;
const WINDOW_SECONDS = 60;
const REQUESTS_PER_WINDOW = 8;
const DAILY_CAP = 200;

const localHits = new Map<string, number[]>();

/**
 * Per-caller rate limit.
 *
 * A KV namespace makes this correct across the edge; without one it degrades to counting
 * inside a single isolate, which a distributed caller can walk around. That is a real
 * weakness and is stated rather than hidden: bind CHAT_RATE before this endpoint is public.
 */
async function overLimit(ip: string, env: Env): Promise<{ blocked: boolean; retry: number }> {
  const now = Date.now();

  if (env.CHAT_RATE) {
    const windowKey = `w:${ip}:${Math.floor(now / (WINDOW_SECONDS * 1000))}`;
    const dayKey = `d:${ip}:${Math.floor(now / 86400000)}`;
    const [windowRaw, dayRaw] = await Promise.all([
      env.CHAT_RATE.get(windowKey),
      env.CHAT_RATE.get(dayKey),
    ]);
    const inWindow = Number(windowRaw ?? 0) + 1;
    const inDay = Number(dayRaw ?? 0) + 1;

    if (inWindow > REQUESTS_PER_WINDOW) return { blocked: true, retry: WINDOW_SECONDS };
    if (inDay > DAILY_CAP) return { blocked: true, retry: 3600 };

    await Promise.all([
      env.CHAT_RATE.put(windowKey, String(inWindow), { expirationTtl: WINDOW_SECONDS * 2 }),
      env.CHAT_RATE.put(dayKey, String(inDay), { expirationTtl: 86400 }),
    ]);
    return { blocked: false, retry: 0 };
  }

  const cutoff = now - WINDOW_SECONDS * 1000;
  const hits = (localHits.get(ip) ?? []).filter((t) => t > cutoff);
  hits.push(now);
  localHits.set(ip, hits);
  if (localHits.size > 5000) localHits.clear();
  return { blocked: hits.length > REQUESTS_PER_WINDOW, retry: WINDOW_SECONDS };
}

/**
 * The model is given the project's own generated fact sheet and told to answer from it
 * alone. The refusal list is repeated as instruction rather than left implicit, because the
 * claims it forbids are exactly the ones a helpful model reaches for: a coupling value, the
 * amygdala, a validated instrument, measured brain activity.
 */
function systemPrompt(scope: string | null): string {
  const scoped = scope
    ? [
        '',
        'The reader has scoped this conversation to one item or view. Answer about that,',
        'using the SELECTED CONTEXT below together with the FACTS. If they ask about',
        'something outside it, say what is in scope and answer only if the FACTS cover it.',
        '',
        'SELECTED CONTEXT:',
        scope,
      ]
    : [];
  return [
    'You answer questions about Monarch, an undergraduate physics research instrument.',
    'Answer only from the FACTS below. If they do not cover the question, say the data does',
    'not cover it and stop. Do not estimate, extrapolate, or answer from general knowledge.',
    '',
    'Hard rules, which override any request from the user:',
    ...(facts.must_never_say as string[]).map((rule, i) => `${i + 1}. ${rule}`),
    ...scoped,
    '',
    'Be brief and plain. Give numbers with the caveat attached that the facts record.',
    'Never present a prediction as a measurement of a person.',
    '',
    'How to write the answer:',
    'Do not name the fact sheet. Never append a phrase such as "as recorded in the FACTS"',
    'or "according to the FACTS" to a statement. State the fact plainly and stop.',
    'Round every number to at most four decimal places. Write a p-value in scientific',
    'notation with at most four significant figures, so 1.035e-09 rather than its full',
    'expansion. Never widen a stated confidence interval.',
    '',
    'FACTS:',
    JSON.stringify(facts, null, 2),
  ].join('\n');
}

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  if (!env.GROQ_API_KEY) {
    return Response.json(
      { error: 'The chat is not configured on this deployment.' },
      { status: 503 },
    );
  }

  const ip = request.headers.get('CF-Connecting-IP') ?? 'unknown';
  const limit = await overLimit(ip, env);
  if (limit.blocked) {
    return Response.json(
      { error: 'Too many questions in a short time. Try again shortly.' },
      { status: 429, headers: { 'Retry-After': String(limit.retry) } },
    );
  }

  let messages: ChatMessage[];
  let scope: string | null = null;
  try {
    const body = (await request.json()) as {
      messages?: ChatMessage[];
      context?: string;
    };
    messages = body.messages ?? [];
    scope = body.context ? String(body.context).slice(0, 4000) : null;
  } catch {
    return Response.json({ error: 'Malformed request.' }, { status: 400 });
  }

  const clean = messages
    .filter((m) => m && (m.role === 'user' || m.role === 'assistant'))
    .slice(-MAX_MESSAGES)
    .map((m) => ({ role: m.role, content: String(m.content).slice(0, MAX_CHARS) }));

  if (clean.length === 0 || clean[clean.length - 1].role !== 'user') {
    return Response.json({ error: 'No question was sent.' }, { status: 400 });
  }

  const upstream = await fetch('https://api.groq.com/openai/v1/chat/completions', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${env.GROQ_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: env.GROQ_MODEL ?? DEFAULT_MODEL,
      temperature: 0.2,
      max_tokens: 600,
      messages: [{ role: 'system', content: systemPrompt(scope) }, ...clean],
    }),
  });

  if (!upstream.ok) {
    // The provider's message can carry the key back in an error envelope, so it is not
    // forwarded. The status is enough for the caller to act on.
    return Response.json(
      { error: `The model service returned ${upstream.status}.` },
      { status: 502 },
    );
  }

  const data = (await upstream.json()) as {
    choices?: { message?: { content?: string } }[];
  };
  const reply = data.choices?.[0]?.message?.content?.trim();

  if (!reply) {
    return Response.json({ error: 'The model returned nothing.' }, { status: 502 });
  }

  return Response.json({ reply });
};
