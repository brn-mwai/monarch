import { loadRoiVertices, type RoiVertices } from './roi-activation';

const TOTAL_VERTS = 20484;

/** Number of masked vertices used to pin the colour scale. See buildScaledRoiActivation. */
const SCALE_ANCHORS = 400;

let cachedMask: Uint8Array | null = null;

/** fsaverage5 medial-wall mask: 1 = cortex, 0 = medial wall, never painted. */
export async function loadMedialMask(basePath = '/mesh'): Promise<Uint8Array | null> {
  if (cachedMask) return cachedMask;
  try {
    const res = await fetch(`${basePath}/medial_mask.bin`);
    if (!res.ok) return null;
    const mask = new Uint8Array(await res.arrayBuffer());
    if (mask.length !== TOTAL_VERTS) return null;
    cachedMask = mask;
    return mask;
  } catch {
    return null;
  }
}

/**
 * Paint the two networks on a scale fixed across the whole corpus.
 *
 * The renderer normalises whatever array it is handed by its own 1st and 99th percentiles.
 * Handed raw means, that is a trap twice over. Around 91% of vertices are background, so the
 * 99th percentile lands on the larger of the two ROI values and paints it pure white, which
 * on light grey cortex reads as nothing at all. Worse, each item is then scaled against its
 * own maximum, so a strongly deliberative item and a weakly deliberative one render
 * identically and a comparison between them means nothing.
 *
 * The fix is to normalise here, against the corpus-wide range, and then stop the renderer
 * from re-normalising. A handful of medial-wall vertices are set to 0 and 1 to pin the
 * percentiles. Those vertices carry no signal and the renderer forces them to grey before
 * anything is drawn, so they change the colour scale without ever appearing. If the mask is
 * unavailable the anchors are omitted rather than painted somewhere real.
 *
 * `lo` and `hi` come from the scanned corpus, so the same colour means the same value on
 * every item.
 */
export function buildScaledRoiActivation(
  rois: RoiVertices,
  aAff: number,
  aDel: number,
  lo: number,
  hi: number,
  medialMask: Uint8Array | null,
): Float32Array {
  const data = new Float32Array(TOTAL_VERTS);
  const span = hi - lo;
  const position = (value: number) =>
    span > 0 ? Math.min(1, Math.max(0, (value - lo) / span)) : 0.5;

  for (const vertex of rois.deliberative) {
    if (vertex >= 0 && vertex < TOTAL_VERTS) data[vertex] = position(aDel);
  }
  for (const vertex of rois.affective) {
    if (vertex >= 0 && vertex < TOTAL_VERTS) data[vertex] = position(aAff);
  }

  if (medialMask) {
    let placed = 0;
    for (let i = 0; i < TOTAL_VERTS && placed < SCALE_ANCHORS; i++) {
      if (medialMask[i] === 0) {
        data[i] = placed % 2 === 0 ? 1 : 0;
        placed++;
      }
    }
  }

  return data;
}

export { loadRoiVertices };
export type { RoiVertices };
