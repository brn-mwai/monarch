'use client';

import { useRef, useState } from 'react';

import { BrainViewer } from '@/components/BrainViewer';
import type { ScanResult } from '@/lib/scan-store';

interface ElementCardProps {
  label: 'A' | 'B';
  scanResult: ScanResult | null;
  isLoading?: boolean;
}

/**
 * Self-contained scan result card matching the dual-brain compare layout.
 *
 * Each card has:
 * - Header with label badge + NAA classification pill
 * - Left: text excerpt or media preview
 * - Right: independent BrainViewer (its own WebGL context)
 * - Bottom: playback controls when a time series is available
 *
 * Two of these stacked vertically produce the A/B compare view.
 */
export function ElementCard({ label, scanResult, isLoading }: ElementCardProps) {
  const [hemisphere, setHemisphere] = useState<'both' | 'left' | 'right'>('both');
  const mediaRef = useRef<HTMLVideoElement | HTMLAudioElement>(null);

  const naa = scanResult?.naa;
  const clsColor =
    naa?.classification === 'HIGH'
      ? 'bg-red-500/10 text-red-400 border-red-500/30'
      : naa?.classification === 'MOD'
      ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
      : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';

  return (
    <div className="overflow-hidden rounded-xl border border-white/10 bg-[#0A0A0A]">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
        <div className="flex items-center gap-2">
          <span
            className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${
              label === 'A'
                ? 'border border-white/30 bg-white/10 text-white'
                : 'border border-red-500/30 bg-red-500/10 text-red-400'
            }`}
          >
            {label}
          </span>
          <span className="text-sm font-medium text-white">Element {label}</span>
        </div>

        {naa && (
          <span
            className={`rounded-full border px-3 py-1 font-mono text-xs ${clsColor}`}
          >
            NAA {naa.naa.toFixed(2)} - {naa.classification}
          </span>
        )}
      </div>

      {/* Content area: text/media + brain side-by-side */}
      <div className="flex gap-0">
        {/* Left: content preview */}
        <div className="w-[40%] p-4">
          {scanResult ? (
            <div className="max-h-48 overflow-y-auto rounded-lg bg-white/[0.03] p-3">
              <p className="font-mono text-[11px] leading-relaxed text-white/60">
                {scanResult.inputContent}
              </p>
            </div>
          ) : isLoading ? (
            <div className="flex h-32 items-center justify-center rounded-lg bg-white/[0.02]">
              <span className="animate-pulse text-xs text-white/30">
                Scanning...
              </span>
            </div>
          ) : (
            <div className="flex h-32 items-center justify-center rounded-lg border border-dashed border-white/10">
              <span className="text-xs text-white/25">
                Paste content to scan
              </span>
            </div>
          )}
        </div>

        {/* Right: independent brain renderer */}
        <div className="relative h-64 w-[60%] bg-[#060606]">
          {/* Hemisphere toggle */}
          <div className="absolute left-1/2 top-3 z-10 flex -translate-x-1/2 gap-1">
            {(['both', 'left', 'right'] as const).map((h) => (
              <button
                key={h}
                type="button"
                onClick={() => setHemisphere(h)}
                className={`rounded-full px-3 py-1 font-mono text-xs uppercase ${
                  hemisphere === h
                    ? 'border border-white/30 bg-white/15 text-white'
                    : 'text-white/40 hover:text-white/60'
                }`}
              >
                {h === 'both' ? 'BOTH' : h === 'left' ? 'L' : 'R'}
              </button>
            ))}
          </div>

          <BrainViewer
            activation={scanResult?.activationVector ?? null}
            colorMode="activation"
            showOverlays={false}
            className="absolute inset-0"
          />
        </div>
      </div>

      {/* Time series playback controls (when available) */}
      {scanResult?.timeSeries && (
        <div className="flex items-center gap-3 border-t border-white/10 px-4 py-2">
          <button
            type="button"
            className="text-xs text-white/50 hover:text-white"
          >
            -10s
          </button>
          <button
            type="button"
            className="flex h-7 w-7 items-center justify-center rounded-full bg-white/10 hover:bg-white/20"
          >
            <span className="ml-0.5 text-xs text-white">&#9654;</span>
          </button>
          <button
            type="button"
            className="text-xs text-white/50 hover:text-white"
          >
            +10s
          </button>
          <span className="font-mono text-xs text-white/40">
            {scanResult.nTrs} TRs
          </span>
        </div>
      )}
    </div>
  );
}
