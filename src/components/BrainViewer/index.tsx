'use client';

import { useEffect, useRef, useState } from 'react';

import { getROIDescription, type ROIDescription } from '@/lib/roi-labels';

import { BrainEngine } from './engine/BrainEngine';
import type {
  BrainViewerProps,
  DataMode,
  HemisphereMode,
  ROILabel,
  SurfaceMode,
} from './types';
import { ActivityLegend } from './ui/ActivityLegend';
import { ControlToggles } from './ui/ControlToggles';
import { MultimodalLegend } from './ui/MultimodalLegend';
import { ROIDescriptionPanel } from './ui/ROIDescriptionPanel';

export { BrainEngine } from './engine/BrainEngine';
export * from './types';

/**
 * Public API -- the interactive fsaverage5 brain renderer.
 *
 * Pass a Float32Array of length 20484 via the `activation` prop to light
 * up the cortex with the hot/fire colormap. Omit it to show the default
 * sulcal-shaded grey brain.
 */
export function BrainViewer({
  activation = null,
  multimodalActivation = null,
  colorMode = 'activation',
  dataMode: dataModeProp,
  highlightROI = null,
  showOverlays = true,
  interactive = true,
  timeSeries = null,
  nTrs = 0,
  tr = 1.0,
  mediaElement = null,
  initialView,
  view,
  className = '',
  onROIClick,
  loading: loadingProp = false,
}: BrainViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const engineRef = useRef<BrainEngine | null>(null);

  const [isLoaded, setIsLoaded] = useState(false);
  const [initError, setInitError] = useState<string | null>(null);
  const [surfaceMode, setSurfaceMode] = useState<SurfaceMode>('normal');
  const [hemisphereMode, setHemisphereMode] = useState<HemisphereMode>('close');
  const [dataMode, setDataMode] = useState<DataMode>(dataModeProp ?? 'predicted');
  const [labelsVisible, setLabelsVisible] = useState(false);
  const [selectedROI, setSelectedROI] = useState<ROIDescription | null>(null);

  // --- Mount / unmount ----------------------------------------------
  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const engine = new BrainEngine(canvas, container);
    engineRef.current = engine;

    let cancelled = false;
    engine
      .init()
      .then(() => {
        if (cancelled) return;
        if (initialView) engine.setView(initialView);
        // Internal handler: opens the bottom-of-panel description card
        // for the clicked ROI. The engine forwards every label click
        // (whether or not a parent supplied onROIClick) through this
        // callback first, then we relay to the parent if present.
        engine.setOnROIClick((roi: ROILabel) => {
          const desc = getROIDescription(roi.name);
          if (desc) setSelectedROI(desc);
          if (onROIClick) onROIClick(roi);
        });
        setIsLoaded(true);
      })
      .catch((err: unknown) => {
        console.error('BrainViewer: init failed', err);
        if (!cancelled) {
          setInitError(err instanceof Error ? err.message : String(err));
        }
      });

    return () => {
      cancelled = true;
      engine.dispose();
      engineRef.current = null;
    };
    // Intentional one-shot: the engine owns its own lifecycle; re-mounting
    // on every prop change would thrash WebGL contexts.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // --- Activation prop changes --------------------------------------
  // The colorMode prop selects which activation source drives the
  // brain colors. Multimodal RGB and single-channel hot/fire are
  // mutually exclusive -- whichever is active gets pushed to the
  // engine; if neither is provided the brain reverts to grey.
  useEffect(() => {
    const engine = engineRef.current;
    if (!engine || !isLoaded) return;
    if (
      colorMode === 'multimodal' &&
      multimodalActivation &&
      multimodalActivation.text.length > 0
    ) {
      engine.setMultimodalActivation(multimodalActivation);
      return;
    }
    if (activation && activation.length > 0) {
      engine.setActivation(activation);
      return;
    }
    engine.clearActivation();
  }, [activation, multimodalActivation, colorMode, isLoaded]);

  // --- Reactive view changes ----------------------------------------
  useEffect(() => {
    if (!isLoaded || !view) return;
    engineRef.current?.setView(view);
  }, [view, isLoaded]);

  // --- ROI highlight (driven by chart hover) ------------------------
  useEffect(() => {
    if (!isLoaded) return;
    engineRef.current?.highlightROI(highlightROI ?? null);
  }, [highlightROI, isLoaded]);

  // --- Interactive toggle (lock the brain in place for hero use) ----
  useEffect(() => {
    if (!isLoaded) return;
    engineRef.current?.setInteractive(interactive);
  }, [interactive, isLoaded]);

  // --- Time series + media binding ----------------------------------
  // Push the (T * 20484) buffer to the engine when it changes; clear
  // when the prop goes null. The animation controller takes over from
  // here, interpolating between TRs every animate() tick.
  useEffect(() => {
    const engine = engineRef.current;
    if (!engine || !isLoaded) return;
    if (timeSeries && nTrs > 0) {
      engine.setTimeSeries(timeSeries, nTrs, tr);
    } else {
      engine.clearTimeSeries();
    }
  }, [timeSeries, nTrs, tr, isLoaded]);

  // Bind / unbind the media element separately so a parent can swap
  // the player without re-uploading the time series.
  useEffect(() => {
    const engine = engineRef.current;
    if (!engine || !isLoaded) return;
    engine.bindMediaElement(mediaElement);
  }, [mediaElement, isLoaded]);

  // --- Resize observer ----------------------------------------------
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        engineRef.current?.resize(width, height);
      }
    });
    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  // --- Toggle handlers -----------------------------------------------
  const handleSurfaceChange = (mode: SurfaceMode) => {
    setSurfaceMode(mode);
    const engine = engineRef.current;
    if (!engine) return;
    if ((mode === 'inflated') !== (engine.getSurfaceMode() === 'inflated')) {
      engine.toggleInflate();
    }
  };

  const handleHemisphereChange = (mode: HemisphereMode) => {
    setHemisphereMode(mode);
    const engine = engineRef.current;
    if (!engine) return;
    if ((mode === 'open') !== (engine.getHemisphereMode() === 'open')) {
      engine.toggleHemispheres();
    }
  };

  const showMultimodal =
    colorMode === 'multimodal' &&
    !!(multimodalActivation && multimodalActivation.text.length > 0);
  const showActivation =
    !showMultimodal && !!(activation && activation.length > 0);
  const showSkeleton = loadingProp || (!isLoaded && !initError);

  return (
    <div
      ref={containerRef}
      className={`relative h-full w-full overflow-hidden ${className}`}
    >
      <canvas ref={canvasRef} className="block h-full w-full" />

      {showSkeleton && (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <div className="h-10 w-10 animate-pulse rounded-full border border-white/30" />
            <span className="text-xs uppercase tracking-[0.2em] text-white/60">
              Loading brain mesh
            </span>
          </div>
        </div>
      )}

      {initError && (
        <div className="absolute inset-0 flex items-center justify-center p-6">
          <div className="max-w-md text-center text-sm text-white/80">
            <p className="mb-2 font-mono text-xs uppercase tracking-wider text-red-400">
              Renderer error
            </p>
            <p>{initError}</p>
          </div>
        </div>
      )}

      {isLoaded && !initError && showOverlays && (
        <>
          {showActivation && <ActivityLegend />}
          {showMultimodal && <MultimodalLegend />}
          <ControlToggles
            dataMode={dataMode}
            surfaceMode={surfaceMode}
            hemisphereMode={hemisphereMode}
            onDataModeChange={setDataMode}
            onSurfaceModeChange={handleSurfaceChange}
            onHemisphereModeChange={handleHemisphereChange}
          />
          {/* ROI label toggle - small pill in the top-left corner.
              Side effect (engine.toggleGuide) is OUTSIDE the React state
              updater so it does not double-fire under Strict Mode. */}
          <button
            type="button"
            onClick={() => {
              const next = !labelsVisible;
              setLabelsVisible(next);
              engineRef.current?.toggleGuide();
              if (!next) setSelectedROI(null);
            }}
            className={`absolute left-4 top-4 z-30 rounded-full border px-3 py-1.5 text-[11px] font-medium uppercase tracking-wider backdrop-blur-md transition-colors ${
              labelsVisible
                ? 'border-white/60 bg-white/15 text-white'
                : 'border-white/20 bg-black/40 text-white/65 hover:border-white/40 hover:text-white'
            }`}
          >
            {labelsVisible ? 'Hide labels' : 'Show labels'}
          </button>
          {selectedROI && (
            <ROIDescriptionPanel
              roi={selectedROI}
              onClose={() => setSelectedROI(null)}
            />
          )}
        </>
      )}
    </div>
  );
}
