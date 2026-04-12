'use client';

interface GuideButtonProps {
  visible: boolean;
  onToggle: () => void;
}

export function GuideButton({ visible, onToggle }: GuideButtonProps) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className="pointer-events-auto absolute left-4 top-4 flex items-center gap-2 rounded-full border border-white/30 bg-black/50 px-4 py-1.5 text-sm text-white outline-none backdrop-blur transition-colors hover:border-white/60"
    >
      <svg
        width="14"
        height="14"
        viewBox="0 0 16 16"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        aria-hidden="true"
      >
        <rect x="2" y="2" width="5" height="5" rx="0.5" />
        <rect x="9" y="2" width="5" height="5" rx="0.5" />
        <rect x="2" y="9" width="5" height="5" rx="0.5" />
        <rect x="9" y="9" width="5" height="5" rx="0.5" />
      </svg>
      <span>{visible ? 'Hide Guide' : 'Show Guide'}</span>
    </button>
  );
}
