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
  const a_lan = (1 - beta_j) / 2;
  const b_lan = 1 / 12;
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

  // Mean-field susceptibility AT the equilibrium: it must vary with NAA, not
  // be a constant. sech^2(arg) = 1 - m*^2 since m* = tanh(arg).
  const sech2 = 1 - mStar * mStar;
  const susceptibility = sech2 / Math.max(1e-6, 1 - beta_j * sech2);

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
      susceptibility,
      external_field_h: h,
      beta_j,
      alpha_hat,
    },
    // Per-ROI activation. Weights are normalised so the affective ROIs
    // average to a_aff and the deliberative ROIs average to a_del -- so the
    // breakdown is consistent with the reported NAA, not an arbitrary scale.
    roiBreakdown: buildRoiBreakdown(a_aff, a_del),
  };
}

interface RoiSeed {
  name: string;
  weight: number;
  system: 'affective' | 'deliberative';
  vertexCount: number;
}

const ROI_SEEDS: RoiSeed[] = [
  { name: 'OFC', weight: 0.94, system: 'affective', vertexCount: 312 },
  { name: 'AAIC', weight: 1.04, system: 'affective', vertexCount: 198 },
  { name: 'a24', weight: 0.84, system: 'affective', vertexCount: 245 },
  { name: 'TGd', weight: 1.18, system: 'affective', vertexCount: 167 },
  { name: 'TE1a', weight: 1.0, system: 'affective', vertexCount: 203 },
  { name: '46', weight: 1.05, system: 'deliberative', vertexCount: 289 },
  { name: 'a9-46v', weight: 0.95, system: 'deliberative', vertexCount: 234 },
  { name: 'd32', weight: 1.12, system: 'deliberative', vertexCount: 178 },
  { name: 'a10p', weight: 0.87, system: 'deliberative', vertexCount: 156 },
  { name: '13l', weight: 1.01, system: 'deliberative', vertexCount: 201 },
];

function buildRoiBreakdown(aAff: number, aDel: number) {
  return ROI_SEEDS.map((r) => ({
    name: r.name,
    activation: r.weight * (r.system === 'affective' ? aAff : aDel),
    system: r.system,
    vertexCount: r.vertexCount,
  }));
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
