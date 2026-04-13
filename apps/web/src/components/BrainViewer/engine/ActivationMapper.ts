// ============================================================
// ActivationMapper.ts -- per-face activation -> face colors
// ============================================================
//
// The brain mesh is non-indexed: each face has its own 3 unique vertex
// slots, and ActivationMapper writes the SAME color to all 3 slots so
// every face renders as a uniform polygon. The face's activation value
// is the average of the 3 original-vertex activations (looked up via
// MeshLoader.getVertexIndices), and that value drives both the heatmap
// LUT lookup and the alpha ramp against the sulcal grey base.
// ============================================================

import * as THREE from 'three';

import { robustNormalize } from '@/lib/normalize';

import { LOOKUP } from './Colormap';
import type { MeshLoader } from './MeshLoader';
import type { MultimodalActivation } from '../types';

const HEMI_VERTS = 10242;
// TRIBE v2 notebook uses alpha_cmap=(0, 0.2):
// alpha = 0 below normalized value 0.0
// alpha = 1 above normalized value 0.2
// linear ramp between 0.0 and 0.2
const ALPHA_LO = 0.0;
const ALPHA_HI = 0.2;

// Multiplier on the per-face emissive contribution. Activated faces
// self-illuminate as `heatmap_color * alpha * EMISSIVE_BOOST`, added on
// top of the regular lighting in the fragment shader. A modest 1.05
// gives a noticeable glow without blowing the activation regions out
// to pure white.
const EMISSIVE_BOOST = 1.05;

export class ActivationMapper {
  private percentile = 99;

  constructor(private loader: MeshLoader) {}

  setPercentile(p: number): void {
    if (p <= 0 || p > 100) throw new Error('percentile must be in (0, 100]');
    this.percentile = p;
  }

  /**
   * Apply a (20484,) activation vector. Both hemispheres are updated;
   * normalization happens once across the whole vector so the two share
   * a consistent color scale.
   */
  applyActivation(
    leftMesh: THREE.Mesh,
    rightMesh: THREE.Mesh,
    data: Float32Array,
  ): void {
    if (data.length !== 2 * HEMI_VERTS) {
      throw new Error(
        `ActivationMapper: expected ${2 * HEMI_VERTS} values, got ${data.length}`,
      );
    }

    // Match TRIBE v2's plotting/utils.py:robust_normalize exactly:
    //   lo = p(1), hi = p(99), out = clip((data - lo) / (hi - lo), 0, 1)
    // Two-sided=true clips both tails symmetrically at the 1st and 99th
    // percentiles so outlier vertices don't wash out the colormap.
    const normalized = robustNormalize(data, this.percentile, true, true);
    this.writeHemi(leftMesh, 'left', normalized, 0);
    this.writeHemi(rightMesh, 'right', normalized, HEMI_VERTS);
  }

