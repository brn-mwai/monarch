// ============================================================
// scan-store.ts -- Monarch shared scan state
// ============================================================
//
// Holds the current scan result(s) and drives EVERY visualization
// in the app:
//
//   - BrainViewer reads the active activation vector from here
//   - All ECharts components read NAA / Landau / ROI data from here
//   - Compare mode holds two results (A and B) and an active toggle
//
// React context + useReducer keeps updates predictable: a single
// SCAN_COMPLETE_A dispatch propagates to the brain renderer AND every
// chart in one render pass, no prop drilling, no fetching from inside
// the visualization components.
// ============================================================

import { createContext, useContext, type Dispatch } from 'react';

import type { DemographicId } from './demographics';

// === Domain types ===

export interface ROIData {
  name: string;
  activation: number;
  system: 'affective' | 'deliberative';
  vertexCount: number;
}

export interface LandauData {
  free_energy_m: number[];
  free_energy_F: number[];
  equilibrium_m: number;
  susceptibility: number | null;
  external_field_h: number;
  beta_j: number;
  alpha_hat: number;
}

export interface NAAData {
  naa: number;
  a_aff: number;
  a_del: number;
  classification: 'LOW' | 'MOD' | 'HIGH';
}

export interface MultimodalVectors {
  text: Float32Array | null;
  audio: Float32Array | null;
  video: Float32Array | null;
}

export interface ScanResult {
  scanId: string;
  naa: NAAData;
  landau: LandauData;
  roiBreakdown: ROIData[];
  modality: 'text' | 'audio' | 'video';
  nTrs: number;
  /** (20484,) model-PREDICTED cortical activation for the brain renderer. */
  activationVector: Float32Array | null;
  /**
   * (20484,) recorded ground-truth activation, present only for benchmark
   * stimuli that ship with real fMRI. Null for arbitrary content -- the
   * true-vs-predicted compare then shows an honest "no reference" state
   * instead of a fabricated brain.
   */
  trueActivation?: Float32Array | null;
  /**
   * Optional flat (T * 20484) Float32 time series. When present, the
   * scanner / report pages can hand it to BrainEngine.setTimeSeries()
   * so playback through a media element drives the brain in real time.
   */
  timeSeries?: Float32Array;
  /** Optional URL to the source media file (for the inline player). */
  mediaUrl?: string;
  /** Optional per-modality vectors for the multimodal RGB pipeline. */
  multimodal?: MultimodalVectors;
  /** Original input string (text content or filename) for display. */
  inputContent: string;
}

export type ScanMode = 'idle' | 'scanning' | 'result' | 'compare';
export type ActiveContent = 'A' | 'B';
export type ColorMode = 'activation' | 'multimodal';
/**
 * Which pairing the Compare tab's two brains represent:
 *   - 'ab':    Content A vs Content B (two different inputs, both predicted).
 *   - 'truth': Recorded true vs model predicted for a single input.
 */
export type CompareView = 'ab' | 'truth';

export interface ScanState {
  mode: ScanMode;
  contentA: ScanResult | null;
  contentB: ScanResult | null;
  activeContent: ActiveContent;
  colorMode: ColorMode;
  /** Active scanner tab id; drives whether the brain panel splits (compare). */
  activeTab: string;
  /** Which pairing the Compare tab's two brains represent. */
  compareView: CompareView;
  /** Audience lens for niched interpretation; does not alter measured values. */
  demographic: DemographicId;
  /** Optional ROI name to highlight on the brain (driven by chart hover). */
  highlightROI: string | null;
  error: string | null;
}

// === Actions ===

export type ScanAction =
  | { type: 'START_SCAN' }
  | { type: 'SCAN_COMPLETE_A'; result: ScanResult }
  | { type: 'SCAN_COMPLETE_B'; result: ScanResult }
  | { type: 'SET_ACTIVE'; active: ActiveContent }
  | { type: 'SET_TAB'; tab: string }
  | { type: 'SET_COMPARE_VIEW'; view: CompareView }
  | { type: 'SET_DEMOGRAPHIC'; demographic: DemographicId }
  | { type: 'SET_COLOR_MODE'; mode: ColorMode }
  | { type: 'SET_HIGHLIGHT_ROI'; roi: string | null }
  | { type: 'CLEAR' }
  | { type: 'ERROR'; message: string };

// === Reducer ===

export function scanReducer(state: ScanState, action: ScanAction): ScanState {
  switch (action.type) {
    case 'START_SCAN':
      return { ...state, mode: 'scanning', error: null };
    case 'SCAN_COMPLETE_A':
      return {
        ...state,
        mode: state.contentB ? 'compare' : 'result',
        contentA: action.result,
        activeContent: 'A',
      };
    case 'SCAN_COMPLETE_B':
      return {
        ...state,
        mode: 'compare',
        contentB: action.result,
      };
    case 'SET_ACTIVE':
      return { ...state, activeContent: action.active };
    case 'SET_TAB':
      return { ...state, activeTab: action.tab };
    case 'SET_COMPARE_VIEW':
      return { ...state, compareView: action.view };
    case 'SET_DEMOGRAPHIC':
      return { ...state, demographic: action.demographic };
    case 'SET_COLOR_MODE':
      return { ...state, colorMode: action.mode };
    case 'SET_HIGHLIGHT_ROI':
      return { ...state, highlightROI: action.roi };
    case 'CLEAR':
      return { ...initialScanState };
    case 'ERROR':
      return { ...state, mode: 'idle', error: action.message };
    default:
      return state;
  }
}

export const initialScanState: ScanState = {
  mode: 'idle',
  contentA: null,
  contentB: null,
  activeContent: 'A',
  colorMode: 'activation',
  activeTab: 'scan',
  compareView: 'ab',
  demographic: 'general',
  highlightROI: null,
  error: null,
};

export interface ScanContextValue {
  state: ScanState;
  dispatch: Dispatch<ScanAction>;
}

export const ScanContext = createContext<ScanContextValue>({
  state: initialScanState,
  dispatch: () => {},
});

export function useScanState(): ScanContextValue {
  return useContext(ScanContext);
}

/** Convenience selector: which result is currently driving the brain. */
export function getActiveResult(state: ScanState): ScanResult | null {
  return state.activeContent === 'A' ? state.contentA : state.contentB;
}
