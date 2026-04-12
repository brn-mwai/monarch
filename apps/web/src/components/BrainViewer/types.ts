// ============================================================
// types.ts -- All type definitions for the BrainViewer component
// ============================================================

export interface BrainMeshData {
  /** (10242, 3) vertex positions in fsaverage5 surface coords (mm) */
  vertices: number[][];
  /** (n_faces, 3) triangle indices into vertices */
  faces: number[][];
  /** (10242,) sulcal depth values, negative = sulci (folds), positive = gyri (ridges) */
  sulcalDepth: number[];
  vertexCount: number;
  faceCount: number;
  hemisphere: 'left' | 'right';
  surfaceType: 'pial' | 'inflated';
}

export interface BrainMeshSet {
  leftPial: BrainMeshData;
  rightPial: BrainMeshData;
  leftInflated: BrainMeshData;
  rightInflated: BrainMeshData;
}

export type ViewPreset =
  | 'left'
  | 'right'
  | 'medial_left'
  | 'medial_right'
  | 'dorsal'
  | 'ventral'
  | 'anterior'
  | 'posterior';

export type SurfaceMode = 'normal' | 'inflated';
export type HemisphereMode = 'open' | 'close';
export type DataMode = 'predicted' | 'true';
export type ROISystem = 'affective' | 'deliberative' | 'reward' | 'default_mode';

/**
 * Which color rendering pipeline is currently active on the brain.
 *   - 'activation': single-channel scalar mapped through the hot/fire LUT
 *   - 'multimodal': three-channel modality activation mapped to RGB
 */
export type ColorMode = 'activation' | 'multimodal';

/**
 * Three modality-specific activation vectors over the same 20484 vertices.
 * Each is processed by an independent encoder (text/audio/video) and
 * mapped to its own color channel in the multimodal RGB visualization.
 */
export interface MultimodalActivation {
  /** (20484,) text encoder activation -- maps to GREEN channel */
  text: Float32Array;
  /** (20484,) audio encoder activation -- maps to BLUE channel */
  audio: Float32Array;
  /** (20484,) video encoder activation -- maps to RED channel */
  video: Float32Array;
}

export interface ROILabel {
  name: string;
  fullName: string;
  hemisphere: 'left' | 'right';
  /** World-space position on the cortical surface (mm) */
  position: [number, number, number];
  system: ROISystem;
}

export interface BrainViewerProps {
  /** Predicted cortical activation: Float32Array of length 20484. */
  activation?: Float32Array | null;
  /** Optional comparison activation for side-by-side or A/B mode. */
  comparisonActivation?: Float32Array | null;
  /** Three-channel modality activation for multimodal RGB visualization. */
  multimodalActivation?: MultimodalActivation | null;
  /** Which color rendering mode is active. Defaults to 'activation'. */
  colorMode?: ColorMode;
  /** Which data stream to display. */
  dataMode?: DataMode;
  /** Show ROI guide labels. */
  showGuide?: boolean;
  /**
   * Optional ROI name to highlight on the brain. When set, the matching
   * region's vertices brighten so the user can see which patch the
   * chart is referring to. Pass null to clear the highlight.
   */
  highlightROI?: string | null;
  /**
   * Optional flat `(T * 20484)` Float32 time series. When provided,
   * the brain animates through TR frames; either bind a media element
   * via `mediaElement` or call the imperative seek API on the engine.
   */
  timeSeries?: Float32Array | null;
  /** Number of TRs in the time series (required when `timeSeries` is set). */
  nTrs?: number;
  /** Seconds per TR. Defaults to 1.0 (TRIBE v2 default). */
  tr?: number;
  /**
   * Optional HTML media element ref. When supplied, the brain reads
   * its current playback position every animation tick.
   */
  mediaElement?: HTMLMediaElement | null;
  /**
   * When false, the BrainViewer suppresses every overlay (Show Guide
   * button, Activity / Multimodal legend, Control toggles). Used by
   * the landing-page hero where the brains should render as a clean
   * silhouette + cortex with no chrome. Defaults to true.
   */
  showOverlays?: boolean;
  /**
   * When false, OrbitControls are disabled so the brain stays frozen
   * in its initial pose. Defaults to true.
   */
  interactive?: boolean;
  /** Initial camera view (applied once on mount). */
  initialView?: ViewPreset;
  /** Reactive camera view: when this prop changes the camera animates to the preset. */
  view?: ViewPreset;
  /** Additional CSS class for the container div. */
  className?: string;
  /** Fired when a ROI label is clicked. */
  onROIClick?: (roi: ROILabel) => void;
  /** When true, show a loading skeleton instead of the canvas. */
  loading?: boolean;
}

export interface ColormapStop {
  /** 0.0 -- 1.0 */
  position: number;
  /** RGB 0--255 */
  color: [number, number, number];
}
