'use client';

import { useEffect, useState } from 'react';

import { LandauCurve } from '@/components/charts/LandauCurve';
import { NAAGauge } from '@/components/charts/NAAGauge';
import { ROIBreakdown } from '@/components/charts/ROIBreakdown';
import { SusceptibilityChart } from '@/components/charts/SusceptibilityChart';
import { NAAExplainer } from '@/components/explainers/NAAExplainer';
import { ScientificDisclaimer } from '@/components/explainers/ScientificDisclaimer';
import {
  DEMO_BLOBS,
  generateSpatialActivation,
  loadBrainCoords,
  type BrainCoords,
} from '@/lib/brain-data';
import {
  EXAMPLE_CONTENTS,
  buildSyntheticScan,
  buildSyntheticTimeSeries,
  type ExampleContent,
} from '@/lib/mock-data';
import { getActiveResult, useScanState } from '@/lib/scan-store';

const NAA_LABEL: Record<'LOW' | 'MOD' | 'HIGH', string> = {
  LOW: 'Neutral',
  MOD: 'Mixed',
  HIGH: 'Reactive',
};

/**
 * "Scan Content" tab. Shows the description text from the spec, the
 * 6 example content cards in a 3-column grid, and (when an active
 * scan exists) a results section with the four primary charts.
 */
export function ScanTab() {
  const { state, dispatch } = useScanState();
  const [coords, setCoords] = useState<BrainCoords | null>(null);
  const active = getActiveResult(state);

  useEffect(() => {
    let cancelled = false;
    loadBrainCoords()
      .then((c) => {
        if (!cancelled) setCoords(c);
      })
      .catch((err: unknown) => {
        console.error('ScanTab: failed to load brain coords', err);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const loadExample = (ex: ExampleContent) => {
    if (!coords) return;
    const activation = generateSpatialActivation(coords, DEMO_BLOBS);
    // Generate a 24-frame (24-second) synthetic time series so the
    // brain can pulse via the AnimationController. The static
    // activationVector is what the gauges/charts read; the timeSeries
    // is what the brain animates through TR-by-TR.
    const timeSeries = buildSyntheticTimeSeries(activation, 24);
    const base = buildSyntheticScan(
      `scan-${ex.id}`,
      ex.text,
      ex.expectedNAA,
      activation,
    );
    dispatch({
      type: 'SCAN_COMPLETE_A',
      result: { ...base, timeSeries, nTrs: 24 },
    });
    dispatch({ type: 'SET_COLOR_MODE', mode: 'activation' });
  };

  return (
    <div className="space-y-5">
      <div className="space-y-3 text-[15px] leading-relaxed text-white/75">
        <p>
          Paste any text, audio, or video content to predict its neural
          processing pathway. Monarch estimates whether the content
          preferentially engages affective-salience or deliberative-control
          brain systems.
        </p>
        <p>
          Content that scores high on the NAA index is predicted to engage
          emotional processing circuits before deliberative reasoning can
          evaluate the framing. This is the processing bias that Monarch makes
          visible.
        </p>
      </div>

      {/* 3-column example grid */}
      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {EXAMPLE_CONTENTS.map((ex) => (
          <button
            key={ex.id}
            type="button"
            disabled={!coords}
            onClick={() => loadExample(ex)}
            className="group flex flex-col overflow-hidden rounded-lg border border-white/10 text-left transition-all duration-200 hover:border-white/25 hover:bg-white/[0.02] disabled:cursor-not-allowed disabled:opacity-40"
          >
            <div className="flex h-32 items-center justify-center border-b border-white/[0.06] bg-white/[0.02] p-4">
              <p className="line-clamp-5 font-mono text-[11px] leading-relaxed text-white/70">
                {ex.text}
              </p>
            </div>
            <div className="flex items-center justify-between px-3 py-2.5 text-[11px]">
              <span className="font-mono text-white/55">
                NAA {ex.expectedNAA.toFixed(2)}
              </span>
              <span className="font-mono uppercase tracking-wider text-white/45">
                {ex.label}
              </span>
            </div>
          </button>
        ))}
      </div>

      {/* Results -- visible only when an active scan exists */}
      {active && (
        <div className="mt-8 space-y-6">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <div className="rounded-lg border border-white/10 p-4">
              <NAAGauge
                naa={active.naa.naa}
                classification={active.naa.classification}
                title={`NAA - ${NAA_LABEL[active.naa.classification]}`}
              />
            </div>
            <div className="rounded-lg border border-white/10 p-4">
              <SusceptibilityChart naa={active.naa.naa} />
            </div>
          </div>
          <div className="rounded-lg border border-white/10 p-4">
            <LandauCurve data={active.landau} />
          </div>
          {/* NAA Explainer - plain-language interpretation */}
          <NAAExplainer
            naa={active.naa.naa}
            classification={active.naa.classification}
            aAff={active.naa.a_aff}
            aDel={active.naa.a_del}
          />

          <div className="rounded-lg border border-white/10 p-4">
            <ROIBreakdown roiData={active.roiBreakdown} />
          </div>

          <ScientificDisclaimer />
        </div>
      )}
    </div>
  );
}
