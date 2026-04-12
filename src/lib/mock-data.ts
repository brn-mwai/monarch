// ============================================================
// mock-data.ts -- synthetic content + scan-result generator
// ============================================================
//
// Until the backend is wired up, every page in the app drives its
// brain + chart updates from this module. Keeping the mock generator
// in one place lets us tune the demo numbers in one spot and avoids
// duplicating Landau math in each page.
// ============================================================

import type { ScanResult } from './scan-store';

const HEMI_VERTS = 10242;
const TOTAL_VERTS = 2 * HEMI_VERTS;

export type ContentCategory =
  | 'neutral'
  | 'high-outrage'
  | 'fear-activating'
  | 'reward-hook';

export interface ExampleContent {
  id: string;
  text: string;
  expectedNAA: number;
  category: ContentCategory;
  /** Short label shown above the body in the example card grid. */
  label: string;
}

export const EXAMPLE_CONTENTS: ExampleContent[] = [
  {
    id: 'fed-calm',
    label: 'Reuters wire',
    text: 'Federal Reserve holds interest rates steady, citing stable inflation outlook and resilient labour market conditions.',
    expectedNAA: 0.84,
    category: 'neutral',
  },
  {
    id: 'fed-outrage',
    label: 'Outrage feed',
    text: 'FED DESTROYS AMERICA - your savings are GONE. The economic collapse they did not want you to know about!',
    expectedNAA: 3.71,
    category: 'high-outrage',
  },
  {
    id: 'wheat-factual',
    label: 'Trade desk',
    text: 'Global wheat production forecast revised upward by 2.3% following favourable weather conditions across major growing regions in the Northern Hemisphere.',
    expectedNAA: 0.62,
    category: 'neutral',
  },
  {
    id: 'health-scare',
    label: 'Engagement bait',
    text: 'DOCTORS ARE HIDING THIS! The secret ingredient in your kitchen that DESTROYS cancer cells overnight. Big Pharma does not want you to know!',
    expectedNAA: 4.12,
    category: 'fear-activating',
  },
  {
    id: 'rct-abstract',
    label: 'PubMed abstract',
    text: 'A randomised controlled trial of 2,847 participants demonstrated statistically significant improvement in glycaemic control with the intervention group showing HbA1c reduction of 0.8% over 12 months.',
    expectedNAA: 0.51,
    category: 'neutral',
  },
  {
    id: 'reward-hook',
    label: 'Reward hook',
    text: 'You WILL NOT BELIEVE what happened next! This mum tried ONE simple trick and made $10,000 in a week. Watch until the end!',
    expectedNAA: 3.89,
    category: 'reward-hook',
  },
];

/**
 * Build a synthetic ScanResult with a Landau curve, NAA breakdown, and
 * an ROI table that all reflect the supplied NAA value. Used by every
 * page in the app while the backend is offline.
 *
 * The activation vector is OPTIONAL because some callers (e.g. the
 * scanner page) generate the spatial activation themselves via
 * `generateSpatialActivation` after the brain coords have loaded.
 */
