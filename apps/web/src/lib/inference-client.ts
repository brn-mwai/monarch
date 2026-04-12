// ============================================================
// inference-client.ts - frontend client for the inference server
// ============================================================
//
// Calls the FastAPI inference server when NEXT_PUBLIC_INFERENCE_URL
// is set, otherwise falls back to synthetic data so the platform
// is always usable during development and demos.
// ============================================================

import type { ScanResult } from './scan-store';
import { buildSyntheticScan, buildSyntheticTimeSeries } from './mock-data';
import {
  DEMO_BLOBS,
  generateSpatialActivation,
  loadBrainCoords,
} from './brain-data';

const INFERENCE_URL = process.env.NEXT_PUBLIC_INFERENCE_URL ?? '';

/** True when a real inference server is configured. */
export const hasInferenceServer = !!INFERENCE_URL;

interface RawScanResponse {
  scan_id: string;
  naa: {
    naa: number;
    a_aff: number;
    a_del: number;
    classification: 'LOW' | 'MOD' | 'HIGH';
  };
  landau: {
    free_energy_m: number[];
    free_energy_F: number[];
    equilibrium_m: number;
    susceptibility: number | null;
    external_field_h: number;
    beta_j: number;
    alpha_hat: number;
  };
  roi_breakdown: {
    name: string;
    activation: number;
    system: string;
    vertex_count: number;
  }[];
  n_trs: number;
  modality: 'text' | 'audio' | 'video';
  activation_url: string;
  timeseries_url?: string;
}

/**
 * Scan text content via the live inference server. Falls back to
 * synthetic data when the server is offline or unconfigured.
 */
export async function scanText(text: string): Promise<ScanResult> {
  if (!INFERENCE_URL) {
    return fallbackSynthetic(text);
  }

  try {
    const res = await fetch(`${INFERENCE_URL}/api/scan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, modality: 'text' }),
    });

    if (!res.ok) {
      console.warn(`Inference server returned ${res.status}, falling back to synthetic`);
      return fallbackSynthetic(text);
    }

    const data: RawScanResponse = await res.json();

    // Fetch the activation binary
    const actRes = await fetch(`${INFERENCE_URL}${data.activation_url}`);
    const actBuf = await actRes.arrayBuffer();
    const activationVector = new Float32Array(actBuf);

    // Fetch time series if available
    let timeSeries: Float32Array | undefined;
    let nTrs = data.n_trs;
    if (data.timeseries_url) {
      const tsRes = await fetch(`${INFERENCE_URL}${data.timeseries_url}`);
      const tsBuf = await tsRes.arrayBuffer();
      timeSeries = new Float32Array(tsBuf);
    }

    return {
      scanId: data.scan_id,
      inputContent: text.slice(0, 120),
      modality: data.modality,
      nTrs,
      activationVector,
      timeSeries,
      naa: data.naa,
      landau: {
        free_energy_m: data.landau.free_energy_m,
        free_energy_F: data.landau.free_energy_F,
        equilibrium_m: data.landau.equilibrium_m,
        susceptibility: data.landau.susceptibility,
        external_field_h: data.landau.external_field_h,
        beta_j: data.landau.beta_j,
        alpha_hat: data.landau.alpha_hat,
      },
      roiBreakdown: data.roi_breakdown.map((r) => ({
        name: r.name,
        activation: r.activation,
        system: r.system as 'affective' | 'deliberative',
        vertexCount: r.vertex_count,
      })),
    };
  } catch (err) {
    console.warn('Inference server unreachable, falling back to synthetic:', err);
    return fallbackSynthetic(text);
  }
}

/**
 * Synthetic fallback when the inference server is not available.
 * Uses a simple heuristic (caps + exclamation density) to produce
 * a plausible NAA value for demonstration purposes.
 */
async function fallbackSynthetic(text: string): Promise<ScanResult> {
  const coords = await loadBrainCoords();
  const activation = generateSpatialActivation(coords, DEMO_BLOBS);
  const ts = buildSyntheticTimeSeries(activation, 24);

  // Heuristic NAA: more ALL-CAPS and exclamation marks = higher NAA
  const upperRatio =
    (text.match(/[A-Z]/g)?.length ?? 0) / Math.max(1, text.length);
  const exclam = (text.match(/!/g)?.length ?? 0) / Math.max(1, text.length / 50);
  const heuristicNAA = Math.max(
    0.3,
    Math.min(4.5, 0.6 + upperRatio * 8 + exclam),
  );

  const result = buildSyntheticScan(
    `synth-${Date.now()}`,
    text.slice(0, 120),
    heuristicNAA,
    activation,
  );

  return { ...result, timeSeries: ts, nTrs: 24 };
}
