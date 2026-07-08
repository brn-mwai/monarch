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

interface HemiData {
  geometry: THREE.BufferGeometry; // rendered indexed geometry (pial-initialised)
  pialPositions: Float32Array; // 163842 * 3
  inflatedPositions: Float32Array; // 163842 * 3
  upsample: Uint32Array; // 163842 -> fsaverage5 index 0..10241
  vertexCount: number; // 163842
}

// White material; the light-grey base of the brain lives in the vertex
// colors (BASE_GREY in ActivationMapper) so activation paint multiplies
// cleanly over it.
const BASE_GREY = 0.82;

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

async function fetchUpsample(url: string): Promise<Uint32Array> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`MeshLoader: failed ${url} (${res.status})`);
  return new Uint32Array(await res.arrayBuffer());
}

export class MeshLoader {
  private gltf = new GLTFLoader();
  private left: HemiData | null = null;
  private right: HemiData | null = null;
  private leftMesh: THREE.Mesh | null = null;
  private rightMesh: THREE.Mesh | null = null;
  private material: THREE.MeshStandardMaterial | null = null;

  constructor(private modelsPath = '/models', private upsamplePath = '/brain-upsample-maps') {}

  async load(): Promise<void> {
    const [
      leftPial,
      rightPial,
      leftInflated,
      rightInflated,
      leftUpsample,
      rightUpsample,
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
      envMapIntensity: 0.55,
      flatShading: false,
      side: THREE.DoubleSide,
    });

    this.left = this.buildHemi(leftPial, leftInflated.positions, leftUpsample);
    this.right = this.buildHemi(rightPial, rightInflated.positions, rightUpsample);

    this.leftMesh = new THREE.Mesh(this.left.geometry, this.material);
    this.leftMesh.name = 'brain-left';
    this.rightMesh = new THREE.Mesh(this.right.geometry, this.material);
    this.rightMesh.name = 'brain-right';
  }

  private buildHemi(
    pial: { geometry: THREE.BufferGeometry; positions: Float32Array },
    inflatedPositions: Float32Array,
    upsample: Uint32Array,
  ): HemiData {
    const geometry = pial.geometry;
    const vertexCount = pial.positions.length / 3;

    // Base-grey vertex colors to start; ActivationMapper paints over these.
    const colors = new Float32Array(vertexCount * 3).fill(BASE_GREY);
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geometry.computeVertexNormals();
    geometry.computeBoundingBox();
    geometry.computeBoundingSphere();

    return {
      geometry,
      pialPositions: pial.positions.slice(),
      inflatedPositions,
      upsample,
      vertexCount,
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

  getVertexCount(side: 'left' | 'right'): number {
    return this.hemi(side).vertexCount;
  }

  getPialPositions(side: 'left' | 'right'): Float32Array {
    return this.hemi(side).pialPositions;
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
