'use client';

import { useEffect, useState } from 'react';

import { LandauCurve } from '@/components/charts/LandauCurve';
import { NAAGauge } from '@/components/charts/NAAGauge';
import {
  DEMO_BLOBS,
  generateSpatialActivation,
  loadBrainCoords,
  type BrainCoords,
} from '@/lib/brain-data';
import { EXAMPLE_CONTENTS, buildSyntheticScan } from '@/lib/mock-data';
import { useScanState } from '@/lib/scan-store';

const PRESET_A = EXAMPLE_CONTENTS.find((c) => c.id === 'fed-calm');
const PRESET_B = EXAMPLE_CONTENTS.find((c) => c.id === 'fed-outrage');

/**
 * "Compare A / B" tab. Pre-fills both textareas with the Fed Reserve
 * neutral / outrage demo, runs both through the synthetic scan
 * generator, and overlays the two Landau curves.
 */
export function CompareTab() {
  const { state, dispatch } = useScanState();
  const [coords, setCoords] = useState<BrainCoords | null>(null);
  const [textA, setTextA] = useState(PRESET_A?.text ?? '');
  const [textB, setTextB] = useState(PRESET_B?.text ?? '');

  useEffect(() => {
    let cancelled = false;
    loadBrainCoords()
      .then((c) => {
        if (!cancelled) setCoords(c);
      })
      .catch((err: unknown) => {
        console.error('CompareTab: failed to load brain coords', err);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const runCompare = () => {
    if (!coords) return;
    const naaA =
      textA === PRESET_A?.text
        ? PRESET_A.expectedNAA
        : Math.max(0.3, Math.min(4.5, 0.5 + heuristic(textA)));
    const naaB =
      textB === PRESET_B?.text
        ? PRESET_B.expectedNAA
        : Math.max(0.3, Math.min(4.5, 0.5 + heuristic(textB)));

    const aAct = generateSpatialActivation(coords, DEMO_BLOBS);
    const bAct = generateSpatialActivation(coords, DEMO_BLOBS);
    dispatch({
      type: 'SCAN_COMPLETE_A',
      result: buildSyntheticScan('cmp-a', 'Content A', naaA, aAct),
    });
    dispatch({
      type: 'SCAN_COMPLETE_B',
      result: buildSyntheticScan('cmp-b', 'Content B', naaB, bAct),
    });
    dispatch({ type: 'SET_COLOR_MODE', mode: 'activation' });
  };

  const a = state.contentA;
  const b = state.contentB;
  const compareReady = state.mode === 'compare' && a && b;
  const activeLandau =
    compareReady && state.activeContent === 'A' ? a.landau : compareReady ? b.landau : null;
  const otherLandau =
    compareReady && state.activeContent === 'A' ? b.landau : compareReady ? a.landau : null;

  return (
    <div className="space-y-5">
      <div className="space-y-3 text-[15px] leading-relaxed text-white/75">
        <p>
          Compare two pieces of content side by side. Same story, different
          predicted processing pathway. This is the core demonstration of what
          Monarch measures.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div>
          <label className="mb-1.5 block font-mono text-[10px] uppercase tracking-wider text-white/50">
            Content A
          </label>
          <textarea
            value={textA}
            onChange={(e) => setTextA(e.target.value)}
            className="min-h-[140px] w-full rounded-lg border border-white/10 bg-white/[0.03] p-4 font-mono text-sm text-white outline-none transition-colors placeholder:text-white/30 focus:border-white/30"
            placeholder="Paste content A..."
          />
        </div>
        <div>
          <label className="mb-1.5 block font-mono text-[10px] uppercase tracking-wider text-white/50">
            Content B
          </label>
          <textarea
            value={textB}
            onChange={(e) => setTextB(e.target.value)}
            className="min-h-[140px] w-full rounded-lg border border-white/10 bg-white/[0.03] p-4 font-mono text-sm text-white outline-none transition-colors placeholder:text-white/30 focus:border-white/30"
            placeholder="Paste content B..."
          />
        </div>
      </div>

      <button
        type="button"
        onClick={runCompare}
        disabled={!textA.trim() || !textB.trim() || !coords}
        className="w-full rounded-lg bg-white py-3 font-mono text-sm font-bold uppercase tracking-wider text-black transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-30"
      >
        Compare
      </button>

      {compareReady && (
        <div className="mt-6 space-y-6">
          {/* A/B brain selector */}
          <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-wider">
            <span className="text-white/50">Brain shows:</span>
            {(['A', 'B'] as const).map((v) => (
              <button
                key={v}
                type="button"
                onClick={() => dispatch({ type: 'SET_ACTIVE', active: v })}
                className={`rounded-full border px-3 py-1 transition-colors ${
                  state.activeContent === v
                    ? 'border-white bg-white text-black'
                    : 'border-white/30 text-white/70 hover:border-white/60'
                }`}
              >
                Content {v}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="rounded-lg border border-white/10 p-4">
              <NAAGauge
                naa={a.naa.naa}
                classification={a.naa.classification}
                title="Content A"
              />
              <p className="mt-2 text-center font-mono text-[10px] uppercase tracking-wider text-white/45">
                Deliberative
              </p>
            </div>
            <div className="rounded-lg border border-white/10 p-4">
              <NAAGauge
                naa={b.naa.naa}
                classification={b.naa.classification}
                title="Content B"
              />
              <p className="mt-2 text-center font-mono text-[10px] uppercase tracking-wider text-white/45">
                Reactive
              </p>
            </div>
          </div>

          {activeLandau && (
            <div className="rounded-lg border border-white/10 p-4">
              <LandauCurve
                data={activeLandau}
                comparisonData={otherLandau}
                title="Free energy: Content A vs B"
              />
            </div>
          )}

          <p className="text-center text-base italic text-white/55">
            Same story. Different brain. Now you can see it.
          </p>
        </div>
      )}
    </div>
  );
}

function heuristic(text: string): number {
  const upperRatio =
    (text.match(/[A-Z]/g)?.length ?? 0) / Math.max(1, text.length);
  const exclam = (text.match(/!/g)?.length ?? 0) / Math.max(1, text.length / 50);
  return upperRatio * 8 + exclam;
}
