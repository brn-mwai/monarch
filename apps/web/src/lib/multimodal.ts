// ============================================================
// multimodal.ts -- per-modality interpretation for the RGB view
// ============================================================
//
// TRIBE v2 fuses three encoders, each of which the paper (Fig 7) maps to a
// different cortical network:
//   text  (LLaMA 3.2-3B)      -> language network + prefrontal  [red]
//   audio (Wav2Vec-BERT 2.0)  -> auditory cortex (prosody)      [green]
//   video (V-JEPA 2)          -> visual + motion cortex         [blue]
//
// Real per-modality NAA comes from POST /api/scan/multimodal on the pod,
// which runs a separate pass per modality. Offline we illustrate the paper's
// DIRECTION rather than invent precise numbers: text routes more to the
// deliberative language/prefrontal system (lower NAA), while audio prosody
// and video faces/motion carry more affective salience (higher NAA).
// ============================================================

export interface PerModalityNaa {
  textNAA: number;
  audioNAA: number;
  videoNAA: number;
  combinedNAA: number;
}

const TEXT_LEAN = 0.78;
const AUDIO_LEAN = 0.95;
const VIDEO_LEAN = 1.12;

export function estimatePerModalityNaa(combined: number): PerModalityNaa {
  return {
    textNAA: combined * TEXT_LEAN,
    audioNAA: combined * AUDIO_LEAN,
    videoNAA: combined * VIDEO_LEAN,
    combinedNAA: combined,
  };
}