  private writeHemi(
    mesh: THREE.Mesh,
    hemi: 'left' | 'right',
    normalized: Float32Array,
    vertOffset: number,
  ): void {
    const geom = mesh.geometry as THREE.BufferGeometry;
    const colorAttr = geom.getAttribute('color') as THREE.BufferAttribute;
    if (!colorAttr) return;
    const colors = colorAttr.array as Float32Array;
    const emissiveAttr = geom.getAttribute('aEmissive') as
      | THREE.BufferAttribute
      | undefined;
    const emissives = emissiveAttr
      ? (emissiveAttr.array as Float32Array)
      : null;

    const sulcal = this.loader.getSulcalColors(hemi);
    const vertexIndices = this.loader.getVertexIndices(hemi);
    const F = this.loader.getFaceCount(hemi);
    const alphaSpan = ALPHA_HI - ALPHA_LO;

    for (let f = 0; f < F; f++) {
      // Average activation across the face's 3 original vertices.
      const i0 = vertexIndices[f * 3 + 0];
      const i1 = vertexIndices[f * 3 + 1];
      const i2 = vertexIndices[f * 3 + 2];
      const a =
        (normalized[vertOffset + i0] +
          normalized[vertOffset + i1] +
          normalized[vertOffset + i2]) /
        3;

      // Alpha ramp (sharp visible boundary).
      let alpha: number;
      if (a <= ALPHA_LO) alpha = 0;
      else if (a >= ALPHA_HI) alpha = 1;
      else alpha = (a - ALPHA_LO) / alphaSpan;

      // Heatmap color from the LUT.
      const idx = Math.min(255, Math.max(0, Math.round(a * 255))) * 3;
      const hr = LOOKUP[idx + 0];
      const hg = LOOKUP[idx + 1];
      const hb = LOOKUP[idx + 2];

      // Sulcal base color (face-uniform; pull from any of the 3 slots).
      const off = f * 9;
      const sr = sulcal[off + 0];
      const sg = sulcal[off + 1];
      const sb = sulcal[off + 2];

      // Blend.
      let r = sr + (hr - sr) * alpha;
      let g = sg + (hg - sg) * alpha;
      let b = sb + (hb - sb) * alpha;

      // Boost activated colors above 1.0 so the renderer's tone mapping
      // (when enabled) compresses them into a soft HDR bloom instead of
      // clipping. Activated faces glow noticeably brighter than the
      // grey brain. Inactive faces (alpha == 0) are untouched.
      if (alpha > 0) {
        const glow = 1.15;
        r *= glow;
        g *= glow;
        b *= glow;
      }

      // Write the same color to all 3 vertex slots of this face so the
      // face renders as a uniform polygon.
      colors[off + 0] = r;
      colors[off + 1] = g;
      colors[off + 2] = b;
      colors[off + 3] = r;
      colors[off + 4] = g;
      colors[off + 5] = b;
      colors[off + 6] = r;
      colors[off + 7] = g;
      colors[off + 8] = b;

      // Per-face emissive: zero on inactive faces, heatmap color *
      // alpha * boost on activated ones. This is added to the standard
      // lighting result in the fragment shader so activated faces stay
      // bright even at grazing angles where lambert drops near zero.
      if (emissives) {
        const er = hr * alpha * EMISSIVE_BOOST;
        const eg = hg * alpha * EMISSIVE_BOOST;
        const eb = hb * alpha * EMISSIVE_BOOST;
        emissives[off + 0] = er;
        emissives[off + 1] = eg;
        emissives[off + 2] = eb;
        emissives[off + 3] = er;
        emissives[off + 4] = eg;
        emissives[off + 5] = eb;
        emissives[off + 6] = er;
        emissives[off + 7] = eg;
        emissives[off + 8] = eb;
      }
    }
    colorAttr.needsUpdate = true;
    if (emissiveAttr) emissiveAttr.needsUpdate = true;
  }

  /**
   * Apply a multimodal RGB activation. Each modality (text, audio,
   * video) is normalized independently with the same percentile, then
   * mapped to a color channel:
   *   R = video, G = text, B = audio
   * Per-face color is the per-modality average across the 3 face
   * vertices, normalized so the dominant modality controls hue.
   */
  applyMultimodalActivation(
    leftMesh: THREE.Mesh,
    rightMesh: THREE.Mesh,
    data: MultimodalActivation,
  ): void {
    const expected = 2 * HEMI_VERTS;
    if (
      data.text.length !== expected ||
      data.audio.length !== expected ||
      data.video.length !== expected
    ) {
      throw new Error(
        `ActivationMapper: multimodal vectors must each be ${expected} long`,
      );
    }

    const textNorm = robustNormalize(data.text, this.percentile, false, true);
    const audioNorm = robustNormalize(data.audio, this.percentile, false, true);
    const videoNorm = robustNormalize(data.video, this.percentile, false, true);

    this.writeHemiMultimodal(leftMesh, 'left', textNorm, audioNorm, videoNorm, 0);
    this.writeHemiMultimodal(
      rightMesh,
      'right',
      textNorm,
      audioNorm,
      videoNorm,
      HEMI_VERTS,
    );
  }

