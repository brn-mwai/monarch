# 05 - Plotting System

Complete walk through of `tribev2/plotting/*`. This is the file the Monarch frontend team needs to port to Three.js shaders.

---

## 0. File map

| File | Purpose |
|---|---|
| `plotting/__init__.py` | Re-exports `BasePlotBrain`, `PlotBrainNilearn`, `PlotBrainPyvista`, `plot_subcortical`, `get_subcortical_roi_indices`, and a dozen utils. Sets `PlotBrain = PlotBrainPyvista` (default). |
| `plotting/base.py` | `BasePlotBrain` (pydantic abstract base) - mesh loading, `get_stat_map`, `get_hemis`, `plot_timesteps`, `plot_timesteps_mp4`, `plot_stimuli`. Subclasses override `plot_surf`. |
| `plotting/cortical.py` | `PlotBrainNilearn` - matplotlib 3D + nilearn.plotting. Deprecated-ish (the default is now pyvista). 12 views. |
| `plotting/cortical_pv.py` | `PlotBrainPyvista` - default. Off-screen pyvista screenshot into matplotlib axes at `dpi=3000`. |
| `plotting/subcortical.py` | Harvard-Oxford subcortical atlas via marching cubes meshes. Independent of the cortical plotter. |
| `plotting/utils.py` | `robust_normalize`, `get_cmap`, `get_scalar_mappable`, `get_thresholded_sm`, `get_alpha_cmap`, `saturate_colors`, `tight_crop`, `get_rainbow_brain`, `get_clip`, `get_audio`, `get_text`. Plus a bunch of mosaic/label helpers. |

---

## 1. Mesh loading: `BasePlotBrain.get_mesh()` (base.py:127-172)

**This is the authoritative code. The `scripts/export_brain_mesh.py` mirror is a superset (it skips the tribev2 import chain).**

```python
def get_mesh(self) -> dict:
    fs_out = cached_fetch_surf_fsaverage(self.mesh)  # nilearn download, lru_cached

    out = {}
    for hemi in ("left", "right"):
        infl_out_xyz, _ = nib.load(getattr(fs_out, f"infl_{hemi}")).darrays
        pial_xyz, faces = nib.load(getattr(fs_out, f"pial_{hemi}")).darrays

        alpha = 0.5
        jr_xyz = infl_out_xyz.data * alpha + (1 - alpha) * pial_xyz.data

        if self.inflate == "half":
            coords = jr_xyz                  # DEFAULT
        elif self.inflate is True:
            coords = infl_out_xyz.data
        elif self.inflate is False:
            coords = pial_xyz.data

        bg_key = "curv" if self.bg_map == "curvature" else "sulc"
        bg_map = nib.load(getattr(fs_out, f"{bg_key}_{hemi}")).darrays[0].data

        if self.bg_map == "thresholded":
            bg_map = 1.0 * (bg_map > -0.10)
            bg_map[-1] = -5
            bg_map[-2] = 2.0

        # Hemisphere offset so the two sides don't overlap at the midline
        if hemi == "left":
            coords[:, 0] = coords[:, 0] - coords[:, 0].max() - self.hemisphere_gap
        else:
            coords[:, 0] = coords[:, 0] - coords[:, 0].min() + self.hemisphere_gap

        out[hemi] = dict(coords=coords, faces=faces.data, bg_map=bg_map)

    out["both"] = dict(
        coords=np.r_[out["left"]["coords"], out["right"]["coords"]],
        faces=np.r_[
            out["left"]["faces"],
            out["right"]["faces"] + out["left"]["faces"].max() + 1,
        ],
        bg_map=np.r_[out["left"]["bg_map"], out["right"]["bg_map"]],
    )
    return out
```

**Shape details (for fsaverage5)**:
- `out["left"]["coords"]`: `(10242, 3)` float32
- `out["left"]["faces"]`: `(20480, 3)` int (verified in `monarch-meshes/metadata.json`)
- `out["left"]["bg_map"]`: `(10242,)` float (sulcal depth)
- `out["both"]["coords"]`: `(20484, 3)` concatenated L then R
- `out["both"]["faces"]`: `(40960, 3)` with right-hemi face indices offset by `left["faces"].max()+1`
- `out["both"]["bg_map"]`: `(20484,)`

