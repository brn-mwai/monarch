// ============================================================
// Colormap.ts -- "hot/fire" colormap used in the TRIBE v2 demo
// ============================================================
//
// Black -> dark red -> red -> orange -> yellow -> white.
// Exposes:
//   - LOOKUP:       256-entry RGB table (0..1 floats)
//   - valueToColor: scalar -> [r,g,b] in 0..1
//   - buildColormapTexture: 256x1 THREE.DataTexture for shader use
//   - normalizeActivation: robust 99th-percentile rescale of a Float32Array
//   - COLORMAP_CSS_GRADIENT: CSS string for the ActivityLegend bar
// ============================================================

import * as THREE from 'three';

import type { ColormapStop } from '../types';

// Hot/fire LUT engineered for the brain's lighting + emissive pipeline.
// Vertex colors are amplified by ~3.6x (key light 2.8x + emissive 0.8x)
// before hitting the framebuffer, so the raw LUT values must be low to
// produce distinct visible colors after amplification. Going too bright
// here causes everything to clamp to pure white/yellow.
const STOPS: ColormapStop[] = [
  { position: 0.0,  color: [0, 0, 0] },
  { position: 0.10, color: [15, 0, 0] },     // very dark red (cusp of alpha)
  { position: 0.18, color: [35, 0, 0] },     // dark red (visible edge)
  { position: 0.28, color: [55, 0, 0] },     // mid red
  { position: 0.40, color: [72, 5, 0] },     // bright red
  { position: 0.50, color: [82, 18, 0] },    // red-orange
  { position: 0.60, color: [88, 32, 0] },    // bright red-orange
  { position: 0.70, color: [92, 48, 0] },    // orange
  { position: 0.78, color: [95, 62, 0] },    // bright orange
  { position: 0.86, color: [95, 78, 5] },    // orange-yellow
  { position: 0.92, color: [92, 92, 18] },   // yellow
  { position: 0.96, color: [98, 98, 55] },   // bright yellow
  { position: 1.0,  color: [130, 130, 130] }, // peak (clamps to white after lighting)
];

/** 256 x 3 lookup table, each entry an RGB triple in 0..1 floats. */
export const LOOKUP: Float32Array = (() => {
  const lut = new Float32Array(256 * 3);
  for (let i = 0; i < 256; i++) {
    const t = i / 255;
    // Find the surrounding stops.
    let lo = STOPS[0];
    let hi = STOPS[STOPS.length - 1];
    for (let s = 0; s < STOPS.length - 1; s++) {
      if (t >= STOPS[s].position && t <= STOPS[s + 1].position) {
        lo = STOPS[s];
        hi = STOPS[s + 1];
        break;
      }
    }
    const span = hi.position - lo.position;
    const k = span === 0 ? 0 : (t - lo.position) / span;
    const r = (lo.color[0] + (hi.color[0] - lo.color[0]) * k) / 255;
    const g = (lo.color[1] + (hi.color[1] - lo.color[1]) * k) / 255;
    const b = (lo.color[2] + (hi.color[2] - lo.color[2]) * k) / 255;
    lut[i * 3 + 0] = r;
    lut[i * 3 + 1] = g;
    lut[i * 3 + 2] = b;
  }
  return lut;
})();

/**
 * Map a scalar value to an RGB triple in 0..1 using the hot/fire colormap.
 * Values outside [vmin, vmax] are clamped.
 */
export function valueToColor(
  value: number,
  vmin: number,
  vmax: number,
): [number, number, number] {
  const span = vmax - vmin;
  if (span <= 0 || !Number.isFinite(span)) {
    return [LOOKUP[0], LOOKUP[1], LOOKUP[2]];
  }
  let t = (value - vmin) / span;
  if (t < 0) t = 0;
  else if (t > 1) t = 1;
  const idx = Math.min(255, Math.max(0, Math.round(t * 255))) * 3;
  return [LOOKUP[idx], LOOKUP[idx + 1], LOOKUP[idx + 2]];
}

/**
 * Build a 256x1 RGB DataTexture that shaders can sample with a u coordinate
 * equal to the normalized value. Not currently consumed by the vertex-color
 * path, but kept for future shader-injection work.
 */
export function buildColormapTexture(): THREE.DataTexture {
  // Three.js r162+ removed RGBFormat, so we pack into RGBA.
  const data = new Uint8Array(256 * 4);
  for (let i = 0; i < 256; i++) {
    data[i * 4 + 0] = Math.round(LOOKUP[i * 3 + 0] * 255);
    data[i * 4 + 1] = Math.round(LOOKUP[i * 3 + 1] * 255);
    data[i * 4 + 2] = Math.round(LOOKUP[i * 3 + 2] * 255);
    data[i * 4 + 3] = 255;
  }
  const tex = new THREE.DataTexture(data, 256, 1, THREE.RGBAFormat);
  tex.needsUpdate = true;
  tex.minFilter = THREE.LinearFilter;
  tex.magFilter = THREE.LinearFilter;
  tex.wrapS = THREE.ClampToEdgeWrapping;
  tex.wrapT = THREE.ClampToEdgeWrapping;
  return tex;
}

/**
 * Robust percentile normalization: rescales data to [0, 1] using
 * min -> 0 and the `percentile`-th value -> 1. Outliers above the
 * percentile are clipped to 1 so the colormap is not washed out.
 */
export function normalizeActivation(
  data: Float32Array,
  percentile = 99,
): Float32Array {
  if (data.length === 0) return new Float32Array();

  // Sort a copy to find vmin and the percentile threshold.
  const sorted = Float32Array.from(data);
  sorted.sort();
  const vmin = sorted[0];
  const idx = Math.min(
    sorted.length - 1,
    Math.max(0, Math.floor((percentile / 100) * (sorted.length - 1))),
  );
  const vmax = sorted[idx];
  const span = vmax - vmin || 1;

  const out = new Float32Array(data.length);
  for (let i = 0; i < data.length; i++) {
    let t = (data[i] - vmin) / span;
    if (t < 0) t = 0;
    else if (t > 1) t = 1;
    out[i] = t;
  }
  return out;
}

// CSS gradient for the legend bar. Uses the *visible* (post-lighting)
// colors, not the raw LUT values, so the legend reads what the brain
// actually displays.
export const COLORMAP_CSS_GRADIENT =
  'linear-gradient(to right, #000000 0%, #500000 10%, #960000 18%, #C80000 28%, #FF0F00 40%, #FF3200 50%, #FF6400 60%, #FF9600 70%, #FFC800 78%, #FFE60F 86%, #FFFF32 92%, #FFFF96 96%, #FFFFFF 100%)';
