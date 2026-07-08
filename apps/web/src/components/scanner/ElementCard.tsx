'use client';

import type { ScanResult } from '@/lib/scan-store';

interface ElementCardProps {
  label: string;
  scanResult: ScanResult | null;
  isLoading?: boolean;
  /** Audience-niched plain-language takeaway, shown under the excerpt. */
  takeaway?: string;
}

/**
 * One side of a compare (A/B content, or True/Predicted), data-only: label,
 * NAA pill and the content excerpt. The two brains themselves live in the
 * split layout's left panel, so the cards stay compact with no redundant brain.
 */
export function ElementCard({
  label,
  scanResult,
  isLoading,
  takeaway,
}: ElementCardProps) {
  const naa = scanResult?.naa;
  const isRedAccent = label === 'B' || label === 'Predicted';
  const title = label === 'A' || label === 'B' ? `Element ${label}` : label;
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
              isRedAccent
                ? 'border border-red-500/30 bg-red-500/10 text-red-400'
                : 'border border-white/30 bg-white/10 text-white'
            }`}
          >
            {label.charAt(0)}
          </span>
          <span className="text-sm font-medium text-white">{title}</span>
        </div>

        {naa && (
          <span
            className={`rounded-full border px-3 py-1 font-mono text-xs ${clsColor}`}
          >
            NAA {naa.naa.toFixed(2)} - {naa.classification}
          </span>
        )}
      </div>

      {/* Content excerpt */}
      <div className="p-4">
        {scanResult ? (
          <div className="max-h-40 overflow-y-auto rounded-lg bg-white/[0.03] p-3">
            <p className="font-mono text-[11px] leading-relaxed text-white/60">
              {scanResult.inputContent}
            </p>
          </div>
        ) : isLoading ? (
          <div className="flex h-20 items-center justify-center rounded-lg bg-white/[0.02]">
            <span className="animate-pulse text-xs text-white/30">
              Scanning...
            </span>
          </div>
        ) : (
          <div className="flex h-20 items-center justify-center rounded-lg border border-dashed border-white/10">
            <span className="text-xs text-white/25">Paste content to scan</span>
          </div>
        )}

        {scanResult && takeaway && (
          <p className="mt-3 rounded-lg border border-white/10 bg-white/[0.02] px-3 py-2 text-[12px] leading-relaxed text-white/70">
            {takeaway}
          </p>
        )}

        {scanResult?.timeSeries && (
          <p className="mt-3 font-mono text-[10px] uppercase tracking-wider text-white/35">
            {scanResult.nTrs} TRs - playback on the brain panel
          </p>
        )}
      </div>
    </div>
  );
}
