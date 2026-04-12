'use client';

import { useMemo } from 'react';

import ReactECharts from './EchartsBase';
import { CHART_CARD_CLASS, monarchTheme } from './echarts-theme';

interface SusceptibilityChartProps {
  /** Current content's NAA score (drives the marker line). */
  naa: number;
  /** Optional precomputed chi(NAA) curve. If absent, a synthetic curve is generated. */
  curve?: { naa: number[]; chi: (number | null)[] } | null;
  /** Sweep range for the synthetic curve. */
  range?: [number, number];
  /** Number of sample points for the synthetic curve. */
  points?: number;
  title?: string;
}

const COLOR_CURVE = '#FFFFFF';
const COLOR_MARKER = '#FF6E00';

/**
 * Population susceptibility chi(NAA).
 *
 * The y-axis shows how strongly an Ising-style population responds to
 * the external field at a given NAA. The vertical marker shows the
 * current content's location on the curve, with a label so users can
 * read off "where this content sits" relative to the divergence.
 *
 * If no curve is supplied the component generates one analytically
 * using the same paramagnetic-regime formula the backend uses, so the
 * chart works in pure-frontend demo mode.
 */
export function SusceptibilityChart({
  naa,
  curve = null,
  range = [0, 5],
  points = 80,
  title = 'Susceptibility chi(NAA)',
}: SusceptibilityChartProps) {
  const option = useMemo(() => {
    const grid =
      curve ??
      generateSyntheticCurve(range[0], range[1], points, /* alpha */ 0.5, /* beta_J */ 0.7);

    const data: [number, number][] = [];
    for (let i = 0; i < grid.naa.length; i++) {
      const c = grid.chi[i];
      if (c == null || !Number.isFinite(c)) continue;
      data.push([grid.naa[i], c]);
    }

    return {
      ...monarchTheme,
      title: { ...monarchTheme.title, text: title },
      tooltip: {
        ...monarchTheme.tooltip,
        trigger: 'axis',
        formatter: (params: { data: [number, number] }[]) => {
          const p = params[0];
          if (!p) return '';
          return `NAA = ${p.data[0].toFixed(2)}<br/>chi = ${p.data[1].toFixed(3)}`;
        },
      },
      grid: { ...monarchTheme.grid, top: 36 },
      xAxis: {
        ...monarchTheme.xAxis,
        type: 'value',
        min: range[0],
        max: range[1],
        name: 'NAA',
        nameLocation: 'middle',
        nameGap: 22,
      },
      yAxis: {
        ...monarchTheme.yAxis,
        type: 'value',
        name: 'chi',
        scale: true,
      },
      series: [
        {
          type: 'line',
          data,
          smooth: true,
          showSymbol: false,
          lineStyle: { color: COLOR_CURVE, width: 2 },
          areaStyle: { color: 'rgba(255,255,255,0.04)' },
          markLine: {
            silent: true,
            symbol: ['none', 'circle'],
            lineStyle: { color: COLOR_MARKER, type: 'dashed', width: 1 },
            label: {
              color: COLOR_MARKER,
              formatter: `this content (NAA=${naa.toFixed(2)})`,
              fontSize: 10,
              position: 'end',
            },
            data: [{ xAxis: naa }],
          },
        },
      ],
    };
  }, [naa, curve, range, points, title]);

  return (
    <div className={CHART_CARD_CLASS}>
      <div className="h-56 w-full">
        <ReactECharts option={option} style={{ height: '100%', width: '100%' }} />
      </div>
    </div>
  );
}

/** Closed-form chi(NAA) for the paramagnetic regime (matches backend landau.py). */
function generateSyntheticCurve(
  naaMin: number,
  naaMax: number,
  n: number,
  alphaHat: number,
  betaJ: number,
): { naa: number[]; chi: (number | null)[] } {
  const naa: number[] = [];
  const chi: (number | null)[] = [];
  for (let i = 0; i < n; i++) {
    const v = naaMin + ((naaMax - naaMin) * i) / (n - 1);
    naa.push(v);

    // Fixed-point iteration for m*
    let m = 0;
    const h = alphaHat * v;
    for (let k = 0; k < 200; k++) {
      const next = Math.tanh(betaJ * m + h);
      if (Math.abs(next - m) < 1e-9) {
        m = next;
        break;
      }
      m = next;
    }

    const arg = betaJ * m + h;
    const sech2 = 1 / Math.pow(Math.cosh(arg), 2);
    const denom = 1 - betaJ * sech2;
    if (Math.abs(denom) < 1e-9) {
      chi.push(null);
    } else {
      chi.push(sech2 / denom);
    }
  }
  return { naa, chi };
}
