'use client';

import { Info } from '@phosphor-icons/react/dist/ssr';
import { useEffect, useLayoutEffect, useRef, useState } from 'react';

/** Smallest gap kept between the popover and either edge of the viewport. */
const GUTTER = 16;

/**
 * A hover explanation for one component.
 *
 * Every chart on this page shows a quantity that is easy to misread, so each carries a plain
 * sentence saying what it is and what it does not prove. Click as well as hover, since a
 * hover-only control is unusable on a touch screen. Hover only reacts to a mouse, because a
 * tap fires a synthetic hover before the click and would otherwise open and close at once.
 */
export function InfoHint({ title, body }: { title: string; body: string }) {
  const [open, setOpen] = useState(false);
  const [shift, setShift] = useState(0);
  const rootRef = useRef<HTMLSpanElement>(null);
  const popoverRef = useRef<HTMLSpanElement>(null);

  // Keep the popover inside the viewport on a phone, where the icon can sit near either edge.
  useLayoutEffect(() => {
    if (!open) {
      setShift(0);
      return;
    }
    const rect = popoverRef.current?.getBoundingClientRect();
    if (!rect) return;
    const width = document.documentElement.clientWidth;
    if (rect.left < GUTTER) setShift(GUTTER - rect.left);
    else if (rect.right > width - GUTTER) setShift(width - GUTTER - rect.right);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: PointerEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false);
    };
    document.addEventListener('pointerdown', onPointerDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('pointerdown', onPointerDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  return (
    <span
      ref={rootRef}
      className="relative inline-flex"
      onPointerEnter={(e) => e.pointerType === 'mouse' && setOpen(true)}
      onPointerLeave={(e) => e.pointerType === 'mouse' && setOpen(false)}
    >
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-label={`About ${title}`}
        aria-expanded={open}
        className="-m-[15px] p-[15px] text-white/30 transition-colors hover:text-white/70"
      >
        <Info size={14} weight="bold" />
      </button>

      {open && (
        <span
          ref={popoverRef}
          role="tooltip"
          className="absolute left-1/2 top-6 z-50 w-72 max-w-[calc(100vw-32px)] rounded-lg border border-white/15 bg-[#0a0a0a] p-4 text-left normal-case tracking-normal shadow-2xl"
          style={{ transform: `translateX(calc(-50% + ${shift}px))` }}
        >
          <span className="block font-mono text-[10px] uppercase tracking-[0.18em] text-white/45">
            {title}
          </span>
          <span className="mt-2 block font-sans text-[14px] leading-relaxed text-white/70 sm:text-[12px]">
            {body}
          </span>
        </span>
      )}
    </span>
  );
}
