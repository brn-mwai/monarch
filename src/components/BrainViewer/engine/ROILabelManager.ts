// ============================================================
// ROILabelManager.ts -- CSS2D labels for HCP ROI regions
// ============================================================
//
// Uses THREE.CSS2DRenderer so labels stay DOM elements that can be styled
// with Tailwind and receive click events. Positions are approximate
// centroids on the fsaverage5 pial surface -- good enough for a guide,
// not medically precise.
// ============================================================

import * as THREE from 'three';
import { CSS2DObject, CSS2DRenderer } from 'three/examples/jsm/renderers/CSS2DRenderer.js';

import type { ROILabel } from '../types';

/**
 * Approximate centroid positions in fsaverage5 mm coords.
 * These were eyeballed on the standard brain; refine with HCP parcellation
 * vertex lookups once tribev2 is importable.
 */
const DEFAULT_ROIS: ROILabel[] = [
  // Affective network
  { name: 'OFC', fullName: 'Orbitofrontal Cortex', hemisphere: 'left', position: [-25, 30, -20], system: 'affective' },
  { name: 'OFC', fullName: 'Orbitofrontal Cortex', hemisphere: 'right', position: [25, 30, -20], system: 'affective' },
  { name: 'Insula', fullName: 'Anterior Insular Cortex', hemisphere: 'left', position: [-38, 5, -5], system: 'affective' },
  { name: 'Insula', fullName: 'Anterior Insular Cortex', hemisphere: 'right', position: [38, 5, -5], system: 'affective' },
  { name: 'ACC', fullName: 'Anterior Cingulate (a24/p24)', hemisphere: 'left', position: [-5, 30, 22], system: 'affective' },
  { name: 'ACC', fullName: 'Anterior Cingulate (a24/p24)', hemisphere: 'right', position: [5, 30, 22], system: 'affective' },
  { name: 'TP', fullName: 'Temporal Pole (TGd)', hemisphere: 'left', position: [-40, 10, -35], system: 'affective' },
  { name: 'TP', fullName: 'Temporal Pole (TGd)', hemisphere: 'right', position: [40, 10, -35], system: 'affective' },
  { name: 'ATC', fullName: 'Anterior Temporal Cortex (TE1a/TE1p)', hemisphere: 'left', position: [-55, -10, -20], system: 'affective' },
  { name: 'ATC', fullName: 'Anterior Temporal Cortex (TE1a/TE1p)', hemisphere: 'right', position: [55, -10, -20], system: 'affective' },

  // Deliberative-control network
  { name: 'DLPFC', fullName: 'Dorsolateral Prefrontal (46/9-46v)', hemisphere: 'left', position: [-42, 35, 28], system: 'deliberative' },
  { name: 'DLPFC', fullName: 'Dorsolateral Prefrontal (46/9-46v)', hemisphere: 'right', position: [42, 35, 28], system: 'deliberative' },
  { name: 'VMPFC', fullName: 'Ventromedial Prefrontal (11l/13l)', hemisphere: 'left', position: [-10, 50, -15], system: 'deliberative' },
  { name: 'VMPFC', fullName: 'Ventromedial Prefrontal (11l/13l)', hemisphere: 'right', position: [10, 50, -15], system: 'deliberative' },
  { name: 'FPC', fullName: 'Frontopolar Cortex (10p/10pp)', hemisphere: 'left', position: [-20, 62, 5], system: 'deliberative' },
  { name: 'FPC', fullName: 'Frontopolar Cortex (10p/10pp)', hemisphere: 'right', position: [20, 62, 5], system: 'deliberative' },
  { name: 'dACC', fullName: 'Dorsal Anterior Cingulate (d32/p32)', hemisphere: 'left', position: [-5, 25, 35], system: 'deliberative' },
  { name: 'dACC', fullName: 'Dorsal Anterior Cingulate (d32/p32)', hemisphere: 'right', position: [5, 25, 35], system: 'deliberative' },
];

