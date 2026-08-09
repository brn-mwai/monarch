import { loadRoiVertices, type RoiVertices } from './roi-activation';

const TOTAL_VERTS = 20484;

/**
 * Build a (20484,) surface array from the two means the scan actually produced.
 *
 * Distinct from `buildRoiActivation`, which exists for illustrative brains: that one seeds
 * a random baseline and jitters every vertex by up to 18% so the networks look textured.
 * Texture invented per vertex is exactly what must not appear next to a measured number.
 *
 * Here each network is filled with its own mean and nothing else is touched. Cortex outside
 * the two networks stays at zero because the scan says nothing about it, and the renderer
 * shows unlit cortex there rather than a value.
 *
 * The result is flat within each ROI by construction. That is not a rendering shortcut: the
 * scan reduces each item's per-vertex prediction to two scalars and keeps only those, so
 * vertex-level structure does not exist to draw.
 */
export function buildMeasuredRoiActivation(
  rois: RoiVertices,
  aAff: number,
  aDel: number,
): Float32Array {
  const data = new Float32Array(TOTAL_VERTS);
  for (const vertex of rois.deliberative) {
    if (vertex >= 0 && vertex < TOTAL_VERTS) data[vertex] = aDel;
  }
  for (const vertex of rois.affective) {
    if (vertex >= 0 && vertex < TOTAL_VERTS) data[vertex] = aAff;
  }
  return data;
}

export { loadRoiVertices };
export type { RoiVertices };
