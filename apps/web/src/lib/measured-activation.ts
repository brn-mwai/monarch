import { loadRoiVertices, type RoiVertices } from './roi-activation';

const TOTAL_VERTS = 20484;

// The renderer rescales whatever it is handed by robustNormalize(data, 99, twoSided), which
// clips to [p1, p99] and stretches that to [0, 1]. Both painters below map into a fixed band
// instead, so the band only survives if p1 and p99 land on anchors rather than on real
// vertices. That needs strictly more than 1% of all vertices at each end: 200 anchors per end
// against the 205 that 1% of 20484 requires is why every map came back restretched and amber.
const RENDER_PERCENTILE = 99;

/** Fallback paint threshold when no corpus-wide one is shipped. Matches Figure 5.3. */
const THRESHOLD_PERCENTILE = 70;
const ANCHORS_PER_END =
  Math.ceil((TOTAL_VERTS * (100 - RENDER_PERCENTILE)) / 100) + 64;

/** Masked vertices used to pin the colour scale. See buildScaledRoiActivation. */
const SCALE_ANCHORS = ANCHORS_PER_END * 2;

// The renderer treats everything below 0.5 as inactive and paints the very top of its ramp
// pure white, which is invisible against light grey cortex. Both painters map into this band
// so the same colour means the same value whichever path drew it.
const RAMP_FLOOR = 0.52;
const RAMP_CEILING = 0.92;

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

  // The corpus position is mapped into the band the ramp actually uses, stopping short of
  // white: the lowest measured value sits at the dark red end and the highest at amber. The
  // mapping stays monotonic, so a higher value is always a warmer colour.
  const position = (value: number) => {
    const t = span > 0 ? Math.min(1, Math.max(0, (value - lo) / span)) : 0.5;
    return RAMP_FLOOR + t * (RAMP_CEILING - RAMP_FLOOR);
  };

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

/** Corpus-wide vertex colour range and paint threshold, measured by export_corpus_web.py. */
export interface VectorScale {
  lo: number;
  hi: number;
  threshold?: number;
}

/**
 * The real per-vertex prediction for an item, when one was kept.
 *
 * A run with --save-vectors writes the (20484,) float32 map the cascade actually produced.
 * That map has genuine structure at every vertex, so nothing here invents a gradient. Items
 * scanned before that flag existed have no map and fall back to the flat two-region fill.
 *
 * The scale is the corpus-wide one, for the reason given on buildScaledRoiActivation: a map
 * normalised against its own percentiles renders every item equally saturated, and the
 * measured spans across this corpus differ by nearly fourfold, so per-item scaling would
 * show a weakly activated item and a strongly activated one as the same picture. Passing no
 * scale falls back to the per-item range, which is honest only for a single brain shown
 * alone.
 *
 * The medial wall is never painted. It carries no signal, and the fallback path masks it, so
 * leaving it lit here would mark the per-vertex maps out with colour the data does not have.
 */
export async function loadItemVector(
  id: string,
  scale?: VectorScale | null,
  medialMask?: Uint8Array | null,
): Promise<Float32Array | null> {
  try {
    const res = await fetch(`/data/vectors/${id}.f32`);
    if (!res.ok) return null;
    const data = new Float32Array(await res.arrayBuffer());
    if (data.length !== TOTAL_VERTS) return null;
    return displayRange(data, scale ?? null, medialMask ?? null);
  } catch {
    return null;
  }
}

/**
 * Place a real per-vertex map in the band the renderer's ramp uses.
 *
 * The renderer paints nothing below 0.5 and reaches white at 1.0. Predicted activation is
 * roughly centred on zero, so handed over raw about half the cortex falls under the floor
 * and renders bare, leaving disconnected patches instead of a graded field. Rescaling by
 * the map's own 1st and 99th percentiles into [0.5, 1] uses the whole ramp: the lowest
 * predicted values sit at dark red and the highest at white, which is how TRIBE's own
 * demo reads.
 *
 * This is a display range, not a change to the data. The mapping is monotonic, so a
 * higher predicted value is always a warmer colour, and no vertex value is invented.
 */
function displayRange(
  data: Float32Array,
  scale: VectorScale | null,
  medialMask: Uint8Array | null,
): Float32Array {
  const cortex = medialMask
    ? data.filter((_, i) => medialMask[i] !== 0)
    : Float32Array.from(data);
  const sorted = Float32Array.from(cortex).sort();
  const at = (q: number) => sorted[Math.floor((q / 100) * (sorted.length - 1))];

  const usable = scale && scale.hi > scale.lo;
  const hi = usable ? scale.hi : at(99);
  // Figure 5.3's rule: paint the top of the map and leave the rest bare so the anatomy stays
  // readable. Without it every vertex carries colour and the surface reads as one lit blob,
  // which is what happens when the whole range is mapped above the renderer's COLOR_VMIN.
  const floor =
    usable && scale.threshold !== undefined ? scale.threshold : at(THRESHOLD_PERCENTILE);

  const span = hi - floor;
  const out = new Float32Array(data.length);

  for (let i = 0; i < data.length; i++) {
    if (medialMask && medialMask[i] === 0) continue;
    if (data[i] < floor) continue;
    const t = span > 0 ? Math.min(1, (data[i] - floor) / span) : 1;
    out[i] = RAMP_FLOOR + t * (RAMP_CEILING - RAMP_FLOOR);
  }

  // Same trick as buildScaledRoiActivation: pin the renderer's own percentile normalisation
  // with anchors on masked vertices, which are forced to grey before anything is drawn.
  // Without them the renderer restretches each map and the shared scale is undone.
  if (medialMask) {
    let placed = 0;
    for (let i = 0; i < TOTAL_VERTS && placed < SCALE_ANCHORS; i++) {
      if (medialMask[i] === 0) {
        out[i] = placed % 2 === 0 ? 1 : 0;
        placed++;
      }
    }
  }

  return out;
}
