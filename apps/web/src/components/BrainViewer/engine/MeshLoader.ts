// ============================================================
// MeshLoader.ts -- fetch & build fsaverage5 brain meshes (per-face)
// ============================================================
//
// Builds NON-INDEXED geometry where each face has its own 3 unique
// vertices. This lets each face be colored uniformly (for the polygonal
// look) instead of having vertex colors interpolated across the face.
//
// Per hemisphere we cache:
//   - pial + inflated face position buffers (F*9 floats each, for morph)
//   - vertex-index lookup (F*3 ints, original vertex index for each
//     face slot, used by ActivationMapper to compute per-face activation)
//   - per-face sulcal palette (pial + inflated + current blended)
//   - per-vertex sulcal depth (kept for recomputation)
// ============================================================

import * as THREE from 'three';

import {
  buildInflatedFaceColors,
  buildPialFaceColors,
} from './SulcalShading';
import type { BrainMeshData, BrainMeshSet } from '../types';

interface HemiGeometries {
  pial: THREE.BufferGeometry;
  inflated: THREE.BufferGeometry;

  // Non-indexed per-face position buffers for morph animation.
  // Each face contributes 9 floats: 3 vertices * 3 coords.
  pialFacePositions: Float32Array;
  inflatedFacePositions: Float32Array;

  // Original vertex index for each non-indexed slot. Length F*3.
  // Used by ActivationMapper to look up per-vertex activation values.
  vertexIndices: Uint32Array;

  // Per-face sulcal RGB colors (F*9 floats each).
  sulcalFaceColorsPial: Float32Array;
  sulcalFaceColorsInflated: Float32Array;
  currentSulcalFaceColors: Float32Array;

  // Original per-vertex sulcal depth and face index buffer (kept for
  // future recomputation).
  sulcalDepth: Float32Array;
  faces: Uint32Array;

  // Per-face emissive RGB buffer (F*9 floats, all zeros initially).
  // Lives on the rendered pial geometry as the `aEmissive` attribute
  // and is written by ActivationMapper so activated faces glow as
  // self-illuminating regardless of viewing angle.
  emissive: Float32Array;

  faceCount: number;
}

function flattenVertices(verts: number[][]): Float32Array {
  const out = new Float32Array(verts.length * 3);
  for (let i = 0; i < verts.length; i++) {
    out[i * 3 + 0] = verts[i][0];
    out[i * 3 + 1] = verts[i][1];
    out[i * 3 + 2] = verts[i][2];
  }
  return out;
}

function flattenFaces(faces: number[][]): Uint32Array {
  const out = new Uint32Array(faces.length * 3);
  for (let i = 0; i < faces.length; i++) {
    out[i * 3 + 0] = faces[i][0];
    out[i * 3 + 1] = faces[i][1];
    out[i * 3 + 2] = faces[i][2];
  }
  return out;
}

/**
 * Expand an indexed (vertex, face) mesh into a non-indexed face buffer.
 * For each face we copy the 3 vertex positions into consecutive slots,
 * so position[f*9 + v*3 + c] is the c-th coordinate of the v-th vertex
 * of the f-th face.
 */
function expandFacePositions(
  positions: Float32Array,
  faces: Uint32Array,
): Float32Array {
  const F = faces.length / 3;
  const out = new Float32Array(F * 9);
  for (let f = 0; f < F; f++) {
    for (let v = 0; v < 3; v++) {
      const idx = faces[f * 3 + v];
      out[f * 9 + v * 3 + 0] = positions[idx * 3 + 0];
      out[f * 9 + v * 3 + 1] = positions[idx * 3 + 1];
      out[f * 9 + v * 3 + 2] = positions[idx * 3 + 2];
    }
  }
  return out;
}


async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`MeshLoader: failed to fetch ${url} (${res.status})`);
  }
  return (await res.json()) as T;
}

export class MeshLoader {
  private basePath: string;
  private meshSet: BrainMeshSet | null = null;
  private left: HemiGeometries | null = null;
  private right: HemiGeometries | null = null;
  private leftMesh: THREE.Mesh | null = null;
  private rightMesh: THREE.Mesh | null = null;
  private material: THREE.MeshPhysicalMaterial | null = null;

