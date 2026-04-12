'use client';

import { UploadSimple } from '@phosphor-icons/react/dist/ssr';
import { useMemo, useState } from 'react';

import { BatchScatter, type BatchItem } from '@/components/charts/BatchScatter';
import { ScientificDisclaimer } from '@/components/explainers/ScientificDisclaimer';
import { scanText } from '@/lib/inference-client';
import { useScanState } from '@/lib/scan-store';

const CATEGORIES: BatchItem['category'][] = [
  'high-outrage',
  'fear-activating',
  'reward-hook',
  'neutral',
];

function buildSyntheticBatch(): BatchItem[] {
  // Same seeded RNG used elsewhere -- divide unsigned seed directly to
  // avoid the signed-int coercion bug we hit earlier.
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

/**
 * "Batch Audit" tab. Drop zone + scatter plot + sortable ranked table.
 * Synthetic 80-item corpus while the backend is offline.
 */
export function BatchTab() {
  const { dispatch } = useScanState();
  const items = useMemo(() => buildSyntheticBatch(), []);
  const ranked = useMemo(() => [...items].sort((a, b) => b.naa - a.naa), [items]);

  const handleItemClick = async (item: BatchItem) => {
    try {
      const result = await scanText(`Corpus item: ${item.label} (NAA ${item.naa.toFixed(2)})`);
      dispatch({ type: 'SCAN_COMPLETE_A', result });
      dispatch({ type: 'SET_COLOR_MODE', mode: 'activation' });
    } catch (err) {
      dispatch({ type: 'ERROR', message: String(err) });
    }
  };

  return (
    <div className="space-y-5">
      <div className="space-y-3 text-[15px] leading-relaxed text-white/75">
        <p>
          Upload a CSV corpus of up to 1,500 content items for batch NAA
          analysis. Each item receives an NAA score and a physics-grounded
          audit report.
        </p>
      </div>

      <label className="flex h-32 cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-white/15 transition-colors hover:border-white/30">
        <UploadSimple size={20} className="text-white/40" />
        <span className="text-xs text-white/45">
          Drop CSV here or click to upload
        </span>
        <span className="font-mono text-[10px] uppercase tracking-wider text-white/30">
          Expected columns: id, text, category
        </span>
        <input type="file" accept=".csv" className="hidden" disabled />
      </label>

      <div className="rounded-lg border border-white/10 p-4">
        <BatchScatter items={items} onItemClick={handleItemClick} />
      </div>

      {/* Ranked table */}
      <section className="rounded-lg border border-white/10">
        <header className="flex items-center justify-between border-b border-white/10 px-4 py-2 font-mono text-[10px] uppercase tracking-wider text-white/50">
          <span>Ranked by NAA</span>
          <span>{ranked.length} items</span>
        </header>
        <div className="max-h-80 overflow-y-auto">
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

      <ScientificDisclaimer />
    </div>
  );
}