export function buildSyntheticScan(
  scanId: string,
  inputContent: string,
  naaValue: number,
  activationVector: Float32Array | null,
): ScanResult {
  const a_del = 0.6;
  const a_aff = a_del * naaValue;

  const beta_j = 0.7;
  const alpha_hat = 0.5;
  const a_lan = 1 - beta_j;
  const b_lan = (beta_j ** 3) / 3;
  const h = alpha_hat * naaValue;

  const free_energy_m: number[] = [];
  const free_energy_F: number[] = [];
  for (let i = 0; i < 200; i++) {
    const mi = -1 + (2 * i) / 199;
    free_energy_m.push(mi);
    free_energy_F.push(a_lan * mi * mi + b_lan * Math.pow(mi, 4) - h * mi);
  }

  // Equilibrium m* via fixed-point iteration of m = tanh(beta_j*m + h)
  let mStar = 0;
  for (let k = 0; k < 200; k++) {
    const next = Math.tanh(beta_j * mStar + h);
    if (Math.abs(next - mStar) < 1e-9) {
      mStar = next;
      break;
    }
    mStar = next;
  }

  return {
    scanId,
    inputContent,
    modality: 'text',
    nTrs: 24,
    activationVector,
    naa: {
      naa: naaValue,
      a_aff,
      a_del,
      classification: naaValue < 1 ? 'LOW' : naaValue <= 2 ? 'MOD' : 'HIGH',
    },
    landau: {
      free_energy_m,
      free_energy_F,
      equilibrium_m: mStar,
      susceptibility: 1 / (1 - beta_j),
      external_field_h: h,
      beta_j,
      alpha_hat,
    },
    roiBreakdown: [
      { name: 'OFC', activation: 0.65 * naaValue * 0.5, system: 'affective', vertexCount: 312 },
      { name: 'AAIC', activation: 0.72 * naaValue * 0.5, system: 'affective', vertexCount: 198 },
      { name: 'a24', activation: 0.58 * naaValue * 0.5, system: 'affective', vertexCount: 245 },
      { name: 'TGd', activation: 0.81 * naaValue * 0.5, system: 'affective', vertexCount: 167 },
      { name: 'TE1a', activation: 0.69 * naaValue * 0.5, system: 'affective', vertexCount: 203 },
      { name: '46', activation: 0.42, system: 'deliberative', vertexCount: 289 },
      { name: '9-46v', activation: 0.38, system: 'deliberative', vertexCount: 234 },
      { name: 'd32', activation: 0.45, system: 'deliberative', vertexCount: 178 },
      { name: '10p', activation: 0.35, system: 'deliberative', vertexCount: 156 },
      { name: '13l', activation: 0.41, system: 'deliberative', vertexCount: 201 },
    ],
  };
}

/**
 * Generate a synthetic time series mimicking what TRIBE v2 would
 * produce for an N-second clip. Output is a flat Float32Array of
 * length `nTrs * 20484`. Frame N starts at index `N * 20484`.
 *
 * The activation pattern oscillates over time so the brain visibly
 * pulses when AnimationController plays it back. Values are in
 * arbitrary units (matching real TRIBE v2 output) - the frontend
 * normalises per-frame via robustNormalize.
 */
export function buildSyntheticTimeSeries(
  baseActivation: Float32Array,
  nTrs: number = 30,
): Float32Array {
  const V = baseActivation.length;
  const out = new Float32Array(nTrs * V);

  for (let t = 0; t < nTrs; t++) {
    // Slow sine modulation (period ~10 TRs) so the activation pulses
    // visibly. Plus a small random per-frame jitter so the brain looks
    // alive instead of perfectly periodic.
    const phase = (t / nTrs) * Math.PI * 4; // 2 full oscillations across the clip
    const envelope = 0.5 + 0.5 * Math.sin(phase);
    const jitter = 0.85 + Math.random() * 0.3;

    const start = t * V;
    for (let i = 0; i < V; i++) {
      out[start + i] = baseActivation[i] * envelope * jitter;
    }
  }

  return out;
}

/**
 * Build a synthetic per-modality activation triple for the multimodal
 * RGB visualisation. Each channel lights a different cortical region.
 */
export function buildSyntheticMultimodal(): {
  text: Float32Array;
  audio: Float32Array;
  video: Float32Array;
} {
  const text = new Float32Array(TOTAL_VERTS);
  const audio = new Float32Array(TOTAL_VERTS);
  const video = new Float32Array(TOTAL_VERTS);
  for (let i = 0; i < TOTAL_VERTS; i++) {
    if (i < 3000 || (i >= HEMI_VERTS && i < HEMI_VERTS + 3000)) {
      text[i] = 0.5 + Math.random() * 0.5;
    } else {
      text[i] = Math.random() * 0.15;
    }
    if (
      (i >= 3000 && i < 5500) ||
      (i >= HEMI_VERTS + 3000 && i < HEMI_VERTS + 5500)
    ) {
      audio[i] = 0.5 + Math.random() * 0.5;
    } else {
      audio[i] = Math.random() * 0.15;
    }
    if ((i >= 7000 && i < HEMI_VERTS) || (i >= HEMI_VERTS + 7000 && i < TOTAL_VERTS)) {
      video[i] = 0.5 + Math.random() * 0.5;
    } else {
      video[i] = Math.random() * 0.15;
    }
  }
  return { text, audio, video };
}