  constructor(basePath = '/mesh') {
    this.basePath = basePath;
  }

  async load(): Promise<BrainMeshSet> {
    const [leftPial, rightPial, leftInflated, rightInflated] = await Promise.all([
      fetchJson<BrainMeshData>(`${this.basePath}/left_pial.json`),
      fetchJson<BrainMeshData>(`${this.basePath}/right_pial.json`),
      fetchJson<BrainMeshData>(`${this.basePath}/left_inflated.json`),
      fetchJson<BrainMeshData>(`${this.basePath}/right_inflated.json`),
    ]);

    this.meshSet = { leftPial, rightPial, leftInflated, rightInflated };

    this.left = this.buildHemisphere(leftPial, leftInflated);
    this.right = this.buildHemisphere(rightPial, rightInflated);

    // Rescale the cached inflated face positions so the combined inflated
    // bbox exactly matches the combined pial bbox. The morph still
    // produces the inflated surface topology, but the overall brain
    // size stays the same when toggling between pial and inflated.
    this.matchInflatedToPialSize();

    // Mostly matte with a faint clearcoat. Slight transparency (90%
    // opacity) gives the surface a glassmorphism feel: a thin frosted
    // layer that lets a hint of light through without making the back
    // of the brain visible (depthWrite stays on so front faces still
    // occlude the back).
    this.material = new THREE.MeshPhysicalMaterial({
      vertexColors: true,
      metalness: 0.0,
      roughness: 0.65,
      clearcoat: 0.14,
      clearcoatRoughness: 0.32,
      reflectivity: 0.18,
      side: THREE.FrontSide,
      flatShading: false,
      transparent: true,
      opacity: 0.98,
      depthWrite: true,
    });

    // Inject a custom per-vertex emissive attribute so activated faces
    // self-illuminate (the activation glow). The aEmissive attribute is
    // zero on non-activated faces and the heatmap color * boost on
    // activated ones (written by ActivationMapper.writeHemi).
    this.material.onBeforeCompile = (shader) => {
      shader.vertexShader = shader.vertexShader.replace(
        '#include <common>',
        `#include <common>
attribute vec3 aEmissive;
varying vec3 vEmissive;`,
      );
      shader.vertexShader = shader.vertexShader.replace(
        '#include <begin_vertex>',
        `#include <begin_vertex>
vEmissive = aEmissive;`,
      );
      shader.fragmentShader = shader.fragmentShader.replace(
        '#include <common>',
        `#include <common>
varying vec3 vEmissive;`,
      );
      shader.fragmentShader = shader.fragmentShader.replace(
        'vec3 totalEmissiveRadiance = emissive;',
        'vec3 totalEmissiveRadiance = emissive + vEmissive;',
      );
    };

    this.leftMesh = new THREE.Mesh(this.left.pial, this.material);
    this.leftMesh.name = 'brain-left';
    this.rightMesh = new THREE.Mesh(this.right.pial, this.material);
    this.rightMesh.name = 'brain-right';

    return this.meshSet;
  }

