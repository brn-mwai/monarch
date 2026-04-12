'use client';

import dynamic from 'next/dynamic';
import type { ComponentProps } from 'react';

/**
 * SSR-safe wrapper around `echarts-for-react`. Next.js renders pages
 * on the server first; ECharts requires a DOM, so we lazy-load the
 * underlying component on the client only.
 *
 * Every chart in `components/charts/` should import this instead of
 * `echarts-for-react` directly so the same loader / no-SSR config is
 * applied across the app.
 */
const ReactECharts = dynamic(() => import('echarts-for-react'), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center text-xs text-white/40">
      Loading chart...
    </div>
  ),
});

export type EchartsProps = ComponentProps<typeof ReactECharts>;
export default ReactECharts;