**Notes for Monarch**:
1. **Inflation modes**: `True`=fully inflated, `False`=pial, `"half"`=50/50 blend. The default is `"half"`. The `monarch-meshes/*_inflated.json` files were exported with `inflate=True` (see `scripts/export_brain_mesh.py:83-85`), NOT the "half" mode. If the Monarch frontend wants the notebook-identical look, it should compute `0.5 * pial + 0.5 * inflated` in JS at mesh load time (trivial vertex-wise lerp).
2. **Hemisphere offset**: Left hemi has `coords[:,0] -= coords[:,0].max()`, so its max X is 0. Right hemi has `coords[:,0] -= coords[:,0].min()`, so its min X is 0. They meet at the midline. `hemisphere_gap=0` by default, so they touch. Non-zero values pull them apart.
3. **`bg_map` modes**:
   - `"sulcal"` (default): raw sulcal depth values (range roughly `-1.49..1.84` on fsaverage5).
   - `"curvature"`: curv file instead of sulc (nilearn has both).
   - `"thresholded"`: binary 0/1 with two sentinel values at the last two vertices (weird; probably for debugging).
4. **Caching**: `cached_fetch_surf_fsaverage = lru_cache(datasets.fetch_surf_fsaverage)` so subsequent calls are free.

## 2. `get_stat_map(data)` - splitting a (20484,) vector by hemisphere (base.py:178-215)

```python
def get_stat_map(self, data: np.ndarray) -> dict:
    # Auto-detect which fsaverage resolution the input is in
    in_mesh = None
    for name, size in FSAVERAGE_SIZES.items():
        if data.shape[0] // 2 == size:
            in_mesh = name
            break
    if in_mesh is None:
        raise ValueError(f"Incoherent number of vertices: {data.shape[0]}")

    left = data[: len(data) // 2]     # first 10242 vertices
    right = data[len(data) // 2 :]    # last 10242 vertices

    # If the input mesh differs from self.mesh, upsample via 5-neighbour KD-tree
    if in_mesh != self.mesh:
        fs_in = cached_fetch_surf_fsaverage(in_mesh)
        fs_out = cached_fetch_surf_fsaverage(self.mesh)
        resampled = {}
        for hemi, values in (("left", left), ("right", right)):
            infl_in_xyz, _ = nib.load(...)
            infl_out_xyz, _ = nib.load(...)
            tree = cKDTree(infl_in_xyz.data)
            distances, indices = tree.query(infl_out_xyz.data, k=5)
            if "int" in data.dtype.name:
                # majority vote
                resampled[hemi] = np.apply_along_axis(
                    lambda x: np.bincount(x).argmax(), axis=1, arr=values[indices]
                )
            else:
                # inverse-distance weighted mean
                distances = np.where(distances == 0, 1e-12, distances)
                weights = 1 / distances
                weights = weights / weights.sum(axis=1, keepdims=True)
                resampled[hemi] = np.sum(values[indices] * weights, axis=1)
        left, right = resampled["left"], resampled["right"]

    return dict(left=left, right=right, both=np.r_[left, right])
```

For Monarch (always `in_mesh == self.mesh == "fsaverage5"`) this is just a split in half:
```js
const leftActivation = activation.slice(0, 10242);
const rightActivation = activation.slice(10242, 20484);
```

## 3. `PlotBrainPyvista.plot_surf` - the colormap pipeline (cortical_pv.py:80-167)

**This is the reference implementation the Monarch JS shader must mirror.**

