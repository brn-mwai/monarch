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
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';

import { ActivationMapper } from './ActivationMapper';
import { AnimationController } from './AnimationController';
import { CameraPresets } from './CameraPresets';
import { HeadShell } from './HeadShell';
import { HemisphereManager } from './HemisphereManager';
import { InflateManager } from './InflateManager';
import { MeshLoader, type SurfaceKind } from './MeshLoader';
import { ROILabelManager } from './ROILabelManager';
import type {
  ColorMode,
  HemisphereMode,
  MultimodalActivation,
  ROILabel,
  SurfaceMode,
  ViewPreset,
} from '../types';

// Solid background used only when exporting (image / rotation), matching the
// app's near-black page so the head silhouette reads. The live canvas stays
// transparent over the page.
const EXPORT_BG = 0x0a0a0a;

export class BrainEngine {
  private renderer: THREE.WebGLRenderer;
  private scene: THREE.Scene;
  private camera: THREE.PerspectiveCamera;
  private controls: OrbitControls;
  private clock = new THREE.Clock();
  private environmentMap: THREE.Texture | null = null;

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
      // Keep the drawing buffer so canvas snapshots / recordings capture the
      // rendered frame reliably (export image + rotation "wrap").
      preserveDrawingBuffer: true,
    });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(width, height, false);
    // ACES tone mapping was crushing the sulcal contrast and washing the
    // brain to near-white when ambient + key lights summed above 1.0.
    // Linear/no tone mapping preserves the grey range we set on the vertex
    // colors; the small exposure lift recovers the soft highlight the Meta
    // TRIBE v2 demo gets from its env map without blowing out the base grey.
    this.renderer.toneMapping = THREE.NoToneMapping;
    this.renderer.toneMappingExposure = 1.0;
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
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

    // Image-based lighting from a neutral room, the same technique the Meta
    // TRIBE v2 demo uses to give the white cortical surface a soft, realistic
    // sheen instead of a flat matte look. Prefiltered into a PMREM once at
    // construction; the texture is held on the scene so every
    // MeshStandardMaterial picks it up as its environment.
    const pmrem = new THREE.PMREMGenerator(this.renderer);
    this.environmentMap = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    this.scene.environment = this.environmentMap;
    pmrem.dispose();

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

    this.meshLoader = new MeshLoader();
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
    // White brain with smooth per-vertex normals. The scene env map now
    // supplies the ambient fill, so the ambient term is trimmed to keep the
    // bright grey base from clipping; the hemisphere + camera-tracking key
    // still carve the gyri/sulci as the viewer orbits.
    const ambient = new THREE.AmbientLight(0xffffff, 0.22);
    const hemi = new THREE.HemisphereLight(0xffffff, 0x6a6a6a, 0.28);
    hemi.position.set(0, 0, 1);

    // Soft camera-tracking key light. Whichever side faces the viewer is
    // lit; the away side falls into soft shadow that reveals the folds.
    // Trimmed so the lit side no longer sums above 1.0 and clips the mid-grey
    // base to white -- the curvature grey now reads as anatomical grey.
    this.cameraLight = new THREE.DirectionalLight(0xffffff, 0.6);
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

    // Load the fsaverage5 medial-wall mask so non-cortex stays grey instead
    // of showing painted (meaningless) activation. Optional: if the asset is
    // missing, painting falls back to the previous behaviour.
    void fetch('/mesh/medial_mask.bin')
      .then((r) => (r.ok ? r.arrayBuffer() : null))
      .then((buf) => {
        if (buf) this.activationMapper?.setMedialMask(new Uint8Array(buf));
      })
      .catch(() => {});

    // Hook the animation controller's per-frame callback so that
    // every interpolated time-series frame lights up the brain via
    // the same path a static activation does.
    this.animationController.onUpdate((frame) => {
      this.activationMapper?.applyNormalized(left, right, frame);
    });

    // Pose the brain FIRST (tilt + lift), THEN fit the head around the
    // posed brain, so the silhouette wraps the brain wherever it ends up.
    // The ~12 deg X tilt sets the frontal lobe slightly above the
    // occipital lobe, matching the natural angle inside the cranium. A
    // gentler tilt keeps the occipital lobe up in the posterior vault
    // instead of dropping it down-and-forward and leaving the back empty.
    const brainTilt = new THREE.Euler(THREE.MathUtils.degToRad(12), 0, 0, 'XYZ');
    left.rotation.copy(brainTilt);
    right.rotation.copy(brainTilt);

    // Nudge laterally so it reads centered from the anterior camera. Fit the
    // head and frame the camera on the brain at REST (no vertical lift), then
    // raise the brain inside the now-fixed head below -- so the silhouette and
    // camera stay put and only the brain rises within the cranium.
    const brainSideShift = 3;
    left.position.set(brainSideShift, 0, 0);
    right.position.set(brainSideShift, 0, 0);

    left.updateMatrixWorld(true);
    right.updateMatrixWorld(true);

    // Measure the resting brain bbox and fit the head silhouette to it.
    const brainBbox = new THREE.Box3().setFromObject(left);
    brainBbox.expandByObject(right);
    this.headShell.fitToActualBrain(brainBbox);

    // Camera presets are framed on the CRANIUM, not the full head. The
    // fitted head bbox includes the protruding face/nose (front) and a long
    // neck (below); framing that zooms the camera out so the brain renders
    // small with slack above and below. Clip the framing box to the cranial
    // vault -- keep the skull crown and occiput, drop the neck below and the
    // face in front -- so the brain fills the frame and the face/jaw fall
    // toward the edges of the faint silhouette.
    const NECK_EXCLUDE_MARGIN = 20; // below the brain base
    const FACE_EXCLUDE_MARGIN = 18; // in front of the frontal pole (smaller = bigger brain)
    const VERTICAL_BIAS = 56; // seats the head/camera; brain lift is separate below
    const headBbox = this.headShell.getFittedBbox();
    const framingBbox = headBbox.clone();
    framingBbox.min.z = brainBbox.min.z - NECK_EXCLUDE_MARGIN - VERTICAL_BIAS;
    framingBbox.max.y = brainBbox.max.y + FACE_EXCLUDE_MARGIN;
    this.cameraPresets.setBoundingBox(framingBbox);
    this.cameraPresets.setView('left', false);

    // Raise ONLY the brain (superior axis) inside the fixed head + camera.
    // Kept under CRANIUM_GAP (HeadShell = 18) so the brain stays under the
    // skull crown rather than poking through it.
    const BRAIN_RISE = 12;
    left.position.z += BRAIN_RISE;
    right.position.z += BRAIN_RISE;
    left.updateMatrixWorld(true);
    right.updateMatrixWorld(true);

    // Construct HemisphereManager AFTER the final pose so its constructor
    // snapshots the lifted pose as the "closed rest" state.
    this.hemisphereManager = new HemisphereManager(left, right);

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

    this.renderer.render(this.scene, this.camera);
    this.roiLabels.render();

    this.animationHandle = requestAnimationFrame(this.animate);
  };

  // ------------------------------------------------------------------
  // Export: still image + rotation "wrap"
  // ------------------------------------------------------------------

  /**
   * Capture the current brain view as a PNG blob. Renders once at
   * ``scale``x the on-screen resolution for a crisp export, then restores.
   */
  async captureImagePNG(scale = 2): Promise<Blob> {
    const canvas = this.renderer.domElement;
    const w = canvas.clientWidth || canvas.width;
    const h = canvas.clientHeight || canvas.height;
    const prevRatio = this.renderer.getPixelRatio();
    // Render on the app's solid dark background so the exported image looks
    // like the on-screen view (the live canvas is transparent over the page).
    this.renderer.setClearColor(EXPORT_BG, 1);
    this.renderer.setPixelRatio(Math.min(scale * window.devicePixelRatio, 4));
    this.renderer.setSize(w, h, false);
    this.renderer.render(this.scene, this.camera);
    const blob = await new Promise<Blob | null>((resolve) =>
      canvas.toBlob(resolve, "image/png"),
    );
    this.renderer.setClearColor(0x000000, 0);
    this.renderer.setPixelRatio(prevRatio);
    this.renderer.setSize(w, h, false);
    if (!blob) throw new Error("BrainEngine: PNG capture failed");
    return blob;
  }

  /**
   * Record a full 360-degree orbit of the brain as a WebM blob (the "wrap").
   * Orbits via OrbitControls.autoRotate for ``durationMs`` while MediaRecorder
   * captures the canvas stream.
   */
  async captureRotationWebM(durationMs = 4000, fps = 30): Promise<Blob> {
    const canvas = this.renderer.domElement as HTMLCanvasElement & {
      captureStream?: (fps: number) => MediaStream;
    };
    if (typeof canvas.captureStream !== "function" || typeof MediaRecorder === "undefined") {
      throw new Error("Rotation capture not supported in this browser");
    }
    const stream = canvas.captureStream(fps);
    const mime = MediaRecorder.isTypeSupported("video/webm;codecs=vp9")
      ? "video/webm;codecs=vp9"
      : "video/webm";
    const recorder = new MediaRecorder(stream, { mimeType: mime, videoBitsPerSecond: 8_000_000 });
    const chunks: Blob[] = [];
    recorder.ondataavailable = (e) => e.data.size && chunks.push(e.data);
    const finished = new Promise<Blob>((resolve) => {
      recorder.onstop = () => resolve(new Blob(chunks, { type: "video/webm" }));
    });

    const prevAuto = this.controls.autoRotate;
    const prevSpeed = this.controls.autoRotateSpeed;
    this.renderer.setClearColor(EXPORT_BG, 1);
    this.controls.autoRotate = true;
    // one full orbit in durationMs (see OrbitControls: 2pi at speed 60/seconds).
    this.controls.autoRotateSpeed = 60000 / durationMs;
    recorder.start();
    await new Promise((r) => setTimeout(r, durationMs));
    recorder.stop();
    this.controls.autoRotate = prevAuto;
    this.controls.autoRotateSpeed = prevSpeed;
    this.renderer.setClearColor(0x000000, 0);
    return finished;
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

  /** Re-paint whatever colors are currently active over the live base. */
  private reapplyColors(): void {
    if (!this.loaded || !this.activationMapper) return;
    const left = this.meshLoader.getLeftMesh();
    const right = this.meshLoader.getRightMesh();
    if (this.currentColorMode === 'multimodal' && this.multimodalData) {
      this.activationMapper.applyMultimodalActivation(left, right, this.multimodalData);
    } else if (this.activationData) {
      this.activationMapper.applyActivation(left, right, this.activationData);
    } else {
      this.activationMapper.clearActivation(left, right);
    }
  }

  /** Set the pial<->inflated morph directly (0 = pial, 1 = inflated). */
  setInflation(t: number): void {
    this.inflateManager?.setT(t);
  }

  /** Set the brain surface opacity (0 = invisible, 1 = solid). */
  setBrainOpacity(opacity: number): void {
    this.meshLoader.setOpacity(opacity);
  }

  /** Set the specular sheen (0 = matte, 1 = glossy). */
  setSpecular(specularity: number): void {
    this.meshLoader.setSpecular(specularity);
  }

  /** Select the base cortical surface (pial / fiducial / white). */
  setSurface(kind: SurfaceKind): void {
    this.meshLoader.setSurface(kind);
    this.inflateManager?.refresh();
  }

  /** Retune the curvature shading and re-paint activation over the new base. */
  setCurvature(brightness: number, contrast: number): void {
    this.meshLoader.recolorCurvature(brightness, contrast);
    this.reapplyColors();
  }

  /** Show or hide one hemisphere. */
  setHemisphereVisible(side: 'left' | 'right', visible: boolean): void {
    const mesh =
      side === 'left'
        ? this.meshLoader.getLeftMesh()
        : this.meshLoader.getRightMesh();
    mesh.visible = visible;
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

  hasTimeline(): boolean {
    return this.animationController.hasTimeSeries();
  }
  getTimelineDuration(): number {
    return this.animationController.getDuration();
  }
  getTimelineTime(): number {
    return this.animationController.getCurrentTime();
  }
  isTimelinePlaying(): boolean {
    return this.animationController.isPlaying();
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

    this.environmentMap?.dispose();
    this.environmentMap = null;
    this.scene.environment = null;

    this.roiLabels.dispose();
    this.headShell.dispose();
    this.animationController.dispose();
    this.meshLoader.dispose();

    this.controls.dispose();
    this.renderer.dispose();
  }
}
