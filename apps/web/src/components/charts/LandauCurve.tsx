'use client';

import { useMemo } from 'react';

import type { LandauData } from '@/lib/scan-store';

import ReactECharts from './EchartsBase';
import { CHART_CARD_CLASS, monarchTheme } from './echarts-theme';

interface LandauCurveProps {
  /** Free energy data for the primary content (Content A). */
  data: LandauData;
  /** Optional second curve for compare mode (Content B). */
  comparisonData?: LandauData | null;
  title?: string;
}

const COLOR_A = '#FFFFFF';
const COLOR_B = '#FF6E00';

/**
 * Landau free-energy curve F(m) vs m.
 *
 * Shows how the NAA field tilts the symmetric Ising potential. The
 * equilibrium polarization m* is marked with a labelled point on the
 * curve. In compare mode a second curve is overlaid in fire-orange.
 */
export function LandauCurve({
  data,
  comparisonData = null,
  title = 'Landau free energy F(m)',
}: LandauCurveProps) {
  const option = useMemo(() => {
    const seriesA = data.free_energy_m.map((m, i) => [m, data.free_energy_F[i]]);
    const equilibriumA: [number, number] = [
      data.equilibrium_m,
      // y-value at the equilibrium m: linear-interpolate F(m*) from the grid
      interpolateF(data.free_energy_m, data.free_energy_F, data.equilibrium_m),
    ];

    const series: Record<string, unknown>[] = [
      {
        name: 'Content A',
        type: 'line',
        data: seriesA,
        smooth: true,
        showSymbol: false,
        lineStyle: { color: COLOR_A, width: 2 },
        areaStyle: { color: 'rgba(255,255,255,0.05)' },
        markPoint: {
          symbol: 'circle',
          symbolSize: 10,
          data: [
            {
              coord: equilibriumA,
              itemStyle: { color: COLOR_A, borderColor: '#000000', borderWidth: 2 },
              label: {
                show: true,
                position: 'top',
                color: COLOR_A,
                formatter: `m* = ${data.equilibrium_m.toFixed(3)}`,
                fontSize: 10,
              },
            },
          ],
        },
      },
    ];

    if (comparisonData) {
      const seriesB = comparisonData.free_energy_m.map((m, i) => [
        m,
        comparisonData.free_energy_F[i],
      ]);
      const equilibriumB: [number, number] = [
        comparisonData.equilibrium_m,
        interpolateF(
          comparisonData.free_energy_m,
          comparisonData.free_energy_F,
          comparisonData.equilibrium_m,
        ),
      ];
      series.push({
        name: 'Content B',
        type: 'line',
        data: seriesB,
        smooth: true,
        showSymbol: false,
        lineStyle: { color: COLOR_B, width: 2 },
        areaStyle: { color: 'rgba(255,110,0,0.06)' },
        markPoint: {
          symbol: 'circle',
          symbolSize: 10,
          data: [
            {
              coord: equilibriumB,
              itemStyle: { color: COLOR_B, borderColor: '#000000', borderWidth: 2 },
              label: {
                show: true,
                position: 'bottom',
                color: COLOR_B,
                formatter: `m* = ${comparisonData.equilibrium_m.toFixed(3)}`,
                fontSize: 10,
              },
            },
          ],
        },
      });
    }

    return {
      ...monarchTheme,
      title: { ...monarchTheme.title, text: title },
      tooltip: {
        ...monarchTheme.tooltip,
        trigger: 'axis',
        formatter: (params: { seriesName: string; data: [number, number] }[]) =>
          params
            .map(
              (p) =>
                `${p.seriesName}<br/>m = ${p.data[0].toFixed(3)}<br/>F = ${p.data[1].toFixed(4)}`,
            )
            .join('<br/><br/>'),
      },
      legend: comparisonData
        ? { ...monarchTheme.legend, top: 18, data: ['Content A', 'Content B'] }
        : { show: false },
      grid: { ...monarchTheme.grid, top: 48 },
      xAxis: {
        ...monarchTheme.xAxis,
        type: 'value',
        min: -1,
        max: 1,
        name: 'm  (deliberative <- -> reactive)',
        nameLocation: 'middle',
        nameGap: 24,
      },
      yAxis: {
        ...monarchTheme.yAxis,
        type: 'value',
        name: 'F(m)',
        scale: true,
      },
      series,
    };
  }, [data, comparisonData, title]);

  return (
    <div className={CHART_CARD_CLASS}>
      <div className="h-64 w-full">
        <ReactECharts option={option} style={{ height: '100%', width: '100%' }} />
      </div>
    </div>
  );
}

/** Linear interpolation of F at a given m using the sampled grid. */
function interpolateF(mGrid: number[], fGrid: number[], mTarget: number): number {
  if (mGrid.length === 0) return 0;
  if (mTarget <= mGrid[0]) return fGrid[0];
  if (mTarget >= mGrid[mGrid.length - 1]) return fGrid[fGrid.length - 1];
  for (let i = 0; i < mGrid.length - 1; i++) {
    if (mGrid[i] <= mTarget && mTarget <= mGrid[i + 1]) {
      const t = (mTarget - mGrid[i]) / (mGrid[i + 1] - mGrid[i] || 1);
      return fGrid[i] + (fGrid[i + 1] - fGrid[i]) * t;
    }
  }
  return fGrid[fGrid.length - 1];
}
