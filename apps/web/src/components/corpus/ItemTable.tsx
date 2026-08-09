'use client';

import { CaretDown, CaretUp } from '@phosphor-icons/react/dist/ssr';
import { useMemo, useState } from 'react';

import {
  CATEGORY_COLORS,
  categoryLabel,
  signed,
  type CorpusItem,
} from '@/lib/corpus-types';

type SortKey = 'score' | 'emotional' | 'deliberate' | 'words' | 'category';

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
  { key: 'words', label: 'Words', numeric: true },
  { key: 'score', label: 'Score', numeric: true },
  { key: 'emotional', label: 'Emotional', numeric: true },
  { key: 'deliberate', label: 'Deliberate', numeric: true },
];

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

export function ItemTable({ rows, selected, onSelect, scaleLo, scaleHi }: Props) {
  const [sort, setSort] = useState<SortKey>('score');
  const [descending, setDescending] = useState(true);

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

  const toggle = (key: SortKey) => {
    if (key === sort) {
      setDescending((d) => !d);
    } else {
      setSort(key);
      setDescending(true);
    }
  };

  return (
    <div className="overflow-hidden rounded-xl border border-white/10">
      <div className="max-h-[620px] overflow-auto">
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
              const bar = barGeometry(row.item.naaSigned, scaleLo, scaleHi);
              const isSelected = row.index === selected;
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
                    {bar && (
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
                    )}
                  </td>
                  <td className="whitespace-nowrap px-3 py-3">
                    <span className="inline-flex items-center gap-2 rounded-full border border-white/10 px-2.5 py-1 text-[11px] text-white/60">
                      <span
                        className="h-1.5 w-1.5 rounded-full"
                        style={{ background: CATEGORY_COLORS[row.item.category] ?? '#888' }}
                      />
                      {categoryLabel(row.item.category)}
                    </span>
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
  );
}
