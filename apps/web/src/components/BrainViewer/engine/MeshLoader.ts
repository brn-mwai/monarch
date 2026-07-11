// ============================================================
// MeshLoader.ts -- high-res white brain from the TRIBE GLB meshes
// ============================================================
//
// Loads the extracted TRIBE v2 fsaverage7 GLB surfaces (163,842 verts/
// hemi), rendered as INDEXED geometry with smooth per-vertex normals and
// a light/white material. Activation (20,484 fsaverage5 values) is painted
// smoothly onto the dense surface via the fsaverage5 -> high upsample map,
// matching the demo's look. No per-face flat fills, no sulcal grey, no
// emissive glow -- gyri show through normal-based shading on the white
// surface.
// ============================================================

import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

export type SurfaceKind = 'pial' | 'fiducial' | 'white';

interface HemiData {
  geometry: THREE.BufferGeometry; // rendered indexed geometry (pial-initialised)
  pialPositions: Float32Array; // 163842 * 3
  fiducialPositions: Float32Array; // 163842 * 3, midthickness (pial+white)/2
  whitePositions: Float32Array; // 163842 * 3, gray/white boundary
  inflatedPositions: Float32Array; // 163842 * 3
  upsample: Uint32Array; // 163842 -> fsaverage5 index 0..10241
  vertexCount: number; // 163842
  baseColors: Float32Array; // vertexCount * 3, curvature grey (sulci dark, gyri light)
  curvatureNorm: Float32Array; // vertexCount, [-1, 1]; re-shadeable at runtime
}

// The light-grey base of the brain lives in the vertex colors (curvature
// grey, see computeCurvatureGrey) so activation paint multiplies cleanly
// over it.
//
// Curvature-grey range: gyri (convex) sit light, sulci (concave) sit dark.
// Tuned to a mid-grey anatomical look (FreeSurfer/pycortex style) rather than
// a bright white blob -- the darker base also makes the activation colormap
// read with more contrast.
// Linear-space greys: the renderer gamma-encodes these to sRGB for display,
// so a linear 0.30 shows as ~0.58 mid-grey. Tuned for the FreeSurfer/pycortex
// matte-grey look (Image reference) after the sRGB lift.
const CURV_MID = 0.3;
const CURV_AMPLITUDE = 0.15;
const CURV_MIN = 0.12;
const CURV_MAX = 0.42;

/**
 * Per-vertex normalized curvature from the pial mesh, in [-1, 1]. Computes a
 * discrete mean-curvature proxy: the uniform Laplacian (neighbour-centroid
 * minus vertex) projected onto the vertex normal, then robustly scaled by the
 * 95th percentile of magnitude. Concave vertices (sulci) are positive, convex
 * (gyri) negative. Frame-independent, so it does not depend on the pial/
 * inflated meshes sharing a coordinate origin or scale. The grey shading is
 * derived from this by greyFromCurvature, so brightness/contrast can be
 * retuned at runtime without recomputing curvature.
 */
function computeCurvatureNorm(
  positions: Float32Array,
  normals: Float32Array,
  index: ArrayLike<number> | null,
  count: number,
): Float32Array {
  const curvature = new Float32Array(count);
  if (!index) return curvature;

  const sumX = new Float32Array(count);
  const sumY = new Float32Array(count);
  const sumZ = new Float32Array(count);
  const degree = new Uint32Array(count);
  const addNeighbour = (a: number, b: number): void => {
    sumX[a] += positions[b * 3];
    sumY[a] += positions[b * 3 + 1];
    sumZ[a] += positions[b * 3 + 2];
    degree[a] += 1;
  };
  for (let f = 0; f < index.length; f += 3) {
    const a = index[f];
    const b = index[f + 1];
    const c = index[f + 2];
    addNeighbour(a, b);
    addNeighbour(a, c);
    addNeighbour(b, a);
    addNeighbour(b, c);
    addNeighbour(c, a);
    addNeighbour(c, b);
  }

  for (let i = 0; i < count; i++) {
    const d = degree[i];
    if (d === 0) continue;
    const lx = sumX[i] / d - positions[i * 3];
    const ly = sumY[i] / d - positions[i * 3 + 1];
    const lz = sumZ[i] / d - positions[i * 3 + 2];
    curvature[i] =
      lx * normals[i * 3] + ly * normals[i * 3 + 1] + lz * normals[i * 3 + 2];
  }

  const magnitudes = Float32Array.from(curvature, Math.abs).sort();
  const scale = magnitudes[Math.floor(magnitudes.length * 0.95)] || 1;
  for (let i = 0; i < count; i++) {
    let c = curvature[i] / scale;
    if (c > 1) c = 1;
    else if (c < -1) c = -1;
    curvature[i] = c;
  }
  return curvature;
}

