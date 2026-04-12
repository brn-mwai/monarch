// ============================================================
// HeadShell.ts -- LeePerrySmith head silhouette overlay
// ============================================================
//
// Loads /models/head.glb (the LeePerrySmith head from the three.js
// examples) and fits it around the actual brain bounding box. Fitting
// is driven by RUNTIME MEASUREMENTS, not hardcoded constants:
//
//   1. loadHead() loads the GLB, swaps materials, and bakes the Y-up ->
//      Z-up orientation matrix into each mesh geometry. NO scale or
//      position is applied here.
//   2. ready() resolves once the GLB is loaded. The engine awaits this
//      before computing the brain bbox.
//   3. fitToActualBrain(brainBbox) is called by the engine. It measures
//      the native head bbox, computes per-axis scale factors so the
//      head encloses the brain on every axis with a margin, then anchors
//      the cranium top a fixed distance above the brain top.
//   4. The vertical fade range is updated to taper the bottom of the
//      head smoothly into the visible neck below the chin.
//
// Per-axis margins encode the brain : head ratio. The brain fills:
//   X (width):  ~89% of head  -> head = brain * 1.12
//   Y (depth):  ~87% of head  -> head = brain * 1.15
//   Z (height): ~55% of head  -> head = brain * 1.80 (face/jaw extends below)
// ============================================================

import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

const HEAD_URL = '/models/head.glb';

// "Needed" multipliers used to derive a UNIFORM scale.
//
// We compute, per axis, how much the head must be enlarged so the brain
// fits inside it (including generous margin for concave regions like
// temples, narrow forehead, short cranium vault). Then we take the MAX
// of the three and apply it uniformly to every axis.
//
// Uniform scaling preserves the LeePerrySmith model's natural face/jaw/
// cranium proportions. Per-axis scaling distorts the head into an
// inhuman shape. At 13% opacity an oversized silhouette is invisible;
// a distorted head is immediately obvious.
const NEEDED_X = 1.55; // brain width * 1.55 must fit head native width  (temples)
const NEEDED_Y = 1.55; // brain depth * 1.55 must fit head native depth  (occipital)
const NEEDED_Z = 1.70; // brain height * 1.70 must fit head native height (face/jaw below)

// Cranium top sits CRANIUM_GAP mm above the brain top (max.z).
const CRANIUM_GAP = 18;

// Y center offset: head bbox center is shifted forward of brain center
// by this much. Small value keeps the back of the skull behind the
// occipital lobe; large values would expose the back of the brain.
const Y_ANTERIOR_SHIFT = 5;

// LeePerrySmith.glb is Y-up with the face along +Z. fsaverage5 is Z-up
// with the face along +Y. The matrix below maps:
//   model +X -> fs -X    (mirrors L/R; head is roughly symmetric)
//   model +Y -> fs +Z    (crown -> superior)
//   model +Z -> fs +Y    (face -> anterior)
// Determinant = +1, proper rotation.
const HEAD_ORIENTATION_MATRIX = new THREE.Matrix4().set(
  -1, 0, 0, 0,
  0, 0, 1, 0,
  0, 1, 0, 0,
  0, 0, 0, 1,
);

// Smooth fade duration for show/hide on Open mode toggle.
const FADE_MS = 600;
// Target opacity when fully visible.
const PEAK_OPACITY = 0.12;

export class HeadShell {
  private group: THREE.Group;
  private material: THREE.MeshStandardMaterial;
  private loadedRoot: THREE.Group | null = null;
  private disposeBag: { dispose: () => void }[] = [];
  private loadPromise: Promise<void>;

  // Vertical fade uniforms — updated after fitToActualBrain so the fade
  // tracks the actual fitted head bottom.
  private fadeUniforms = {
    uFadeTop: { value: -110 },
    uFadeBottom: { value: -160 },
  };

  // Fade state for show/hide animation.
  private currentOpacity = PEAK_OPACITY;
  private targetOpacity = PEAK_OPACITY;
  private fadeFrom = PEAK_OPACITY;
  private fadeStart = 0;
  private fading = false;