  private writeHemiMultimodal(
    mesh: THREE.Mesh,
    hemi: 'left' | 'right',
    text: Float32Array,
    audio: Float32Array,
    video: Float32Array,
    vertOffset: number,
  ): void {
    const geom = mesh.geometry as THREE.BufferGeometry;
    const colorAttr = geom.getAttribute('color') as THREE.BufferAttribute;
    if (!colorAttr) return;
    const colors = colorAttr.array as Float32Array;
    const emissiveAttr = geom.getAttribute('aEmissive') as
      | THREE.BufferAttribute
      | undefined;
    const emissives = emissiveAttr
      ? (emissiveAttr.array as Float32Array)
      : null;

    const sulcal = this.loader.getSulcalColors(hemi);
    const vertexIndices = this.loader.getVertexIndices(hemi);
    const F = this.loader.getFaceCount(hemi);
    const alphaSpan = ALPHA_HI - ALPHA_LO;
    const glow = 1.15;

    for (let f = 0; f < F; f++) {
      // Per-face average for each modality across the face's 3 verts.
      const i0 = vertexIndices[f * 3 + 0];
      const i1 = vertexIndices[f * 3 + 1];
      const i2 = vertexIndices[f * 3 + 2];
      const tAvg =
        (text[vertOffset + i0] + text[vertOffset + i1] + text[vertOffset + i2]) / 3;
      const aAvg =
        (audio[vertOffset + i0] + audio[vertOffset + i1] + audio[vertOffset + i2]) / 3;
      const vAvg =
        (video[vertOffset + i0] + video[vertOffset + i1] + video[vertOffset + i2]) / 3;

      // Total activation strength drives the alpha blend against the
      // sulcal grey base. Same sharp ramp as single-mode activation.
      const total = Math.max(tAvg, aAvg, vAvg);
      let alpha: number;
      if (total <= ALPHA_LO) alpha = 0;
      else if (total >= ALPHA_HI) alpha = 1;
      else alpha = (total - ALPHA_LO) / alphaSpan;

      // Map modality strengths to RGB. Normalize by the max so the
      // dominant modality reaches 1.0 in its channel and pure-modality
      // regions read as saturated red/green/blue.
      const maxVal = Math.max(tAvg, aAvg, vAvg, 1e-6);
      const mr = (vAvg / maxVal) * glow;
      const mg = (tAvg / maxVal) * glow;
      const mb = (aAvg / maxVal) * glow;

      // Sulcal base color (face-uniform).
      const off = f * 9;
      const sr = sulcal[off + 0];
      const sg = sulcal[off + 1];
      const sb = sulcal[off + 2];

      // Blend sulcal grey -> multimodal RGB.
      const r = sr + (mr - sr) * alpha;
      const g = sg + (mg - sg) * alpha;
      const b = sb + (mb - sb) * alpha;

      colors[off + 0] = r;
      colors[off + 1] = g;
      colors[off + 2] = b;
      colors[off + 3] = r;
      colors[off + 4] = g;
      colors[off + 5] = b;
      colors[off + 6] = r;
      colors[off + 7] = g;
      colors[off + 8] = b;

      // Per-face emissive: same boost path as single-mode activation
      // so multimodal regions glow consistently with the rest of the
      // pipeline. Emissive is the (un-glow-boosted) per-channel ratio
      // scaled by alpha and EMISSIVE_BOOST.
      if (emissives) {
        const er = (vAvg / maxVal) * alpha * EMISSIVE_BOOST;
        const eg = (tAvg / maxVal) * alpha * EMISSIVE_BOOST;
        const eb = (aAvg / maxVal) * alpha * EMISSIVE_BOOST;
        emissives[off + 0] = er;
        emissives[off + 1] = eg;
        emissives[off + 2] = eb;
        emissives[off + 3] = er;
        emissives[off + 4] = eg;
        emissives[off + 5] = eb;
        emissives[off + 6] = er;
        emissives[off + 7] = eg;
        emissives[off + 8] = eb;
      }
    }
    colorAttr.needsUpdate = true;
    if (emissiveAttr) emissiveAttr.needsUpdate = true;
  }

  /** Revert both meshes to their sulcal-only grey shading. */
  clearActivation(leftMesh: THREE.Mesh, rightMesh: THREE.Mesh): void {
    this.resetHemi(leftMesh, 'left');
    this.resetHemi(rightMesh, 'right');
  }

  private resetHemi(mesh: THREE.Mesh, hemi: 'left' | 'right'): void {
    const geom = mesh.geometry as THREE.BufferGeometry;
    const colorAttr = geom.getAttribute('color') as THREE.BufferAttribute;
    if (!colorAttr) return;
    const sulcal = this.loader.getSulcalColors(hemi);
    (colorAttr.array as Float32Array).set(sulcal);
    colorAttr.needsUpdate = true;

    // Clear the emissive contribution so the brain reverts to pure
    // grey shading with no glow.
    const emissiveAttr = geom.getAttribute('aEmissive') as
      | THREE.BufferAttribute
      | undefined;
    if (emissiveAttr) {
      (emissiveAttr.array as Float32Array).fill(0);
      emissiveAttr.needsUpdate = true;
    }
  }
}
