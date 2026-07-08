'use client';

import { useEffect, useState } from 'react';

import { MultimodalBars } from '@/components/charts/MultimodalBars';
import { buildSyntheticScan } from '@/lib/mock-data';
import {
  buildModalityActivation,
  loadModalityVertices,
  type ModalityVertices,
} from '@/lib/roi-activation';
import { getActiveResult, useScanState } from '@/lib/scan-store';

type Variant = 'combined' | 'text' | 'audio' | 'video';

const VARIANT_LABEL: Record<Variant, string> = {
  combined: 'Combined',
  text: 'Text only',
  audio: 'Audio only',
  video: 'Video only',
};

const VARIANT_NOTE: Record<Variant, string> = {
  combined: 'Full RGB overlay - text/audio/video on the same surface',
  text: 'LLaMA 3.2-3B activation pathway only',
  audio: 'Wav2Vec-BERT audio encoder only',
  video: 'V-JEPA 2 video encoder only',
};

/**
 * "Multimodal" tab. Shows the RGB triangle legend, four selector cards
 * for combined / text / audio / video views, and a per-modality NAA bar
 * chart when an active multimodal scan exists.
 */
export function MultimodalTab() {
  const { state, dispatch } = useScanState();
  const [modality, setModality] = useState<ModalityVertices | null>(null);
  const [activeVariant, setActiveVariant] = useState<Variant>('combined');
  const active = getActiveResult(state);

  useEffect(() => {
    let cancelled = false;
    loadModalityVertices()
      .then((m) => {
        if (!cancelled) setModality(m);
      })
      .catch((err: unknown) => {
        console.error('MultimodalTab: failed to load modality vertices', err);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const loadVariant = (variant: Variant) => {
    if (!modality) return;
    setActiveVariant(variant);
    const naa = 1.8;
    const base = buildSyntheticScan(
      `multimodal-${variant}`,
      `Multimodal - ${variant}`,
      naa,
      null,
    );
    const mm = buildModalityActivation(modality);

    if (variant === 'combined') {
      dispatch({
        type: 'SCAN_COMPLETE_A',
        result: { ...base, multimodal: mm },
      });
      dispatch({ type: 'SET_COLOR_MODE', mode: 'multimodal' });
      return;
    }

    const single =
      variant === 'text' ? mm.text : variant === 'audio' ? mm.audio : mm.video;
    dispatch({
      type: 'SCAN_COMPLETE_A',
      result: { ...base, activationVector: single },
    });
    dispatch({ type: 'SET_COLOR_MODE', mode: 'activation' });
  };

  return (
    <div className="space-y-5">
      <div className="space-y-3 text-[15px] leading-relaxed text-white/75">
        <p>
          See which brain areas rely most on text, audio, or video information.
          This multimodal breakdown shows how TRIBE v2 integrates all three
          input streams simultaneously, reflecting how the brain itself
          combines information across senses.
        </p>
      </div>

      {/* RGB triangle legend */}
      <div className="flex items-center gap-4 rounded-lg border border-white/10 p-4">
        <RGBTriangle />
        <div className="text-xs text-white/55">
          <p className="mb-1 font-mono uppercase tracking-wider text-white/40">
            Channel mapping
          </p>
          <p>
            Red = text, Green = audio, Blue = video. Pure colours show single-
            modality regions; blends mark areas integrating multiple senses.
          </p>
        </div>
      </div>

      {/* Selector cards (TRIBE v2 subject-card style) */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {(['combined', 'text', 'audio', 'video'] as const).map((v) => {
          const isActive = activeVariant === v;
          return (
            <button
              key={v}
              type="button"
              disabled={!modality}
              onClick={() => loadVariant(v)}
              className={`flex h-32 flex-col items-center justify-center rounded-lg border p-4 text-center transition-all ${
                isActive
                  ? 'border-white/30 bg-white/5 text-white'
                  : 'border-white/10 text-white/65 hover:border-white/25 hover:bg-white/[0.02]'
              } disabled:cursor-not-allowed disabled:opacity-40`}
            >
              <span className="text-base font-medium">{VARIANT_LABEL[v]}</span>
              <span className="mt-2 px-2 text-[10px] leading-snug text-white/45">
                {VARIANT_NOTE[v]}
              </span>
            </button>
          );
        })}
      </div>

      {active?.multimodal && (
        <div className="rounded-lg border border-white/10 p-4">
          <MultimodalBars
            videoNAA={active.naa.naa * 1.1}
            textNAA={active.naa.naa * 0.7}
            audioNAA={active.naa.naa * 0.9}
            combinedNAA={active.naa.naa}
          />
        </div>
      )}
    </div>
  );
}

/** Three additive screen-blend circles producing the RGB colour triangle. */
function RGBTriangle() {
  return (
    <svg width="80" height="76" viewBox="0 0 80 76" aria-hidden="true">
      <circle
        cx="40"
        cy="22"
        r="22"
        fill="#FF0000"
        opacity="0.55"
        style={{ mixBlendMode: 'screen' }}
      />
      <circle
        cx="24"
        cy="50"
        r="22"
        fill="#00FF00"
        opacity="0.55"
        style={{ mixBlendMode: 'screen' }}
      />
      <circle
        cx="56"
        cy="50"
        r="22"
        fill="#0066FF"
        opacity="0.55"
        style={{ mixBlendMode: 'screen' }}
      />
      <text
        x="40"
        y="9"
        textAnchor="middle"
        fill="#FF6464"
        fontSize="8"
        fontFamily="ui-monospace, SFMono-Regular, monospace"
      >
        VIDEO
      </text>
      <text
        x="6"
        y="72"
        textAnchor="start"
        fill="#64FF64"
        fontSize="8"
        fontFamily="ui-monospace, SFMono-Regular, monospace"
      >
        TEXT
      </text>
      <text
        x="74"
        y="72"
        textAnchor="end"
        fill="#64A0FF"
        fontSize="8"
        fontFamily="ui-monospace, SFMono-Regular, monospace"
      >
        AUDIO
      </text>
    </svg>
  );
}
