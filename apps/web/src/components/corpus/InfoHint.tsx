'use client';

import { Info } from '@phosphor-icons/react/dist/ssr';
import { useState } from 'react';

/**
 * A hover explanation for one component.
 *
 * Every chart on this page shows a quantity that is easy to misread, so each carries a plain
 * sentence saying what it is and what it does not prove. Click as well as hover, since a
 * hover-only control is unusable on a touch screen.
 */
export function InfoHint({ title, body }: { title: string; body: string }) {
  const [open, setOpen] = useState(false);

  return (
    <span
      className="relative inline-flex"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-label={`About ${title}`}
        className="text-white/30 transition-colors hover:text-white/70"
      >
        <Info size={14} weight="bold" />
      </button>

      {open && (
        <span className="absolute left-1/2 top-6 z-50 w-72 -translate-x-1/2 rounded-lg border border-white/15 bg-[#0a0a0a] p-4 text-left shadow-2xl">
          <span className="block font-mono text-[10px] uppercase tracking-[0.18em] text-white/45">
            {title}
          </span>
          <span className="mt-2 block text-[12px] leading-relaxed text-white/70">{body}</span>
        </span>
      )}
    </span>
  );
}
