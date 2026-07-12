'use client';

import { useRouter } from 'next/navigation';
import { useRef, useState } from 'react';

import { LandauCurve } from '@/components/charts/LandauCurve';
import { NAAGauge } from '@/components/charts/NAAGauge';
import { ROIBreakdown } from '@/components/charts/ROIBreakdown';
import { SusceptibilityChart } from '@/components/charts/SusceptibilityChart';
import { NAAExplainer } from '@/components/explainers/NAAExplainer';
import { ScientificDisclaimer } from '@/components/explainers/ScientificDisclaimer';
import {
  demographicAction,
  demographicLabel,
  demographicLens,
  demographicTakeaway,
} from '@/lib/demographics';
import { examplesForAudience } from '@/lib/example-content';
import { scanMedia, scanText } from '@/lib/inference-client';
import { type ExampleContent } from '@/lib/mock-data';
import { NAA_LABEL } from '@/lib/naa-format';
import { getActiveResult, useScanState } from '@/lib/scan-store';

import { ArrowRight } from '@/components/icons';

type InputMode = 'text' | 'media';

// TRIBE is tri-modal (text/audio/video); audio uploads route to the audio
// encoder, everything else visual routes to video (an image = one frame).
function modalityForFile(file: File): 'audio' | 'video' {
  return file.type.startsWith('audio/') ? 'audio' : 'video';
}

/**
 * "Scan Content" tab. Shows the description text from the spec, the
 * 6 example content cards in a 3-column grid, and (when an active
 * scan exists) a results section with the four primary charts.
 */