/**
 * Build the DOM for one ROI label.
 *
 * Layout (relative to the projected 3D anchor point at the wrapper's
 * own (0, 0)):
 *
 *      ┌─────────┐  <- pill (clickable)
 *      │   OFC   │
 *      └────┬────┘
 *           │      <- 18px connector line
 *           ●      <- 6px anchor dot ON the cortex
 *
 * The wrapper is a 0x0 box that CSS2DRenderer centres on the projected
 * vertex centroid. The dot, line, and pill are absolutely positioned
 * relative to that wrapper origin so the dot sits exactly on the brain
 * surface and the pill floats above with a thin leader line connecting
 * the two.
 */
function labelElement(roi: ROILabel): HTMLDivElement {
  const wrapper = document.createElement('div');
  wrapper.style.cssText = [
    'position: absolute',
    'width: 0',
    'height: 0',
    'pointer-events: none',
  ].join(';');

  // Anchor dot - sits ON the cortex at the centroid
  const dot = document.createElement('div');
  dot.style.cssText = [
    'position: absolute',
    'top: -3px',
    'left: -3px',
    'width: 6px',
    'height: 6px',
    'border-radius: 50%',
    'background: rgba(255, 255, 255, 0.95)',
    'border: 1px solid rgba(0, 0, 0, 0.6)',
    'box-shadow: 0 0 6px rgba(255, 255, 255, 0.4)',
    'pointer-events: none',
  ].join(';');

  // Connector line - 18px tall, 1px wide, going up from the dot
  const line = document.createElement('div');
  line.style.cssText = [
    'position: absolute',
    'top: -21px',
    'left: -0.5px',
    'width: 1px',
    'height: 18px',
    'background: rgba(255, 255, 255, 0.55)',
    'pointer-events: none',
  ].join(';');

  // Pill label - clickable, sits above the line
  const pill = document.createElement('div');
  pill.textContent = roi.name;
  pill.title = roi.fullName;
  pill.style.cssText = [
    'position: absolute',
    'top: -21px',
    'left: 0',
    'transform: translate(-50%, -100%)',
    'color: #ffffff',
    'font-family: ui-monospace, SFMono-Regular, Menlo, monospace',
    'font-size: 11px',
    'font-weight: 600',
    'background: rgba(0, 0, 0, 0.82)',
    'border: 1px solid rgba(255, 255, 255, 0.4)',
    'border-radius: 999px',
    'padding: 3px 10px',
    'cursor: pointer',
    'pointer-events: auto',
    'white-space: nowrap',
    'user-select: none',
    'box-shadow: 0 2px 12px rgba(0, 0, 0, 0.6)',
    'backdrop-filter: blur(4px)',
    'transition: border-color 120ms ease, background 120ms ease',
  ].join(';');
  pill.addEventListener('mouseenter', () => {
    pill.style.borderColor = 'rgba(255, 255, 255, 0.9)';
    pill.style.background = 'rgba(0, 0, 0, 0.95)';
  });
  pill.addEventListener('mouseleave', () => {
    pill.style.borderColor = 'rgba(255, 255, 255, 0.4)';
    pill.style.background = 'rgba(0, 0, 0, 0.82)';
  });

  wrapper.appendChild(dot);
  wrapper.appendChild(line);
  wrapper.appendChild(pill);

  // Expose the pill as the click target via a data attribute, so the
  // outer click handler in buildLabels() finds it instead of the
  // wrapper (the wrapper itself has pointer-events: none).
  (wrapper as HTMLDivElement & { _pill?: HTMLDivElement })._pill = pill;

  return wrapper;
}

export class ROILabelManager {
  private labelRenderer: CSS2DRenderer;
  private group: THREE.Group;
  private objects: CSS2DObject[] = [];
  private visible = false;
  private onClick?: (roi: ROILabel) => void;

  // Scratch vectors reused per render tick to avoid allocations.
  private _normal = new THREE.Vector3();
  private _toCamera = new THREE.Vector3();
  // The labels are anchored in fsaverage5 mm coords roughly centred
  // on the origin; using (0, 0, 0) as the brain centre gives a good
  // outward-normal approximation for the visibility test.
  private _brainCenter = new THREE.Vector3(0, -10, 10);

