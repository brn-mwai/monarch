'use client';

import { useMemo } from 'react';

import ReactECharts from './EchartsBase';
import {
  CHART_CARD_CLASS,
  MULTIMODAL_COLORS,
  monarchTheme,
} from './echarts-theme';

interface MultimodalBarsProps {
  textNAA: number;
  audioNAA: number;
  videoNAA: number;
  combinedNAA: number;
  title?: string;
}

/**
 * Per-modality NAA contribution bar chart.
 *
 * Bars colored to match the brain's RGB multimodal pipeline:
 *   R = video
 *   G = text
 *   B = audio
 *   white = combined
 *
 * Only meaningful when the scan was run with multimodal data; the demo
 * page hides this chart in single-mode.
 */
export function MultimodalBars({
  textNAA,
  audioNAA,
  videoNAA,
  combinedNAA,
  title = 'Per-modality NAA',
}: MultimodalBarsProps) {
  const option = useMemo(() => {
    const data = [
      { name: 'Video', value: videoNAA, color: MULTIMODAL_COLORS.video },
      { name: 'Text', value: textNAA, color: MULTIMODAL_COLORS.text },
      { name: 'Audio', value: audioNAA, color: MULTIMODAL_COLORS.audio },
      { name: 'Combined', value: combinedNAA, color: '#FFFFFF' },
    ];

    return {
      ...monarchTheme,
      title: { ...monarchTheme.title, text: title },
      tooltip: {
        ...monarchTheme.tooltip,
        trigger: 'item',
        formatter: (params: { name: string; value: number }) =>
          `${params.name}<br/>NAA = ${params.value.toFixed(3)}`,
      },
      grid: { ...monarchTheme.grid, top: 36, bottom: 30 },
      xAxis: {
        ...monarchTheme.xAxis,
        type: 'category',
        data: data.map((d) => d.name),
      },
      yAxis: {
        ...monarchTheme.yAxis,
        type: 'value',
        name: 'NAA',
      },
      series: [
        {
          type: 'bar',
          barMaxWidth: 32,
          data: data.map((d) => ({
            value: d.value,
            itemStyle: { color: d.color, borderRadius: [3, 3, 0, 0] },
          })),
          label: {
            show: true,
            position: 'top',
            color: 'rgba(255,255,255,0.7)',
            fontSize: 10,
            formatter: (p: { value: number }) => p.value.toFixed(2),
          },
        },
      ],
    };
  }, [textNAA, audioNAA, videoNAA, combinedNAA, title]);

  return (
    <div className={CHART_CARD_CLASS}>
      <div className="h-56 w-full">
        <ReactECharts option={option} style={{ height: '100%', width: '100%' }} />
      </div>
    </div>
  );
}
