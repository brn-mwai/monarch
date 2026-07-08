'use client';

import { type ReactNode } from 'react';

import { BrainViewer } from '@/components/BrainViewer';
import { getActiveResult, useScanState } from '@/lib/scan-store';

interface SplitLayoutProps {
  /** Right-panel content -- charts, controls, page-specific UI. */
  children: ReactNode;
  /**
   * When true, compare mode (two results) splits the brain panel into two
   * stacked brains (A over B) instead of one. The result cards on the
   * right stay data-only, so the view shows exactly two brains.
   */
  compareAware?: boolean;
}

function CompareBrainHalf({
  activation,
  label,
  timeSeries = null,
  nTrs = 0,
  unavailableNote,
}: {
  activation: Float32Array | null;
  label: string;
  timeSeries?: Float32Array | null;
  nTrs?: number;
  /**
   * Shown when activation is null in true-vs-predicted mode: Monarch has no
   * recorded fMRI for arbitrary content, so the TRUE half states that
   * honestly rather than rendering a fabricated brain.
   */
  unavailableNote?: string;
}) {
  const unavailable = !activation && !!unavailableNote;

  return (
    <div className="relative h-1/2 w-full border-b border-white/10 last:border-b-0">
      <span className="absolute left-3 top-3 z-10 rounded-full border border-white/25 bg-black/50 px-2.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-white/75 backdrop-blur">
        {label}
      </span>
      <BrainViewer
        activation={activation}
        colorMode="activation"
        showOverlays={false}
        timeSeries={timeSeries}
        nTrs={timeSeries ? nTrs : 0}
        className="absolute inset-0"
      />
      {unavailable && (
        <div className="pointer-events-none absolute inset-x-0 bottom-4 z-10 flex justify-center px-6">
          <p className="max-w-xs rounded-lg border border-white/10 bg-black/70 px-3 py-2 text-center font-mono text-[10px] leading-relaxed tracking-wide text-white/55 backdrop-blur">
            {unavailableNote}
          </p>
        </div>
      )}
    </div>
  );
}

/**
 * Persistent two-column layout used by Scanner / Report / Batch.
 *   - LEFT: 47% brain panel (one brain, or two stacked in compare mode).
 *   - RIGHT: scrollable content panel (tabs / forms / charts).
 */
export function SplitLayout({ children, compareAware = false }: SplitLayoutProps) {
  const { state } = useScanState();
  const active = getActiveResult(state);

  const inCompareTab = compareAware && state.activeTab === 'compare';
  // True-vs-predicted needs only ONE scanned content (Content A); the two
  // halves are the recorded true and the model prediction of that one input.
  const isTruthCompare =
    inCompareTab && state.compareView === 'truth' && !!state.contentA;
  // A-vs-B needs both contents present.
  const isABCompare =
    inCompareTab &&
    state.compareView === 'ab' &&
    !!state.contentA &&
    !!state.contentB;

  const activation = active?.activationVector ?? null;
  const multimodal = active?.multimodal
    ? {
        text: active.multimodal.text ?? new Float32Array(),
        audio: active.multimodal.audio ?? new Float32Array(),
        video: active.multimodal.video ?? new Float32Array(),
      }
    : null;

  return (
    <div className="flex h-[calc(100vh-4rem)] w-full overflow-hidden">
      {/* LEFT column -- brain panel */}
      <aside className="relative h-full w-[47%] min-w-[380px] border-r border-white/10 bg-[#080808]">
        {isTruthCompare ? (
          <div className="flex h-full flex-col">
            <CompareBrainHalf
              activation={state.contentA?.trueActivation ?? null}
              label="True"
              unavailableNote="No recorded fMRI reference for this content. True brain appears for benchmark stimuli once the model is connected."
            />
            <CompareBrainHalf
              activation={state.contentA?.activationVector ?? null}
              label="Predicted"
              timeSeries={state.contentA?.timeSeries ?? null}
              nTrs={state.contentA?.nTrs ?? 0}
            />
          </div>
        ) : isABCompare ? (
          <div className="flex h-full flex-col">
            <CompareBrainHalf
              activation={state.contentA?.activationVector ?? null}
              label="A"
              timeSeries={state.contentA?.timeSeries ?? null}
              nTrs={state.contentA?.nTrs ?? 0}
            />
            <CompareBrainHalf
              activation={state.contentB?.activationVector ?? null}
              label="B"
              timeSeries={state.contentB?.timeSeries ?? null}
              nTrs={state.contentB?.nTrs ?? 0}
            />
          </div>
        ) : (
          <BrainViewer
            activation={state.colorMode === 'activation' ? activation : null}
            multimodalActivation={
              state.colorMode === 'multimodal' ? multimodal : null
            }
            colorMode={state.colorMode}
            timeSeries={active?.timeSeries ?? null}
            nTrs={active?.timeSeries ? active.nTrs : 0}
            className="absolute inset-0"
          />
        )}
      </aside>

      {/* RIGHT column -- scrollable content panel */}
      <div className="min-w-0 flex-1 overflow-y-auto bg-black px-8 py-5">
        {children}
      </div>
    </div>
  );
}
