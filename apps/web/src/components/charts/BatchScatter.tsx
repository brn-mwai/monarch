'use client';

import { useMemo } from 'react';

import ReactECharts from './EchartsBase';
import { CHART_CARD_CLASS, monarchTheme } from './echarts-theme';

export type BatchCategory =
  | 'high-outrage'
  | 'fear-activating'
  | 'reward-hook'
  | 'neutral';

export interface BatchItem {
  id: string;
  /** Stable ordering for the x axis (typically the corpus index). */
  index: number;
  naa: number;
  category: BatchCategory;
  label: string;
}

interface BatchScatterProps {
  items: BatchItem[];
  /** Fired when the user clicks a dot. The handler should fetch and dispatch. */
  onItemClick?: (item: BatchItem) => void;
  title?: string;
}

const CATEGORY_COLORS: Record<BatchCategory, string> = {
  'high-outrage': '#FF6E00',
  'fear-activating': '#FF453A',
  'reward-hook': '#FFD60A',
  neutral: 'rgba(255,255,255,0.7)',
};

const CATEGORY_LABELS: Record<BatchCategory, string> = {
  'high-outrage': 'High-outrage',
  'fear-activating': 'Fear-activating',
  'reward-hook': 'Reward-hook',
  neutral: 'Neutral',
};

/**
 * Scatter of every batch item by NAA score, coloured by category.
 *
 * Horizontal threshold lines mark NAA = 1.0 (LOW/MOD boundary) and
 * NAA = 2.0 (MOD/HIGH boundary). Clicking a dot calls the supplied
 * onItemClick handler -- the demo / scanner page is responsible for
 * fetching the activation binary and dispatching SCAN_COMPLETE_A.
 */
export function BatchScatter({
  items,
  onItemClick,
  title = 'Corpus NAA distribution',
}: BatchScatterProps) {
  const option = useMemo(() => {
    const grouped: Record<BatchCategory, BatchItem[]> = {
      'high-outrage': [],
      'fear-activating': [],
      'reward-hook': [],
      neutral: [],
    };
    for (const item of items) {
      // Defensive: any item with an unknown category falls into the
      // neutral bucket instead of crashing the chart. The TypeScript
      // type guarantees this can't happen statically, but data-source
      // bugs (e.g. signed-int RNG returning negative indices) have
      // shipped through in the past.
      const bucket = grouped[item.category] ?? grouped.neutral;
      bucket.push(item);
    }

    const series = (Object.keys(grouped) as BatchCategory[]).map((cat) => ({
      name: CATEGORY_LABELS[cat],
      type: 'scatter',
      symbolSize: 8,
      itemStyle: {
        color: CATEGORY_COLORS[cat],
        borderColor: 'rgba(0,0,0,0.6)',
        borderWidth: 1,
      },
      emphasis: {
        scale: 1.6,
      },
      data: grouped[cat].map((it) => ({
        value: [it.index, it.naa],
        item: it,
      })),
      ...(cat === 'neutral'
        ? {
            markLine: {
              silent: true,
              symbol: 'none',
              lineStyle: { color: 'rgba(255,255,255,0.25)', type: 'dashed' },
              label: {
                show: true,
                color: 'rgba(255,255,255,0.5)',
                fontSize: 9,
                position: 'end',
              },
              data: [
                { yAxis: 1.0, name: 'NAA = 1.0' },
                { yAxis: 2.0, name: 'NAA = 2.0' },
              ],
            },
          }
        : {}),
    }));

    return {
      ...monarchTheme,
      title: { ...monarchTheme.title, text: title },
      tooltip: {
        ...monarchTheme.tooltip,
        trigger: 'item',
        formatter: (params: { data: { item: BatchItem } }) => {
          const it = params.data.item;
          return `
            <div style="font-weight:600;">${it.label}</div>
            <div>category: ${CATEGORY_LABELS[it.category]}</div>
            <div>NAA: ${it.naa.toFixed(3)}</div>
            <div style="opacity:0.5;">click to load on brain</div>
          `;
        },
      },
      legend: {
        ...monarchTheme.legend,
        top: 20,
        textStyle: { color: 'rgba(255,255,255,0.65)', fontSize: 10 },
      },
      grid: { ...monarchTheme.grid, top: 56 },
      xAxis: {
        ...monarchTheme.xAxis,
        type: 'value',
        name: 'item index',
        nameLocation: 'middle',
        nameGap: 22,
        scale: true,
      },
      yAxis: {
        ...monarchTheme.yAxis,
        type: 'value',
        name: 'NAA',
        min: 0,
        max: (val: { max: number }) => Math.max(3, Math.ceil(val.max)),
      },
      series,
    };
  }, [items, title]);

  const onEvents = useMemo(
    () => ({
      click: (params: { data: { item?: BatchItem } }) => {
        const it = params.data?.item;
        if (it && onItemClick) onItemClick(it);
      },
    }),
    [onItemClick],
  );

  return (
    <div className={CHART_CARD_CLASS}>
      <div className="h-72 w-full">
        <ReactECharts
          option={option}
          onEvents={onEvents}
          style={{ height: '100%', width: '100%' }}
        />
      </div>
    </div>
  );
}
