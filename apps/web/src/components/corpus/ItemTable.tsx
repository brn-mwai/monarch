'use client';

import { ArrowDown, ArrowUp, CaretDown, CaretUp } from '@phosphor-icons/react/dist/ssr';
import { useEffect, useMemo, useState } from 'react';

import {
  CATEGORY_COLORS,
  categoryLabel,
  signed,
  type CorpusItem,
} from '@/lib/corpus-types';

type SortKey = 'score' | 'emotional' | 'deliberate' | 'words' | 'category' | 'label';

interface Row {
  item: CorpusItem;
  index: number;
}

interface Props {
  rows: Row[];
  selected: number;
  onSelect: (index: number) => void;
  scaleLo: number;
  scaleHi: number;
}

const COLUMNS: { key: SortKey; label: string; numeric: boolean }[] = [
  { key: 'category', label: 'Category', numeric: false },
  { key: 'label', label: 'Pre-scan label', numeric: false },
  { key: 'words', label: 'Words', numeric: true },
  { key: 'score', label: 'Score', numeric: true },
  { key: 'emotional', label: 'Emotional', numeric: true },
  { key: 'deliberate', label: 'Deliberate', numeric: true },
];

/** Cards rendered per step on narrow screens, so a 400-item corpus is not one endless page. */
const CARD_STEP = 30;

function valueOf(row: Row, key: SortKey): number | string {
  switch (key) {
    case 'score':
      return row.item.naaSigned ?? 0;
    case 'emotional':
      return row.item.aAff ?? 0;
    case 'deliberate':
      return row.item.aDel ?? 0;
    case 'words':
      return row.item.wordCount ?? 0;
    case 'category':
      return categoryLabel(row.item.category);
    case 'label':
      return row.item.source ?? '';
  }
}

/** Position of a score inside the corpus range, as a percentage for the bar. */
function barGeometry(value: number | null, lo: number, hi: number) {
  if (value === null || hi <= lo) return null;
  const zero = ((0 - lo) / (hi - lo)) * 100;
  const point = ((value - lo) / (hi - lo)) * 100;
  return {
    left: Math.min(zero, point),
    width: Math.max(0.8, Math.abs(point - zero)),
    positive: value >= 0,
  };
}

function ScoreBar({ value, lo, hi }: { value: number | null; lo: number; hi: number }) {
  const bar = barGeometry(value, lo, hi);
  if (!bar) return null;
  return (
    <span className="mt-2 flex h-1 w-full max-w-[260px] overflow-hidden rounded-full bg-white/[0.06]">
      <span
        className="h-full rounded-full"
        style={{
          marginLeft: `${bar.left}%`,
          width: `${bar.width}%`,
          background: bar.positive ? '#e8730c' : '#4a9eda',
        }}
      />
    </span>
  );
}

function CategoryChip({ category }: { category: string }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-white/10 px-2.5 py-1 text-[11px] text-white/60">
      <span
        className="h-1.5 w-1.5 rounded-full"
        style={{ background: CATEGORY_COLORS[category] ?? '#888' }}
      />
      {categoryLabel(category)}
    </span>
  );
}

function prescanLabel(item: CorpusItem): string | null {
  if (!item.labelManipulative) return null;
  return item.labelManipulative === '1' ? 'manipulative' : 'neutral';
}

function Metric({ label, value, align }: { label: string; value: string; align?: 'right' }) {
  return (
    <span className={align === 'right' ? 'text-right' : undefined}>
      <span className="block text-[10px] uppercase tracking-[0.12em] text-white/40">{label}</span>
      <span className="mt-1 block text-white/75">{value}</span>
    </span>
  );
}

