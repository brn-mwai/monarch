// ============================================================
// BrainEngine.ts -- top-level orchestrator for the BrainViewer
// ============================================================
//
// Owns the Three.js scene/camera/renderer and all sub-managers. The
// React layer holds a single instance of this class per mounted viewer
// and talks to it via setActivation / setView / toggle* methods.
// ============================================================

import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

import { ActivationMapper } from './ActivationMapper';
import { AnimationController } from './AnimationController';
import { CameraPresets } from './CameraPresets';
import { HeadShell } from './HeadShell';
import { HemisphereManager } from './HemisphereManager';
import { InflateManager } from './InflateManager';
import { MeshLoader } from './MeshLoader';
import { ROILabelManager } from './ROILabelManager';
import type {
  ColorMode,
  HemisphereMode,
  MultimodalActivation,
  ROILabel,
  SurfaceMode,
  ViewPreset,
} from '../types';

export class BrainEngine {
  private renderer: THREE.WebGLRenderer;
  private scene: THREE.Scene;
  private camera: THREE.PerspectiveCamera;
  private controls: OrbitControls;
  private clock = new THREE.Clock();

  private meshLoader: MeshLoader;
  private activationMapper: ActivationMapper | null = null;
  private hemisphereManager: HemisphereManager | null = null;
  private inflateManager: InflateManager | null = null;
  private cameraPresets: CameraPresets;
  private roiLabels: ROILabelManager;
  private headShell: HeadShell;
  private animationController: AnimationController;

  private lights: THREE.Light[] = [];
  private cameraLight: THREE.DirectionalLight | null = null;
  private animationHandle = 0;
  private loaded = false;
  private disposed = false;
  private activationActive = false;
  private activationData: Float32Array | null = null;
  private multimodalData: MultimodalActivation | null = null;
  private currentColorMode: ColorMode = 'activation';
  private wasMorphAnimating = false;

