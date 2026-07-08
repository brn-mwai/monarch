// ============================================================
// ActivationMapper.ts -- smooth per-vertex activation painting
// ============================================================
//
// Paints a (20484,) fsaverage5 activation onto the dense high-res (163,842
// verts/hemi) brain via the upsample map: each dense vertex takes the
// colour of its nearest fsaverage5 value, written as an indexed per-vertex
// colour so the GPU interpolates smoothly across triangles -- the demo's
// painted look. Inactive cortex stays light grey (BASE_GREY); active
// cortex is the fire colormap blended over it.
// ============================================================

import * as THREE from 'three';

import { robustNormalize } from '@/lib/normalize';

import { LOOKUP, normalizedToColorStop } from './Colormap';
import type { MeshLoader } from './MeshLoader';
import type { MultimodalActivation } from '../types';

const HEMI_VERTS = 10242;
const BASE_GREY = 0.82;
// TRIBE alpha_cmap: opacity ramps to 1 by colormap-stop 0.2.
const ALPHA_HI = 0.2;

export class ActivationMapper {
  private percentile = 99;
  private medialMask: Uint8Array | null = null;

  constructor(private loader: MeshLoader) {}

  setPercentile(p: number): void {
    if (p <= 0 || p > 100) throw new Error('percentile must be in (0, 100]');
    this.percentile = p;
  }

  /**
   * fsaverage5 medial-wall mask (20484 uint8: 1 = cortex, 0 = medial wall).
   * Masked vertices are forced to BASE_GREY and never painted - TRIBE's
   * predictions on the medial wall are not real cortical signal.
   */
  setMedialMask(mask: Uint8Array | null): void {
    if (mask && mask.length !== 2 * HEMI_VERTS) {
      throw new Error(
        `medial mask must be ${2 * HEMI_VERTS} long, got ${mask.length}`,
      );
    }
    this.medialMask = mask;
  }

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
    const normalized = robustNormalize(data, this.percentile, true, true);
    this.paintHemi(leftMesh, 'left', normalized, 0);
    this.paintHemi(rightMesh, 'right', normalized, HEMI_VERTS);
  }

  /** Apply a frame already robust-normalized to [0, 1] (playback path). */
  applyNormalized(
    leftMesh: THREE.Mesh,
    rightMesh: THREE.Mesh,
    normalized: Float32Array,
  ): void {
    if (normalized.length !== 2 * HEMI_VERTS) {
      throw new Error(
        `ActivationMapper: expected ${2 * HEMI_VERTS} values, got ${normalized.length}`,
      );
    }
    this.paintHemi(leftMesh, 'left', normalized, 0);
    this.paintHemi(rightMesh, 'right', normalized, HEMI_VERTS);
  }

  private paintHemi(
    mesh: THREE.Mesh,
    side: 'left' | 'right',
    normalized: Float32Array,
    activationOffset: number,
  ): void {
    const colorAttr = mesh.geometry.getAttribute('color') as
      | THREE.BufferAttribute
      | undefined;
    if (!colorAttr) return;
    const colors = colorAttr.array as Float32Array;
    const upsample = this.loader.getUpsampleMap(side);
    const count = this.loader.getVertexCount(side);

    for (let i = 0; i < count; i++) {
      const fsav = activationOffset + upsample[i];
      if (this.medialMask && this.medialMask[fsav] === 0) {
        const om = i * 3;
        colors[om] = BASE_GREY;
        colors[om + 1] = BASE_GREY;
        colors[om + 2] = BASE_GREY;
        continue;
      }
      const nv = normalized[fsav];
      const t = normalizedToColorStop(nv);
      let r = BASE_GREY;
      let g = BASE_GREY;
      let b = BASE_GREY;
      if (t > 0) {
        const alpha = t >= ALPHA_HI ? 1 : t / ALPHA_HI;
        const idx = Math.min(255, Math.max(0, Math.round(t * 255))) * 3;
        r = BASE_GREY + (LOOKUP[idx] - BASE_GREY) * alpha;
        g = BASE_GREY + (LOOKUP[idx + 1] - BASE_GREY) * alpha;
        b = BASE_GREY + (LOOKUP[idx + 2] - BASE_GREY) * alpha;
      }
      const o = i * 3;
      colors[o] = r;
      colors[o + 1] = g;
      colors[o + 2] = b;
    }
    colorAttr.needsUpdate = true;
  }

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
    const textN = robustNormalize(data.text, this.percentile, false, true);
    const audioN = robustNormalize(data.audio, this.percentile, false, true);
    const videoN = robustNormalize(data.video, this.percentile, false, true);
    this.paintHemiMultimodal(leftMesh, 'left', textN, audioN, videoN, 0);
    this.paintHemiMultimodal(rightMesh, 'right', textN, audioN, videoN, HEMI_VERTS);
  }

  private paintHemiMultimodal(
    mesh: THREE.Mesh,
    side: 'left' | 'right',
    textN: Float32Array,
    audioN: Float32Array,
    videoN: Float32Array,
    offset: number,
  ): void {
    const colorAttr = mesh.geometry.getAttribute('color') as
      | THREE.BufferAttribute
      | undefined;
    if (!colorAttr) return;
    const colors = colorAttr.array as Float32Array;
    const upsample = this.loader.getUpsampleMap(side);
    const count = this.loader.getVertexCount(side);

    for (let i = 0; i < count; i++) {
      const src = offset + upsample[i];
      if (this.medialMask && this.medialMask[src] === 0) {
        const om = i * 3;
        colors[om] = BASE_GREY;
        colors[om + 1] = BASE_GREY;
        colors[om + 2] = BASE_GREY;
        continue;
      }
      const tv = textN[src];
      const av = audioN[src];
      const vv = videoN[src];
      const total = Math.max(tv, av, vv);
      const alpha = total >= ALPHA_HI ? 1 : total <= 0 ? 0 : total / ALPHA_HI;
      const maxVal = Math.max(tv, av, vv, 1e-6);
      // Paper Fig 7: R = text, G = audio, B = video.
      const cr = tv / maxVal;
      const cg = av / maxVal;
      const cb = vv / maxVal;
      const o = i * 3;
      colors[o] = BASE_GREY + (cr - BASE_GREY) * alpha;
      colors[o + 1] = BASE_GREY + (cg - BASE_GREY) * alpha;
      colors[o + 2] = BASE_GREY + (cb - BASE_GREY) * alpha;
    }
    colorAttr.needsUpdate = true;
  }

  clearActivation(leftMesh: THREE.Mesh, rightMesh: THREE.Mesh): void {
    this.fillGrey(leftMesh);
    this.fillGrey(rightMesh);
  }

  private fillGrey(mesh: THREE.Mesh): void {
    const colorAttr = mesh.geometry.getAttribute('color') as
      | THREE.BufferAttribute
      | undefined;
    if (!colorAttr) return;
    (colorAttr.array as Float32Array).fill(BASE_GREY);
    colorAttr.needsUpdate = true;
  }
}
