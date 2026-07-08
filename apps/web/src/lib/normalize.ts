// ============================================================
// normalize.ts - exact port of TRIBE v2's robust_normalize
// ============================================================
//
// Source: tribev2/plotting/utils.py:19-35 (robust_normalize)
//
// The function clips to [p(100-percentile), p(percentile)] when
// two_sided=true (default), or [min, p(percentile)] when false.
// Then rescales to [0, 1]. This is what the TRIBE v2 notebook calls
// with norm_percentile=99.
//
// NOTE: The previous implementation used abs(data) + vminFraction.
// That was WRONG. TRIBE v2 does NOT use absolute values or a vmin
// fraction. It uses a straightforward two-sided percentile clip.
// ============================================================

/**
 * Robust percentile-based normalisation matching TRIBE v2's
 * `plotting/utils.py:robust_normalize`.
 *
 * @param data        (V,) activation array in arbitrary units
 * @param percentile  Upper percentile for clipping. Default 99.
 * @param twoSided    When true, lo = p(100-percentile). When false,
 *                    lo = min(data). Default true.
 * @param clip        Clamp output to [0, 1]. Default true.
 */
export function robustNormalize(
  data: Float32Array | number[],
  percentile: number = 99,
  twoSided: boolean = true,
  clip: boolean = true,
): Float32Array {
  const n = data.length;
  const out = new Float32Array(n);
  if (n === 0) return out;

  // Sort a copy to compute percentiles. Non-finite values (NaN/inf) sort to
  // the end; count the finite prefix so the percentiles ignore them and a
  // corrupt vertex never sets the colour scale or poisons the geometry.
  const sorted = new Float32Array(n);
  for (let i = 0; i < n; i++) sorted[i] = data[i];
  sorted.sort();

  let nFinite = n;
  while (nFinite > 0 && !Number.isFinite(sorted[nFinite - 1])) nFinite--;
  if (nFinite === 0) return out;

  const pct = (q: number) =>
    sorted[Math.min(nFinite - 1, Math.max(0, Math.floor((q / 100) * (nFinite - 1))))];

  const hi = pct(percentile);
  const lo = twoSided ? pct(100 - percentile) : sorted[0];
  const range = hi - lo;

  if (range <= 0) return out;

  for (let i = 0; i < n; i++) {
    const x = data[i];
    if (!Number.isFinite(x)) {
      out[i] = 0;
      continue;
    }
    let t = (x - lo) / range;
    if (clip) {
      if (t < 0) t = 0;
      if (t > 1) t = 1;
    }
    out[i] = t;
  }
  return out;
}