  constructor(
    private canvas: HTMLCanvasElement,
    private container: HTMLElement,
  ) {
    const rect = container.getBoundingClientRect();
    const width = Math.max(1, rect.width);
    const height = Math.max(1, rect.height);

    this.renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: true,
    });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(width, height, false);
    // ACES tone mapping was crushing the sulcal contrast and washing the
    // brain to near-white when ambient + key lights summed above 1.0.
    // Linear/no tone mapping with reduced light intensities preserves the
    // grey range we set on the vertex colors.
    this.renderer.toneMapping = THREE.NoToneMapping;
    this.renderer.toneMappingExposure = 1.0;
    this.renderer.setClearColor(0x000000, 0);
    // The HeadShell uses a per-material clipping plane to hide the
    // LeePerrySmith model's neck stub below chin level.
    this.renderer.localClippingEnabled = true;
    // Enable shadow maps so the directional key light can cast real
    // self-shadows on the brain (front of each gyrus blocks light from
    // reaching the deep sulci behind it).
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    this.scene = new THREE.Scene();

    this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 2000);
    // fsaverage5 uses Z = superior, so the camera's "up" reference must be
    // +Z, otherwise every preset gets rotated 90 degrees from the standard
    // neuroimaging orientation. The CameraPresets module overrides this
    // per view (dorsal/ventral need (0, 1, 0) instead).
    this.camera.up.set(0, 0, 1);
    this.camera.position.set(-220, 0, 15);
    this.camera.lookAt(0, 0, 15);

    this.controls = new OrbitControls(this.camera, canvas);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.enablePan = true;
    this.controls.enableZoom = true;
    this.controls.minDistance = 120;
    this.controls.maxDistance = 700;
    this.controls.autoRotate = false;

    this.addLights();

    this.meshLoader = new MeshLoader('/mesh');
    this.cameraPresets = new CameraPresets(this.camera, this.controls);
    this.roiLabels = new ROILabelManager(this.scene, this.camera, container);

    // Add the head silhouette overlay immediately so it's visible during
    // the skeleton / loading phase as well as after the brain loads.
    this.headShell = new HeadShell();
    this.scene.add(this.headShell.object3d);

    // The animation controller can be set up immediately; the actual
    // applyActivation hook lands once the meshes have loaded inside
    // init() (we need leftMesh / rightMesh to push the frame to).
    this.animationController = new AnimationController();
  }

  private addLights(): void {
    // Harsh lighting: very low ambient + minimal hemisphere fill so the
    // camera-tracking key light dominates entirely. Per-face flat
    // normals on the non-indexed brain mesh produce dramatic polygon
    // shadow contrast under this setup.
    const ambient = new THREE.AmbientLight(0xffffff, 0.015);
    const hemi = new THREE.HemisphereLight(0xffffff, 0x000000, 0.01);
    hemi.position.set(0, 0, 1);

    // Very strong camera-tracking key light. Whichever side of the
    // brain faces the viewer is lit; the away-side polygons drop into
    // near-black shadow. Bumped up to 3.6 to widen the contrast gap.
    this.cameraLight = new THREE.DirectionalLight(0xffffff, 3.6);
    this.cameraLight.position.set(-220, 0, 15);
    this.cameraLight.target.position.set(0, 0, 15);

    // Cast self-shadows. Orthographic shadow camera frustum is sized
    // to enclose the brain bbox (~+/-90mm) with margin so the front of
    // each gyrus can shadow the sulcus behind it. Bias is negative to
    // pull the shadow toward the caster and avoid shadow acne on the
    // lit side.
    this.cameraLight.castShadow = true;
    this.cameraLight.shadow.mapSize.set(2048, 2048);
    this.cameraLight.shadow.camera.left = -130;
    this.cameraLight.shadow.camera.right = 130;
    this.cameraLight.shadow.camera.top = 130;
    this.cameraLight.shadow.camera.bottom = -130;
    this.cameraLight.shadow.camera.near = 1;
    this.cameraLight.shadow.camera.far = 2000;
    this.cameraLight.shadow.bias = -0.0008;
    this.cameraLight.shadow.normalBias = 0.5;
    this.cameraLight.shadow.radius = 4;

    this.lights = [ambient, hemi, this.cameraLight];
    for (const light of this.lights) this.scene.add(light);
    this.scene.add(this.cameraLight.target);
  }

  async init(): Promise<void> {
    // Wait for both the brain meshes AND the head GLB before fitting,
    // because fitToActualBrain needs the actual measured brain bbox and
    // the loaded head geometry at the same time.
    await Promise.all([this.meshLoader.load(), this.headShell.ready()]);

    const left = this.meshLoader.getLeftMesh();
    const right = this.meshLoader.getRightMesh();
    // Brain meshes both cast and receive shadows so the front of each
    // gyrus self-shadows the deep sulci behind it.
    left.castShadow = true;
    left.receiveShadow = true;
    right.castShadow = true;
    right.receiveShadow = true;
    this.scene.add(left);
    this.scene.add(right);

    this.inflateManager = new InflateManager(left, right, this.meshLoader);
    this.activationMapper = new ActivationMapper(this.meshLoader);

    // Hook the animation controller's per-frame callback so that
    // every interpolated time-series frame lights up the brain via
    // the same path a static activation does.
    this.animationController.onUpdate((frame) => {
      this.activationMapper?.applyActivation(left, right, frame);
    });

    // Measure the actual brain bbox from the loaded meshes (no hardcoded
    // dimensions) and use it to fit the head silhouette around the brain.
    const brainBbox = new THREE.Box3().setFromObject(left);
    brainBbox.expandByObject(right);
    const brainSize = brainBbox.getSize(new THREE.Vector3());
    const brainCenter = brainBbox.getCenter(new THREE.Vector3());
    // eslint-disable-next-line no-console
    console.log('[BrainEngine] === BRAIN BBOX (init) ===');
    // eslint-disable-next-line no-console
    console.log('  min:', brainBbox.min.toArray().map((v) => v.toFixed(1)));
    // eslint-disable-next-line no-console
    console.log('  max:', brainBbox.max.toArray().map((v) => v.toFixed(1)));
    // eslint-disable-next-line no-console
    console.log('  size:', brainSize.toArray().map((v) => v.toFixed(1)));
    // eslint-disable-next-line no-console
    console.log('  center:', brainCenter.toArray().map((v) => v.toFixed(1)));

    this.headShell.fitToActualBrain(brainBbox);

    // Tilt both brain meshes ~10 degrees around the X axis so the
    // frontal lobe sits slightly higher than the occipital lobe,
    // matching the natural angle the brain takes inside the cranium.
    // The rotation happens around each mesh's own origin (fs (0,0,0),
    // near the brain center). The head silhouette and the camera are
    // unaffected.
    const brainTilt = new THREE.Euler(
      THREE.MathUtils.degToRad(22),
      0,
      0,
      'XYZ',
    );
    left.rotation.copy(brainTilt);
    right.rotation.copy(brainTilt);

    // Lift the brain slightly upward inside the cranium so the crown
    // sits closer to the inside of the skull top, shift it forward so
    // the frontal lobe sits closer to the inside of the forehead, and
    // nudge it laterally so it appears centered when viewed from the
    // anterior camera. (Anterior camera maps world +X to screen left.)
    const brainLift = 12;
    const brainForward = 9;
    const brainSideShift = 3;
    left.position.set(brainSideShift, brainForward, brainLift);
    right.position.set(brainSideShift, brainForward, brainLift);

    // Construct HemisphereManager AFTER the brain pose is set so its
    // constructor snapshots this pose as the "closed rest" state.
    // Otherwise toggling open/close would zero out the side / forward
    // shift on the next close animation.
    this.hemisphereManager = new HemisphereManager(left, right);

    // Camera presets are framed on the FITTED head bbox so the head
    // sits centered in the viewport and the brain naturally appears
    // inside the cranium.
    const headBbox = this.headShell.getFittedBbox();
    this.cameraPresets.setBoundingBox(headBbox);
    this.cameraPresets.setView('left', false);

    this.loaded = true;
    this.animate();
  }

  private animate = (): void => {
    if (this.disposed) return;
    const deltaTime = this.clock.getDelta();

    this.controls.update();
    this.hemisphereManager?.update(deltaTime);
    this.inflateManager?.update(deltaTime);
    this.cameraPresets.update(deltaTime);
    this.headShell.update(deltaTime);
    this.animationController.update(deltaTime);

    // Drag the headlight along with the camera each frame so the lit side
    // of the brain is always whatever side the viewer is looking at.
    if (this.cameraLight) {
      this.cameraLight.position.copy(this.camera.position);
      this.cameraLight.target.position.copy(this.controls.target);
      this.cameraLight.target.updateMatrixWorld();
    }

    // While the inflate morph is running the current sulcal palette needs
    // to track the morph parameter, and whatever activation is displayed
    // must be re-blended against the new palette. We do this whenever the
    // morph is actively animating, plus one extra frame at the end so the
    // final state settles correctly.
    if (this.inflateManager) {
      const nowAnimating = this.inflateManager.isAnimating();
      if (nowAnimating || this.wasMorphAnimating) {
        const t = this.inflateManager.getCurrentT();
        this.refreshColorsForMorph(t);
      }
      this.wasMorphAnimating = nowAnimating;
    }

    this.renderer.render(this.scene, this.camera);
    this.roiLabels.render();

    this.animationHandle = requestAnimationFrame(this.animate);
  };

  private refreshColorsForMorph(t: number): void {
    if (!this.activationMapper) return;
    this.meshLoader.updateMorphSulcal(t);
    const left = this.meshLoader.getLeftMesh();
    const right = this.meshLoader.getRightMesh();
    if (!this.activationActive) {
      this.activationMapper.clearActivation(left, right);
      return;
    }
    if (this.currentColorMode === 'multimodal' && this.multimodalData) {
      this.activationMapper.applyMultimodalActivation(
        left,
        right,
        this.multimodalData,
      );
    } else if (this.activationData) {
      this.activationMapper.applyActivation(left, right, this.activationData);
    }
  }

  // ------------------------------------------------------------------
  // Public API
  // ------------------------------------------------------------------

  setActivation(data: Float32Array): void {
    if (!this.loaded || !this.activationMapper) return;
    const left = this.meshLoader.getLeftMesh();
    const right = this.meshLoader.getRightMesh();
    // Cache a copy so mid-morph refreshes can re-blend against the live
    // sulcal palette without depending on React props staying stable.
    this.activationData = new Float32Array(data);
    this.multimodalData = null;
    this.currentColorMode = 'activation';
    this.activationMapper.applyActivation(left, right, this.activationData);
    this.activationActive = true;
  }

  /**
   * Apply a multimodal RGB activation (text/audio/video). Each modality
   * lights its own color channel; overlap regions blend; areas with no
   * activation revert to the underlying sulcal grey.
   */
  setMultimodalActivation(data: MultimodalActivation): void {
    if (!this.loaded || !this.activationMapper) return;
    const left = this.meshLoader.getLeftMesh();
    const right = this.meshLoader.getRightMesh();
    // Cache a copy so mid-morph refreshes can re-apply.
    this.multimodalData = {
      text: new Float32Array(data.text),
      audio: new Float32Array(data.audio),
      video: new Float32Array(data.video),
    };
    this.activationData = null;
    this.currentColorMode = 'multimodal';
    this.activationMapper.applyMultimodalActivation(
      left,
      right,
      this.multimodalData,
    );
    this.activationActive = true;
  }

  clearActivation(): void {
    if (!this.loaded || !this.activationMapper) return;
    const left = this.meshLoader.getLeftMesh();
    const right = this.meshLoader.getRightMesh();
    this.activationMapper.clearActivation(left, right);
    this.activationActive = false;
    this.activationData = null;
    this.multimodalData = null;
    this.currentColorMode = 'activation';
  }

  isActivationActive(): boolean {
    return this.activationActive;
  }

  getColorMode(): ColorMode {
    return this.currentColorMode;
  }

  /**
   * Highlight a single HCP MMP1.0 region by name. Currently a no-op
   * placeholder that just records the request -- the per-vertex
   * highlight pass needs the cached ROI vertex JSON from the backend
   * (`data/roi_definitions.json`) to land before we can light up the
   * specific vertex set. Wired now so the BrainViewer prop contract is
   * stable; the actual highlight pass plugs into the same emissive
   * pipeline activation already uses.
   */
  highlightROI(_roiName: string | null): void {
    // Intentionally a no-op for now. See note above.
  }

  setView(preset: ViewPreset): void {
    this.cameraPresets.setView(preset);
  }

  toggleHemispheres(): void {
    if (!this.hemisphereManager) return;
    const willOpen = !this.hemisphereManager.isOpen();
    this.hemisphereManager.toggle();
    if (willOpen) {
      // Auto-frame the open mode with the posterior camera (the angle
      // that shows both medial walls together once the hemispheres
      // rotate) and fade the head shell out so it doesn't visually
      // contradict the spread-apart hemispheres.
      this.cameraPresets.setView('posterior');
      this.headShell.fadeOut();
    } else {
      // Restore the head silhouette when closing back to a normal brain.
      this.headShell.fadeIn();
    }
  }

  getHemisphereMode(): HemisphereMode {
    return this.hemisphereManager?.isOpen() ? 'open' : 'close';
  }

  toggleInflate(): void {
    this.inflateManager?.toggle();
  }

  getSurfaceMode(): SurfaceMode {
    return this.inflateManager?.isInflated() ? 'inflated' : 'normal';
  }

  toggleGuide(): void {
    this.roiLabels.toggle();
  }

  isGuideVisible(): boolean {
    return this.roiLabels.isVisible();
  }

  setOnROIClick(cb: (roi: ROILabel) => void): void {
    this.roiLabels.setOnClick(cb);
  }

  /**
   * Toggle pointer interaction. When false, the OrbitControls stop
   * responding to mouse / touch / wheel events so the brain holds its
   * current view -- used by the landing-page hero where the brains
   * should stay frozen in their initial lateral pose.
   */
  setInteractive(enabled: boolean): void {
    this.controls.enabled = enabled;
  }

  // === Time-series animation API ============================================

  /**
   * Load a `(T * 20484)` Float32 time series. Call once per scan; the
   * brain will tween between TR frames as either a bound media element
   * advances or the manual playback timer ticks.
   */
  setTimeSeries(data: Float32Array, nTrs: number, tr = 1.0): void {
    this.animationController.setTimeSeries(data, nTrs, tr);
  }

  clearTimeSeries(): void {
    this.animationController.clearTimeSeries();
  }

  /** Bind to an HTML <video> or <audio> element for playback sync. */
  bindMediaElement(element: HTMLMediaElement | null): void {
    this.animationController.bindMediaElement(element);
  }

  /** Seek the brain to a specific time without bound media. */
  seekTimeSeries(timeSeconds: number): void {
    this.animationController.seekTo(timeSeconds);
  }

  /** Start the internal manual timer (for text content with no track). */
  playManualTimeline(): void {
    this.animationController.playManual();
  }
  pauseManualTimeline(): void {
    this.animationController.pauseManual();
  }

  resize(width: number, height: number): void {
    const w = Math.max(1, width);
    const h = Math.max(1, height);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h, false);
    this.roiLabels.setSize(w, h);
  }

  isLoaded(): boolean {
    return this.loaded;
  }

  dispose(): void {
    if (this.disposed) return;
    this.disposed = true;
    cancelAnimationFrame(this.animationHandle);

    for (const light of this.lights) this.scene.remove(light);
    if (this.cameraLight?.target) this.scene.remove(this.cameraLight.target);
    this.lights = [];
    this.cameraLight = null;

    this.roiLabels.dispose();
    this.headShell.dispose();
    this.animationController.dispose();
    this.meshLoader.dispose();

    this.controls.dispose();
    this.renderer.dispose();
  }
}
