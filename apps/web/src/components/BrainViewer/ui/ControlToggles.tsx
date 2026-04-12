'use client';

import type { DataMode, HemisphereMode, SurfaceMode } from '../types';

interface ControlTogglesProps {
  dataMode: DataMode;
  surfaceMode: SurfaceMode;
  hemisphereMode: HemisphereMode;
  onDataModeChange: (mode: DataMode) => void;
  onSurfaceModeChange: (mode: SurfaceMode) => void;
  onHemisphereModeChange: (mode: HemisphereMode) => void;
}

interface PairProps<T extends string> {
  value: T;
  options: readonly { value: T; label: string }[];
  onChange: (value: T) => void;
}

function TogglePair<T extends string>({ value, options, onChange }: PairProps<T>) {
  return (
    <div className="flex items-center gap-1 rounded-full border border-white/20 bg-black/60 p-1 backdrop-blur">
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            className={
              'rounded-full px-5 py-1.5 text-sm font-medium outline-none transition-colors duration-150 ' +
              (active
                ? 'bg-white/15 text-white shadow-[inset_0_0_0_1px_rgba(255,255,255,0.08)]'
                : 'bg-transparent text-white/60 hover:text-white')
            }
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}

const DATA_OPTS = [
  { value: 'true', label: 'True' },
  { value: 'predicted', label: 'Predicted' },
] as const;

const SURFACE_OPTS = [
  { value: 'normal', label: 'Normal' },
  { value: 'inflated', label: 'Inflated' },
] as const;

const HEMI_OPTS = [
  { value: 'open', label: 'Open' },
  { value: 'close', label: 'Close' },
] as const;

export function ControlToggles({
  dataMode,
  surfaceMode,
  hemisphereMode,
  onDataModeChange,
  onSurfaceModeChange,
  onHemisphereModeChange,
}: ControlTogglesProps) {
  return (
    <div className="pointer-events-auto absolute bottom-4 left-1/2 flex -translate-x-1/2 items-center gap-4">
      <TogglePair value={dataMode} options={DATA_OPTS} onChange={onDataModeChange} />
      <TogglePair
        value={surfaceMode}
        options={SURFACE_OPTS}
        onChange={onSurfaceModeChange}
      />
      <TogglePair
        value={hemisphereMode}
        options={HEMI_OPTS}
        onChange={onHemisphereModeChange}
      />
    </div>
  );
}
