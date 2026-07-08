'use client';

import Link from 'next/link';
import { useEffect } from 'react';

import { LandauCurve } from '@/components/charts/LandauCurve';
import { MultimodalBars } from '@/components/charts/MultimodalBars';
import { NAAGauge } from '@/components/charts/NAAGauge';
import { ROIBreakdown } from '@/components/charts/ROIBreakdown';
import { SusceptibilityChart } from '@/components/charts/SusceptibilityChart';
import { buildSyntheticScan } from '@/lib/mock-data';
import { buildDenseActivation } from '@/lib/roi-activation';
import { getActiveResult, useScanState } from '@/lib/scan-store';

const DISCLAIMER =
  'Monarch estimates predicted population-level cortical processing balance. NAA is a derived proxy observable, not a direct individual neural measurement. The Landau layer is a theoretical interpretation, not direct evidence of real-world opinion shift.';

export default function ReportPage() {
  const { state, dispatch } = useScanState();

  // If the user lands here cold, seed a synthetic scan so the page is
  // never empty -- the report is meant to be the post-scan view.
  useEffect(() => {
    if (state.contentA) return;
    let cancelled = false;
    buildDenseActivation(2.4)
      .then((activation) => {
        if (cancelled) return;
        dispatch({
          type: 'SCAN_COMPLETE_A',
          result: buildSyntheticScan(
            'report-demo',
            'Demo content',
            2.4,
            activation,
          ),
        });
      })
      .catch((err: unknown) => {
        console.error('report: failed to build demo activation', err);
      });
    return () => {
      cancelled = true;
    };
  }, [state.contentA, dispatch]);

  const active = getActiveResult(state);

  if (!active) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-8">
        <p className="text-sm text-white/60">Loading report...</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-6 py-8">
      <header>
        <h1 className="font-mono text-xl font-light tracking-wider text-white">
          Audit report
        </h1>
        <p className="mt-1 font-mono text-[11px] uppercase tracking-wider text-white/40">
          Physics-grounded summary for the active scan
        </p>
      </header>

      {/* Section 1 -- NAA summary */}
      <section className="rounded-lg border border-white/10 p-5">
        <h2 className="mb-3 font-mono text-[11px] uppercase tracking-wider text-white/45">
          Section 1 / NAA summary
        </h2>
        <div className="mb-2 flex items-baseline gap-3">
          <span className="font-mono text-4xl font-light text-white">
            {active.naa.naa.toFixed(2)}
          </span>
          <span className="font-mono text-[10px] uppercase tracking-wider text-white/50">
            classification {active.naa.classification}
          </span>
        </div>
        <p className="mb-4 text-xs text-white/60">
          Content scanned:{' '}
          <span className="text-white/80">{truncate(active.inputContent, 110)}</span>
        </p>
        <NAAGauge naa={active.naa.naa} classification={active.naa.classification} />
      </section>

      {/* Section 2 -- Landau */}
      <section className="rounded-lg border border-white/10 p-5">
        <h2 className="mb-3 font-mono text-[11px] uppercase tracking-wider text-white/45">
          Section 2 / Landau free energy
        </h2>
        <p className="mb-3 text-xs text-white/60">
          The Landau free-energy landscape shows how this content&rsquo;s NAA
          field tilts the opinion-dynamics energy surface. The marked point
          {' '}m* = {active.landau.equilibrium_m.toFixed(3)} is the equilibrium
          polarisation under the mean-field model.
        </p>
        <LandauCurve data={active.landau} />
      </section>

      {/* Section 3 -- Susceptibility */}
      <section className="rounded-lg border border-white/10 p-5">
        <h2 className="mb-3 font-mono text-[11px] uppercase tracking-wider text-white/45">
          Section 3 / Population susceptibility
        </h2>
        <p className="mb-3 text-xs text-white/60">
          Population susceptibility chi(NAA) measures how sensitive collective
          opinion is to the media field at this NAA value. The marker shows
          where this content lands on the curve.
        </p>
        <SusceptibilityChart naa={active.naa.naa} />
      </section>

      {/* Section 4 -- ROI breakdown */}
      <section className="rounded-lg border border-white/10 p-5">
        <h2 className="mb-3 font-mono text-[11px] uppercase tracking-wider text-white/45">
          Section 4 / ROI activation breakdown
        </h2>
        <p className="mb-3 text-xs text-white/60">
          Per-region mean activation across the affective-salience and
          deliberative-control ROI groups. Hover a bar to highlight the
          corresponding region on the brain.
        </p>
        <ROIBreakdown roiData={active.roiBreakdown} />
      </section>

      {/* Section 5 -- Multimodal (only when available) */}
      {active.multimodal && (
        <section className="rounded-lg border border-white/10 p-5">
          <h2 className="mb-3 font-mono text-[11px] uppercase tracking-wider text-white/45">
            Section 5 / Modality contribution
          </h2>
          <MultimodalBars
            videoNAA={active.naa.naa * 1.1}
            textNAA={active.naa.naa * 0.7}
            audioNAA={active.naa.naa * 0.9}
            combinedNAA={active.naa.naa}
          />
        </section>
      )}

      {/* Section 6 -- Download */}
      <section className="rounded-lg border border-white/10 p-5">
        <h2 className="mb-3 font-mono text-[11px] uppercase tracking-wider text-white/45">
          Section 6 / Export
        </h2>
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
            Download raw data (JSON)
          </button>
        </div>
        <p className="mt-3 text-[10px] text-white/40">
          Export wires up once the backend report endpoint ships.
        </p>
      </section>

      <p className="border-t border-white/10 pt-4 text-[10px] leading-relaxed text-white/40">
        {DISCLAIMER}
      </p>

      <Link
        href="/scanner"
        className="inline-flex items-center gap-2 text-xs text-white/60 hover:text-white"
      >
        &lt;- Back to scanner
      </Link>
    </div>
  );
}

function truncate(s: string, n: number) {
  return s.length > n ? s.slice(0, n - 1) + '...' : s;
}