export function ItemTable({ rows, selected, onSelect, scaleLo, scaleHi }: Props) {
  const [sort, setSort] = useState<SortKey>('score');
  const [descending, setDescending] = useState(true);
  const [visible, setVisible] = useState(CARD_STEP);

  const sorted = useMemo(() => {
    const copy = [...rows];
    copy.sort((a, b) => {
      const va = valueOf(a, sort);
      const vb = valueOf(b, sort);
      if (typeof va === 'string' || typeof vb === 'string') {
        return descending
          ? String(vb).localeCompare(String(va))
          : String(va).localeCompare(String(vb));
      }
      return descending ? vb - va : va - vb;
    });
    return copy;
  }, [rows, sort, descending]);

  useEffect(() => {
    setVisible(CARD_STEP);
  }, [rows, sort, descending]);

  const toggle = (key: SortKey) => {
    if (key === sort) {
      setDescending((d) => !d);
    } else {
      setSort(key);
      setDescending(true);
    }
  };

  return (
    <>
      <div className="lg:hidden">
        <div className="mb-3 flex items-end gap-2">
          <label className="min-w-0 flex-1">
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/45">
              Sort by
            </span>
            <span className="relative mt-2 block">
              <select
                value={sort}
                onChange={(e) => {
                  setSort(e.target.value as SortKey);
                  setDescending(true);
                }}
                className="h-11 w-full appearance-none rounded-lg border border-white/15 bg-[#0a0a0a] pl-4 pr-10 text-[16px] text-white focus:border-white/40 focus:outline-none"
              >
                {COLUMNS.map((column) => (
                  <option key={column.key} value={column.key}>
                    {column.label}
                  </option>
                ))}
              </select>
              <CaretDown
                size={14}
                weight="bold"
                className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-white/40"
              />
            </span>
          </label>
          <button
            type="button"
            onClick={() => setDescending((d) => !d)}
            aria-label={descending ? 'Sorted high to low, switch to low to high' : 'Sorted low to high, switch to high to low'}
            className="flex h-11 shrink-0 items-center gap-2 rounded-lg border border-white/15 px-4 font-mono text-[11px] uppercase tracking-[0.15em] text-white/70 transition-colors hover:border-white/35"
          >
            {descending ? <ArrowDown size={14} weight="bold" /> : <ArrowUp size={14} weight="bold" />}
            {descending ? 'High first' : 'Low first'}
          </button>
        </div>

        <ul className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {sorted.slice(0, visible).map((row, position) => {
            const isSelected = row.index === selected;
            const label = prescanLabel(row.item);
            return (
              <li key={row.index}>
                <button
                  type="button"
                  onClick={() => onSelect(row.index)}
                  className={`block h-full w-full rounded-xl border p-4 text-left transition-colors ${
                    isSelected
                      ? 'border-white/40 bg-white/[0.06]'
                      : 'border-white/10 bg-white/[0.015] active:bg-white/[0.04]'
                  }`}
                >
                  <span className="flex items-start justify-between gap-3">
                    <span className="flex min-w-0 flex-wrap items-center gap-2">
                      <CategoryChip category={row.item.category} />
                      {label && (
                        <span className="font-mono text-[10px] uppercase tracking-[0.12em] text-white/40">
                          {label}
                        </span>
                      )}
                    </span>
                    <span className="shrink-0 text-right">
                      <span className="block font-mono text-[18px] leading-none tabular-nums text-white">
                        {signed(row.item.naaSigned)}
                      </span>
                      <span className="mt-1.5 block font-mono text-[10px] uppercase tracking-[0.15em] text-white/35">
                        Score, #{position + 1}
                      </span>
                    </span>
                  </span>

                  <span className="mt-3 line-clamp-3 text-[14px] leading-relaxed text-white/80">
                    {row.item.preview}
                  </span>
                  <ScoreBar value={row.item.naaSigned} lo={scaleLo} hi={scaleHi} />

                  <span className="mt-3 grid grid-cols-3 gap-2 border-t border-white/10 pt-3 font-mono text-[13px] tabular-nums">
                    <Metric label="Emotional" value={signed(row.item.aAff)} />
                    <Metric label="Deliberate" value={signed(row.item.aDel)} />
                    <Metric
                      label="Words"
                      value={row.item.wordCount === null ? '--' : String(row.item.wordCount)}
                      align="right"
                    />
                  </span>
                  {row.item.source && (
                    <span className="mt-2 block truncate text-[12px] text-white/40">
                      {row.item.source}
                    </span>
                  )}
                </button>
              </li>
            );
          })}
        </ul>

        {sorted.length > visible && (
          <button
            type="button"
            onClick={() => setVisible((v) => v + CARD_STEP)}
            className="mt-4 flex h-11 w-full items-center justify-center rounded-lg border border-white/15 font-mono text-[11px] uppercase tracking-[0.15em] text-white/70 transition-colors hover:border-white/35"
          >
            Show more, {visible} of {sorted.length}
          </button>
        )}
      </div>

      <div className="hidden overflow-hidden rounded-xl border border-white/10 lg:block">
        <div className="scroll-slim max-h-[620px] overflow-auto">
          <table className="w-full min-w-[820px] border-collapse text-left text-[13px]">
            <thead className="sticky top-0 z-10 bg-[#0a0a0a] font-mono text-[10px] uppercase tracking-[0.18em] text-white/40">
              <tr className="border-b border-white/10">
                <th className="w-10 px-4 py-3 text-right font-normal">#</th>
                <th className="px-3 py-3 font-normal">Item</th>
                {COLUMNS.map((column) => (
                  <th
                    key={column.key}
                    className={`whitespace-nowrap px-3 py-3 font-normal ${
                      column.numeric ? 'text-right' : ''
                    }`}
                  >
                    <button
                      type="button"
                      onClick={() => toggle(column.key)}
                      className={`inline-flex items-center gap-1 transition-colors hover:text-white ${
                        sort === column.key ? 'text-white' : ''
                      }`}
                    >
                      {column.label}
                      {sort === column.key &&
                        (descending ? <CaretDown size={10} /> : <CaretUp size={10} />)}
                    </button>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map((row, position) => {
                const isSelected = row.index === selected;
                const label = prescanLabel(row.item);
                return (
                  <tr
                    key={row.index}
                    onClick={() => onSelect(row.index)}
                    className={`cursor-pointer border-b border-white/5 align-top transition-colors ${
                      isSelected ? 'bg-white/[0.06]' : 'hover:bg-white/[0.03]'
                    }`}
                  >
                    <td className="px-4 py-3 text-right font-mono text-[11px] tabular-nums text-white/30">
                      {position + 1}
                    </td>
                    <td className="max-w-sm px-3 py-3">
                      <span className="line-clamp-2 text-white/80">{row.item.preview}</span>
                      <ScoreBar value={row.item.naaSigned} lo={scaleLo} hi={scaleHi} />
                    </td>
                    <td className="whitespace-nowrap px-3 py-3">
                      <CategoryChip category={row.item.category} />
                    </td>
                    <td className="whitespace-nowrap px-3 py-3">
                      <span className="text-[11px] text-white/45">{row.item.source}</span>
                      {label && (
                        <span className="mt-1 block font-mono text-[10px] uppercase tracking-[0.12em] text-white/30">
                          {label}
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-3 text-right font-mono tabular-nums text-white/40">
                      {row.item.wordCount ?? '--'}
                    </td>
                    <td className="px-3 py-3 text-right font-mono tabular-nums text-white">
                      {signed(row.item.naaSigned)}
                    </td>
                    <td className="px-3 py-3 text-right font-mono tabular-nums text-white/60">
                      {signed(row.item.aAff)}
                    </td>
                    <td className="px-3 py-3 text-right font-mono tabular-nums text-white/60">
                      {signed(row.item.aDel)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
