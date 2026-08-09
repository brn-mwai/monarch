'use client';

import { CaretDown, MagnifyingGlass } from '@phosphor-icons/react/dist/ssr';
import { useEffect, useMemo, useRef, useState } from 'react';

import {
  CATEGORY_COLORS,
  categoryLabel,
  signed,
  type CorpusItem,
} from '@/lib/corpus-types';

interface Option {
  item: CorpusItem;
  index: number;
}

interface Props {
  label: string;
  value: number;
  options: Option[];
  onChange: (index: number) => void;
}

export function ItemSelect({ label, value, options, onChange }: Props) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [active, setActive] = useState(0);
  const rootRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  const selected = options.find((o) => o.index === value) ?? options[0];

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return options;
    return options.filter(
      (o) =>
        o.item.preview.toLowerCase().includes(q) ||
        categoryLabel(o.item.category).toLowerCase().includes(q),
    );
  }, [options, query]);

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onPointerDown);
    return () => document.removeEventListener('mousedown', onPointerDown);
  }, [open]);

  useEffect(() => {
    if (open) setActive(0);
    else setQuery('');
  }, [open]);

  // Keep the highlighted row in view when arrowing through a long corpus.
  useEffect(() => {
    if (!open) return;
    listRef.current?.children[active]?.scrollIntoView({ block: 'nearest' });
  }, [active, open]);

  const commit = (index: number) => {
    onChange(index);
    setOpen(false);
  };

  const onKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setActive((a) => Math.min(a + 1, filtered.length - 1));
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      setActive((a) => Math.max(a - 1, 0));
    } else if (event.key === 'Enter' && filtered[active]) {
      event.preventDefault();
      commit(filtered[active].index);
    } else if (event.key === 'Escape') {
      setOpen(false);
    }
  };

  return (
    <div ref={rootRef} className="relative">
      <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/45">
        {label}
      </span>

      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
        className="mt-2 flex w-full items-center gap-3 rounded-lg border border-white/15 bg-white/[0.02] px-4 py-3 text-left transition-colors hover:border-white/30"
      >
        {selected && (
          <>
            <span
              className="h-2.5 w-2.5 shrink-0 rounded-full"
              style={{ background: CATEGORY_COLORS[selected.item.category] ?? '#888' }}
            />
            <span className="w-[74px] shrink-0 font-mono text-[12px] tabular-nums text-white">
              {signed(selected.item.naaSigned)}
            </span>
            <span className="min-w-0 flex-1 truncate text-[13px] text-white/70">
              {selected.item.preview}
            </span>
          </>
        )}
        <CaretDown
          size={14}
          weight="bold"
          className={`shrink-0 text-white/40 transition-transform ${open ? 'rotate-180' : ''}`}
        />
      </button>

      {open && (
        <div className="absolute z-30 mt-2 w-full overflow-hidden rounded-lg border border-white/15 bg-[#0a0a0a] shadow-2xl">
          <div className="flex items-center gap-2 border-b border-white/10 px-3 py-2.5">
            <MagnifyingGlass size={14} className="shrink-0 text-white/35" />
            <input
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Filter by text or category"
              className="w-full bg-transparent text-[13px] text-white placeholder:text-white/30 focus:outline-none"
            />
            <span className="shrink-0 font-mono text-[10px] tabular-nums text-white/35">
              {filtered.length}
            </span>
          </div>

          <ul ref={listRef} role="listbox" className="scroll-slim max-h-[320px] overflow-y-auto">
            {filtered.length === 0 && (
              <li className="px-4 py-6 text-center text-[13px] text-white/40">
                Nothing matches that
              </li>
            )}
            {filtered.map((o, i) => (
              <li key={o.index}>
                <button
                  type="button"
                  role="option"
                  aria-selected={o.index === value}
                  onMouseEnter={() => setActive(i)}
                  onClick={() => commit(o.index)}
                  className={`flex w-full items-start gap-3 px-4 py-2.5 text-left transition-colors ${
                    i === active ? 'bg-white/[0.06]' : ''
                  } ${o.index === value ? 'border-l-2 border-white/70' : 'border-l-2 border-transparent'}`}
                >
                  <span
                    className="mt-1.5 h-2 w-2 shrink-0 rounded-full"
                    style={{ background: CATEGORY_COLORS[o.item.category] ?? '#888' }}
                  />
                  <span className="w-[70px] shrink-0 font-mono text-[12px] tabular-nums text-white">
                    {signed(o.item.naaSigned)}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="line-clamp-2 text-[13px] leading-snug text-white/75">
                      {o.item.preview}
                    </span>
                    <span className="mt-1 block font-mono text-[10px] uppercase tracking-[0.15em] text-white/35">
                      {categoryLabel(o.item.category)}
                    </span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