```python
def plot_surf(
    self,
    data,                                    # (20484,) or (10242,) depending on view
    axes,
    views="left",
    alpha_cmap=None,                         # (threshold, scale) e.g. (0, 0.2)
    vmin: float | None = None,
    vmax: float | None = None,
    symmetric_cbar: bool = False,
    threshold: float | None = None,
    cmap: str = "hot",
    norm_percentile: float | None = None,
    annotated_rois=None,
    annotated_rois_kwargs=None,
):
    # 3.1 Robust-normalise if requested (percentile-based clipping)
    if norm_percentile is not None:
        data = robust_normalize(data, percentile=norm_percentile)

    # 3.2 Normalise axes/views shapes
    if isinstance(views, str):
        views = [views]
    views, axes = self.get_axarr_and_views(axes, views)

    # 3.3 Build colormap (with optional alpha ramp)
    cmap = get_cmap(cmap, alpha_cmap=alpha_cmap)

    # 3.4 Build ScalarMappable with vmin/vmax (applied after norm)
    sm = get_scalar_mappable(
        data, cmap,
        vmin=vmin, vmax=vmax,
        threshold=threshold,
        symmetric_cbar=symmetric_cbar,
    )

    # 3.5 Split by hemisphere (and upsample if needed)
    stat_maps = self.get_stat_map(data)   # dict "left"/"right"/"both"

    for ax, view in zip(axes, views):
        selected_hemi = (
            "left"  if view in ("left",  "medial_left")  else
            "right" if view in ("right", "medial_right") else
            "both"
        )
        mesh = self._mesh[selected_hemi]
        vertices, faces = mesh["coords"], mesh["faces"]
        stat_map = stat_maps[selected_hemi]

        # 3.6 Map values through the colormap -> RGBA (N, 4)
        rgba = sm.to_rgba(stat_map)

        # 3.7 Compute the sulcal background gray
        bg_map = mesh["bg_map"]
        bg_norm = (bg_map - bg_map.min()) / (bg_map.max() - bg_map.min() + 1e-8)
        bg_rgb = 1 - np.column_stack(
            [self.bg_darkness + bg_norm * (1 - self.bg_darkness)] * 3
        )
        # With bg_darkness=0 (default): bg_rgb = 1 - bg_norm_stacked_x3
        # So deep sulci (bg_norm=1) -> bg_rgb=(0,0,0) black
        #    flat gyri (bg_norm=0) -> bg_rgb=(1,1,1) white

        # 3.8 Alpha blend the activation colour over the sulcal gray
        colors = rgba[:, 3:4] * rgba[:, :3] + (1 - rgba[:, 3:4]) * bg_rgb

        # 3.9 Build the pyvista mesh and screenshot it
        pv_faces = np.column_stack([np.full(len(faces), 3), faces])
        ax_size = ax.get_position()
        pl = pv.Plotter(
            window_size=[int(ax_size.width * self.dpi), int(ax_size.height * self.dpi)],
            off_screen=True,
        )

        surf = pv.PolyData(vertices, pv_faces)
        surf.point_data["colors"] = colors
        pl.add_mesh(
            surf,
            scalars="colors",
            rgb=True,
            smooth_shading=True,
            ambient=self.ambient,            # 0.3 by default
        )

        pl.set_background("white")
        vec, up = VIEW_DICT[view]
        pl.view_vector(vec, viewup=up)

        if annotated_rois is not None:
            self.annotate_rois(pl, annotated_rois, **(annotated_rois_kwargs or {}))

        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            img = pl.screenshot(tmp.name, return_img=True)
        img = tight_crop(img, w_pad=self.w_pad, h_pad=self.h_pad)
        pl.clear()
        ax.axis("off")
        ax.imshow(img, aspect="equal")
    return sm
```

### Colormap pipeline distilled for the JS port

1. **Start**: `(20484,)` float activation vector, arbitrary units (see `02_config_analysis.md` for what this is).
2. **Robust normalize** (optional if `norm_percentile` set; notebook uses `99`):
   - `lo = np.percentile(data, 100 - 99) = np.percentile(data, 1)`
   - `hi = np.percentile(data, 99)`
   - `out = clip((data - lo) / (hi - lo), 0, 1)`
