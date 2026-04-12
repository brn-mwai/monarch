// ============================================================
// SulcalShading.ts -- per-face grey palette from sulcal depth
// ============================================================
//
// The brain renders as non-indexed geometry where each face has its own
// 3 unique vertices, and we set the same color on all 3 vertices of a
// face. This produces uniform per-face coloring -- the polygonal look
// from the reference renders.
//
// We expose a per-face color builder that takes the original per-vertex
// sulcal-depth array plus the original face index buffer, computes the
// average sulcal depth for each face, and writes it as the same RGB
// triple to all 3 vertices of that face in the output buffer (length
// F*9 floats).
//
// Two palettes:
//   PIAL     -- moderate grey range used on the folded pial surface.
//   INFLATED -- muted, lighter grey for the smooth inflated surface.
// ============================================================

import * as THREE from 'three';

const DARK_PIAL = 0.05;
const LIGHT_PIAL = 0.58;
const DARK_INFL = 0.62;
const LIGHT_INFL = 0.85;
const PIAL_GAMMA = 1.3;

function buildFaceGreys(
  sulcalDepth: ArrayLike<number>,
  faces: ArrayLike<number>,
  dark: number,
  light: number,
  gamma: number,
): Float32Array {
  // Find min/max for normalization across the whole hemisphere.
  let lo = Infinity;
  let hi = -Infinity;
  for (let i = 0; i < sulcalDepth.length; i++) {
    const v = sulcalDepth[i];
    if (v < lo) lo = v;
    if (v > hi) hi = v;
  }
  const span = hi - lo || 1;

  const F = faces.length / 3;
  const out = new Float32Array(F * 9); // 3 verts * 3 RGB per face

  for (let f = 0; f < F; f++) {
    const i0 = faces[f * 3 + 0];
    const i1 = faces[f * 3 + 1];
    const i2 = faces[f * 3 + 2];

    // Average sulcal depth across the face's 3 original vertices, then
    // normalize, gamma, and map into the grey range.
    const sAvg = (sulcalDepth[i0] + sulcalDepth[i1] + sulcalDepth[i2]) / 3;
    let t = (sAvg - lo) / span;
    if (gamma !== 1.0) t = Math.pow(t, gamma);
    const grey = dark + (light - dark) * (1 - t);

    // Per-face deterministic jitter (hash from face index) so adjacent
    // faces have visibly different shades, creating a multi-toned
    // patchwork look across the surface. Reproducible across renders.
    const hash = ((f * 7919 + f * f * 104729) % 1000) / 1000;
    const jitter = (hash - 0.5) * 0.12;
    const greyJ = Math.max(0, Math.min(1, grey + jitter));

    // Same color on all 3 vertices of this face -> uniform face color.
    const off = f * 9;
    out[off + 0] = greyJ;
    out[off + 1] = greyJ;
    out[off + 2] = greyJ;
    out[off + 3] = greyJ;
    out[off + 4] = greyJ;
    out[off + 5] = greyJ;
    out[off + 6] = greyJ;
    out[off + 7] = greyJ;
    out[off + 8] = greyJ;
  }
  return out;
}

/** Pial-surface per-face grey colors (high-contrast palette). */
export function buildPialFaceColors(
  sulcalDepth: ArrayLike<number>,
  faces: ArrayLike<number>,
): Float32Array {
  return buildFaceGreys(sulcalDepth, faces, DARK_PIAL, LIGHT_PIAL, PIAL_GAMMA);
}

/** Inflated-surface per-face grey colors (muted lighter palette). */
export function buildInflatedFaceColors(
  sulcalDepth: ArrayLike<number>,
  faces: ArrayLike<number>,
): Float32Array {
  return buildFaceGreys(sulcalDepth, faces, DARK_INFL, LIGHT_INFL, 1.0);
}

// Legacy per-vertex helpers, kept so anything still importing them keeps
// compiling. The brain renderer now uses the buildFaceColors functions
// above, but the head-shell-style "apply to a generic geometry" form may
// still be useful for other surfaces.

export function sulcalToVertexColors(
  sulcalDepth: number[] | Float32Array,
): Float32Array {
  const n = sulcalDepth.length;
  let lo = Infinity;
  let hi = -Infinity;
  for (let i = 0; i < n; i++) {
    const v = sulcalDepth[i];
    if (v < lo) lo = v;
    if (v > hi) hi = v;
  }
  const span = hi - lo || 1;
  const out = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    let t = (sulcalDepth[i] - lo) / span;
    t = Math.pow(t, PIAL_GAMMA);
    const grey = DARK_PIAL + (LIGHT_PIAL - DARK_PIAL) * (1 - t);
    out[i * 3 + 0] = grey;
    out[i * 3 + 1] = grey;
    out[i * 3 + 2] = grey;
  }
  return out;
}

export function applySulcalShading(
  geometry: THREE.BufferGeometry,
  sulcalDepth: number[] | Float32Array,
): Float32Array {
  const colors = sulcalToVertexColors(sulcalDepth);
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  return colors;
}
