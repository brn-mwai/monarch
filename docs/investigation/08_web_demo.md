# 08 - Web Demo (aidemos.atmeta.com/tribev2) Reverse Engineering

This file documents what we know about Meta's public demo at **`aidemos.atmeta.com/tribev2/`**. The source is NOT in the repo (`tribev2.github.io` is hosted externally and its JS/GLB assets are unversioned here). Most of this comes from the user's partial reverse engineering.

---

## 1. Assets inventory (per the user's observation)

- **5 GLB meshes**:
  1. `pial_L.glb` - left hemisphere pial surface
  2. `pial_R.glb` - right hemisphere pial surface
  3. `inflated_L.glb` - left hemisphere inflated surface
  4. `inflated_R.glb` - right hemisphere inflated surface
  5. `head_shell.glb` - an outer skull / head-shape shell for visual context
- **JSON activation manifests** e.g. `left-hemisphere-face-colors-binary-prediction.json`. "Binary" here likely means a single scalar per face (one channel) as opposed to the multi-channel RGB mode.
- **Per-face color rendering** - the shader looks up face colours from a texture atlas keyed by face index rather than vertex-based interpolation.

## 2. Shader uniforms (per the user's observation)

```
uFaceTex   : sampler2D       - texture atlas containing all frames' face colours
uAtlasW    : float           - atlas texture width in pixels
uAtlasH    : float           - atlas texture height in pixels
uNumFaces  : int             - faces per hemisphere (20480 for fsaverage5)
uFrame0    : int             - current frame index
uFrame1    : int             - next frame index for interpolation
uAlpha     : float           - blend factor between uFrame0 and uFrame1 (0..1)
```

This is a **temporal atlas**: the JSON manifest packs every TR into a 2D RGBA texture that the GPU reads row by row. The shader linearly blends frame0 and frame1 based on `uAlpha` which is driven by the video `currentTime`.

Rough atlas layout guess:
- `uAtlasW = ceil(sqrt(numFrames))` faces wide
- `uAtlasH = numFrames * numFaces / uAtlasW`
- Each texel holds RGBA for one (face, frame) pair
- Face index lookup: `atlas_uv = (face_index % uAtlasW, frame_index * faces_per_row + face_index / uAtlasW)`

## 3. Animation driver

The user says: "Two-frame interpolation, video `currentTime` drives the frame index". So the flow is:

```
<video> element plays the source video
  |
  v
requestAnimationFrame loop:
  t = video.currentTime  (seconds)
  frame_float = t / TR                  // TR is the model's 1 Hz output rate
  frame_idx = floor(frame_float)
  alpha = frame_float - frame_idx
  update shader uniforms:
     uFrame0 = frame_idx
     uFrame1 = frame_idx + 1
     uAlpha = alpha
  |
  v
Three.js renders:
  brain_surface.material.uniforms.uFrame0/1/alpha are applied,
  the shader samples the texture atlas and lerps per-face colours,
  then renders with standard lighting.
```

This gives smooth perceived animation at 60 Hz even though the model only produces 1 frame per second.

## 4. Implication: this is NOT live inference

The demo's animation plays **precomputed** activations from a JSON manifest that was generated once on a server. Not a single `TribeModel.from_pretrained` call happens in the browser. The JSON manifest is just a `(T, 20480)` array of face colours (per-face means are computed from the per-vertex TRIBE outputs via `face_color = mean(vertex_colors[face.vertices])`).

So "the TRIBE web demo" is actually two things:
1. **Server-side**: A batch job that ran TRIBE's `predict()` on a specific video, averaged the vertex outputs into face colours, and packed the result into an RGBA texture atlas + manifest JSON.
2. **Client-side**: A Three.js viewer that plays the video in an HTML5 `<video>` element and samples the pre-baked texture atlas in sync.

## 5. Contrast with Monarch MVP

| Aspect | TRIBE web demo | Monarch MVP |
|---|---|---|
| Inference timing | Precomputed, static | Live per-scan (user hits "Scan" -> backend runs TribeModel.predict -> frontend renders) |
| Temporal axis | Full `(T, 20480)` time series baked into atlas | Single `(20484,)` static activation per scan (the item-pooled vector) |
| Animation | Yes, driven by video.currentTime | No (MVP) - static snapshot per scan |
| Per-face vs per-vertex | Per-face (averaged over triangle) | Per-vertex (native TRIBE output space) |
| Mesh format | 5 GLBs (two hemispheres x two inflation states + shell) | 4 JSONs in `monarch-meshes/` + the combined `.bin` |
| Colour pipeline | Face colours precomputed (server did the robust_normalize + cmap + alpha blend) | Frontend needs to do robust_normalize + cmap + alpha blend in shader because activation is live |
| Input modalities | Single chosen demo video | Text, audio, or video user upload |

