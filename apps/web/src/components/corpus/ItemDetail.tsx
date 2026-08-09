'use client';

import { X } from '@phosphor-icons/react/dist/ssr';
import { useEffect } from 'react';

import { categoryNote } from '@/lib/category-notes';
import {
  CATEGORY_COLORS,
  categoryLabel,
  signed,
  type CategorySummary,
  type CorpusItem,
} from '@/lib/corpus-types';

interface Props {
  item: CorpusItem | null;
  category: CategorySummary | undefined;
  scoreLo: number;
  scoreHi: number;
  regionLo: number;
  regionHi: number;
  rank: number | null;
  total: number;
  onClose: () => void;
}

/** Horizontal bar for one value against the corpus range, with zero marked. */
function ValueBar({
  label,
  value,
  lo,
  hi,
  colour,
}: {
  label: string;
  value: number | null;
  lo: number;
  hi: number;
  colour: string;
}) {
  if (value === null || hi <= lo) {
    return (
      <div className="text-[12px] text-white/40">
        {label}: not defined for this item
      </div>
    );
  }
  const pct = (v: number) => Math.min(100, Math.max(0, ((v - lo) / (hi - lo)) * 100));
  const zero = pct(0);
  const point = pct(value);
  const left = Math.min(zero, point);
  const width = Math.max(0.6, Math.abs(point - zero));

  return (
    <div>
      <div className="flex items-baseline justify-between gap-4">
        <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-white/45">
          {label}
        </span>
        <span className="font-mono text-[12px] tabular-nums text-white">
          {signed(value)}
        </span>
      </div>
      <div className="relative mt-2 h-2 w-full overflow-hidden rounded-full bg-white/[0.06]">
        <span
          className="absolute top-0 h-full w-px bg-white/25"
          style={{ left: `${zero}%` }}
        />
        <span
          className="absolute top-0 h-full rounded-full"
          style={{ left: `${left}%`, width: `${width}%`, background: colour }}
        />
      </div>
    </div>
  );
}

export function ItemDetail({
  item,
  category,
  scoreLo,
  scoreHi,
  regionLo,
  regionHi,
  rank,
  total,
  onClose,
}: Props) {
  useEffect(() => {
    if (!item) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = '';
    };
  }, [item, onClose]);

  if (!item) return null;

  const note = categoryNote(item.category);
  const colour = CATEGORY_COLORS[item.category] ?? '#888';
  const leads =
    item.aAff === null || item.aDel === null
      ? null
      : item.aAff > item.aDel
        ? 'The emotional side responded more'
        : 'The deliberate side responded more';

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/80 p-4 backdrop-blur-sm sm:p-8"
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-3xl rounded-xl border border-white/15 bg-[#0a0a0a] shadow-2xl"
      >
        <div className="flex items-start justify-between gap-4 border-b border-white/10 px-6 py-4">
          <div className="flex flex-wrap items-center gap-3">
            <span className="inline-flex items-center gap-2 rounded-full border border-white/10 px-3 py-1 text-[11px] text-white/70">
              <span
                className="h-1.5 w-1.5 rounded-full"
                style={{ background: colour }}
              />
              {categoryLabel(item.category)}
            </span>
            {rank !== null && (
              <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-white/40">
                Rank {rank} of {total}
              </span>
            )}
            {item.wordCount !== null && (
              <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-white/40">
                {item.wordCount} words
              </span>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded-full border border-white/15 p-2 text-white/60 transition-colors hover:border-white/40 hover:text-white"
          >
            <X size={14} weight="bold" />
          </button>
        </div>

        <div className="space-y-6 px-6 py-6">
          <section>
            <h3 className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/45">
              Full text
            </h3>
            <p className="mt-3 whitespace-pre-wrap text-[14px] leading-relaxed text-white/75">
              {item.text ?? item.preview}
            </p>
          </section>

          <section className="rounded-lg border border-white/10 p-5">
            <div className="flex items-baseline justify-between">
              <h3 className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/45">
                Measured values
              </h3>
              {leads && <span className="text-[12px] text-white/55">{leads}</span>}
            </div>
            <div className="mt-5 space-y-4">
              <ValueBar
                label="Emotional region"
                value={item.aAff}
                lo={regionLo}
                hi={regionHi}
                colour="#e8730c"
              />
              <ValueBar
                label="Deliberate region"
                value={item.aDel}
                lo={regionLo}
                hi={regionHi}
                colour="#4a9eda"
              />
              <ValueBar
                label="Score, emotional minus deliberate"
                value={item.naaSigned}
                lo={scoreLo}
                hi={scoreHi}
                colour="#c9a227"
              />
            </div>
            <p className="mt-5 text-[12px] leading-relaxed text-white/45">
              Bars run across the range measured over the whole corpus, with the vertical rule
              at zero. The ratio form is{' '}
              {item.naaRatio === null
                ? 'not defined for this item, because a region average falls below its baseline'
                : `${item.naaRatio.toFixed(4)} here`}
              .
            </p>
          </section>

          {category && (
            <section className="rounded-lg border border-white/10 p-5">
              <h3 className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/45">
                How this compares within {categoryLabel(item.category)}
              </h3>
              <dl className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
                {[
                  { k: 'Items', v: String(category.n) },
                  { k: 'Average', v: signed(category.mean) },
                  { k: 'Middle', v: signed(category.median) },
                  {
                    k: 'Spread',
                    v: category.sd === null ? '--' : category.sd.toFixed(4),
                  },
                ].map((cell) => (
                  <div key={cell.k}>
                    <dt className="font-mono text-[10px] uppercase tracking-[0.18em] text-white/40">
                      {cell.k}
                    </dt>
                    <dd className="mt-1 font-mono text-[13px] tabular-nums text-white">
                      {cell.v}
                    </dd>
                  </div>
                ))}
              </dl>
              {note && (
                <p className="mt-4 text-[12px] leading-relaxed text-white/50">
                  {note.definition}
                </p>
              )}
            </section>
          )}
        </div>
      </div>
    </div>
  );
}