  constructor(
    private scene: THREE.Scene,
    private camera: THREE.Camera,
    container: HTMLElement,
  ) {
    this.labelRenderer = new CSS2DRenderer();
    const rect = container.getBoundingClientRect();
    this.labelRenderer.setSize(rect.width, rect.height);
    const el = this.labelRenderer.domElement;
    el.style.position = 'absolute';
    el.style.top = '0';
    el.style.left = '0';
    // Sit above the WebGL canvas (z-index auto) so the projected
    // labels are visible, but below the React-managed toggle button
    // and ROIDescriptionPanel (z-30).
    el.style.zIndex = '20';
    el.style.pointerEvents = 'none';
    container.appendChild(el);

    this.group = new THREE.Group();
    this.group.name = 'roi-labels';
    this.group.visible = false;
    this.scene.add(this.group);

    this.buildLabels();
  }

  setOnClick(cb: (roi: ROILabel) => void): void {
    this.onClick = cb;
  }

  private buildLabels(): void {
    for (const roi of DEFAULT_ROIS) {
      const el = labelElement(roi);
      // The wrapper has pointer-events: none; the click handler must
      // attach to the pill child (which has pointer-events: auto).
      const pill = (el as HTMLDivElement & { _pill?: HTMLDivElement })._pill;
      const clickTarget = pill ?? el;
      clickTarget.addEventListener('click', (e) => {
        e.stopPropagation();
        this.onClick?.(roi);
      });
      const obj = new CSS2DObject(el);
      obj.position.set(...roi.position);
      this.group.add(obj);
      this.objects.push(obj);
    }
  }

  show(): void {
    this.visible = true;
    this.group.visible = true;
  }

  hide(): void {
    this.visible = false;
    this.group.visible = false;
  }

  toggle(): void {
    if (this.visible) this.hide();
    else this.show();
  }

  isVisible(): boolean {
    return this.visible;
  }

  setSize(width: number, height: number): void {
    this.labelRenderer.setSize(width, height);
  }

  /**
   * Hide labels whose anchor faces away from the camera. The outward
   * normal at each label is approximated as `(anchor - brainCenter)`
   * normalised; if the dot product with the (camera - anchor) direction
   * is negative, the label is on the far side of the brain and we set
   * its element opacity to zero (with a tiny linear fade between -0.1
   * and 0.15 so labels do not pop in/out abruptly during orbit).
   */
  private updateVisibility(): void {
    if (!this.visible) return;
    const cameraPos = (this.camera as THREE.PerspectiveCamera).position;

    for (const obj of this.objects) {
      // Outward normal: vector from brain centre to label anchor
      this._normal
        .copy(obj.position)
        .sub(this._brainCenter)
        .normalize();

      // Direction from anchor to camera
      this._toCamera.subVectors(cameraPos, obj.position).normalize();

      const dot = this._normal.dot(this._toCamera);

      // Hard hide on the back side, soft fade through a small band so
      // labels glide in/out as the user orbits.
      let opacity: number;
      if (dot <= -0.05) opacity = 0;
      else if (dot >= 0.15) opacity = 1;
      else opacity = (dot + 0.05) / 0.2;

      const el = obj.element as HTMLDivElement & { _pill?: HTMLDivElement };
      el.style.opacity = String(opacity);
      // Disable pill clicks while the label is fading or hidden so the
      // user does not accidentally click an invisible target.
      if (el._pill) {
        el._pill.style.pointerEvents = opacity > 0.5 ? 'auto' : 'none';
      }
    }
  }

  render(): void {
    this.updateVisibility();
    this.labelRenderer.render(this.scene, this.camera);
  }

  dispose(): void {
    for (const obj of this.objects) {
      this.group.remove(obj);
      const el = obj.element as HTMLDivElement;
      el.parentNode?.removeChild(el);
    }
    this.objects = [];
    this.scene.remove(this.group);
    if (this.labelRenderer.domElement.parentNode) {
      this.labelRenderer.domElement.parentNode.removeChild(
        this.labelRenderer.domElement,
      );
    }
  }
}
