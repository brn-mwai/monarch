// ============================================================
// inference-client.ts - frontend client for the inference server
// ============================================================
//
// Calls the FastAPI inference server when NEXT_PUBLIC_INFERENCE_URL
// is set, otherwise falls back to synthetic data so the platform
// is always usable during development and demos.
// ============================================================

import type { ScanResult } from './scan-store';
import {
  demographicAction,
  demographicLabel,
  demographicLens,
  demographicTakeaway,
  type DemographicId,
} from './demographics';
import { buildSyntheticScan, buildSyntheticTimeSeries } from './mock-data';
import { buildDenseActivation } from './roi-activation';

const INFERENCE_URL = process.env.NEXT_PUBLIC_INFERENCE_URL ?? '';

/** True when a real inference server is configured. */
export const hasInferenceServer = !!INFERENCE_URL;

/**
 * Plain-language audit narrative for a scan. ``source`` distinguishes a real
 * Gemma-via-Fireworks generation from the deterministic template fallback so
 * the UI can attribute it honestly.
 */
export interface AuditReport {
  summary: string;
  source: 'gemma' | 'fallback';
  model: string;
}

/**
 * Fetch the plain-language audit report for a completed scan. Calls the
 * backend Gemma endpoint (POST /api/report) when an inference server is
 * configured; otherwise, or on any failure, returns a deterministic
 * client-side narrative built from the scan's own numbers so the report
 * page always has something honest to show.
 */
export async function fetchReport(
  result: ScanResult,
  demographic: DemographicId = 'general',
): Promise<AuditReport> {
  if (INFERENCE_URL) {
    try {
      // Data-in endpoint: send the numbers the UI already holds, so Gemma
      // writes the report for any scan -- live or synthetic -- without a
      // server-side cached activation.
      const res = await fetch(`${INFERENCE_URL}/api/report/audit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          naa: result.naa,
          landau: result.landau,
          roi_breakdown: result.roiBreakdown.map((r) => ({
            name: r.name,
            activation: r.activation,
            system: r.system,
            vertex_count: r.vertexCount,
          })),
          content_excerpt: result.inputContent.slice(0, 400),
          demographic,
          modality: result.modality,
        }),
      });
      if (res.ok) {
        return (await res.json()) as AuditReport;
      }
      console.warn(`Report endpoint returned ${res.status}, using local template`);
    } catch (err) {
      console.warn('Report endpoint unreachable, using local template:', err);
    }
  }
  return {
    summary: buildTemplateReport(result, demographic),
    source: 'fallback',
    model: 'template',
  };
}

/**
 * Render and download the full styled PDF (logo, charts, physics, audit)
 * from the numbers already on screen. Posts to the data-in endpoint so it
 * works for any active scan -- live or synthetic demo -- and the PDF matches
 * the report exactly. Returns false when no inference server is configured
 * or the request fails, so the caller can fall back to the browser print
 * dialog.
 */
export async function downloadReportPdf(
  result: ScanResult,
  report: AuditReport | null,
  demographic = 'general',
): Promise<boolean> {
  if (!INFERENCE_URL) return false;

  try {
    const res = await fetch(`${INFERENCE_URL}/api/report/pdf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scan_id: result.scanId,
        naa: result.naa,
        landau: result.landau,
        roi_breakdown: result.roiBreakdown.map((r) => ({
          name: r.name,
          activation: r.activation,
          system: r.system,
          vertex_count: r.vertexCount,
        })),
        audit: report,
        content_excerpt: result.inputContent.slice(0, 400),
        demographic,
        modality: result.modality,
      }),
    });

    if (!res.ok) {
      console.warn(`PDF endpoint returned ${res.status}, falling back to print`);
      return false;
    }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `monarch-scan-${result.scanId.slice(0, 12)}.pdf`;
    anchor.click();
    URL.revokeObjectURL(url);
    return true;
  } catch (err) {
    console.warn('PDF endpoint unreachable, falling back to print:', err);
    return false;
  }
}

