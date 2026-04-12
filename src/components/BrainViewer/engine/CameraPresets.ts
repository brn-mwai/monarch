// ============================================================
// CameraPresets.ts -- animated transitions between standard views
// ============================================================
//
// fsaverage5 axis convention (in mm):
//   X = lateral       (negative = left,    positive = right)
//   Y = anteroposterior (negative = posterior, positive = anterior)
//   Z = inferosuperior  (negative = inferior,  positive = superior)
//
// Three.js defaults camera.up to (0, 1, 0). With our brain that would
// treat anatomical anterior as screen-up and rotate everything 90 degrees
// from the standard neuroimaging convention. Each preset therefore declares
// its own up vector explicitly:
//
//   - Lateral / medial / anterior / posterior views use up = (0, 0, 1)
//     (anatomical superior is screen-up).
//   - Dorsal / ventral views look along the Z axis where (0, 0, 1) is
//     parallel to the view direction; they use up = (0, 1, 0) so that
//     anatomical anterior is screen-up.
// ============================================================

import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

import type { ViewPreset } from '../types';

const DURATION_MS = 800;

interface Preset {
  position: THREE.Vector3;
  target: THREE.Vector3;
  up: THREE.Vector3;
}

function easeInOutCubic(t: number): number {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

const Z_UP = new THREE.Vector3(0, 0, 1);
const Y_UP = new THREE.Vector3(0, 1, 0);

/**
 * Compute 8 presets framed on a given bounding box. Pass the FITTED
 * head bbox here -- camera distance is derived from the head radius
 * and the target is the head center, so the head silhouette sits
 * centered in the viewport with the brain inside it.
 */
export function computePresets(bbox: THREE.Box3): Record<ViewPreset, Preset> {
  const center = bbox.getCenter(new THREE.Vector3());
  const size = bbox.getSize(new THREE.Vector3());
  const radius = Math.max(size.x, size.y, size.z) * 0.5;
  // Distance multiplier: head fills ~70% of the viewport with comfortable
  // margin so chin + crown + ears never clip on any preset.
  const d = radius * 2.8;

  return {
    // ----- Lateral views (camera on the X axis, up = +Z) -----
    left: {
      position: new THREE.Vector3(center.x - d, center.y, center.z),
      target: center.clone(),
      up: Z_UP.clone(),
    },
    right: {
      position: new THREE.Vector3(center.x + d, center.y, center.z),
      target: center.clone(),
      up: Z_UP.clone(),
    },

    // ----- Medial views: camera sits just on the opposite side of the
    //       midline and looks toward the hemisphere of interest. Useful
    //       when the brain is in "open" mode and the medial wall is
    //       exposed.
    medial_left: {
      position: new THREE.Vector3(center.x + d * 0.5, center.y, center.z),
      target: new THREE.Vector3(center.x - size.x * 0.3, center.y, center.z),
      up: Z_UP.clone(),
    },
    medial_right: {
      position: new THREE.Vector3(center.x - d * 0.5, center.y, center.z),
      target: new THREE.Vector3(center.x + size.x * 0.3, center.y, center.z),
      up: Z_UP.clone(),
    },

    // ----- Dorsal / ventral (camera on the Z axis, up = +Y) -----
    dorsal: {
      position: new THREE.Vector3(center.x, center.y, center.z + d),
      target: center.clone(),
      up: Y_UP.clone(),
    },
    ventral: {
      position: new THREE.Vector3(center.x, center.y, center.z - d),
      target: center.clone(),
      up: Y_UP.clone(),
    },

    // ----- Anterior / posterior (camera on the Y axis, up = +Z) -----
    anterior: {
      position: new THREE.Vector3(center.x, center.y + d, center.z),
      target: center.clone(),
      up: Z_UP.clone(),
    },
    posterior: {
      position: new THREE.Vector3(center.x, center.y - d, center.z),
      target: center.clone(),
      up: Z_UP.clone(),
    },
  };
}

export class CameraPresets {
  private presets: Record<ViewPreset, Preset> | null = null;
  private animating = false;
  private animStart = 0;
  private fromPos = new THREE.Vector3();
  private fromTarget = new THREE.Vector3();
  private fromUp = new THREE.Vector3();
  private toPos = new THREE.Vector3();
  private toTarget = new THREE.Vector3();
  private toUp = new THREE.Vector3();
  private currentView: ViewPreset | null = null;

  constructor(
    private camera: THREE.PerspectiveCamera,
    private controls: OrbitControls,
  ) {}

  setBoundingBox(bbox: THREE.Box3): void {
    this.presets = computePresets(bbox);
  }

  setView(preset: ViewPreset, animate = true): void {
    if (!this.presets) return;
    const target = this.presets[preset];
    if (!target) return;

    if (!animate) {
      this.camera.up.copy(target.up);
      this.camera.position.copy(target.position);
      this.controls.target.copy(target.target);
      this.camera.lookAt(target.target);
      this.controls.update();
      this.currentView = preset;
      return;
    }

    this.fromPos.copy(this.camera.position);
    this.fromTarget.copy(this.controls.target);
    this.fromUp.copy(this.camera.up);
    this.toPos.copy(target.position);
    this.toTarget.copy(target.target);
    this.toUp.copy(target.up);
    this.animStart = performance.now();
    this.animating = true;
    this.currentView = preset;
  }

  getCurrentView(): ViewPreset | null {
    return this.currentView;
  }

  update(_deltaTime: number): void {
    if (!this.animating) return;
    const elapsed = performance.now() - this.animStart;
    const t = Math.min(1, elapsed / DURATION_MS);
    const k = easeInOutCubic(t);
    this.camera.position.lerpVectors(this.fromPos, this.toPos, k);
    this.controls.target.lerpVectors(this.fromTarget, this.toTarget, k);
    // Slerp-ish lerp for the up vector -- linear lerp + normalize is fine
    // for 90-degree transitions and avoids the cost of quaternion math.
    this.camera.up
      .copy(this.fromUp)
      .lerp(this.toUp, k)
      .normalize();
    this.controls.update();
    if (t >= 1) this.animating = false;
  }
}
