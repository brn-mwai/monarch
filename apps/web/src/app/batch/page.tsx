'use client';

import { useRouter } from 'next/navigation';

import { BatchTab } from '@/components/scanner-tabs/BatchTab';

/**
 * Standalone /batch route. Renders the same real Batch Audit panel as the
 * scanner tab; clicking an item loads it as the active scan and opens its
 * full report.
 */
export default function BatchPage() {
  const router = useRouter();

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-6 py-8">
      <header>
        <h1 className="font-mono text-xl font-light tracking-wider text-white">
          Batch audit
        </h1>
        <p className="mt-1 font-mono text-[11px] uppercase tracking-wider text-white/40">
          Score a corpus by NAA and open any item&rsquo;s full report
        </p>
      </header>

      <BatchTab onInspect={() => router.push('/report')} />
    </div>
  );
}
