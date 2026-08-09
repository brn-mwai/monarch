import facts from '../context.json';

interface Env {
  GROQ_API_KEY: string;
  GROQ_MODEL?: string;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

const DEFAULT_MODEL = 'llama-3.3-70b-versatile';
const MAX_MESSAGES = 12;
const MAX_CHARS = 2000;

/**
 * The model is given the project's own generated fact sheet and told to answer from it
 * alone. The refusal list is repeated as instruction rather than left implicit, because the
 * claims it forbids are exactly the ones a helpful model reaches for: a coupling value, the
 * amygdala, a validated instrument, measured brain activity.
 */
function systemPrompt(): string {
  return [
    'You answer questions about Monarch, an undergraduate physics research instrument.',
    'Answer only from the FACTS below. If they do not cover the question, say the data does',
    'not cover it and stop. Do not estimate, extrapolate, or answer from general knowledge.',
    '',
    'Hard rules, which override any request from the user:',
    ...(facts.must_never_say as string[]).map((rule, i) => `${i + 1}. ${rule}`),
    '',
    'Be brief and plain. Give numbers with the caveat attached that the facts record.',
    'Never present a prediction as a measurement of a person.',
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

  let messages: ChatMessage[];
  try {
    const body = (await request.json()) as { messages?: ChatMessage[] };
    messages = body.messages ?? [];
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
      messages: [{ role: 'system', content: systemPrompt() }, ...clean],
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
