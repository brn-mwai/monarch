// ============================================================
// HemisphereManager.ts -- open/close hemisphere "book" view
// ============================================================
//
// "Close": both hemispheres at their natural pose (rotation 0,
//          position 0). They sit side-by-side at the midline, just
//          like the raw fsaverage5 mesh data.
//
// "Open": each hemisphere is rotated 90 degrees around the Z axis so
//         that its medial wall (originally facing +/-X) now faces -Y
//         (toward a posterior camera), and translated outward along X
//         so the two medial walls sit side-by-side rather than on top
//         of each other. This is the standard "book" view used in
//         neuroimaging to expose the medial cortex.
//
// Both rotation and position are animated together via a single
// progress parameter t in [0, 1]; t = 1 means fully open. The Three.js
// mesh transform is `position * rotation * scale`, so we just lerp the
// rotation Z angle and the position X (and a small Y nudge so the
// medial walls sit at y = 0 -- their natural plane after rotation).
// ============================================================

import * as THREE from 'three';

const SEPARATION_X = 105; // mm of X translation per hemisphere when open
const DURATION_MS = 700;

// Final pose for each hemisphere when fully open. The Y nudge undoes the
// effect of the rotation pivot being at the world origin instead of the
// hemisphere's own center -- after rotating around Z by +/- pi/2, the
// originally-medial X=0 plane lies along Y = 0, and the rest of the
// hemisphere extends in +Y. Pulling everything by -SEPARATION_Y centers
// the rotated hemispheres on the world Y axis.
const SEPARATION_Y = 35;

interface Pose {
  positionX: number;
  positionY: number;
  rotationZ: number;
}

const POSE_OPEN_LEFT: Pose = {
  positionX: -SEPARATION_X,
  positionY: -SEPARATION_Y,
  rotationZ: -Math.PI / 2,
};

const POSE_OPEN_RIGHT: Pose = {
  positionX: SEPARATION_X,
  positionY: -SEPARATION_Y,
  rotationZ: Math.PI / 2,
};

function easeInOutCubic(t: number): number {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

function applyPose(mesh: THREE.Mesh, pose: Pose): void {
  mesh.position.x = pose.positionX;
  mesh.position.y = pose.positionY;
  mesh.rotation.z = pose.rotationZ;
}

export class HemisphereManager {
  private open = false;
  private animating = false;
  private animStart = 0;
  private fromLeft: Pose = { positionX: 0, positionY: 0, rotationZ: 0 };
  private fromRight: Pose = { positionX: 0, positionY: 0, rotationZ: 0 };
  private toLeft: Pose = { positionX: 0, positionY: 0, rotationZ: 0 };
  private toRight: Pose = { positionX: 0, positionY: 0, rotationZ: 0 };

  // Snapshotted at construction time. Used as the "closed" target so
  // closing the brain returns each hemisphere to whatever pose it had
  // when this manager was created -- preserving the brain's tilt /
  // lift / forward shift / lateral shift set up by BrainEngine.
  private readonly restLeft: Pose;
  private readonly restRight: Pose;

  constructor(
    private leftMesh: THREE.Mesh,
    private rightMesh: THREE.Mesh,
  ) {
    this.restLeft = {
      positionX: leftMesh.position.x,
      positionY: leftMesh.position.y,
      rotationZ: leftMesh.rotation.z,
    };
    this.restRight = {
      positionX: rightMesh.position.x,
      positionY: rightMesh.position.y,
      rotationZ: rightMesh.rotation.z,
    };
  }

  openHemispheres(): void {
    this.startAnimation(true);
  }

  closeHemispheres(): void {
    this.startAnimation(false);
  }

  toggle(): void {
    this.startAnimation(!this.open);
  }

  isOpen(): boolean {
    return this.open;
  }

  isAnimating(): boolean {
    return this.animating;
  }

  private startAnimation(target: boolean): void {
    this.open = target;
    this.fromLeft.positionX = this.leftMesh.position.x;
    this.fromLeft.positionY = this.leftMesh.position.y;
    this.fromLeft.rotationZ = this.leftMesh.rotation.z;
    this.fromRight.positionX = this.rightMesh.position.x;
    this.fromRight.positionY = this.rightMesh.position.y;
    this.fromRight.rotationZ = this.rightMesh.rotation.z;

    if (target) {
      this.toLeft = { ...POSE_OPEN_LEFT };
      this.toRight = { ...POSE_OPEN_RIGHT };
    } else {
      this.toLeft = { ...this.restLeft };
      this.toRight = { ...this.restRight };
    }

    this.animStart = performance.now();
    this.animating = true;
  }

  update(_deltaTime: number): void {
    if (!this.animating) return;
    const elapsed = performance.now() - this.animStart;
    const t = Math.min(1, elapsed / DURATION_MS);
    const k = easeInOutCubic(t);

    applyPose(this.leftMesh, {
      positionX: lerp(this.fromLeft.positionX, this.toLeft.positionX, k),
      positionY: lerp(this.fromLeft.positionY, this.toLeft.positionY, k),
      rotationZ: lerp(this.fromLeft.rotationZ, this.toLeft.rotationZ, k),
    });
    applyPose(this.rightMesh, {
      positionX: lerp(this.fromRight.positionX, this.toRight.positionX, k),
      positionY: lerp(this.fromRight.positionY, this.toRight.positionY, k),
      rotationZ: lerp(this.fromRight.rotationZ, this.toRight.rotationZ, k),
    });

    if (t >= 1) this.animating = false;
  }
}
