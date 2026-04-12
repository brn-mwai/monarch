'use client';

import { useMemo } from 'react';

import { useScanState, type ROIData } from '@/lib/scan-store';

import ReactECharts from './EchartsBase';
import { CHART_CARD_CLASS, monarchTheme } from './echarts-theme';

interface ROIBreakdownProps {
  roiData: ROIData[];
  title?: string;
}

const COLOR_AFFECTIVE = '#FF6E00';
const COLOR_DELIBERATIVE = 'rgba(255,255,255,0.85)';

/**
 * Horizontal bar chart of per-ROI mean activation, sorted descending.
 *
 * Affective-salience ROIs render in fire-orange; deliberative-control
 * ROIs render in white. Hovering a bar dispatches SET_HIGHLIGHT_ROI to
 * the shared scan store so the brain renderer can highlight the
 * corresponding region (if/when the highlight pipeline ships).
 */
export function ROIBreakdown({
  roiData,
  title = 'ROI activation',
}: ROIBreakdownProps) {
  const { dispatch } = useScanState();

  const option = useMemo(() => {
    const sorted = [...roiData].sort((a, b) => b.activation - a.activation);

    return {
      ...monarchTheme,
      title: { ...monarchTheme.title, text: title },
      tooltip: {
        ...monarchTheme.tooltip,
        trigger: 'item',
        formatter: (params: {
          name: string;
          value: number;
          data: { system: string; vertexCount: number };
        }) => `
          <div style="font-weight:600;">${params.name}</div>
          <div>system: ${params.data.system}</div>
          <div>activation: ${params.value.toFixed(3)}</div>
          <div>${params.data.vertexCount} vertices</div>
        `,
      },
      grid: { ...monarchTheme.grid, top: 36, left: 64, right: 24, bottom: 20 },
      xAxis: {
        ...monarchTheme.xAxis,
        type: 'value',
        max: (val: { max: number }) => Math.max(1, val.max * 1.05),
      },
      yAxis: {
        ...monarchTheme.yAxis,
        type: 'category',
        data: sorted.map((r) => r.name),
        inverse: true,
        axisLabel: {
          ...monarchTheme.yAxis.axisLabel,
          fontSize: 10,
        },
      },
      series: [
        {
          type: 'bar',
          barMaxWidth: 14,
          data: sorted.map((r) => ({
            value: r.activation,
            system: r.system,
            vertexCount: r.vertexCount,
            itemStyle: {
              color: r.system === 'affective' ? COLOR_AFFECTIVE : COLOR_DELIBERATIVE,
              borderRadius: [0, 3, 3, 0],
            },
          })),
        },
      ],
    };
  }, [roiData, title]);

  const onEvents = useMemo(
    () => ({
      mouseover: (params: { name: string }) => {
        dispatch({ type: 'SET_HIGHLIGHT_ROI', roi: params.name });
      },
      mouseout: () => {
        dispatch({ type: 'SET_HIGHLIGHT_ROI', roi: null });
      },
    }),
    [dispatch],
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
      <div className="mt-2 flex gap-4 text-[10px] uppercase tracking-wider">
        <span className="flex items-center gap-1.5">
          <span
            className="inline-block h-2 w-3 rounded-sm"
            style={{ background: COLOR_AFFECTIVE }}
          />
          <span className="text-white/60">Affective-salience</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span
            className="inline-block h-2 w-3 rounded-sm"
            style={{ background: COLOR_DELIBERATIVE }}
          />
          <span className="text-white/60">Deliberative-control</span>
        </span>
      </div>
    </div>
  );
}