/**
 * Grey vertex colors from normalized curvature. ``brightness`` sets the base
 * grey level (gyri); ``contrast`` sets how much darker the sulci go.
 */
function greyFromCurvature(
  curvatureNorm: Float32Array,
  brightness: number,
  contrast: number,
): Float32Array {
  const count = curvatureNorm.length;
  const colors = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
    let grey = brightness - curvatureNorm[i] * contrast;
    if (grey < CURV_MIN) grey = CURV_MIN;
    else if (grey > CURV_MAX) grey = CURV_MAX;
    colors[i * 3] = grey;
    colors[i * 3 + 1] = grey;
    colors[i * 3 + 2] = grey;
  }
  return colors;
}

async function fetchPositions(
  loader: GLTFLoader,
  url: string,
): Promise<{ geometry: THREE.BufferGeometry; positions: Float32Array }> {
  const gltf = await loader.loadAsync(url);
  let geometry: THREE.BufferGeometry | null = null;
  gltf.scene.traverse((node) => {
    const mesh = node as THREE.Mesh;
    if (!geometry && mesh.isMesh) geometry = mesh.geometry as THREE.BufferGeometry;
  });
  if (!geometry) throw new Error(`MeshLoader: no mesh in ${url}`);
  const positions = ((geometry as THREE.BufferGeometry).getAttribute(
    'position',
  ).array as Float32Array).slice();
  return { geometry, positions };
}

function centroid(positions: Float32Array): [number, number, number] {
  let sx = 0;
  let sy = 0;
  let sz = 0;
  const n = positions.length / 3;
  for (let i = 0; i < positions.length; i += 3) {
    sx += positions[i];
    sy += positions[i + 1];
    sz += positions[i + 2];
  }
  return [sx / n, sy / n, sz / n];
}

/**
 * The inflated GLBs are each exported centered at the origin, so both
 * hemispheres' inflated surfaces sit on the midline and overlap when the
 * pial->inflated morph runs. Translate the inflated vertices so their
 * centroid matches the pial centroid: each hemisphere then inflates in place
 * and keeps its natural left/right separation instead of collapsing together.
 */
function alignInflatedToPial(
  inflated: Float32Array,
  pial: Float32Array,
): Float32Array {
  const [ix, iy, iz] = centroid(inflated);
  const [px, py, pz] = centroid(pial);
  const dx = px - ix;
  const dy = py - iy;
  const dz = pz - iz;
  const out = new Float32Array(inflated.length);
  for (let i = 0; i < inflated.length; i += 3) {
    out[i] = inflated[i] + dx;
    out[i + 1] = inflated[i + 1] + dy;
    out[i + 2] = inflated[i + 2] + dz;
  }
  return out;
}

async function fetchUpsample(url: string): Promise<Uint32Array> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`MeshLoader: failed ${url} (${res.status})`);
  return new Uint32Array(await res.arrayBuffer());
}

async function fetchFloat32(url: string): Promise<Float32Array> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`MeshLoader: failed ${url} (${res.status})`);
  return new Float32Array(await res.arrayBuffer());
}

