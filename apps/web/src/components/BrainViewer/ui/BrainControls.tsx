'use client';

export type SurfaceKind = 'pial' | 'fiducial' | 'white';

export interface BrainControlValues {
  surface: SurfaceKind;
  inflation: number;
  opacity: number;
  specularity: number;
  curvBrightness: number;
  curvContrast: number;
  leftVisible: boolean;
  rightVisible: boolean;
}

const SURFACE_OPTIONS: { value: SurfaceKind; label: string }[] = [
  { value: 'pial', label: 'Pial' },
  { value: 'fiducial', label: 'Fiducial' },
  { value: 'white', label: 'White' },
];

interface BrainControlsProps extends BrainControlValues {
  onChange: (patch: Partial<BrainControlValues>) => void;
  onClose: () => void;
}

interface SliderRowProps {
  label: string;
  min: number;
  max: number;
  step: number;
  value: number;
  onChange: (value: number) => void;
}

function SliderRow({ label, min, max, step, value, onChange }: SliderRowProps) {
  return (
    <label className="flex items-center gap-2.5 py-1.5">
      <span className="w-[68px] shrink-0 font-mono text-[10px] uppercase tracking-wider text-white/50">
        {label}
      </span>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="h-1 min-w-0 flex-1 cursor-pointer appearance-none rounded-full bg-white/15 accent-white/80"
      />
      <span className="w-8 shrink-0 text-right font-mono text-[10px] tabular-nums text-white/70">
        {value.toFixed(2)}
      </span>
    </label>
  );
}

interface ToggleRowProps {
  label: string;
  value: boolean;
  onChange: (value: boolean) => void;
}

function ToggleRow({ label, value, onChange }: ToggleRowProps) {
  return (
    <label className="flex cursor-pointer items-center justify-between py-1.5">
      <span className="font-mono text-[10px] uppercase tracking-wider text-white/50">
        {label}
      </span>
      <button
        type="button"
        onClick={() => onChange(!value)}
        className={`h-4 w-8 rounded-full border transition-colors ${
          value ? 'border-white/50 bg-white/25' : 'border-white/20 bg-transparent'
        }`}
        aria-pressed={value}
      >
        <span
          className={`block h-3 w-3 rounded-full bg-white transition-transform ${
            value ? 'translate-x-4' : 'translate-x-0.5'
          }`}
        />
      </button>
    </label>
  );
}

/**
 * Advanced brain-surface controls (hidden by default). Mirrors the pycortex
 * "surface" panel with the knobs Monarch's engine supports: inflate morph,
 * opacity, curvature brightness/contrast, and per-hemisphere visibility.
 */
export function BrainControls({
  surface,
  inflation,
  opacity,
  specularity,
  curvBrightness,
  curvContrast,
  leftVisible,
  rightVisible,
  onChange,
  onClose,
}: BrainControlsProps) {
  return (
    <div className="absolute left-4 top-16 z-30 w-64 rounded-lg border border-white/15 bg-black/70 p-4 backdrop-blur-md">
      <div className="mb-2 flex items-center justify-between">
        <span className="font-mono text-[11px] uppercase tracking-wider text-white/60">
          Surface
        </span>
        <button
          type="button"
          onClick={onClose}
          className="font-mono text-[10px] uppercase tracking-wider text-white/45 transition-colors hover:text-white"
        >
          Hide
        </button>
      </div>

      <div className="flex items-center gap-2.5 py-1.5">
        <span className="w-[68px] shrink-0 font-mono text-[10px] uppercase tracking-wider text-white/50">
          Surface
        </span>
        <div className="flex flex-1 gap-1 rounded-full border border-white/15 p-0.5">
          {SURFACE_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => onChange({ surface: opt.value })}
              className={`flex-1 rounded-full py-0.5 font-mono text-[9px] uppercase tracking-wider transition-colors ${
                surface === opt.value
                  ? 'bg-white/20 text-white'
                  : 'text-white/50 hover:text-white/80'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      <SliderRow
        label="Inflate"
        min={0}
        max={1}
        step={0.01}
        value={inflation}
        onChange={(v) => onChange({ inflation: v })}
      />
      <SliderRow
        label="Opacity"
        min={0.1}
        max={1}
        step={0.01}
        value={opacity}
        onChange={(v) => onChange({ opacity: v })}
      />
      <SliderRow
        label="Specular"
        min={0}
        max={1}
        step={0.01}
        value={specularity}
        onChange={(v) => onChange({ specularity: v })}
      />

      <div className="my-2 border-t border-white/10" />

      <SliderRow
        label="Brightness"
        min={0.15}
        max={0.7}
        step={0.01}
        value={curvBrightness}
        onChange={(v) => onChange({ curvBrightness: v })}
      />
      <SliderRow
        label="Contrast"
        min={0}
        max={0.35}
        step={0.01}
        value={curvContrast}
        onChange={(v) => onChange({ curvContrast: v })}
      />

      <div className="my-2 border-t border-white/10" />

      <ToggleRow
        label="Left"
        value={leftVisible}
        onChange={(v) => onChange({ leftVisible: v })}
      />
      <ToggleRow
        label="Right"
        value={rightVisible}
        onChange={(v) => onChange({ rightVisible: v })}
      />
    </div>
  );
}