  private buildHemisphere(
    pial: BrainMeshData,
    inflated: BrainMeshData,
  ): HemiGeometries {
    const pialPositions = flattenVertices(pial.vertices);
    const inflatedPositions = flattenVertices(inflated.vertices);
    const sulcalDepth = Float32Array.from(pial.sulcalDepth);
    const faces = flattenFaces(pial.faces);

    const F = faces.length / 3;

    // Non-indexed face positions for both surfaces.
    const pialFacePositions = expandFacePositions(pialPositions, faces);
    const inflatedFacePositions = expandFacePositions(inflatedPositions, faces);

    // Vertex indices: for each non-indexed slot, which original vertex
    // it came from. Identical to the flat face buffer.
    const vertexIndices = new Uint32Array(faces);

    // Per-face sulcal grey palettes.
    const sulcalFaceColorsPial = buildPialFaceColors(sulcalDepth, faces);
    const sulcalFaceColorsInflated = buildInflatedFaceColors(sulcalDepth, faces);
    const currentSulcalFaceColors = new Float32Array(sulcalFaceColorsPial);

    // Per-face emissive buffer for the activation glow. Starts as zero
    // (no glow) and is written by ActivationMapper.
    const emissive = new Float32Array(F * 9);

    // Build the pial geometry (the one initially rendered). Only the
    // pial geom gets the emissive attribute since only it is rendered.
    const pialGeom = this.buildFaceGeometry(
      pialFacePositions,
      currentSulcalFaceColors,
      emissive,
    );

    // Build the inflated geometry. Even though only one is on the mesh
    // at a time, the InflateManager morphs the active geometry's
    // position buffer in place; this second geometry is kept for the
    // morph animation source-of-truth.
    const inflatedGeom = this.buildFaceGeometry(
      inflatedFacePositions,
      sulcalFaceColorsInflated,
    );

    return {
      pial: pialGeom,
      inflated: inflatedGeom,
      pialFacePositions,
      inflatedFacePositions,
      vertexIndices,
      sulcalFaceColorsPial,
      sulcalFaceColorsInflated,
      currentSulcalFaceColors,
      sulcalDepth,
      faces,
      emissive,
      faceCount: F,
    };
  }

  private buildFaceGeometry(
    facePositions: Float32Array,
    faceColors: Float32Array,
    emissive?: Float32Array,
  ): THREE.BufferGeometry {
    const geom = new THREE.BufferGeometry();
    // Slice the position buffer so InflateManager's in-place writes do
    // not alias the cached source buffer.
    geom.setAttribute('position', new THREE.BufferAttribute(facePositions.slice(), 3));
    geom.setAttribute('color', new THREE.BufferAttribute(faceColors, 3));
    if (emissive) {
      // Custom attribute consumed by the onBeforeCompile shader patch
      // to add per-face self-illumination on activated polygons.
      geom.setAttribute('aEmissive', new THREE.BufferAttribute(emissive, 3));
    }
    // Non-indexed: computeVertexNormals assigns the face normal to each
    // of the 3 face vertices, giving free flat per-face normals.
    geom.computeVertexNormals();
    geom.computeBoundingBox();
    geom.computeBoundingSphere();
    return geom;
  }

  /**
   * Rescale the cached inflated face positions so their combined bbox
   * exactly matches the combined pial bbox. Per-axis scale + recenter
   * around the pial center, applied in place to both hemispheres'
   * inflatedFacePositions arrays. The morph in InflateManager reads
   * directly from these arrays so the rescale takes effect immediately.
   */
  private matchInflatedToPialSize(): void {
    if (!this.left || !this.right) return;

    const pialBbox = this.combinedBufferBbox([
      this.left.pialFacePositions,
      this.right.pialFacePositions,
    ]);
    const inflBbox = this.combinedBufferBbox([
      this.left.inflatedFacePositions,
      this.right.inflatedFacePositions,
    ]);

    const pialSize = new THREE.Vector3().subVectors(pialBbox.max, pialBbox.min);
    const inflSize = new THREE.Vector3().subVectors(inflBbox.max, inflBbox.min);
    if (inflSize.x === 0 || inflSize.y === 0 || inflSize.z === 0) return;

    const sx = pialSize.x / inflSize.x;
    const sy = pialSize.y / inflSize.y;
    const sz = pialSize.z / inflSize.z;

    const pialCenter = new THREE.Vector3()
      .addVectors(pialBbox.min, pialBbox.max)
      .multiplyScalar(0.5);
    const inflCenter = new THREE.Vector3()
      .addVectors(inflBbox.min, inflBbox.max)
      .multiplyScalar(0.5);

    // newPos = (oldPos - inflCenter) * scale + pialCenter
    for (const hemi of [this.left, this.right]) {
      const arr = hemi.inflatedFacePositions;
      for (let i = 0; i < arr.length; i += 3) {
        arr[i + 0] = (arr[i + 0] - inflCenter.x) * sx + pialCenter.x;
        arr[i + 1] = (arr[i + 1] - inflCenter.y) * sy + pialCenter.y;
        arr[i + 2] = (arr[i + 2] - inflCenter.z) * sz + pialCenter.z;
      }
    }
  }

