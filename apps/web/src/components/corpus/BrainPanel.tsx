'use client';

import dynamic from 'next/dynamic';
import { useMemo } from 'react';

import { categoryLabel, signed, type CorpusItem } from '@/lib/corpus-types';
import {
  buildScaledRoiActivation,
  type RoiVertices,
} from '@/lib/measured-activation';

const BrainViewer = dynamic(
  () => import('@/components/BrainViewer').then((m) => m.BrainViewer),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-full items-center justify-center text-xs text-white/40">
        Loading surface
      </div>
    ),
  },
);

interface Props {
  item: CorpusItem;
  rois: RoiVertices | null;
  mask: Uint8Array | null;
  scaleLo: number;
  scaleHi: number;
  height?: number;
  compact?: boolean;
  /** False inside the shared-control comparison frame, which supplies its own chrome. */
  chrome?: boolean;
}

export function BrainPanel({
  item,
  rois,
  mask,
  scaleLo,
  scaleHi,
  height = 420,
  compact = false,
  chrome = true,
}: Props) {
  const activation = useMemo(() => {
    if (!rois || item.aAff === null || item.aDel === null) return null;
    return buildScaledRoiActivation(rois, item.aAff, item.aDel, scaleLo, scaleHi, mask);
  }, [rois, item, scaleLo, scaleHi, mask]);

  const leads =
    item.aAff === null || item.aDel === null
      ? null
      : item.aAff > item.aDel
        ? 'affective'
        : 'deliberative';

  const body = (
    <>
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 px-5 py-3">
        <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/45">
          {categoryLabel(item.category)}
        </span>
        <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/45">
          {leads === null ? 'no values' : `${leads} leads`}
        </span>
      </div>

      <p
        className={`px-5 pt-4 text-[13px] leading-relaxed text-white/70 ${
          compact ? 'line-clamp-3' : ''
        }`}
      >
        {item.preview}
      </p>

      <div className="px-3 py-3" style={{ height }}>
        {activation ? (
          <BrainViewer
            activation={activation}
            colorMode="activation"
            interactive
            showOverlays={chrome}
          />
        ) : (
          <div className="flex h-full items-center justify-center text-xs text-white/40">
            This item has no measured values
          </div>
        )}
      </div>

      <dl className="grid grid-cols-3 gap-3 border-t border-white/10 px-5 py-4 font-mono text-[11px] tabular-nums">
        <div>
          <dt className="text-white/40">Affective</dt>
          <dd className="mt-1 text-white">{signed(item.aAff)}</dd>
        </div>
        <div>
          <dt className="text-white/40">Deliberative</dt>
          <dd className="mt-1 text-white">{signed(item.aDel)}</dd>
        </div>
        <div>
          <dt className="text-white/40">Difference</dt>
          <dd className="mt-1 text-white">{signed(item.naaSigned)}</dd>
        </div>
      </dl>
    </>
  );

  if (!chrome) return <div className="flex h-full flex-col">{body}</div>;

  return (
    <div className="flex h-full flex-col rounded-xl border border-white/10 bg-white/[0.015]">
      {body}
    </div>
  );
}
