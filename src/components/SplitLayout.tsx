'use client';

import { type ReactNode } from 'react';

import { BrainViewer } from '@/components/BrainViewer';
import { getActiveResult, useScanState } from '@/lib/scan-store';

interface SplitLayoutProps {
  /** Right-panel content -- charts, controls, page-specific UI. */
  children: ReactNode;
}

/**
 * Persistent two-column layout used by Scanner / Report / Batch.
 *
 * Mirrors the TRIBE v2 demo layout exactly:
 *   - LEFT: 47% wide, bg #080808 (subtly recessed from the content
 *     panel), 1px right border. The brain canvas fills the panel
 *     edge-to-edge via absolute positioning so the head silhouette
 *     and overlays butt against the panel borders.
 *   - RIGHT: pure-black scroll surface with px-8 py-5 padding for
 *     the tab strip / form fields / chart cards.
 *
 * The whole layout occupies the viewport minus the 48px global header.
 */
export function SplitLayout({ children }: SplitLayoutProps) {
  const { state } = useScanState();
  const active = getActiveResult(state);

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
      </aside>

      {/* RIGHT column -- scrollable content panel */}
      <div className="min-w-0 flex-1 overflow-y-auto bg-black px-8 py-5">
        {children}
      </div>
    </div>
  );
}
