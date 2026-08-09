'use client';

import { CaretDown } from '@phosphor-icons/react/dist/ssr';

import { categoryLabel, signed, type CorpusItem } from '@/lib/corpus-types';

interface Props {
  label: string;
  value: number;
  options: { item: CorpusItem; index: number }[];
  onChange: (index: number) => void;
}

export function ItemSelect({ label, value, options, onChange }: Props) {
  return (
    <label className="block">
      <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/45">
        {label}
      </span>
      <div className="relative mt-2">
        <select
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="w-full appearance-none rounded-lg border border-white/15 bg-black px-4 py-3 pr-10 text-[13px] text-white transition-colors hover:border-white/30 focus:border-white/50 focus:outline-none"
        >
          {options.map(({ item, index }) => (
            <option key={index} value={index}>
              {signed(item.naaSigned)} · {categoryLabel(item.category)} ·{' '}
              {item.preview.slice(0, 70)}
            </option>
          ))}
        </select>
        <CaretDown
          size={14}
          weight="bold"
          className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-white/40"
        />
      </div>
    </label>
  );
}
