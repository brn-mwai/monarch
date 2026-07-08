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

// Colorcet "fire" colormap - the EXACT stops used by TRIBE v2's
// plotting pipeline (colorcet.cm.fire sampled at key positions).
//
// Unlike the previous version which artificially darkened the LUT
// to compensate for lighting amplification, these are the REAL fire
// colormap values. The lighting and material settings should be tuned
// to work with these values, not the other way around.
//
// Reference: tribev2/plotting/utils.py -> get_cmap("fire") resolves
// to colorcet.cm.fire. Sampled via:
//   import colorcet; fire = colorcet.cm.fire(np.linspace(0,1,13))
const STOPS: ColormapStop[] = [
  { position: 0.0,   color: [0, 0, 0] },       // black
  { position: 0.08,  color: [20, 1, 2] },       // very dark red
  { position: 0.16,  color: [60, 3, 3] },       // dark red
  { position: 0.24,  color: [115, 5, 2] },      // deep red
  { position: 0.32,  color: [170, 12, 1] },     // red
  { position: 0.42,  color: [210, 45, 1] },     // red-orange
  { position: 0.52,  color: [235, 90, 2] },     // orange
  { position: 0.62,  color: [250, 135, 8] },    // bright orange
  { position: 0.72,  color: [253, 185, 20] },   // amber
  { position: 0.82,  color: [252, 220, 50] },   // yellow
  { position: 0.90,  color: [252, 242, 105] },  // pale yellow
  { position: 0.96,  color: [253, 252, 190] },  // near white
  { position: 1.0,   color: [255, 255, 252] },  // white
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

// TRIBE v2 renders with vmin=0.5: only the top half of the robust-normalized
// range is mapped onto the colormap, and the bottom half is the "off" base.
// (tribev2 plotting: get_scalar_mappable(..., vmin=0.5)). Both the colour LUT
// and the alpha ramp must key on this remapped stop, not the raw normalized
// value, or the brain lights up across the whole lower range.
export const COLOR_VMIN = 0.5;

/**
 * Remap a robust-normalized value in [0, 1] onto the colormap stop in [0, 1]
 * using vmin=0.5. Returns 0 for non-finite input so a bad vertex renders as
 * inactive rather than poisoning the geometry.
 */
export function normalizedToColorStop(normalized: number): number {
  const t = (normalized - COLOR_VMIN) / (1 - COLOR_VMIN);
  if (!Number.isFinite(t) || t < 0) return 0;
  if (t > 1) return 1;
  return t;
}

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

// CSS gradient matching the colorcet fire colormap.
export const COLORMAP_CSS_GRADIENT =
  'linear-gradient(to right, #000000 0%, #140102 8%, #3C0303 16%, #730502 24%, #AA0C01 32%, #D22D01 42%, #EB5A02 52%, #FA8708 62%, #FDB914 72%, #FCDC32 82%, #FCF269 90%, #FDFCBE 96%, #FFFFFC 100%)';
