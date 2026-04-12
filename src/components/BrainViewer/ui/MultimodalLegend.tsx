'use client';

/**
 * MultimodalLegend -- RGB color key for the three-encoder visualization.
 *
 * Three overlapping circles in additive (screen) blend mode produce the
 * RGB color triangle: pure R/G/B at the corners, secondary colors
 * (cyan, magenta, yellow) where two circles overlap, white in the
 * center where all three meet. Matches the channel mapping used by
 * ActivationMapper.applyMultimodalActivation:
 *   R = Video, G = Text, B = Audio
 */
export function MultimodalLegend() {
  return (
    <div className="pointer-events-none absolute right-4 top-4 flex flex-col items-center gap-1 rounded-md bg-black/40 px-3 py-2 backdrop-blur">
      <svg width="96" height="86" viewBox="0 0 96 86">
        {/* Three overlapping circles in additive blend produce the RGB triangle. */}
        <circle
          cx="48"
          cy="26"
          r="26"
          fill="#FF0000"
          opacity="0.55"
          style={{ mixBlendMode: 'screen' }}
        />
        <circle
          cx="28"
          cy="58"
          r="26"
          fill="#00FF00"
          opacity="0.55"
          style={{ mixBlendMode: 'screen' }}
        />
        <circle
          cx="68"
          cy="58"
          r="26"
          fill="#0066FF"
          opacity="0.55"
          style={{ mixBlendMode: 'screen' }}
        />

        {/* Channel labels positioned just outside each corner. */}
        <text
          x="48"
          y="9"
          textAnchor="middle"
          fill="#FF6464"
          fontSize="9"
          fontFamily="ui-monospace, SFMono-Regular, monospace"
        >
          VIDEO
        </text>
        <text
          x="10"
          y="80"
          textAnchor="start"
          fill="#64FF64"
          fontSize="9"
          fontFamily="ui-monospace, SFMono-Regular, monospace"
        >
          TEXT
        </text>
        <text
          x="86"
          y="80"
          textAnchor="end"
          fill="#64A0FF"
          fontSize="9"
          fontFamily="ui-monospace, SFMono-Regular, monospace"
        >
          AUDIO
        </text>
      </svg>
      <span className="text-[10px] uppercase tracking-wider text-white/60">
        Multimodal
      </span>
    </div>
  );
}
