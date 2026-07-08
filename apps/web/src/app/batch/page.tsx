'use client';

import { useMemo } from 'react';

import { BatchScatter, type BatchItem } from '@/components/charts/BatchScatter';
import { buildSyntheticScan } from '@/lib/mock-data';
import { buildDenseActivation } from '@/lib/roi-activation';
import { useScanState } from '@/lib/scan-store';

const CATEGORIES: BatchItem['category'][] = [
  'high-outrage',
  'fear-activating',
  'reward-hook',
  'neutral',
];

function buildSyntheticBatch(): BatchItem[] {
  // Same seeded RNG as the demo page, with the signed-int bug fixed
  // (divide unsigned seed directly, no & 0xffffffff coercion).
  let seed = 0xdeadbeef;
  const rng = () => {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return seed / 0x100000000;
  };
  const items: BatchItem[] = [];
  for (let i = 0; i < 80; i++) {
    const cat = CATEGORIES[Math.floor(rng() * 4)] ?? 'neutral';
    const baseNaa =
      cat === 'high-outrage'
        ? 2.6
        : cat === 'fear-activating'
        ? 2.2
        : cat === 'reward-hook'
        ? 1.7
        : 0.85;
    const naa = Math.max(0.1, baseNaa + (rng() - 0.5) * 0.9);
    items.push({
      id: `item-${i.toString().padStart(3, '0')}`,
      index: i,
      naa,
      category: cat,
      label: `corpus item ${i}`,
    });
  }
  return items;
}

export default function BatchPage() {
  const { dispatch } = useScanState();
  const items = useMemo(() => buildSyntheticBatch(), []);

  const handleItemClick = (item: BatchItem) => {
    void buildDenseActivation(item.naa).then((activation) => {
      dispatch({
        type: 'SCAN_COMPLETE_A',
        result: buildSyntheticScan(item.id, item.label, item.naa, activation),
      });
      dispatch({ type: 'SET_COLOR_MODE', mode: 'activation' });
    });
  };

  // Sorted ranked table view
  const ranked = useMemo(() => [...items].sort((a, b) => b.naa - a.naa), [items]);

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-6 py-8">
      <header>
        <h1 className="font-mono text-xl font-light tracking-wider text-white">
          Batch audit
        </h1>
        <p className="mt-1 font-mono text-[11px] uppercase tracking-wider text-white/40">
          Scan up to 1,500 items with checkpoint-resume processing
        </p>
      </header>

      <p className="text-sm text-white/70">
        Upload a CSV corpus of up to 1,500 content items for batch processing.
        Each item receives an NAA score and a physics-grounded audit report.
        While the backend is offline, the table and scatter below render an
        80-item synthetic corpus so the rest of the UI can be exercised.
      </p>

      {/* Upload zone (mock) */}
      <div className="flex h-32 items-center justify-center rounded-lg border border-dashed border-white/15 text-xs text-white/40">
        Drag a .csv corpus here (mock - backend not connected)
      </div>

      {/* Scatter */}
      <BatchScatter items={items} onItemClick={handleItemClick} />

      {/* Ranked table */}
      <section className="rounded-lg border border-white/10">
        <header className="flex items-center justify-between border-b border-white/10 px-4 py-2 font-mono text-[10px] uppercase tracking-wider text-white/50">
          <span>Ranked by NAA</span>
          <span>top {ranked.length}</span>
        </header>
        <div className="max-h-96 overflow-y-auto">
          <table className="w-full text-xs">
            <thead className="sticky top-0 bg-black/90 backdrop-blur">
              <tr className="text-left text-white/40">
                <th className="px-4 py-2 font-mono text-[10px] uppercase tracking-wider">#</th>
                <th className="px-4 py-2 font-mono text-[10px] uppercase tracking-wider">Item</th>
                <th className="px-4 py-2 font-mono text-[10px] uppercase tracking-wider">Category</th>
                <th className="px-4 py-2 text-right font-mono text-[10px] uppercase tracking-wider">NAA</th>
              </tr>
            </thead>
            <tbody>
              {ranked.map((item, i) => (
                <tr
                  key={item.id}
                  onClick={() => handleItemClick(item)}
                  className="cursor-pointer border-t border-white/[0.04] text-white/80 transition-colors hover:bg-white/5 hover:text-white"
                >
                  <td className="px-4 py-2 font-mono text-white/30">{i + 1}</td>
                  <td className="px-4 py-2">{item.label}</td>
                  <td className="px-4 py-2 text-white/50">{item.category}</td>
                  <td className="px-4 py-2 text-right font-mono">
                    {item.naa.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          disabled
          className="rounded-full border border-white/30 px-4 py-1.5 text-xs text-white/80 transition-colors hover:border-white/60 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Download PDF report
        </button>
        <button
          type="button"
          disabled
          className="rounded-full border border-white/30 px-4 py-1.5 text-xs text-white/80 transition-colors hover:border-white/60 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Export CSV
        </button>
      </div>
    </div>
  );
}