3. **Apply colormap**: 256-stop LUT, linearly sampled from `colorcet.cm.fire`. In JS this is a `Texture2D` of size 1x256 RGBA or a 1D array you read from.
4. **Apply alpha_cmap** (if set): overwrites the LUT's alpha channel with:
   - `alpha=0` below `threshold`
   - `alpha=1` above `threshold + scale`
   - `alpha=ramp_linear(0,1)` between
5. **Apply ScalarMappable `Normalize(vmin, vmax)`**: rescales the pre-LUT lookup index. With `vmin=0.5, vmax=None (=>1.0)`, the effective LUT is clamped so values below 0.5 map to index 0 and values >= 1.0 map to index 255.
6. **Fetch sulcal background**:
   - `bg_norm = (sulc - sulc.min()) / (sulc.max() - sulc.min())`
   - `bg_rgb = (1 - bg_norm) * vec3(1,1,1)` when `bg_darkness=0` (default). I.e., deeper sulci = darker.
7. **Alpha blend** per vertex/fragment:
   - `final_rgb = alpha * lut_rgb + (1 - alpha) * bg_rgb`
   - In WebGL, this is a straightforward `mix(bg_rgb, lut_rgb, alpha)`.
8. **Apply shader lighting**: pyvista uses `smooth_shading=True, ambient=0.3`. The JS equivalent is standard Phong / directional lighting at ambient 0.3, and PyVista's default diffuse is 0.7.
9. **Final camera**: `view_vector(vec, viewup=up)` for one of the 10 named views in `VIEW_DICT`.

### `VIEW_DICT` (cortical_pv.py:27-38)

```python
VIEW_DICT = {
    "ventral":          ([0, 0, -1], [1, 0, 0]),
    "dorsal":           ([0, 0, 1],  [0, 1, 0]),
    "left":             ([-1, 0, 0], [0, 0, 1]),
    "right":            ([1, 0, 0],  [0, 0, 1]),
    "anterior":         ([0, 1, 0],  [0, 0, -1]),
    "posterior":        ([0, -1, 0], [0, 0, 1]),
    "medial_left":      ([1, 0, 0],  [0, 0, 1]),
    "medial_right":     ([-1, 0, 0], [0, 0, 1]),
    "posterior_left":   ([-1, 0, 0], [0, 0, 1]),
    "posterior_right":  ([-1, 0, 0], [0, 0, 1]),
}
```

First vector is the camera's direction of view (pointing from camera to origin), second is the view-up axis. Note `medial_left` and `right` share the same vec/up - the difference is that medial_left shows the right hemisphere from the inside (camera on right side of brain looking left). The view implicitly selects a hemisphere based on name (see `plot_surf`'s hemisphere-selection logic).

## 4. `robust_normalize` (utils.py:19-35)

```python
def robust_normalize(
    array,
    axis=None,
    percentile=99,
    clip=True,
    final_range=None,
    two_sided=True,
):
    hi = np.percentile(array, percentile, axis=axis, keepdims=True)
    if two_sided:
        lo = np.percentile(array, 100 - percentile, axis=axis, keepdims=True)
    else:
        lo = np.min(array, axis=axis, keepdims=True)
    out = (array - lo) / (hi - lo)
    if clip:
        out = np.clip(out, 0, 1)
    if final_range is not None:
        if final_range == "original":
            final_range = (lo, hi)
        out = out * (final_range[1] - final_range[0]) + final_range[0]
    return out
```

**Usage map**:
- `plot_timesteps(..., norm_percentile=P)` -> `robust_normalize(neuro, percentile=P)`. Default `P=None` (no normalization); notebook uses `P=99`.
- `plot_surf(..., norm_percentile=P)` -> same. Default `None`.
- `plot_surf_rgb(..., norm_percentile=P)` -> calls with `percentile=P, two_sided=False, axis=1` (or `axis=None`). Default `95`.
- `subcortical.plot_subcortical(..., norm_percentile=P)` -> calls with `percentile=P`.

**Key asymmetry**: `two_sided=True` means `lo = p(100-P)`, i.e. a symmetric percentile clip on both tails (if `P=99`, clip to `[p1, p99]`). `two_sided=False` means `lo = array.min()`, clip only the top tail (used by `plot_surf_rgb`).

