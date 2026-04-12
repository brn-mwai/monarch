'use client';

import { useMemo } from 'react';

import ReactECharts from './EchartsBase';
import { CHART_CARD_CLASS, NAA_COLORS, monarchTheme } from './echarts-theme';

interface NAAGaugeProps {
  /** Current NAA score (0..5 typical range, but accepts any positive value). */
  naa: number;
  /** Optional explicit classification; derived from naa if omitted. */
  classification?: 'LOW' | 'MOD' | 'HIGH';
  /** Optional title shown above the gauge. */
  title?: string;
}

function classify(naa: number): 'LOW' | 'MOD' | 'HIGH' {
  if (naa < 1.0) return 'LOW';
  if (naa <= 2.0) return 'MOD';
  return 'HIGH';
}

/**
 * Semicircular NAA gauge.
 *
 * Three colored zones across the arc:
 *   - 0.0 .. 0.2 of the dial (NAA 0..1) = LOW
 *   - 0.2 .. 0.4 of the dial (NAA 1..2) = MOD
 *   - 0.4 .. 1.0 of the dial (NAA 2..5) = HIGH
 *
 * Big number in the center, classification label below.
 */
export function NAAGauge({ naa, classification, title = 'NAA' }: NAAGaugeProps) {
  const cls = classification ?? classify(naa);

  const option = useMemo(() => {
    const naaClamped = Math.max(0, Math.min(5, naa));

    return {
      ...monarchTheme,
      title: { ...monarchTheme.title, text: title },
      // Gauge has no Cartesian axes; explicitly hide the inherited
      // xAxis/yAxis from the shared theme so their grid lines do not
      // bleed through behind the dial.
      xAxis: { show: false },
      yAxis: { show: false },
      grid: { show: false, containLabel: false, top: 0, right: 0, bottom: 0, left: 0 },
      series: [
        {
          type: 'gauge',
          startAngle: 200,
          endAngle: -20,
          min: 0,
          max: 5,
          radius: '92%',
          center: ['50%', '62%'],
          progress: { show: false },
          axisLine: {
            lineStyle: {
              width: 14,
              color: [
                [0.2, NAA_COLORS.LOW],
                [0.4, NAA_COLORS.MOD],
                [1, NAA_COLORS.HIGH],
              ],
            },
          },
          axisTick: {
            show: true,
            length: 6,
            lineStyle: { color: 'rgba(255,255,255,0.4)', width: 1 },
          },
          splitLine: {
            length: 12,
            lineStyle: { color: 'rgba(255,255,255,0.7)', width: 2 },
          },
          axisLabel: {
            distance: 22,
            color: 'rgba(255,255,255,0.55)',
            fontSize: 9,
            fontFamily: monarchTheme.textStyle.fontFamily,
          },
          pointer: {
            itemStyle: { color: '#FFFFFF' },
            length: '64%',
            width: 4,
          },
          anchor: {
            show: true,
            showAbove: true,
            size: 10,
            itemStyle: { color: '#FFFFFF' },
          },
          detail: {
            valueAnimation: true,
            formatter: (val: number) => val.toFixed(2),
            color: '#FFFFFF',
            fontSize: 28,
            fontWeight: 600,
            fontFamily: monarchTheme.textStyle.fontFamily,
            offsetCenter: [0, '36%'],
          },
          data: [{ value: naaClamped }],
        },
      ],
    };
  }, [naa, title]);

  return (
    <div className={CHART_CARD_CLASS}>
      <div className="relative h-56 w-full">
        <ReactECharts option={option} style={{ height: '100%', width: '100%' }} />
      </div>
      <div className="mt-1 flex items-center justify-center gap-2 text-xs">
        <span className="uppercase tracking-wider text-white/50">Classification</span>
        <span
          className="font-mono text-sm font-semibold"
          style={{ color: NAA_COLORS[cls] }}
        >
          {cls}
        </span>
      </div>
    </div>
  );
}
