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
import { buildDenseActivation } from './roi-activation';

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
  true_activation_url?: string;
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
    return buildResultFromResponse(data, text.slice(0, 120));
  } catch (err) {
    console.warn('Inference server unreachable, falling back to synthetic:', err);
    return fallbackSynthetic(text);
  }
}

/**
 * Scan an uploaded media file (video or audio) via the live inference
 * server. Falls back to synthetic data keyed on the filename when the
 * server is offline or unconfigured, so the Compare flow stays usable
 * for demos without a model deployment.
 */
export async function scanMedia(
  file: File,
  modality: 'audio' | 'video',
): Promise<ScanResult> {
  if (!INFERENCE_URL) {
    return fallbackSynthetic(file.name, modality);
  }

  try {
    const form = new FormData();
    form.append('file', file);
    form.append('modality', modality);

    const res = await fetch(`${INFERENCE_URL}/api/scan/upload`, {
      method: 'POST',
      body: form,
    });

    if (!res.ok) {
      console.warn(`Inference server returned ${res.status}, falling back to synthetic`);
      return fallbackSynthetic(file.name, modality);
    }

    const data: RawScanResponse = await res.json();
    return buildResultFromResponse(data, file.name);
  } catch (err) {
    console.warn('Inference server unreachable, falling back to synthetic:', err);
    return fallbackSynthetic(file.name, modality);
  }
}

/**
 * Assemble a ScanResult from a server response: fetches the predicted
 * activation blob, the optional playback time series, and the optional
 * recorded ground-truth reference. Shared by text and media scans.
 */
async function buildResultFromResponse(
  data: RawScanResponse,
  inputContent: string,
): Promise<ScanResult> {
  const actRes = await fetch(`${INFERENCE_URL}${data.activation_url}`);
  const activationVector = new Float32Array(await actRes.arrayBuffer());

  let timeSeries: Float32Array | undefined;
  if (data.timeseries_url) {
    const tsRes = await fetch(`${INFERENCE_URL}${data.timeseries_url}`);
    timeSeries = new Float32Array(await tsRes.arrayBuffer());
  }

  let trueActivation: Float32Array | null = null;
  if (data.true_activation_url) {
    const trueRes = await fetch(`${INFERENCE_URL}${data.true_activation_url}`);
    trueActivation = new Float32Array(await trueRes.arrayBuffer());
  }

  return {
    scanId: data.scan_id,
    inputContent,
    modality: data.modality,
    nTrs: data.n_trs,
    activationVector,
    trueActivation,
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
}

/**
 * Synthetic fallback when the inference server is not available.
 * Uses a simple heuristic (caps + exclamation density) to produce
 * a plausible NAA value for demonstration purposes.
 */
async function fallbackSynthetic(
  content: string,
  modality: 'text' | 'audio' | 'video' = 'text',
): Promise<ScanResult> {
  // Heuristic NAA: more ALL-CAPS and exclamation marks = higher NAA. For
  // uploaded media the only client-side signal is the filename, so the
  // heuristic runs over that until the real model is connected.
  const upperRatio =
    (content.match(/[A-Z]/g)?.length ?? 0) / Math.max(1, content.length);
  const exclam =
    (content.match(/!/g)?.length ?? 0) / Math.max(1, content.length / 50);
  const heuristicNAA = Math.max(
    0.3,
    Math.min(4.5, 0.6 + upperRatio * 8 + exclam),
  );

  const activation = await buildDenseActivation(heuristicNAA);
  const ts = buildSyntheticTimeSeries(activation, 24);

  const result = buildSyntheticScan(
    `synth-${Date.now()}`,
    content.slice(0, 120),
    heuristicNAA,
    activation,
  );

  return { ...result, modality, timeSeries: ts, nTrs: 24 };
}