export function ScanTab() {
  const router = useRouter();
  const { state, dispatch } = useScanState();
  const [scanning, setScanning] = useState(false);
  const [draft, setDraft] = useState('');
  const [mode, setMode] = useState<InputMode>('text');
  const [file, setFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const active = getActiveResult(state);

  const examples = examplesForAudience(state.demographic);
  const canScan =
    !scanning && (mode === 'media' ? !!file : draft.trim().length > 0);

  const runScanning = async (scan: () => ReturnType<typeof scanText>) => {
    setScanning(true);
    dispatch({ type: 'START_SCAN' });
    try {
      const result = await scan();
      dispatch({ type: 'SCAN_COMPLETE_A', result });
      dispatch({ type: 'SET_COLOR_MODE', mode: 'activation' });
    } catch (err) {
      dispatch({
        type: 'ERROR',
        message: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setScanning(false);
    }
  };

  const submitScan = () => {
    if (!canScan) return;
    if (mode === 'media' && file) {
      void runScanning(() => scanMedia(file, modalityForFile(file)));
    } else {
      void runScanning(() => scanText(draft.trim()));
    }
  };

  const loadExample = (ex: ExampleContent) => {
    void runScanning(() => scanText(ex.text));
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

      {/* Custom content input -- text, or a real audio/video upload */}
      <div className="rounded-lg border border-white/10 bg-white/[0.02] p-4">
        <div className="mb-2.5 flex items-center justify-between">
          <span className="font-mono text-[10px] uppercase tracking-wider text-white/40">
            Your content
          </span>
          <div className="inline-flex rounded-md border border-white/10 bg-white/[0.03] p-0.5">
            {(['text', 'media'] as const).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => setMode(m)}
                className={`rounded px-3 py-0.5 font-mono text-[9px] uppercase tracking-wider transition-colors ${
                  mode === m ? 'bg-white text-black' : 'text-white/50 hover:text-white/80'
                }`}
              >
                {m === 'text' ? 'Text' : 'Audio / Video'}
              </button>
            ))}
          </div>
        </div>

        {mode === 'text' ? (
          <textarea
            id="scan-input"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') submitScan();
            }}
            disabled={scanning}
            placeholder="Paste a headline, post, script, or paragraph to scan its neural processing pathway..."
            rows={4}
            className="w-full resize-y rounded-md border border-white/10 bg-black/40 px-3 py-2.5 text-sm leading-relaxed text-white/85 placeholder:text-white/30 focus:border-white/30 focus:outline-none disabled:opacity-50"
          />
        ) : (
          <div className="flex min-h-[96px] flex-col items-center justify-center gap-2 rounded-md border border-dashed border-white/15 bg-black/40 p-4 text-center">
            <input
              ref={fileInputRef}
              type="file"
              accept="audio/*,video/*,image/*"
              className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
            {file ? (
              <>
                <span className="max-w-full truncate font-mono text-xs text-white/75">
                  {file.name}
                </span>
                <span className="font-mono text-[10px] uppercase tracking-wider text-white/40">
                  {modalityForFile(file)} encoder
                </span>
                <div className="mt-1 flex gap-2">
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="rounded-md border border-white/15 px-3 py-1 font-mono text-[10px] uppercase tracking-wider text-white/70 transition-colors hover:border-white/35 hover:text-white"
                  >
                    Switch file
                  </button>
                  <button
                    type="button"
                    onClick={() => setFile(null)}
                    className="rounded-md border border-white/10 px-3 py-1 font-mono text-[10px] uppercase tracking-wider text-white/45 transition-colors hover:text-white/70"
                  >
                    Remove
                  </button>
                </div>
              </>
            ) : (
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="rounded-md border border-white/15 px-4 py-2 font-mono text-xs text-white/70 transition-colors hover:border-white/35 hover:text-white"
              >
                Select an audio or video file
              </button>
            )}
          </div>
        )}

        <div className="mt-2.5 flex items-center justify-between gap-3">
          <span className="font-mono text-[10px] text-white/30">
            {scanning
              ? 'Analysing content...'
              : mode === 'text'
                ? 'Ctrl/Cmd + Enter to scan'
                : 'Audio routes to the audio encoder, video to the video encoder'}
          </span>
          <button
            type="button"
            disabled={!canScan}
            onClick={submitScan}
            className="rounded-full border border-white/30 px-4 py-1.5 font-mono text-[11px] uppercase tracking-wider text-white/85 transition-colors hover:border-white/60 hover:text-white disabled:cursor-not-allowed disabled:border-white/10 disabled:text-white/30"
          >
            {scanning ? 'Scanning...' : 'Scan content'}
          </button>
        </div>
      </div>

      {/* Audience-specific example grid */}
      <p className="mt-6 font-mono text-[10px] uppercase tracking-wider text-white/35">
        Or try an example for {demographicLabel(state.demographic).toLowerCase()}
      </p>
      <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {examples.map((ex) => (
          <button
            key={ex.id}
            type="button"
            disabled={scanning}
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

      {scanning && (
        <div className="mt-6 flex items-center gap-3 rounded-lg border border-white/10 bg-white/[0.02] px-4 py-3">
          <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/20 border-t-white/70" />
          <span className="font-mono text-[11px] uppercase tracking-wider text-white/55">
            Predicting cortical activation...
          </span>
        </div>
      )}

      {/* Results -- visible only when an active scan exists */}
      {active && (
        <div className="mt-8 space-y-6">
          <div className="flex items-start justify-between gap-4 rounded-lg border border-white/10 bg-white/[0.02] p-4">
            <div className="min-w-0">
              <div className="mb-1.5 flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
                <p className="font-mono text-[10px] uppercase tracking-wider text-white/40">
                  {demographicLabel(state.demographic)} takeaway
                </p>
                <span className="font-mono text-[10px] text-white/30">
                  {demographicLens(state.demographic)}
                </span>
              </div>
              <p className="text-[15px] leading-relaxed text-white/80">
                {demographicTakeaway(state.demographic, active.naa)}
              </p>
              <p className="mt-2 text-[13px] leading-relaxed text-white/60">
                <span className="font-mono text-[10px] uppercase tracking-wider text-white/40">
                  Recommended:{' '}
                </span>
                {demographicAction(state.demographic, active.naa)}
              </p>
            </div>
            <button
              type="button"
              onClick={() => router.push('/report')}
              className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-white/30 px-4 py-1.5 font-mono text-[11px] uppercase tracking-wider text-white/85 transition-colors hover:border-white/60 hover:text-white"
            >
              View full report
              <ArrowRight size={13} />
            </button>
          </div>
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
