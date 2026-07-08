// ============================================================
// AnimationController.ts - drives the brain off media playback
// ============================================================
//
// Holds a flat (T * 20484) Float32 time series. Every frame the brain
// animation loop calls update() and we read currentTime from the bound
// HTML media element, convert it to a fractional frame index, lerp
// between the two enclosing TR frames, and fire a callback with the
// resulting (20484,) vector. The callback is hooked up by BrainEngine
// to ActivationMapper.applyActivation so the brain pops on the next
// render pass.
//
// For text content (no audible/visual track), there is no media
// element. Callers can either skip animation entirely (showing only
// the static mean-pooled vector) or call seekTo / playManual to
// drive the time series with an internal timer.
// ============================================================

import { robustNormalize } from '@/lib/normalize';

const VERTS = 20484;

export class AnimationController {
  private timeSeries: Float32Array | null = null;
  private nTrs = 0;
  private tr = 1.0;
  private mediaElement: HTMLMediaElement | null = null;
  private mediaPlaying = false;

  // Internal time driver for text-mode playback (no media element).
  private manualTime = 0;
  private manualPlaying = false;

  private currentFrame: Float32Array;
  private onFrameUpdate: ((frame: Float32Array) => void) | null = null;

  // Track the last frame index we pushed so we can skip redundant work.
  private lastEmittedFrame = -1;

  constructor() {
    this.currentFrame = new Float32Array(VERTS);
  }

  /**
   * Load a time series. `data` is a flat Float32Array of length
   * `nTrs * 20484`; frame N starts at index `N * 20484`.
   * `tr` is the temporal resolution in seconds (TRIBE v2 default = 1.0).
   */
  setTimeSeries(data: Float32Array, nTrs: number, tr = 1.0): void {
    if (data.length !== nTrs * VERTS) {
      throw new Error(
        `AnimationController: expected ${nTrs * VERTS} values, got ${data.length}`,
      );
    }
    // Normalize ONCE across the entire (T, V) series so every frame shares
    // one colour scale. Per-frame normalization would flicker the brain to
    // full brightness on every TR and erase the relative changes over time
    // that the playback is meant to show. Frames emitted downstream are
    // already in [0, 1] and go through ActivationMapper.applyNormalized.
    this.timeSeries = robustNormalize(data, 99, true, true);
    this.nTrs = nTrs;
    this.tr = tr;
    this.lastEmittedFrame = -1;
    this.manualTime = 0;
  }

  clearTimeSeries(): void {
    this.timeSeries = null;
    this.nTrs = 0;
    this.lastEmittedFrame = -1;
    this.manualPlaying = false;
  }

  hasTimeSeries(): boolean {
    return this.timeSeries !== null && this.nTrs > 0;
  }

  /** Total playback length in seconds. */
  getDuration(): number {
    return this.nTrs * this.tr;
  }

  /** Current playback position in seconds (media-synced or manual). */
  getCurrentTime(): number {
    if (this.mediaElement) return this.mediaElement.currentTime;
    return this.manualTime;
  }

  isPlaying(): boolean {
    return this.manualPlaying || this.mediaPlaying;
  }

  /**
   * Bind to an HTML <video> or <audio> element. The controller listens
   * to play / pause / ended events and reads currentTime each frame.
   */
  bindMediaElement(element: HTMLMediaElement | null): void {
    if (this.mediaElement) {
      this.mediaElement.removeEventListener('play', this.onPlay);
      this.mediaElement.removeEventListener('pause', this.onPause);
      this.mediaElement.removeEventListener('ended', this.onPause);
    }
    this.mediaElement = element;
    this.mediaPlaying = false;
    if (element) {
      element.addEventListener('play', this.onPlay);
      element.addEventListener('pause', this.onPause);
      element.addEventListener('ended', this.onPause);
      // Drive a single seek update so the brain matches the current
      // currentTime even before the user hits play.
      this.seekTo(element.currentTime);
    }
  }

  private onPlay = () => {
    this.mediaPlaying = true;
  };
  private onPause = () => {
    this.mediaPlaying = false;
  };

  /** Register the per-frame callback. BrainEngine wires this to the mapper. */
  onUpdate(callback: (frame: Float32Array) => void): void {
    this.onFrameUpdate = callback;
  }

  /**
   * Internal manual playback (for text content with no media element).
   * Advances time by deltaTime seconds each animate() tick.
   */
  playManual(): void {
    this.manualPlaying = true;
    // Resume from the current position; only rewind if we're at the end.
    if (this.manualTime >= this.getDuration()) this.manualTime = 0;
  }
  pauseManual(): void {
    this.manualPlaying = false;
  }

  /**
   * Per-frame tick driven by the brain animation loop. Pulls time from
   * the media element if bound and playing, otherwise advances the
   * internal manual timer if it is running.
   */
  update(deltaTime: number): void {
    if (!this.timeSeries || this.nTrs === 0) return;

    let timeSeconds = 0;
    if (this.mediaElement) {
      // Sync to media. We always sample currentTime, even when paused
      // or scrubbing, so the brain follows scrubber drags.
      timeSeconds = this.mediaElement.currentTime;
    } else if (this.manualPlaying) {
      this.manualTime += deltaTime;
      const duration = this.nTrs * this.tr;
      if (this.manualTime >= duration) this.manualTime = 0;
      timeSeconds = this.manualTime;
    } else {
      return;
    }

    this.applyTime(timeSeconds);
  }

  /** External seek (e.g. timeline scrubber). */
  seekTo(timeSeconds: number): void {
    if (!this.timeSeries || this.nTrs === 0) return;
    // Keep the manual timer in sync so a subsequent play resumes from the
    // scrubbed position rather than jumping back to the old time.
    if (!this.mediaElement) {
      const clamped = Math.max(0, Math.min(timeSeconds, this.getDuration()));
      this.manualTime = clamped;
    }
    this.applyTime(timeSeconds);
  }

  private applyTime(timeSeconds: number): void {
    const series = this.timeSeries!;
    const frameFloat = timeSeconds / this.tr;
    const maxFrame = this.nTrs - 1;
    const clamped = frameFloat < 0 ? 0 : frameFloat > maxFrame ? maxFrame : frameFloat;

    const frame0 = Math.floor(clamped);
    const frame1 = Math.min(frame0 + 1, maxFrame);
    const alpha = clamped - frame0;

    // Skip if neither frame nor blend has changed enough to matter.
    const quantized = frame0 * 1000 + Math.round(alpha * 1000);
    if (quantized === this.lastEmittedFrame) return;
    this.lastEmittedFrame = quantized;

    const start0 = frame0 * VERTS;
    const start1 = frame1 * VERTS;
    for (let i = 0; i < VERTS; i++) {
      this.currentFrame[i] =
        series[start0 + i] * (1 - alpha) + series[start1 + i] * alpha;
    }

    if (this.onFrameUpdate) this.onFrameUpdate(this.currentFrame);
  }

  dispose(): void {
    if (this.mediaElement) {
      this.mediaElement.removeEventListener('play', this.onPlay);
      this.mediaElement.removeEventListener('pause', this.onPause);
      this.mediaElement.removeEventListener('ended', this.onPause);
    }
    this.mediaElement = null;
    this.timeSeries = null;
    this.onFrameUpdate = null;
  }
}