**JS port**:
```js
function robustNormalize(arr, percentile = 99, twoSided = true, clip = true) {
  const sorted = [...arr].sort((a, b) => a - b);
  const p = (q) => sorted[Math.floor((q/100) * (sorted.length - 1))];
  const hi = p(percentile);
  const lo = twoSided ? p(100 - percentile) : sorted[0];
  const range = hi - lo;
  return arr.map(v => {
    let x = (v - lo) / range;
    return clip ? Math.min(1, Math.max(0, x)) : x;
  });
}
```

For performance on 20484 values, a TypedArray sort is fine (<1ms on modern hardware).

## 5. `get_cmap` (utils.py:139-161)

```python
def get_cmap(cmap_name, alpha_cmap=None):
    if isinstance(cmap_name, str):
        cmap = (
            getattr(matplotlib.cm, cmap_name, None)
            or getattr(sns.cm,  cmap_name, None)
            or getattr(colorcet.cm, cmap_name, None)
        )
    else:
        cmap = cmap_name
    if not cmap:
        raise ValueError(f"Invalid cmap: {cmap}")
    if alpha_cmap is not None:
        threshold, scale = alpha_cmap
        cmap = get_alpha_cmap(
            cmap,
            threshold=threshold,
            scale=scale,
            symmetric=(cmap_name in ["seismic", "bwr"]),
        )
    return cmap
```

Fallback chain: **matplotlib -> seaborn -> colorcet**. `"hot"` resolves in matplotlib. `"fire"` resolves in colorcet (`colorcet.cm.fire`). `"viridis"` / `"jet"` / etc. resolve in matplotlib. If Monarch ships its own LUT it can ignore this entirely and just use a pre-baked 256x4 RGBA array.

### Available named colormaps that show up in the code

| Name | Source | Where |
|---|---|---|
| `hot` | matplotlib | default in `plot_surf`, `plot_subcortical` |
| `fire` | colorcet | notebook; default of `plot_colorbar`; `subcortical.__main__` |
| `gray_r` | matplotlib | background in `plot_surf_rgb` |
| `seismic`, `bwr` | matplotlib | mentioned in `get_cmap` alpha symmetric branch (for diverging cmaps) |
| `Set1` (palette) | seaborn | subcortical `__main__` demo |
| `tab10` | matplotlib | `plot_surf_rgb` cmap="tab10" option |

**Recommendation for Monarch**: Bake `colorcet.cm.fire` into a 256-stop LUT at build time. It's a perceptually uniform warm gradient that's close to `hot` but with smoother lightness transitions. Sample via Python at build time:

```python
import colorcet
import numpy as np
fire = colorcet.cm.fire(np.linspace(0, 1, 256))  # (256, 4) RGBA
np.save("fire_lut.npy", fire)
```

## 6. `get_alpha_cmap` (utils.py:114-136)

```python
def get_alpha_cmap(cmap, threshold=0, scale=1, symmetric=False):
    assert 0 <= threshold <= 1
    from matplotlib.colors import ListedColormap

    n_points = 1024
    new_cmap = cmap(np.linspace(0, 1, n_points))     # (1024, 4)
    alpha = np.zeros_like(new_cmap[:, 3])

    min_idx = int(threshold * (n_points - 1))
    max_idx = int((threshold + scale) * (n_points - 1))
    ramp = np.linspace(0, 1, max_idx - min_idx)
    alpha[min_idx : min(max_idx, n_points)] = ramp[: min(max_idx, n_points) - min_idx]
    alpha[min(max_idx, n_points) :] = 1

    if symmetric:
        alpha = np.concatenate([alpha[::-2], alpha[::2]])

    new_cmap[:, 3] = alpha
    return ListedColormap(new_cmap)
```

**Notebook call**: `alpha_cmap=(0, 0.2)` -> `threshold=0, scale=0.2`.
- `min_idx = 0`
- `max_idx = int(0.2 * 1023) = 204`
- `alpha[0:204] = linspace(0, 1, 204)` -> ramp
- `alpha[204:] = 1` -> fully opaque above value 0.2

