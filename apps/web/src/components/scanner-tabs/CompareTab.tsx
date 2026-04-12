'use client';

import { useState } from 'react';

import { LandauCurve } from '@/components/charts/LandauCurve';
import { ScientificDisclaimer } from '@/components/explainers/ScientificDisclaimer';
import { ElementCard } from '@/components/scanner/ElementCard';
import { scanText } from '@/lib/inference-client';
import { EXAMPLE_CONTENTS } from '@/lib/mock-data';
import { useScanState, type ScanResult } from '@/lib/scan-store';

const PRESET_A = EXAMPLE_CONTENTS.find((c) => c.id === 'fed-calm');
const PRESET_B = EXAMPLE_CONTENTS.find((c) => c.id === 'fed-outrage');

/**
 * "Compare A / B" tab. Dual-brain compare with independent Element
 * Cards, overlaid Landau curves, and the tagline.
 */
export function CompareTab() {
  const { dispatch } = useScanState();
  const [textA, setTextA] = useState(PRESET_A?.text ?? '');
  const [textB, setTextB] = useState(PRESET_B?.text ?? '');
  const [resultA, setResultA] = useState<ScanResult | null>(null);
  const [resultB, setResultB] = useState<ScanResult | null>(null);
  const [scanning, setScanning] = useState(false);

  const runCompare = async () => {
    if (!textA.trim() || !textB.trim()) return;
    setScanning(true);

    try {
      const [rA, rB] = await Promise.all([scanText(textA), scanText(textB)]);
      setResultA(rA);
      setResultB(rB);
      dispatch({ type: 'SCAN_COMPLETE_A', result: rA });
      dispatch({ type: 'SCAN_COMPLETE_B', result: rB });
      dispatch({ type: 'SET_COLOR_MODE', mode: 'activation' });
    } catch (err) {
      dispatch({ type: 'ERROR', message: String(err) });
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className="space-y-5">
      <div className="space-y-3 text-[15px] leading-relaxed text-white/75">
        <p>
          Compare two pieces of content side by side. Same story, different
          predicted processing pathway. Each element gets its own brain
          showing the predicted neural response.
        </p>
      </div>

      {/* Input row */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div>
          <label className="mb-1.5 block font-mono text-[10px] uppercase tracking-wider text-white/50">
            Content A
          </label>
          <textarea
            value={textA}
            onChange={(e) => setTextA(e.target.value)}
            placeholder="Paste URL, text, or drop a file..."
            className="h-28 w-full resize-none rounded-lg border border-white/10 bg-white/[0.03] p-3 font-mono text-sm text-white outline-none transition-colors placeholder:text-white/20 focus:border-white/30"
          />
        </div>
        <div>
          <label className="mb-1.5 block font-mono text-[10px] uppercase tracking-wider text-white/50">
            Content B
          </label>
          <textarea
            value={textB}
            onChange={(e) => setTextB(e.target.value)}
            placeholder="Paste URL, text, or drop a file..."
            className="h-28 w-full resize-none rounded-lg border border-white/10 bg-white/[0.03] p-3 font-mono text-sm text-white outline-none transition-colors placeholder:text-white/20 focus:border-white/30"
          />
        </div>
      </div>

      <button
        type="button"
        onClick={runCompare}
        disabled={scanning || !textA.trim() || !textB.trim()}
        className="w-full rounded-lg bg-white py-3 font-mono text-sm font-semibold uppercase tracking-wider text-black transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-30"
      >
        {scanning ? 'Comparing...' : 'Compare'}
      </button>

      {/* Results: two Element Cards stacked */}
      {(resultA || resultB) && (
        <div className="mt-6 space-y-4">
          <ElementCard label="A" scanResult={resultA} isLoading={scanning} />
          <ElementCard label="B" scanResult={resultB} isLoading={scanning} />

          {/* Physics comparison */}
          {resultA && resultB && (
            <div className="rounded-xl border border-white/10 bg-[#0A0A0A] p-5">
              <h3 className="mb-4 font-mono text-[10px] uppercase tracking-wider text-white/40">
                Physics comparison
              </h3>
              <LandauCurve
                data={resultA.landau}
                comparisonData={resultB.landau}
                title="Free energy: Content A vs B"
              />
              <p className="mt-6 text-center text-base italic text-white/45">
                Same story. Different brain. Now you can see it.
              </p>
            </div>
          )}

          <ScientificDisclaimer />
        </div>
      )}
    </div>
  );
}