## 6. Stretch goal for Monarch: "video-timeline animation"

If Monarch wants to match the TRIBE demo's animated look, it needs to:

1. **Send the full `(T, 20484)` time series over the wire.** For a 60-second clip this is `60 * 20484 * 4 bytes = ~5 MB`, which is fine over HTTP. For a 5-minute clip it's 25 MB, borderline.
2. **Normalise once on the backend** (robust_normalize percentile=99 over the whole T slab) OR on the frontend (same math in JS, once per new scan).
3. **Either**
   - pack into a 2D texture atlas and mimic the TRIBE shader (per-face averaging is trivial: `faceColor[i] = mean(vertexColors[faces[i]])`),
   - or store the `(T, 20484)` as a Float32Array and animate by computing `lerp(frame_t, frame_t+1, alpha)` per frame in JS before pushing to GPU (slower but simpler).
4. **Drive animation from an audio element's currentTime** when the user's input is audio or video. When the user's input is text, there's no natural time driver so animate at a fixed 1 FPS + interpolation.

**The existing `monarch-meshes/` JSONs ship per-vertex data (not per-face).** That's fine - per-vertex rendering in Three.js with `BufferGeometry.attributes.color` is well supported. The TRIBE demo chose per-face for a minor perf win (20480 colours to update instead of 20484), but the visual difference is minimal.

## 7. What to inspect if you really need the demo source

The user's reverse-engineering covered the shader uniforms and asset list, but if the build team wants to diff the demo's logic exactly, they can:

1. Open `aidemos.atmeta.com/tribev2/` in Chrome DevTools.
2. Network tab: filter for `.glb`, `.json`, `.js`. The demo is likely a single hashed `main.*.js` bundle plus a handful of assets.
3. Sources tab: the bundle is minified but React + Three.js component names survive as string literals. Search for "face_color", "frame0", "frame1".
4. The manifests `left-hemisphere-face-colors-binary-prediction.json` will contain a flat array of length `20480 * n_frames` - save one, inspect it, confirm the per-face layout.

**None of this is required for the Monarch MVP.** The MVP uses a single `(20484,)` vector per scan, which doesn't need any of the atlas / interpolation machinery.

## 8. Key differences to call out in the Monarch design doc

1. **Monarch is the first live-inference TRIBE v2 frontend.** The public demo is a pre-baked animation.
2. **Monarch MVP renders a single static snapshot per scan.** No animation, no `(T, 20484)`, just the mean-pooled `(20484,)` item vector.
3. **Monarch renders per-vertex**, not per-face, for simplicity.
4. **Monarch's mesh assets are already generated and checked in** at `C:\Users\Windows\Downloads\tribev2\monarch-meshes\` - see `01_file_map.md` and `05_plotting_system.md` for what's inside.
5. **The "A/B compare mode" in Monarch is unique** - two `predict()` calls producing two `(20484,)` vectors side by side. No TRIBE demo feature matches this.

## 9. Stretch goal roadmap

If a future Monarch milestone wants the video-timeline animation:

- [ ] Extend the `/scan` response to include the full `(T, 20484)` when the input is audio/video. Keep `(20484,)` for text.
- [ ] Add a `timeSeries: Float32Array | null` field on the BrainViewer component's props.
- [ ] Switch to a per-face rendering path (average vertex colours into face colours client-side) OR keep per-vertex and just upload a new `BufferAttribute` each frame.
- [ ] Drive `uFrame0/uFrame1/uAlpha` (or the JS equivalent) from `audioElement.currentTime` / `videoElement.currentTime`.
- [ ] Add a "play/pause" control in the UI.
- [ ] Size the payload: for 60s audio that's 60 * 20484 * 4 = 4.9 MB per scan. Compressed with gzip (float32 compresses poorly) or with quantisation to int8 (ratio 4x). Budget: a few seconds of download per scan.
- [ ] Possibly compute the robust_normalize on the server so the client doesn't spend 20484 * T * log(T) sort cycles.

The MVP doesn't need any of this. The stretch goal is a visible product differentiator but adds 1-2 weeks of frontend work and server-side optimisation.
