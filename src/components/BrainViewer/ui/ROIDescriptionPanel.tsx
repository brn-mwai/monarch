'use client';

import { X } from '@phosphor-icons/react/dist/ssr';

import {
  SYSTEM_INFO,
  type ROIDescription,
} from '@/lib/roi-labels';

interface ROIDescriptionPanelProps {
  roi: ROIDescription;
  onClose: () => void;
}

/**
 * Slide-up description panel that appears at the bottom of the brain
 * viewer when the user clicks an ROI label. Mirrors the bottom card
 * style used in the TRIBE v2 demo's "Explore In-Silico" tab.
 */
export function ROIDescriptionPanel({ roi, onClose }: ROIDescriptionPanelProps) {
  const sys = SYSTEM_INFO[roi.system];

  return (
    <div className="absolute inset-x-0 bottom-0 z-30 animate-roi-slide-up border-t border-white/10 bg-[#0a0a0a]/95 px-5 py-4 backdrop-blur-md">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span
              className="inline-block h-2.5 w-2.5 shrink-0 rounded-full"
              style={{ backgroundColor: sys.color }}
            />
            <h3 className="truncate text-sm font-semibold text-white">
              {roi.name}
            </h3>
            <span className="font-mono text-[10px] uppercase tracking-wider text-white/35">
              {roi.shortName}
            </span>
          </div>
          <p className="mt-1 font-mono text-[10px] uppercase tracking-wider text-white/45">
            {sys.label}
          </p>
          <p className="mt-3 text-[12px] leading-relaxed text-white/70">
            {roi.description}
          </p>
          <p className="mt-3 font-mono text-[9px] uppercase tracking-wider text-white/30">
            HCP parcels: {roi.hcpParcels.join(', ')}
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-full p-1 text-white/40 transition-colors hover:bg-white/5 hover:text-white"
          aria-label="Close ROI description"
        >
          <X size={16} weight="bold" />
        </button>
      </div>
    </div>
  );
}
