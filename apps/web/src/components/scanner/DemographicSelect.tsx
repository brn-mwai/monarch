'use client';

import { useEffect, useRef, useState } from 'react';

import { DEMOGRAPHICS } from '@/lib/demographics';
import type { DemographicId } from '@/lib/demographics';
import { useScanState } from '@/lib/scan-store';

function Chevron({ open }: { open: boolean }) {
  return (
    <svg
      width="12"
      height="12"
      viewBox="0 0 12 12"
      fill="none"
      aria-hidden="true"
      className={`text-white/50 transition-transform duration-200 ${
        open ? 'rotate-180' : ''
      }`}
    >
      <path
        d="M3 4.5L6 7.5L9 4.5"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function Check() {
  return (
    <svg width="13" height="13" viewBox="0 0 12 12" fill="none" aria-hidden="true">
      <path
        d="M2.5 6.5L4.8 8.8L9.5 3.5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/**
 * Audience selector. Choosing a demographic niches the plain-language
 * takeaway in results; the measured NAA, physics, and brain prediction are
 * unchanged (they are objective model outputs, not audience-dependent).
 *
 * Custom listbox (button + popover) so the option list matches Monarch's dark
 * theme instead of the OS-native select menu. Keyboard, outside-click, and
 * Escape are handled for accessibility.
 */
export function DemographicSelect() {
  const { state, dispatch } = useScanState();
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState(0);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const selectedIndex = Math.max(
    0,
    DEMOGRAPHICS.findIndex((d) => d.id === state.demographic),
  );
  const current = DEMOGRAPHICS[selectedIndex];

  useEffect(() => {
    if (!open) return;
    setHighlight(selectedIndex);

    const onPointerDown = (e: MouseEvent) => {
      if (!containerRef.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onPointerDown);
    return () => document.removeEventListener('mousedown', onPointerDown);
  }, [open, selectedIndex]);

  const choose = (id: DemographicId) => {
    dispatch({ type: 'SET_DEMOGRAPHIC', demographic: id });
    setOpen(false);
  };

  const onButtonKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setOpen(false);
      return;
    }
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      if (!open) {
        setOpen(true);
        return;
      }
      setHighlight((h) => {
        const next = e.key === 'ArrowDown' ? h + 1 : h - 1;
        return (next + DEMOGRAPHICS.length) % DEMOGRAPHICS.length;
      });
      return;
    }
    if (open && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      choose(DEMOGRAPHICS[highlight].id);
    }
  };

  return (
    <div
      ref={containerRef}
      className="relative flex flex-wrap items-center justify-end gap-x-3 gap-y-1"
    >
      <span className="font-mono text-[10px] uppercase tracking-wider text-white/50">
        Audience
      </span>

      <button
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
        onKeyDown={onButtonKeyDown}
        className={`flex w-56 items-center justify-between gap-2 rounded-lg border bg-white/[0.03] px-3 py-1.5 text-left text-sm text-white transition-colors ${
          open
            ? 'border-white/40 bg-white/[0.06]'
            : 'border-white/15 hover:border-white/30'
        }`}
      >
        <span className="truncate">{current.label}</span>
        <Chevron open={open} />
      </button>

      {open && (
        <ul
          role="listbox"
          aria-label="Audience"
          tabIndex={-1}
          className="absolute right-0 top-full z-50 mt-2 w-80 overflow-hidden rounded-xl border border-white/10 bg-[#0E0E0E] p-1 shadow-[0_20px_60px_rgba(0,0,0,0.6)]"
        >
          {DEMOGRAPHICS.map((d, i) => {
            const isSelected = d.id === current.id;
            const isHighlighted = i === highlight;
            return (
              <li
                key={d.id}
                role="option"
                aria-selected={isSelected}
                onMouseEnter={() => setHighlight(i)}
                onClick={() => choose(d.id)}
                className={`flex cursor-pointer items-start gap-2.5 rounded-lg px-3 py-2 transition-colors ${
                  isHighlighted ? 'bg-white/[0.07]' : ''
                }`}
              >
                <span
                  className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center ${
                    isSelected ? 'text-white' : 'text-transparent'
                  }`}
                >
                  <Check />
                </span>
                <span className="min-w-0">
                  <span className="block text-sm font-medium text-white">
                    {d.label}
                  </span>
                  <span className="block text-xs leading-snug text-white/45">
                    {d.lens}
                  </span>
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