  constructor() {
    this.material = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: PEAK_OPACITY,
      roughness: 0.6,
      metalness: 0.0,
      // FrontSide so back-facing polygons (the inside of the head) never
      // render -- prevents internal mesh artifacts inside the silhouette.
      side: THREE.FrontSide,
      depthWrite: false,
    });
    this.disposeBag.push(this.material);

    // Inject a vertical fade in the fragment shader so the bottom of
    // the model (neck/torso stub) tapers smoothly to alpha = 0.
    this.material.onBeforeCompile = (shader) => {
      shader.uniforms.uFadeTop = this.fadeUniforms.uFadeTop;
      shader.uniforms.uFadeBottom = this.fadeUniforms.uFadeBottom;

      shader.vertexShader = shader.vertexShader.replace(
        '#include <common>',
        `#include <common>
varying float vHeadWorldZ;`,
      );
      shader.vertexShader = shader.vertexShader.replace(
        '#include <begin_vertex>',
        `#include <begin_vertex>
vHeadWorldZ = (modelMatrix * vec4(transformed, 1.0)).z;`,
      );

      shader.fragmentShader = shader.fragmentShader.replace(
        '#include <common>',
        `#include <common>
varying float vHeadWorldZ;
uniform float uFadeTop;
uniform float uFadeBottom;`,
      );
      shader.fragmentShader = shader.fragmentShader.replace(
        'vec4 diffuseColor = vec4( diffuse, opacity );',
        `float headFade = clamp((vHeadWorldZ - uFadeBottom) / (uFadeTop - uFadeBottom), 0.0, 1.0);
vec4 diffuseColor = vec4( diffuse, opacity * headFade );`,
      );
    };

    this.group = new THREE.Group();
    this.group.name = 'head-shell-group';
    this.group.renderOrder = 2;

    // Kick off loading immediately. The engine MUST await ready() and
    // then call fitToActualBrain(brainBbox) before the head is sized.
    this.loadPromise = this.loadHead();
  }

  /** Resolves once the GLB is loaded and oriented (but not yet fitted). */
  ready(): Promise<void> {
    return this.loadPromise;
  }

  fadeOut(): void {
    this.startFade(0);
  }

  fadeIn(): void {
    this.startFade(PEAK_OPACITY);
  }

  private startFade(target: number): void {
    if (Math.abs(this.currentOpacity - target) < 1e-4) return;
    this.targetOpacity = target;
    this.fadeFrom = this.currentOpacity;
    this.fadeStart = performance.now();
    this.fading = true;
    this.group.visible = true;
  }

  /** Call once per frame from the engine animate loop. */
  update(_dt: number): void {
    if (!this.fading) return;
    const elapsed = performance.now() - this.fadeStart;
    const t = Math.min(1, elapsed / FADE_MS);
    const k = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    this.currentOpacity = this.fadeFrom + (this.targetOpacity - this.fadeFrom) * k;
    this.material.opacity = this.currentOpacity;
    if (t >= 1) {
      this.fading = false;
      if (this.currentOpacity <= 0.001) {
        this.group.visible = false;
      }
    }
  }

  private async loadHead(): Promise<void> {
    const loader = new GLTFLoader();
    try {
      const gltf = await loader.loadAsync(HEAD_URL);
      this.applyMaterial(gltf.scene);

      // Bake the orientation rotation into each mesh's geometry. After
      // this point the geometry is in fs (Z-up, +Y-anterior) coordinates
      // and any further scaling is just per-axis stretch in fs space.
      gltf.scene.traverse((obj) => {
        const mesh = obj as THREE.Mesh;
        if (mesh.isMesh && mesh.geometry) {
          mesh.geometry.applyMatrix4(HEAD_ORIENTATION_MATRIX);
        }
      });
      gltf.scene.updateMatrixWorld(true);

      gltf.scene.name = 'head-shell-mesh';
      this.loadedRoot = gltf.scene;
      this.group.add(gltf.scene);
    } catch (err) {
      console.warn('HeadShell: failed to load /models/head.glb', err);
    }
  }

  /** Replace every mesh material with our shared transparent one. */
  private applyMaterial(root: THREE.Object3D): void {
    root.traverse((obj) => {
      if ((obj as THREE.Mesh).isMesh) {
        const mesh = obj as THREE.Mesh;
        mesh.material = this.material;
        mesh.renderOrder = 2;
        if (mesh.geometry) this.disposeBag.push(mesh.geometry);
      }
    });
  }

  /**
   * Fit the head silhouette around the ACTUAL brain bounding box.
   *
   * Algorithm:
   *   1. Reset the loaded root to identity transform.
   *   2. Measure its native (oriented) bbox.
   *   3. Compute target head dims = brain dims * per-axis margins.
   *   4. Apply scale = target / native on each axis.
   *   5. Re-measure scaled bbox; offset so cranium top is CRANIUM_GAP
   *      above brain top, X centered on brain midline, Y slightly
   *      anterior of brain center.
   *   6. Verify enclosure on all 6 sides; warn if any side is violated.
   *   7. Update the vertical fade uniforms so the bottom of the head
   *      tapers cleanly into transparency below the visible neck.
   */
  fitToActualBrain(brainBbox: THREE.Box3): void {
    if (!this.loadedRoot) {
      console.warn('HeadShell.fitToActualBrain: head not loaded yet');
      return;
    }

    // 1. Reset transform so measurements start from native oriented size.
    this.loadedRoot.position.set(0, 0, 0);
    this.loadedRoot.scale.set(1, 1, 1);
    this.loadedRoot.updateMatrixWorld(true);

    // 2. Measure native head bbox (after orientation, before scaling).
    const nativeHeadBbox = new THREE.Box3().setFromObject(this.loadedRoot);
    const nativeHeadSize = nativeHeadBbox.getSize(new THREE.Vector3());
    if (
      nativeHeadSize.x === 0 ||
      nativeHeadSize.y === 0 ||
      nativeHeadSize.z === 0
    ) {
      console.warn('HeadShell: native head bbox has zero extent, cannot fit');
      return;
    }

    const brainSize = brainBbox.getSize(new THREE.Vector3());
    const brainCenter = brainBbox.getCenter(new THREE.Vector3());

    // 3. Compute the per-axis enlargement factor needed to clear the
    //    brain (including concavity margin), then take the MAX so a
    //    single uniform scale enlarges every axis enough to enclose
    //    the brain. This preserves the head's natural proportions.
    const neededX = (brainSize.x * NEEDED_X) / nativeHeadSize.x;
    const neededY = (brainSize.y * NEEDED_Y) / nativeHeadSize.y;
    const neededZ = (brainSize.z * NEEDED_Z) / nativeHeadSize.z;
    const uniformScale = Math.max(neededX, neededY, neededZ);

    // 4. Apply uniform scale.
    this.loadedRoot.scale.setScalar(uniformScale);
    this.loadedRoot.updateMatrixWorld(true);

    // 5. Re-measure scaled bbox to compute the world-space offset needed
    //    to anchor the cranium top above the brain top.
    const scaledHeadBbox = new THREE.Box3().setFromObject(this.loadedRoot);
    const scaledHeadCenter = scaledHeadBbox.getCenter(new THREE.Vector3());

    const xOffset = brainCenter.x - scaledHeadCenter.x;
    const yOffset = (brainCenter.y + Y_ANTERIOR_SHIFT) - scaledHeadCenter.y;
    const zOffset = (brainBbox.max.z + CRANIUM_GAP) - scaledHeadBbox.max.z;

    this.loadedRoot.position.set(xOffset, yOffset, zOffset);
    this.loadedRoot.updateMatrixWorld(true);

    // 6. Verify enclosure programmatically. ALL six checks must pass;
    //    if any fail, the corresponding margin needs to be increased.
    const finalHeadBbox = new THREE.Box3().setFromObject(this.loadedRoot);
    const f = (v: number): string => v.toFixed(1);
    const enclX0 = finalHeadBbox.min.x < brainBbox.min.x;
    const enclX1 = finalHeadBbox.max.x > brainBbox.max.x;
    const enclY0 = finalHeadBbox.min.y < brainBbox.min.y;
    const enclY1 = finalHeadBbox.max.y > brainBbox.max.y;
    const enclZ0 = finalHeadBbox.min.z < brainBbox.min.z;
    const enclZ1 = finalHeadBbox.max.z > brainBbox.max.z;

    // eslint-disable-next-line no-console
    console.log('[HeadShell] === BRAIN BBOX ===');
    // eslint-disable-next-line no-console
    console.log('  min:', brainBbox.min.toArray().map(f));
    // eslint-disable-next-line no-console
    console.log('  max:', brainBbox.max.toArray().map(f));
    // eslint-disable-next-line no-console
    console.log('  size:', brainSize.toArray().map(f));
    // eslint-disable-next-line no-console
    console.log('[HeadShell] === FINAL HEAD BBOX ===');
    // eslint-disable-next-line no-console
    console.log('  min:', finalHeadBbox.min.toArray().map(f));
    // eslint-disable-next-line no-console
    console.log('  max:', finalHeadBbox.max.toArray().map(f));
    // eslint-disable-next-line no-console
    console.log('  size:', finalHeadBbox.getSize(new THREE.Vector3()).toArray().map(f));
    // eslint-disable-next-line no-console
    console.log('[HeadShell] enclosure x.min/max:', enclX0, enclX1);
    // eslint-disable-next-line no-console
    console.log('[HeadShell] enclosure y.min/max:', enclY0, enclY1);
    // eslint-disable-next-line no-console
    console.log('[HeadShell] enclosure z.min/max:', enclZ0, enclZ1);
    if (!(enclX0 && enclX1 && enclY0 && enclY1 && enclZ0 && enclZ1)) {
      // eslint-disable-next-line no-console
      console.warn('[HeadShell] WARNING: brain pokes outside head silhouette');
    }

    // 7. Update vertical fade range to taper smoothly at the actual
    //    fitted head bottom. Visible above (brain.min.z - 50), fully
    //    transparent at the head's actual bottom. This gives a clean
    //    visible-neck region between the chin and the bottom edge.
    this.fadeUniforms.uFadeTop.value = brainBbox.min.z - 50;
    this.fadeUniforms.uFadeBottom.value = finalHeadBbox.min.z + 5;
  }

  /** World-space bbox of the currently fitted head. */
  getFittedBbox(): THREE.Box3 {
    return new THREE.Box3().setFromObject(this.group);
  }

  get object3d(): THREE.Group {
    return this.group;
  }

  setVisible(visible: boolean): void {
    this.group.visible = visible;
  }

  dispose(): void {
    for (const d of this.disposeBag) d.dispose();
    this.disposeBag = [];
    if (this.loadedRoot) {
      this.group.remove(this.loadedRoot);
      this.loadedRoot = null;
    }
    if (this.group.parent) this.group.parent.remove(this.group);
  }
}
