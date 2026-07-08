'use client';

import { Pause, Play } from '@phosphor-icons/react';

interface PlaybackControlsProps {
  playing: boolean;
  time: number;
  duration: number;
  onPlayPause: () => void;
  onSeek: (seconds: number) => void;
}

function formatTime(seconds: number): string {
  const total = Math.max(0, Math.floor(seconds));
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export function PlaybackControls({
  playing,
  time,
  duration,
  onPlayPause,
  onSeek,
}: PlaybackControlsProps) {
  const max = Math.max(0.001, duration);
  return (
    <div className="absolute bottom-20 left-1/2 z-30 flex -translate-x-1/2 items-center gap-3 rounded-full border border-white/20 bg-black/50 px-4 py-2 backdrop-blur-md">
      <button
        type="button"
        onClick={onPlayPause}
        aria-label={playing ? 'Pause brain activity' : 'Play brain activity'}
        className="flex h-7 w-7 items-center justify-center rounded-full border border-white/30 text-white transition-colors hover:bg-white/15"
      >
        {playing ? <Pause size={14} weight="fill" /> : <Play size={14} weight="fill" />}
      </button>
      <input
        type="range"
        min={0}
        max={max}
        step={0.01}
        value={Math.min(time, max)}
        onChange={(e) => onSeek(parseFloat(e.target.value))}
        aria-label="Seek brain activity"
        className="h-1 w-40 cursor-pointer accent-white"
      />
      <span className="font-mono text-[11px] tabular-nums text-white/70">
        {formatTime(time)} / {formatTime(duration)}
      </span>
    </div>
  );
}