/**
 * Deterministic narrative from the scan numbers. Mirrors the backend
 * template (Summary / Key findings / Caveats) so an offline demo degrades in
 * wording, not in correctness, and keeps the same honesty guarantees.
 */
function buildTemplateReport(result: ScanResult, demographic: DemographicId): string {
  const { naa, classification } = result.naa;
  const lean =
    naa > 1
      ? 'emotional systems more than reasoning systems'
      : 'reasoning systems more than emotional systems';
  const audience = demographicLabel(demographic);
  const lens = demographicLens(demographic);
  const summary =
    `Read for ${audience} -- ${lens}\n` +
    `This ${result.modality} item is predicted to engage ${lean} ` +
    `(NAA = ${naa.toFixed(2)}, class ${classification}). ` +
    `${demographicTakeaway(demographic, result.naa)}`;

  const topBySystem = (system: 'affective' | 'deliberative') =>
    result.roiBreakdown
      .filter((r) => r.system === system)
      .sort((a, b) => b.activation - a.activation)
      .slice(0, 3)
      .map((r) => r.name)
      .join(', ') || 'none';

  const findings = [
    `- Predicted emotional-region activation: ${result.naa.a_aff.toFixed(3)}`,
    `- Predicted reasoning-region activation: ${result.naa.a_del.toFixed(3)}`,
    `- Most-engaged emotional regions: ${topBySystem('affective')}`,
    `- Most-engaged reasoning regions: ${topBySystem('deliberative')}`,
    `- Recommended for ${audience.toLowerCase()}: ${demographicAction(demographic, result.naa)}`,
  ].join('\n');

  const caveats = [
    '- This is a prediction for an average brain about the content, not a measurement of any real person.',
    '- The collective-opinion figures use an uncalibrated constant and are illustrative only, not validated predictions.',
  ].join('\n');

  return `Summary\n${summary}\n\nKey findings\n${findings}\n\nCaveats\n${caveats}`;
}

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
    const submit = await fetch(`${INFERENCE_URL}/api/scan/jobs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, modality: 'text' }),
    });

    if (!submit.ok) {
      console.warn(`Inference server returned ${submit.status}, falling back to synthetic`);
      return fallbackSynthetic(text);
    }

    const { job_id: jobId } = (await submit.json()) as { job_id: string };
    const data = await pollScanJob(jobId);
    return buildResultFromResponse(data, text.slice(0, 120));
  } catch (err) {
    console.warn('Inference server unreachable, falling back to synthetic:', err);
    return fallbackSynthetic(text);
  }
}

const JOB_POLL_INTERVAL_MS = 2_500;
const JOB_TIMEOUT_MS = 15 * 60_000;

/**
 * Poll a queued scan until it finishes.
 *
 * A cold scan runs the whole TRIBE cascade and takes minutes, which outlives
 * the request timeout of any proxy in front of the API, so the result is
 * collected over short polls instead of one long-held connection.
 */
async function pollScanJob(jobId: string): Promise<RawScanResponse> {
  const deadline = Date.now() + JOB_TIMEOUT_MS;

  while (Date.now() < deadline) {
    await new Promise((resolve) => setTimeout(resolve, JOB_POLL_INTERVAL_MS));

    const res = await fetch(`${INFERENCE_URL}/api/scan/jobs/${jobId}`);
    if (!res.ok) {
      throw new Error(`Scan job ${jobId} lookup failed: ${res.status}`);
    }

    const body = (await res.json()) as {
      status: 'pending' | 'running' | 'done' | 'error';
      result?: RawScanResponse;
      error?: string;
    };

    if (body.status === 'done' && body.result) {
      return body.result;
    }
    if (body.status === 'error') {
      throw new Error(body.error ?? 'Scan failed on the inference server');
    }
  }

  throw new Error(`Scan job ${jobId} did not finish within ${JOB_TIMEOUT_MS / 60_000} minutes`);
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