export class MeshLoader {
  private gltf = new GLTFLoader();
  private left: HemiData | null = null;
  private right: HemiData | null = null;
  private leftMesh: THREE.Mesh | null = null;
  private rightMesh: THREE.Mesh | null = null;
  private material: THREE.MeshStandardMaterial | null = null;
  private currentSurface: SurfaceKind = 'pial';

  constructor(private modelsPath = '/models', private upsamplePath = '/brain-upsample-maps') {}

  async load(): Promise<void> {
    const [
      leftPial,
      rightPial,
      leftInflated,
      rightInflated,
      leftUpsample,
      rightUpsample,
      leftWhite,
      rightWhite,
      leftFiducial,
      rightFiducial,
    ] = await Promise.all([
      fetchPositions(this.gltf, `${this.modelsPath}/brain-left-hemishpere-high.glb`),
      fetchPositions(this.gltf, `${this.modelsPath}/brain-right-hemisphere-high.glb`),
      fetchPositions(
        this.gltf,
        `${this.modelsPath}/brain-left-hemishpere-high-inflated.glb`,
      ),
      fetchPositions(
        this.gltf,
        `${this.modelsPath}/brain-right-hemisphere-high-inflated.glb`,
      ),
      fetchUpsample(`${this.upsamplePath}/fsaverage5-to-high-left.bin`),
      fetchUpsample(`${this.upsamplePath}/fsaverage5-to-high-right.bin`),
      fetchFloat32(`${this.modelsPath}/brain-left-white.bin`),
      fetchFloat32(`${this.modelsPath}/brain-right-white.bin`),
      fetchFloat32(`${this.modelsPath}/brain-left-fiducial.bin`),
      fetchFloat32(`${this.modelsPath}/brain-right-fiducial.bin`),
    ]);

    // Matches the Meta TRIBE v2 demo brain material: a white, fully
    // non-metallic standard surface that reads its sheen from the scene's
    // image-based environment map (set in BrainEngine). DoubleSide keeps the
    // medial wall and inflated/cut views solid from the inside.
    this.material = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      vertexColors: true,
      roughness: 0.72,
      metalness: 0.0,
      envMapIntensity: 0.2, // sheen amount; driven by setSpecular at runtime
      flatShading: false,
      side: THREE.DoubleSide,
    });

    this.left = this.buildHemi(
      leftPial,
      alignInflatedToPial(leftInflated.positions, leftPial.positions),
      leftUpsample,
      leftWhite,
      leftFiducial,
    );
    this.right = this.buildHemi(
      rightPial,
      alignInflatedToPial(rightInflated.positions, rightPial.positions),
      rightUpsample,
      rightWhite,
      rightFiducial,
    );

    this.leftMesh = new THREE.Mesh(this.left.geometry, this.material);
    this.leftMesh.name = 'brain-left';
    this.rightMesh = new THREE.Mesh(this.right.geometry, this.material);
    this.rightMesh.name = 'brain-right';
  }

  private buildHemi(
    pial: { geometry: THREE.BufferGeometry; positions: Float32Array },
    inflatedPositions: Float32Array,
    upsample: Uint32Array,
    whitePositions: Float32Array,
    fiducialPositions: Float32Array,
  ): HemiData {
    const geometry = pial.geometry;
    const vertexCount = pial.positions.length / 3;

    // Normals first: the curvature shading projects the Laplacian onto them.
    geometry.computeVertexNormals();
    const indexAttr = geometry.getIndex();
    const curvatureNorm = computeCurvatureNorm(
      pial.positions,
      geometry.getAttribute('normal').array as Float32Array,
      indexAttr ? (indexAttr.array as ArrayLike<number>) : null,
      vertexCount,
    );
    const baseColors = greyFromCurvature(curvatureNorm, CURV_MID, CURV_AMPLITUDE);
    // Seed the rendered colors with the curvature grey; ActivationMapper
    // paints activation over a copy of this per-vertex base.
    geometry.setAttribute('color', new THREE.BufferAttribute(baseColors.slice(), 3));
    geometry.computeBoundingBox();
    geometry.computeBoundingSphere();

    return {
      geometry,
      pialPositions: pial.positions.slice(),
      fiducialPositions,
      whitePositions,
      inflatedPositions,
      upsample,
      vertexCount,
      baseColors,
      curvatureNorm,
    };
  }

  private hemi(side: 'left' | 'right'): HemiData {
    const data = side === 'left' ? this.left : this.right;
    if (!data) throw new Error('MeshLoader: load() not called yet');
    return data;
  }

  getLeftMesh(): THREE.Mesh {
    if (!this.leftMesh) throw new Error('MeshLoader: load() not called yet');
    return this.leftMesh;
  }

  getRightMesh(): THREE.Mesh {
    if (!this.rightMesh) throw new Error('MeshLoader: load() not called yet');
    return this.rightMesh;
  }

  getUpsampleMap(side: 'left' | 'right'): Uint32Array {
    return this.hemi(side).upsample;
  }

  /** Per-vertex curvature-grey base colors (vertexCount * 3). */
  getBaseColors(side: 'left' | 'right'): Float32Array {
    return this.hemi(side).baseColors;
  }

  /** Set the brain surface opacity (enables transparency below 1). */
  setOpacity(opacity: number): void {
    if (!this.material) return;
    this.material.transparent = opacity < 1;
    this.material.opacity = opacity;
    this.material.needsUpdate = true;
  }

  /**
   * Set the specular sheen (0 = matte, 1 = glossy). Drives the environment-
   * map reflection intensity -- the reflected highlight is what gives the
   * gyri their wet sheen; kept low by default for the matte anatomical grey.
   */
  setSpecular(specularity: number): void {
    if (!this.material) return;
    const s = specularity < 0 ? 0 : specularity > 1 ? 1 : specularity;
    this.material.envMapIntensity = s;
    this.material.needsUpdate = true;
  }

  /**
   * Re-derive the curvature-grey base colors from the stored curvature with
   * new brightness/contrast, in place. Callers must re-apply activation after
   * (the rendered color attribute paints over these bases).
   */
  recolorCurvature(brightness: number, contrast: number): void {
    for (const side of ['left', 'right'] as const) {
      const hemi = this.left && side === 'left' ? this.left : this.right;
      if (!hemi) continue;
      hemi.baseColors.set(
        greyFromCurvature(hemi.curvatureNorm, brightness, contrast),
      );
    }
  }

  getVertexCount(side: 'left' | 'right'): number {
    return this.hemi(side).vertexCount;
  }

  getPialPositions(side: 'left' | 'right'): Float32Array {
    return this.hemi(side).pialPositions;
  }

  /** Select the base cortical surface (pial / fiducial / white). */
  setSurface(kind: SurfaceKind): void {
    this.currentSurface = kind;
  }

  getSurface(): SurfaceKind {
    return this.currentSurface;
  }

  /** Positions of the currently selected base surface -- the morph origin. */
  getBasePositions(side: 'left' | 'right'): Float32Array {
    const hemi = this.hemi(side);
    if (this.currentSurface === 'white') return hemi.whitePositions;
    if (this.currentSurface === 'fiducial') return hemi.fiducialPositions;
    return hemi.pialPositions;
  }

  getInflatedPositions(side: 'left' | 'right'): Float32Array {
    return this.hemi(side).inflatedPositions;
  }

  recomputeSmoothNormals(mesh: THREE.Mesh, _side: 'left' | 'right'): void {
    mesh.geometry.computeVertexNormals();
  }

  getCombinedBoundingBox(): THREE.Box3 {
    const box = new THREE.Box3();
    if (this.leftMesh) box.expandByObject(this.leftMesh);
    if (this.rightMesh) box.expandByObject(this.rightMesh);
    return box;
  }

  dispose(): void {
    this.left?.geometry.dispose();
    this.right?.geometry.dispose();
    this.material?.dispose();
    this.left = null;
    this.right = null;
    this.leftMesh = null;
    this.rightMesh = null;
    this.material = null;
  }
}
