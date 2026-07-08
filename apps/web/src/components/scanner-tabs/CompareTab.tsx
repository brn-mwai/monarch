'use client';

import { useRef, useState } from 'react';

import { LandauCurve } from '@/components/charts/LandauCurve';
import { ScientificDisclaimer } from '@/components/explainers/ScientificDisclaimer';
import { ElementCard } from '@/components/scanner/ElementCard';
import { demographicTakeaway } from '@/lib/demographics';
import { scanMedia, scanText } from '@/lib/inference-client';
import { EXAMPLE_CONTENTS } from '@/lib/mock-data';
import { useScanState, type ScanResult } from '@/lib/scan-store';

const PRESET_A = EXAMPLE_CONTENTS.find((c) => c.id === 'fed-calm');
const PRESET_B = EXAMPLE_CONTENTS.find((c) => c.id === 'fed-outrage');

type InputMode = 'text' | 'media';

// TRIBE is tri-modal (text/audio/video); there is no separate image encoder,
// so a still image is treated as a single video frame. Audio uploads route to
// the audio encoder; everything visual routes to video.
function modalityForFile(file: File): 'audio' | 'video' {
  return file.type.startsWith('audio/') ? 'audio' : 'video';
}

/** One comparison side: switch between pasted text and an uploaded clip/image. */
function SideInput({
  label,
  mode,
  onMode,
  text,
  onText,
  file,
  onFile,
}: {
  label: string;
  mode: InputMode;
  onMode: (m: InputMode) => void;
  text: string;
  onText: (t: string) => void;
  file: File | null;
  onFile: (f: File | null) => void;
}) {
  const inputRef = useRef<HTMLInputElement | null>(null);

  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between">
        <label className="font-mono text-[10px] uppercase tracking-wider text-white/50">
          {label}
        </label>
        <div className="inline-flex rounded-md border border-white/10 bg-white/[0.03] p-0.5">
          {(['text', 'media'] as const).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => onMode(m)}
              className={`rounded px-2.5 py-0.5 font-mono text-[9px] uppercase tracking-wider transition-colors ${
                mode === m
                  ? 'bg-white text-black'
                  : 'text-white/50 hover:text-white/80'
              }`}
            >
              {m}
            </button>
          ))}
        </div>
      </div>

      {mode === 'text' ? (
        <textarea
          value={text}
          onChange={(e) => onText(e.target.value)}
          placeholder="Paste URL, text, or a transcript..."
          className="h-28 w-full resize-none rounded-lg border border-white/10 bg-white/[0.03] p-3 font-mono text-sm text-white outline-none transition-colors placeholder:text-white/20 focus:border-white/30"
        />
      ) : (
        <div className="flex h-28 flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-white/15 bg-white/[0.02] p-3 text-center">
          <input
            ref={inputRef}
            type="file"
            accept="video/*,image/*"
            className="hidden"
            onChange={(e) => onFile(e.target.files?.[0] ?? null)}
          />
          {file ? (
            <>
              <span className="max-w-full truncate font-mono text-xs text-white/70">
                {file.name}
              </span>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => inputRef.current?.click()}
                  className="rounded-md border border-white/15 px-3 py-1 font-mono text-[10px] uppercase tracking-wider text-white/70 transition-colors hover:border-white/35 hover:text-white"
                >
                  Switch file
                </button>
                <button
                  type="button"
                  onClick={() => onFile(null)}
                  className="rounded-md border border-white/10 px-3 py-1 font-mono text-[10px] uppercase tracking-wider text-white/45 transition-colors hover:text-white/70"
                >
                  Remove
                </button>
              </div>
            </>
          ) : (
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              className="rounded-lg border border-white/15 px-4 py-2 font-mono text-xs text-white/70 transition-colors hover:border-white/35 hover:text-white"
            >
              Select video or image
            </button>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * "Compare A / B" tab. Two brains side by side; each side takes pasted
 * text or an uploaded video, switchable per side. The A/B view compares
 * two inputs; the True/Predicted view compares one input's recorded fMRI
 * against the model prediction.
 */
export function CompareTab() {
  const { state, dispatch } = useScanState();
  const compareView = state.compareView;
  const isTruth = compareView === 'truth';

  const [textA, setTextA] = useState(PRESET_A?.text ?? '');
  const [textB, setTextB] = useState(PRESET_B?.text ?? '');
  const [modeA, setModeA] = useState<InputMode>('text');
  const [modeB, setModeB] = useState<InputMode>('text');
  const [fileA, setFileA] = useState<File | null>(null);
  const [fileB, setFileB] = useState<File | null>(null);
  const [resultA, setResultA] = useState<ScanResult | null>(null);
  const [resultB, setResultB] = useState<ScanResult | null>(null);
  const [scanning, setScanning] = useState(false);

  const setView = (view: 'ab' | 'truth') =>
    dispatch({ type: 'SET_COMPARE_VIEW', view });

  const sideReady = (mode: InputMode, text: string, file: File | null) =>
    mode === 'media' ? !!file : !!text.trim();

  const scanSide = (mode: InputMode, text: string, file: File | null) =>
    mode === 'media' && file
      ? scanMedia(file, modalityForFile(file))
      : scanText(text);

  const runCompare = async () => {
    const aReady = sideReady(modeA, textA, fileA);
    const bReady = sideReady(modeB, textB, fileB);
    if (!aReady || (!isTruth && !bReady)) return;
    setScanning(true);

    try {
      if (isTruth) {
        const rA = await scanSide(modeA, textA, fileA);
        setResultA(rA);
        setResultB(null);
        dispatch({ type: 'SCAN_COMPLETE_A', result: rA });
      } else {
        const [rA, rB] = await Promise.all([
          scanSide(modeA, textA, fileA),
          scanSide(modeB, textB, fileB),
        ]);
        setResultA(rA);
        setResultB(rB);
        dispatch({ type: 'SCAN_COMPLETE_A', result: rA });
        dispatch({ type: 'SCAN_COMPLETE_B', result: rB });
      }
      dispatch({ type: 'SET_COLOR_MODE', mode: 'activation' });
    } catch (err) {
      dispatch({ type: 'ERROR', message: String(err) });
    } finally {
      setScanning(false);
    }
  };

  const runDisabled =
    scanning ||
    !sideReady(modeA, textA, fileA) ||
    (!isTruth && !sideReady(modeB, textB, fileB));

  const takeawayFor = (result: ScanResult | null) =>
    result ? demographicTakeaway(state.demographic, result.naa) : undefined;

  return (
    <div className="space-y-5">
      {/* View toggle: A-vs-B content compare, or true-vs-predicted of one input */}
      <div className="inline-flex rounded-lg border border-white/10 bg-white/[0.03] p-0.5">
        {(['ab', 'truth'] as const).map((view) => (
          <button
            key={view}
            type="button"
            onClick={() => setView(view)}
            className={`rounded-md px-4 py-1.5 font-mono text-[10px] uppercase tracking-wider transition-colors ${
              compareView === view
                ? 'bg-white text-black'
                : 'text-white/55 hover:text-white/85'
            }`}
          >
            {view === 'ab' ? 'A / B content' : 'True / Predicted'}
          </button>
        ))}
      </div>

      <div className="space-y-3 text-[15px] leading-relaxed text-white/75">
        {isTruth ? (
          <p>
            Compare the recorded brain response (True) against Monarch&apos;s
            model prediction (Predicted) for a single input -- pasted text, or
            an uploaded video or image. The True brain is available for
            benchmark stimuli with real fMRI; arbitrary content shows the
            prediction only.
          </p>
        ) : (
          <p>
            Compare two pieces of content side by side. Paste text or upload a
            video or image for each, switch the media per side, and watch the
            predicted neural response diverge.
          </p>
        )}
      </div>

      {/* Input row */}
      <div
        className={`grid grid-cols-1 gap-4 ${isTruth ? '' : 'md:grid-cols-2'}`}
      >
        <SideInput
          label={isTruth ? 'Content' : 'Content A'}
          mode={modeA}
          onMode={setModeA}
          text={textA}
          onText={setTextA}
          file={fileA}
          onFile={setFileA}
        />
        {!isTruth && (
          <SideInput
            label="Content B"
            mode={modeB}
            onMode={setModeB}
            text={textB}
            onText={setTextB}
            file={fileB}
            onFile={setFileB}
          />
        )}
      </div>

      <button
        type="button"
        onClick={runCompare}
        disabled={runDisabled}
        className="w-full rounded-lg bg-white py-3 font-mono text-sm font-semibold uppercase tracking-wider text-black transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-30"
      >
        {scanning ? 'Comparing...' : isTruth ? 'Run' : 'Compare'}
      </button>

      {/* Results: the two brains side by side */}
      {(resultA || resultB) && (
        <div className="mt-6 space-y-4">
          {isTruth ? (
            <div className="grid grid-cols-1 gap-4">
              <ElementCard
                label="Predicted"
                scanResult={resultA}
                isLoading={scanning}
                takeaway={takeawayFor(resultA)}
              />
              {resultA && !resultA.trueActivation && (
                <p className="rounded-lg border border-white/10 bg-white/[0.02] px-4 py-3 text-center font-mono text-[11px] leading-relaxed tracking-wide text-white/45">
                  No recorded fMRI reference for this content. The True brain
                  lights up for benchmark stimuli once the model is connected.
                </p>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <ElementCard
                label="A"
                scanResult={resultA}
                isLoading={scanning}
                takeaway={takeawayFor(resultA)}
              />
              <ElementCard
                label="B"
                scanResult={resultB}
                isLoading={scanning}
                takeaway={takeawayFor(resultB)}
              />
            </div>
          )}

          {/* Physics comparison (A-vs-B only) */}
          {!isTruth && resultA && resultB && (
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