  private combinedBufferBbox(buffers: Float32Array[]): THREE.Box3 {
    const box = new THREE.Box3();
    box.makeEmpty();
    const v = new THREE.Vector3();
    for (const buf of buffers) {
      for (let i = 0; i < buf.length; i += 3) {
        v.set(buf[i], buf[i + 1], buf[i + 2]);
        box.expandByPoint(v);
      }
    }
    return box;
  }

  private hemi(side: 'left' | 'right'): HemiGeometries {
    const h = side === 'left' ? this.left : this.right;
    if (!h) throw new Error('MeshLoader: load() not called yet');
    return h;
  }

  getLeftMesh(): THREE.Mesh {
    if (!this.leftMesh) throw new Error('MeshLoader: load() not called yet');
    return this.leftMesh;
  }

  getRightMesh(): THREE.Mesh {
    if (!this.rightMesh) throw new Error('MeshLoader: load() not called yet');
    return this.rightMesh;
  }

  getMeshSet(): BrainMeshSet {
    if (!this.meshSet) throw new Error('MeshLoader: load() not called yet');
    return this.meshSet;
  }

  getPialFacePositions(side: 'left' | 'right'): Float32Array {
    return this.hemi(side).pialFacePositions;
  }

  getInflatedFacePositions(side: 'left' | 'right'): Float32Array {
    return this.hemi(side).inflatedFacePositions;
  }

  getVertexIndices(side: 'left' | 'right'): Uint32Array {
    return this.hemi(side).vertexIndices;
  }

  getFaceCount(side: 'left' | 'right'): number {
    return this.hemi(side).faceCount;
  }

  getSulcalDepth(side: 'left' | 'right'): Float32Array {
    return this.hemi(side).sulcalDepth;
  }

  /**
   * Returns the CURRENT per-face sulcal color buffer (length F*9).
   * The InflateManager triggers updateMorphSulcal() during the morph
   * to lerp between the pial and inflated palettes.
   */
  getSulcalColors(side: 'left' | 'right'): Float32Array {
    return this.hemi(side).currentSulcalFaceColors;
  }

  /**
   * Blend pial <-> inflated sulcal palettes into currentSulcalFaceColors
   * for both hemispheres. `t` follows InflateManager's morph parameter
   * (0 = fully pial, 1 = fully inflated).
   */
  updateMorphSulcal(t: number): void {
    const k = t < 0 ? 0 : t > 1 ? 1 : t;
    for (const h of [this.left, this.right]) {
      if (!h) continue;
      const pial = h.sulcalFaceColorsPial;
      const infl = h.sulcalFaceColorsInflated;
      const cur = h.currentSulcalFaceColors;
      for (let i = 0; i < cur.length; i++) {
        cur[i] = pial[i] + (infl[i] - pial[i]) * k;
      }
    }
  }

  /**
   * Recompute per-face flat normals for a mesh whose position buffer
   * has been updated in place (e.g. by InflateManager after a morph).
   * On non-indexed geometry computeVertexNormals assigns each face's
   * cross-product normal to all three of its vertex slots, which is
   * exactly the fully-flat polygonal look we want.
   *
   * Method name is kept ("smooth") because InflateManager calls it by
   * that name -- but the implementation is now flat per-face.
   */
  recomputeSmoothNormals(mesh: THREE.Mesh, _side: 'left' | 'right'): void {
    mesh.geometry.computeVertexNormals();
  }

  /** Combined bounding box over both hemispheres in current geometry. */
  getCombinedBoundingBox(): THREE.Box3 {
    const box = new THREE.Box3();
    if (this.leftMesh) box.expandByObject(this.leftMesh);
    if (this.rightMesh) box.expandByObject(this.rightMesh);
    return box;
  }

  dispose(): void {
    if (this.left) {
      this.left.pial.dispose();
      this.left.inflated.dispose();
    }
    if (this.right) {
      this.right.pial.dispose();
      this.right.inflated.dispose();
    }
    if (this.material) this.material.dispose();
    this.left = null;
    this.right = null;
    this.leftMesh = null;
    this.rightMesh = null;
    this.material = null;
    this.meshSet = null;
  }
}
