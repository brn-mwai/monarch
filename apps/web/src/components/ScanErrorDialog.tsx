'use client';

import { useScanState } from '@/lib/scan-store';

/**
 * Reports a scan that the model could not produce.
 *
 * Monarch shows no brain map and no NAA when a scan fails: a synthetic map
 * would be indistinguishable from a real prediction on screen, and this is
 * research output. The dialog is the only thing the user gets instead.
 */
export function ScanErrorDialog() {
  const { state, dispatch } = useScanState();

  if (!state.error) return null;

  const dismiss = () => dispatch({ type: 'ERROR', message: '' });

  return (
    <div
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="scan-error-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4"
      onClick={dismiss}
    >
      <div
        className="w-full max-w-md border border-neutral-700 bg-neutral-950 p-6"
        onClick={(event) => event.stopPropagation()}
      >
        <h2
          id="scan-error-title"
          className="font-mono text-sm uppercase tracking-widest text-red-400"
        >
          Scan failed
        </h2>

        <p className="mt-4 text-sm leading-relaxed text-neutral-200">{state.error}</p>

        <p className="mt-4 text-xs leading-relaxed text-neutral-500">
          No brain map is shown, because Monarch does not display simulated activation in
          place of a real TRIBE v2 prediction.
        </p>

        <button
          type="button"
          onClick={dismiss}
          className="mt-6 w-full border border-neutral-700 px-4 py-2 font-mono text-xs uppercase tracking-widest text-neutral-200 transition hover:bg-neutral-800"
        >
          Close
        </button>
      </div>
    </div>
  );
}
