'use client';

import { ArrowUp, ChatCircle, X } from '@phosphor-icons/react/dist/ssr';
import { useEffect, useRef, useState } from 'react';

import { Markdown } from '@/components/Markdown';
import { subscribeChatContext, type ChatContext } from '@/lib/chat-context';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

const SUGGESTIONS = [
  'What does this actually measure?',
  'What did the 400 items show?',
  'Why can you not say it detects manipulation?',
  'Is any of this a real brain?',
];

export function Chat() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState('');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scope, setScope] = useState<ChatContext | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => subscribeChatContext(setScope), []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, pending]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, []);

  async function send(text: string) {
    const question = text.trim();
    if (!question || pending) return;

    const next = [...messages, { role: 'user' as const, content: question }];
    setMessages(next);
    setDraft('');
    setError(null);
    setPending(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: next, context: scope?.detail ?? null }),
      });
      const data = (await res.json()) as { reply?: string; error?: string };

      if (!res.ok || !data.reply) {
        // The endpoint's own message is shown rather than a generic failure, because
        // "not configured" and "too many questions" need different responses from a reader.
        setError(data.error ?? `Request failed (${res.status}).`);
        return;
      }
      setMessages([...next, { role: 'assistant', content: data.reply }]);
    } catch {
      setError('Could not reach the assistant.');
    } finally {
      setPending(false);
    }
  }

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed bottom-4 right-4 z-40 inline-flex items-center gap-2 rounded-full border border-white/20 bg-[#0a0a0a] px-4 py-3 text-[13px] text-white shadow-2xl transition-colors hover:border-white/50 sm:bottom-6 sm:right-6 sm:px-5"
      >
        <ChatCircle size={16} weight="duotone" />
        <span className="sm:hidden">Ask</span>
        <span className="hidden sm:inline">Ask about this project</span>
      </button>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 left-4 z-50 flex h-[min(560px,calc(100dvh-6rem))] flex-col rounded-xl border border-white/15 bg-[#0a0a0a] shadow-2xl sm:bottom-6 sm:right-6 sm:left-auto sm:h-[560px] sm:w-[min(420px,calc(100vw-3rem))]">
      <div className="flex items-center justify-between border-b border-white/10 px-5 py-3">
        <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/45">
          Ask about this project
        </span>
        <button
          type="button"
          onClick={() => setOpen(false)}
          aria-label="Close"
          className="rounded-full border border-white/15 p-1.5 text-white/60 transition-colors hover:border-white/40 hover:text-white"
        >
          <X size={12} weight="bold" />
        </button>
      </div>

      {scope && (
        <div className="border-b border-white/10 px-5 py-2.5">
          <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-white/35">
            Answering about
          </p>
          <p className="mt-1 truncate text-[12px] text-white/70">{scope.label}</p>
        </div>
      )}

      <div className="scroll-slim flex-1 space-y-4 overflow-y-auto px-5 py-4">
        {messages.length === 0 && (
          <div>
            <p className="text-[13px] leading-relaxed text-white/60">
              Answers come from this project&apos;s own measurements. When something is not in
              them, it says so rather than guessing.
            </p>
            <div className="mt-4 flex flex-col gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => send(s)}
                  className="rounded-lg border border-white/10 px-3 py-2 text-left text-[12px] text-white/65 transition-colors hover:border-white/30 hover:text-white"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div
            key={i}
            className={m.role === 'user' ? 'flex justify-end' : 'flex justify-start'}
          >
            <div
              className={`max-w-[85%] rounded-lg px-3 py-2 text-[13px] leading-relaxed ${
                m.role === 'user'
                  ? 'whitespace-pre-wrap bg-white/[0.08] text-white'
                  : 'border border-white/10 text-white/75'
              }`}
            >
              {m.role === 'user' ? m.content : <Markdown text={m.content} />}
            </div>
          </div>
        ))}

        {pending && (
          <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/35">
            Thinking
          </p>
        )}
        {error && (
          <p className="rounded-lg border border-white/15 px-3 py-2 text-[12px] text-white/60">
            {error}
          </p>
        )}
        <div ref={endRef} />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(draft);
        }}
        className="flex items-center gap-2 border-t border-white/10 px-4 py-3"
      >
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Ask a question"
          maxLength={2000}
          className="w-full bg-transparent text-[13px] text-white placeholder:text-white/30 focus:outline-none"
        />
        <button
          type="submit"
          disabled={pending || !draft.trim()}
          aria-label="Send"
          className="rounded-full border border-white/20 p-2 text-white/70 transition-colors hover:border-white/50 hover:text-white disabled:opacity-30"
        >
          <ArrowUp size={13} weight="bold" />
        </button>
      </form>
    </div>
  );
}
