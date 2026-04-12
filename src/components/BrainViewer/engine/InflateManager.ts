// ============================================================
// InflateManager.ts -- pial <-> inflated morph animation
// ============================================================
//
// The brain mesh is non-indexed: each face contributes 9 floats to the
// position buffer (3 verts * 3 coords). MeshLoader caches the pial and
// inflated face-position buffers; the morph lerps element-wise between
// them and writes the result to the active mesh's position attribute.
// Normals are recomputed only on animation completion (most expensive).
// ============================================================

import * as THREE from 'three';

import type { MeshLoader } from './MeshLoader';

const DURATION_MS = 600;

function easeInOutCubic(t: number): number {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

export class InflateManager {
  private inflated = false;
  private animating = false;
  private animStart = 0;
  private fromT = 0;
  private toT = 0;
  private currentT = 0;

  constructor(
    private leftMesh: THREE.Mesh,
    private rightMesh: THREE.Mesh,
    private loader: MeshLoader,
  ) {}

  setNormal(): void {
    this.startAnimation(0);
  }

  setInflated(): void {
    this.startAnimation(1);
  }

  toggle(): void {
    this.startAnimation(this.inflated ? 0 : 1);
  }

  isInflated(): boolean {
    return this.inflated;
  }

  /** 0 = fully pial, 1 = fully inflated. */
  getCurrentT(): number {
    return this.currentT;
  }

  isAnimating(): boolean {
    return this.animating;
  }

  private startAnimation(targetT: number): void {
    // If we're already at the target, nothing to do.
    if (Math.abs(this.currentT - targetT) < 1e-6 && !this.animating) return;
    this.fromT = this.currentT;
    this.toT = targetT;
    this.animStart = performance.now();
    this.animating = true;
    this.inflated = targetT > 0.5;
  }

  update(_deltaTime: number): void {
    if (!this.animating) return;
    const elapsed = performance.now() - this.animStart;
    const t = Math.min(1, elapsed / DURATION_MS);
    const k = easeInOutCubic(t);
    this.currentT = this.fromT + (this.toT - this.fromT) * k;

    this.lerpHemi(this.leftMesh, 'left', this.currentT);
    this.lerpHemi(this.rightMesh, 'right', this.currentT);

    if (t >= 1) {
      this.animating = false;
      // Normals are most expensive; only recompute on completion.
      // Use the loader's smooth-normal helper instead of the geometry's
      // own computeVertexNormals (which would give flat per-face normals
      // on the non-indexed mesh and break the tubular shading).
      this.loader.recomputeSmoothNormals(this.leftMesh, 'left');
      this.loader.recomputeSmoothNormals(this.rightMesh, 'right');
    }
  }

  private lerpHemi(mesh: THREE.Mesh, hemi: 'left' | 'right', t: number): void {
    const geom = mesh.geometry as THREE.BufferGeometry;
    const posAttr = geom.getAttribute('position') as THREE.BufferAttribute;
    const target = posAttr.array as Float32Array;
    const pial = this.loader.getPialFacePositions(hemi);
    const infl = this.loader.getInflatedFacePositions(hemi);

    for (let i = 0; i < target.length; i++) {
      target[i] = pial[i] + (infl[i] - pial[i]) * t;
    }
    posAttr.needsUpdate = true;
  }
}
