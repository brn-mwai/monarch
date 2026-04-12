'use client';

import { useReducer, type ReactNode } from 'react';

import { ScanContext, initialScanState, scanReducer } from './scan-store';

/**
 * Wraps the app with the Monarch shared scan state. Mount this once at
 * the root layout so every page (Scanner, Report, Batch, Demo) reads
 * from the same store and dispatching from any chart updates the
 * brain renderer in the same render pass.
 */
export function ScanProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(scanReducer, initialScanState);
  return (
    <ScanContext.Provider value={{ state, dispatch }}>
      {children}
    </ScanContext.Provider>
  );
}
