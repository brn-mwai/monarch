// ============================================================
// normalize.ts - frontend port of TRIBE v2's robust_normalize
// ============================================================
//
// Mirrors `tribev2/plotting/utils.py` so the brain renders the same
// way the official notebook does:
//
//   sorted = sort(abs(data))
//   vmax_abs = sorted[int(N * percentile / 100)]    (99th-pctile by default)
//   vmin_abs = vmin_fraction * vmax_abs              (notebook uses 0.5)
//   normalized = clip((data - vmin_abs) / (vmax_abs - vmin_abs), 0, 1)
//
// The vmin_fraction trick is the key thing the old per-min/per-max
// normalizer was missing: it kills the bottom half of the dynamic
// range so background noise vertices register as zero (transparent
// against the sulcal grey) instead of leaking faint colour everywhere.
// ============================================================

/**
 * Robust per-vector normalisation. Returns a NEW Float32Array of the
 * same length, values in [0, 1].
 *
 * @param data            (V,) raw activation array (any units, may include negatives)
 * @param percentile      Which percentile of |data| defines vmax. Default 99.
 * @param vminFraction    Fraction of vmax_abs treated as the floor. Default 0.5.
 *                        Set to 0 to keep all positive values; set to 0.5 to
 *                        kill the bottom half of the dynamic range (matches
 *                        the TRIBE v2 notebook's default plot call).
 */
export function robustNormalize(
  data: Float32Array | number[],
  percentile: number = 99,
  vminFraction: number = 0.5,
): Float32Array {
  const n = data.length;
  const out = new Float32Array(n);
  if (n === 0) return out;

  // Build sorted absolute values to find the percentile cap.
  const abs = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    const v = data[i];
    abs[i] = v < 0 ? -v : v;
  }
  abs.sort();

  const pIdx = Math.min(n - 1, Math.max(0, Math.floor((n * percentile) / 100)));
  const vmaxAbs = abs[pIdx];
  if (vmaxAbs <= 0) return out;

  const vminAbs = vminFraction * vmaxAbs;
  const range = vmaxAbs - vminAbs;
  if (range <= 0) return out;

  for (let i = 0; i < n; i++) {
    const t = (data[i] - vminAbs) / range;
    out[i] = t < 0 ? 0 : t > 1 ? 1 : t;
  }
  return out;
}
