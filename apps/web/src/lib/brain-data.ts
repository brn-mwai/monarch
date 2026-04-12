// ============================================================
// brain-data.ts -- utilities for fetching fsaverage5 coords
// and generating spatially coherent demo activations.
// ============================================================

const HEMI_VERTS = 10242;

export interface BrainCoords {
  /** Flat (10242 * 3,) pial vertex positions for the left hemisphere. */
  left: Float32Array;
  /** Flat (10242 * 3,) pial vertex positions for the right hemisphere. */
  right: Float32Array;
}

interface BrainMeshJson {
  vertices: number[][];
  hemisphere: 'left' | 'right';
}

function flatten(verts: number[][]): Float32Array {
  const out = new Float32Array(verts.length * 3);
  for (let i = 0; i < verts.length; i++) {
    out[i * 3 + 0] = verts[i][0];
    out[i * 3 + 1] = verts[i][1];
    out[i * 3 + 2] = verts[i][2];
  }
  return out;
}

/** Fetch the pial vertex positions for both hemispheres. */
export async function loadBrainCoords(basePath = '/mesh'): Promise<BrainCoords> {
  const [left, right] = await Promise.all([
    fetch(`${basePath}/left_pial.json`).then((r) => r.json() as Promise<BrainMeshJson>),
    fetch(`${basePath}/right_pial.json`).then((r) => r.json() as Promise<BrainMeshJson>),
  ]);
  return {
    left: flatten(left.vertices),
    right: flatten(right.vertices),
  };
}

export interface SpatialBlob {
  hemi: 'left' | 'right';
  /** World-space center of the blob in fsaverage5 mm coords. */
  center: [number, number, number];
  /** Gaussian standard deviation (mm). */
  sigma: number;
  /** Peak value at the center before clamping. */
  peak: number;
}

/**
 * Generate a spatially coherent (20484,) activation vector by summing
 * supergaussian blobs (Gaussian raised to a power for a sharper edge)
 * centered at anatomical coordinates. The supergaussian falls off much
 * faster than a true Gaussian outside ~sigma, producing visibly crisper
 * hot-spot boundaries on the cortex.
 */
export function generateSpatialActivation(
  coords: BrainCoords,
  blobs: SpatialBlob[],
  baselineNoise = 0.005,
): Float32Array {
  const data = new Float32Array(2 * HEMI_VERTS);

  // Very low baseline -- sits well below the alpha cutoff after
  // 99th-percentile normalization so inactive cortex stays grey.
  for (let i = 0; i < data.length; i++) {
    data[i] = Math.random() * baselineNoise;
  }

  for (const blob of blobs) {
    const verts = blob.hemi === 'left' ? coords.left : coords.right;
    const offset = blob.hemi === 'left' ? 0 : HEMI_VERTS;
    const [cx, cy, cz] = blob.center;
    const twoSigmaSq = 2 * blob.sigma * blob.sigma;

    for (let i = 0; i < HEMI_VERTS; i++) {
      const dx = verts[i * 3 + 0] - cx;
      const dy = verts[i * 3 + 1] - cy;
      const dz = verts[i * 3 + 2] - cz;
      const d2 = dx * dx + dy * dy + dz * dz;
      // Supergaussian (power 1.6): broader flat-ish core, then a sharp
      // shoulder. Compared to a plain Gaussian this gives more vertices
      // at the peak intensity and a crisper edge instead of a smear.
      const r2 = d2 / twoSigmaSq;
      const g = Math.exp(-Math.pow(r2, 1.6));
      data[offset + i] += blob.peak * g;
    }
  }

  // Clamp to [0, 1].
  for (let i = 0; i < data.length; i++) {
    if (data[i] < 0) data[i] = 0;
    if (data[i] > 1) data[i] = 1;
  }

  return data;
}

/**
 * Default demo blob set: strong bilateral lateral-temporal activation,
 * a temporoparietal hot spot, and an orbital/inferior frontal component.
 * All peaks at 1.0 so each region is unmistakably active. Coordinates
 * are in fsaverage5 mm.
 */
export const DEMO_BLOBS: SpatialBlob[] = [
  // Lateral temporal -- main focus.
  { hemi: 'left', center: [-54, -18, -8], sigma: 20, peak: 1.0 },
  { hemi: 'right', center: [54, -18, -8], sigma: 20, peak: 1.0 },
  // Temporoparietal junction.
  { hemi: 'left', center: [-50, -58, 22], sigma: 16, peak: 0.95 },
  { hemi: 'right', center: [50, -58, 22], sigma: 16, peak: 0.95 },
  // Orbital / inferior frontal.
  { hemi: 'left', center: [-28, 32, -18], sigma: 13, peak: 0.85 },
  { hemi: 'right', center: [28, 32, -18], sigma: 13, peak: 0.85 },
];
