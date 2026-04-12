'use client';

import { COLORMAP_CSS_GRADIENT } from '../engine/Colormap';

export function ActivityLegend() {
  return (
    <div className="pointer-events-none absolute right-4 top-4 flex flex-col items-center gap-1">
      <div className="flex items-center gap-2">
        <span className="text-xs text-white">Low</span>
        <div
          className="h-2.5 w-40 rounded-sm border border-white/20"
          style={{ background: COLORMAP_CSS_GRADIENT }}
        />
        <span className="text-xs text-white">High</span>
      </div>
      <span className="text-[10px] uppercase tracking-wider text-white/60">Activity</span>
    </div>
  );
}
