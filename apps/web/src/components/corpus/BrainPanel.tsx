'use client';

import dynamic from 'next/dynamic';
import { useEffect, useMemo, useState } from 'react';

import { categoryLabel, signed, type CorpusItem } from '@/lib/corpus-types';
import {
  buildScaledRoiActivation,
  loadItemVector,
  type RoiVertices,
  type VectorScale,
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
  /** Corpus-wide vertex range, so two per-vertex maps are comparable. */
  vectorScale?: VectorScale | null;
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
  vectorScale = null,
  height = 420,
  compact = false,
  chrome = true,
}: Props) {
  const [expanded, setExpanded] = useState(false);
  const [vector, setVector] = useState<Float32Array | null>(null);

  // The real per-vertex map when the scan kept one. It replaces the flat fill entirely
  // rather than being blended with it, so what is drawn is the prediction itself.
  useEffect(() => {
    let cancelled = false;
    setVector(null);
    if (!item.hasVector) return;
    loadItemVector(item.id, vectorScale, mask).then((v) => {
      if (!cancelled) setVector(v);
    });
    return () => {
      cancelled = true;
    };
  }, [item, vectorScale, mask]);

  const fallback = useMemo(() => {
    if (!rois || item.aAff === null || item.aDel === null) return null;
    return buildScaledRoiActivation(rois, item.aAff, item.aDel, scaleLo, scaleHi, mask);
  }, [rois, item, scaleLo, scaleHi, mask]);

  const activation = vector ?? fallback;
  const perVertex = vector !== null;

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
        <span className="flex items-center gap-3">
          <span
            className={`font-mono text-[9px] uppercase tracking-[0.18em] ${
              perVertex ? 'text-white/70' : 'text-white/30'
            }`}
            title={
              perVertex
                ? 'Every vertex carries its own predicted value. Vertices below the stated threshold are left unpainted so the anatomy stays readable.'
                : 'Two region averages; the per-vertex map was not kept for this item'
            }
          >
            {perVertex
              ? vectorScale?.threshold === undefined
                ? 'Per vertex'
                : `Per vertex, above ${signed(vectorScale.threshold)}`
              : 'Region average'}
          </span>
          <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/45">
            {leads === null ? 'no values' : `${leads} leads`}
          </span>
        </span>
      </div>

      <div className="px-5 pt-4">
        <p className="line-clamp-3 text-[13px] leading-relaxed text-white/70">
          {item.preview}
        </p>
        {(item.text ?? '').length > item.preview.length && (
          <button
            type="button"
            onClick={() => setExpanded(true)}
            className="mt-2 font-mono text-[10px] uppercase tracking-[0.15em] text-white/45 underline-offset-4 transition-colors hover:text-white hover:underline"
          >
            See more
          </button>
        )}
      </div>

      {expanded && (
        <div
          className="fixed inset-0 z-[60] flex items-start justify-center overflow-y-auto bg-black/80 p-4 backdrop-blur-sm sm:p-10"
          onClick={() => setExpanded(false)}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-2xl rounded-xl border border-white/15 bg-[#0a0a0a] p-6 shadow-2xl"
          >
            <div className="flex items-center justify-between gap-4">
              <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/45">
                {categoryLabel(item.category)}
              </span>
              <button
                type="button"
                onClick={() => setExpanded(false)}
                className="font-mono text-[10px] uppercase tracking-[0.15em] text-white/50 transition-colors hover:text-white"
              >
                Hide
              </button>
            </div>
            <p className="mt-4 whitespace-pre-wrap text-[14px] leading-relaxed text-white/80">
              {item.text ?? item.preview}
            </p>
          </div>
        </div>
      )}

      <div className="px-3 py-3" style={{ height }}>
        {activation ? (
          <BrainViewer
            activation={activation}
            activationPreNormalized
            colorMode="activation"
            interactive
            autoRotate
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
