'use client';

// The authentic activity legend graphic from Meta's TRIBE v2 demo, fetched
// as a self-contained SVG (gradient bar + baked-in labels). Monarch's painted
// fire colormap is ported from the same source, so this legend is the
// authoritative key for the brain panel.
export function ActivityLegend() {
  return (
    <div className="pointer-events-none absolute right-4 top-4">
      <img
        src="/legends/legend-activity-4d3959ff.svg"
        alt="Brain activity scale, low to high"
        width={200}
        height={55}
        draggable={false}
        className="h-auto w-[180px] select-none"
      />
    </div>
  );
}