So the final effect: fully opaque for normalized values >= 0.2, fully transparent at value 0, linear ramp in between. Combined with `vmin=0.5` in `get_scalar_mappable`, the *visible* portion of the brain is where the normalized value is between 0 and 1 and specifically brighter than 0.5 in the colormap (because values below vmin all map to the colormap's index-0 colour, which has the alpha ramp).

Caveat: because `get_alpha_cmap` has `n_points=1024` while `get_thresholded_sm` uses `cmap.N` (which is 1024 for the alpha'd cmap), the ramp is consistently sampled.

## 7. `get_scalar_mappable` / `get_thresholded_sm` (utils.py:38-74)

```python
def get_scalar_mappable(data, cmap, vmin=None, vmax=None, symmetric_cbar=False, threshold=None, alpha_cmap=None):
    vmin = vmin if vmin is not None else np.nanmin(data)
    vmax = vmax if vmax is not None else np.nanmax(data)
    if symmetric_cbar:
        vmin, vmax = -vmax, vmax
    sm = get_thresholded_sm(vmin, vmax, threshold=threshold, cmap=cmap)
    return sm

def get_thresholded_sm(vmin, vmax, threshold=None, cmap=None):
    if cmap is None:
        cmap = matplotlib.cm.get_cmap("hot")
    norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
    cmaplist = [cmap(i) for i in range(cmap.N)]
    if threshold is not None:                        # grey-out abs values below threshold
        istart = int(norm(-threshold, clip=True) * (cmap.N - 1))
        istop  = int(norm( threshold, clip=True) * (cmap.N - 1))
        for i in range(istart, istop):
            cmaplist[i] = (0.5, 0.5, 0.5, 1.0)
    our_cmap = LinearSegmentedColormap.from_list("Custom cmap", cmaplist, cmap.N)
    sm = plt.cm.ScalarMappable(cmap=our_cmap, norm=norm)
    sm._A = []
    return sm
```

Key points:
- `vmin / vmax` default to `np.nanmin(data)` / `np.nanmax(data)`. Over a post-`robust_normalize` array this is ~0..1. With `vmin=0.5` hardcoded, half the range is hidden.
- `threshold` is an absolute-value grey-out band. Not used by the notebook; Monarch can ignore.
- `symmetric_cbar` is the diverging-cmap mirror: `vmin=-vmax`. Not used by the notebook.

## 8. `annotate_rois` (cortical_pv.py:54-78)

```python
def annotate_rois(self, pl, rois, hemi="left", **kwargs):
    if isinstance(rois, str):
        rois = [rois]
    hemis = ["left", "right"] if hemi == "both" else [hemi]
    n = FSAVERAGE_SIZES[self.mesh]      # 10242
    for h in hemis:
        verts = self._mesh[h]["coords"]
        for roi in rois:
            idx = get_hcp_roi_indices(roi, mesh=self.mesh, hemi=h)
            if h == "right":
                idx = np.array(idx) - n   # subtract because the indices from get_hcp_roi_indices
                                          # are already offset by 10242 for the right hemi
            center = verts[idx].mean(axis=0)
            name = rois[roi] if isinstance(rois, dict) else roi
            pl.add_point_labels(
                center.reshape(1, 3),
                [name],
                shape_opacity=0,
                **kwargs,
            )
```

**Per-ROI centre-of-mass labelling.** Monarch can port this to HTML labels in Three.js (`CSS2DRenderer`) positioned at `verts[idx].mean(axis=0)`. Use the mesh already shipped in `monarch-meshes/*.json`.

## 9. `plot_surf_rgb` (cortical_pv.py:169-280 and cortical.py:161-271)

The RGB multi-modality visualiser. Takes a list of 2 or 3 signals (e.g. `[audio_activation, video_activation, text_activation]`) and maps each to one colour channel.

```python
def plot_surf_rgb(
    self,
    signals,                 # list of (20484,) arrays
    alpha_signals=None,      # optional (20484,) alpha mask
    norm_percentile=95,
    alpha_bg=0,
    cmap="rgb" | "rgb_argmax" | "tab10",
    saturation_factor=None,
    axes=None,
    views=["left"],
    bg_on_data=False,
):
    # ... (atlas handling, then:)
    hemis = [self.get_hemis(signal) for signal in signals]

    for selected_hemis in ("left", "right", "both"):
        stat_maps = [hemi[selected_hemis]["stat_map"] for hemi in hemis]
        colors = np.stack(stat_maps, axis=1)         # (N, 2 or 3)

        if cmap.startswith("rgb"):
            if len(signals) == 2:
                colors = np.concatenate([colors, np.zeros((colors.shape[0], 1))], axis=1)
            assert colors.shape[1] == 3
            if "argmax" in cmap:
                # per-vertex: only the winning modality has value 1, others 0
                colors = robust_normalize(colors, axis=1, percentile=100)
                colors = (colors >= 1).astype(float)
            if norm_percentile is not None:
                colors = robust_normalize(colors, percentile=norm_percentile, two_sided=False)
            if saturation_factor is not None:
                colors = saturate_colors(colors, saturation_factor)
            colors = np.concatenate([colors, np.ones((colors.shape[0], 1))], axis=1)
        else:
            # e.g. cmap="tab10"
            indices = np.argmax(colors, axis=1)
            cm = get_cmap(cmap)
            colors = cm(indices - 1)
            colors[indices == 0, :3] = 0

        if alpha_signals is not None:
            alpha = alpha_hemis[selected_hemis]["stat_map"]
            alpha_bg = 1 - alpha[:, None]

        bg = hemis[0][selected_hemis]["bg_map"]
        cmap_bg = plt.get_cmap("gray_r")
        bg = robust_normalize(bg, percentile=100)
        bg = cmap_bg(bg)
        if bg_on_data:
            colors[:, :3] = colors[:, :3] * bg[:, :3]          # multiply blend
        else:
            colors[:, :3] = colors[:, :3] * (1 - alpha_bg) + bg[:, :3] * alpha_bg  # alpha blend
```

This is the reference for Monarch's "multimodal RGB" visualisation that the backend's `predict_multimodal` method already produces. The backend runs three separate `predict()` calls and averages. For the RGB visualisation, it should skip the averaging and pass the three vectors straight to a shader that does the stack+normalise+blend above.

## 10. `plot_timesteps` (base.py:235-365)

Drives multi-TR rendering. Critical points for Monarch:
- Accepts `neuro` either as ndarray or dict[str, ndarray]. Dict mode renders multiple rows (e.g. "Predicted" + "Ground truth").
- `plot_every_k_timesteps` - temporal downsampling.
- `norm_percentile` - applied to the full `neuro` array BEFORE splitting into per-TR plots, so all TRs share a common normalisation range.
- `show_stimuli=True` adds 1-3 extra rows for audio waveform, transcript words, and video frames (if available).
- `timestamps` - override the default `range(0, N*k, k)` integers. When None, labels read `"t=0s"`, `"t=1s"`, etc.
- Returns a matplotlib `Figure` suitable for `fig.savefig(...)`.

**Monarch interpretation**: the frontend animation should apply `robust_normalize(preds, percentile=99)` ONCE to the whole `(T, 20484)` array, then animate by indexing into the normalised buffer. Doing per-frame normalisation would cause flicker (the brightest activation of each TR would always land on white).

## 11. `plot_timesteps_mp4` (base.py:431-490)

Runs ffmpeg with `-framerate 1 -i tmp_%05d.png -vf minterpolate=fps=<interpolated_fps>`. Writes individual PNGs at DPI 300 to `<filepath>.parent/tmp/` first. **The interpolation between TRs is done by ffmpeg's motion-compensated frame interpolation filter, not by the model.** Monarch can do the same client-side: linearly interpolate `lerp(frames[t], frames[t+1], alpha)` where `alpha = video_currentTime - t`.

## 12. `plot_stimuli` (base.py:367-429)

Renders the audio waveform, transcript words, and video frames below the brain row. Consumes `segments` from `model.predict()`. Not relevant for Monarch's Three.js view, but useful for the PDF report generator if Monarch wants to show stimulus overlay.

## 13. Subcortical (`plotting/subcortical.py`)

Completely independent of the cortical pipeline. Uses Harvard-Oxford 1mm/2mm atlas. Marching cubes extracts a mesh per label (`get_mesh(label, resolution)` lru-cached). `plot_subcortical(voxel_scores, cmap, norm_percentile, ...)` renders an "exploded" view with each subcortical structure pushed outward. 

**Unused by the released model** - the released `facebook/tribev2` weights are cortical only. If Monarch wants subcortical NAA (for Nucleus Accumbens / Ventral Striatum), it needs a subcortical checkpoint that does not exist.

## 14. What Monarch must port to JavaScript

Summary of the JS shader logic the build team needs:

```glsl
// Vertex shader: pass sulc + activation index through
attribute vec3 position;
attribute vec3 normal;
attribute float sulcalDepth;       // from monarch-meshes JSON
attribute uint vertexIndex;        // 0..20483

uniform mat4 modelViewMatrix;
uniform mat4 projectionMatrix;
uniform sampler2D uLUT;            // 1x256 RGBA, e.g. fire cmap
uniform float uVmin;               // 0.5 in the notebook
uniform float uVmax;               // 1.0 after normalisation
uniform float uAlphaThreshold;     // 0.0
uniform float uAlphaScale;         // 0.2
uniform float uBgDarkness;         // 0.0
uniform float uSulcMin;            // from metadata.json
uniform float uSulcMax;            // from metadata.json
uniform float uActivation[20484];  // the pre-normalised (T, 20484) frame's current slice

varying vec3 vColor;
varying float vAlpha;

void main() {
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);

    float normVal = (uActivation[vertexIndex] - uVmin) / (uVmax - uVmin);
    normVal = clamp(normVal, 0.0, 1.0);

    // Alpha ramp
    float alpha;
    if (normVal < uAlphaThreshold) alpha = 0.0;
    else if (normVal >= uAlphaThreshold + uAlphaScale) alpha = 1.0;
    else alpha = (normVal - uAlphaThreshold) / uAlphaScale;

    vec3 lutColor = texture2D(uLUT, vec2(normVal, 0.5)).rgb;

    // Sulcal bg gray
    float bgNorm = (sulcalDepth - uSulcMin) / (uSulcMax - uSulcMin + 1e-6);
    float bgShade = 1.0 - (uBgDarkness + bgNorm * (1.0 - uBgDarkness));
    vec3 bgRgb = vec3(bgShade);

    vColor = mix(bgRgb, lutColor, alpha);
    vAlpha = 1.0;
}

// Fragment shader
varying vec3 vColor;
varying float vAlpha;

void main() {
    gl_FragColor = vec4(vColor, vAlpha);
}
```

Notes:
1. **Storing 20484 floats as a uniform array is over the WebGL2 limit** (max uniform array size is typically 1024 vec4's). Use a `sampler2D` of size 144x144 (= 20736 texels) instead and look up by `vertexIndex`. Or a `UBO` / `SSBO` for WebGL2.
2. `normVal` should be computed from a pre-normalized buffer on the CPU side (apply `robust_normalize` once per frame in JS before uploading). This avoids computing `np.percentile` in the shader.
3. The LUT texture should be 256 wide, 1 tall, `RGBA8`. Sample with `LINEAR` filter for a smooth gradient.
4. Lighting: add ambient 0.3 + simple directional Phong diffuse (0.7). PyVista uses `smooth_shading=True` which is per-vertex normal smoothing. The `monarch-meshes/*.json` files ship only vertex positions + faces + sulc; you'll need to compute per-vertex normals in JS from face adjacency. `three.js` has `BufferGeometry.computeVertexNormals()` which does this out of the box.
5. `bg_darkness=0` in the notebook. The shader above simplifies to `bgShade = 1 - bgNorm` - deeper sulci are darker. Matches the PyVista output.
