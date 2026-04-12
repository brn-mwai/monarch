'use client';

import { useMemo } from 'react';

import ReactECharts from './EchartsBase';
import { monarchTheme } from './echarts-theme';

interface NAADistributionMiniProps {
  /** Optional explicit height (px). Defaults to 220. */
  height?: number;
}

/**
 * Compact distribution chart for the landing page. Shows two synthetic
 * NAA histograms (a "neutral" wire-corpus-shaped curve and a
 * right-skewed "outrage feed" curve) so the reader can see at a glance
 * what NAA looks like across a population of content items.
 *
 * Pure visual - no shared store, no real data. The numbers are
 * deterministic so SSR and client renders agree.
 */
export function NAADistributionMini({ height = 220 }: NAADistributionMiniProps) {
  const option = useMemo(() => {
    const xs: number[] = [];
    const wireA: number[] = [];
    const outrageB: number[] = [];

    // Wire-style distribution: tight Gaussian centred on NAA=0.9
    const wireMu = 0.9;
    const wireSigma = 0.35;
    // Outrage-feed distribution: broader Gaussian centred on NAA=2.6
    const outrageMu = 2.6;
    const outrageSigma = 0.55;

    for (let i = 0; i <= 60; i++) {
      const naa = (i / 60) * 5;
      xs.push(naa);
      wireA.push(gauss(naa, wireMu, wireSigma) * 60);
      outrageB.push(gauss(naa, outrageMu, outrageSigma) * 80);
    }

    return {
      ...monarchTheme,
      title: { show: false },
      tooltip: {
        ...monarchTheme.tooltip,
        trigger: 'axis',
        formatter: (params: { seriesName: string; data: number; axisValue: string }[]) => {
          const naa = parseFloat(params[0]?.axisValue ?? '0').toFixed(2);
          return params
            .map(
              (p) => `${p.seriesName}<br/>NAA &asymp; ${naa}<br/>density ${p.data.toFixed(1)}`,
            )
            .join('<br/><br/>');
        },
      },
      legend: {
        ...monarchTheme.legend,
        top: 4,
        textStyle: { color: 'rgba(255,255,255,0.6)', fontSize: 10 },
        data: ['Reuters wire', 'Outrage feed'],
      },
      grid: { ...monarchTheme.grid, top: 28, bottom: 28, right: 12, left: 36 },
      xAxis: {
        ...monarchTheme.xAxis,
        type: 'category',
        data: xs.map((x) => x.toFixed(1)),
        boundaryGap: false,
        axisLabel: {
          ...monarchTheme.xAxis.axisLabel,
          interval: 11,
          formatter: (v: string) => parseFloat(v).toFixed(0),
        },
        name: 'NAA',
        nameLocation: 'middle',
        nameGap: 20,
        nameTextStyle: { color: 'rgba(255,255,255,0.5)', fontSize: 10 },
      },
      yAxis: {
        ...monarchTheme.yAxis,
        type: 'value',
        axisLabel: { show: false },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } },
      },
      series: [
        {
          name: 'Reuters wire',
          type: 'line',
          smooth: true,
          showSymbol: false,
          lineStyle: { color: '#FFFFFF', width: 2 },
          areaStyle: { color: 'rgba(255,255,255,0.06)' },
          data: wireA,
        },
        {
          name: 'Outrage feed',
          type: 'line',
          smooth: true,
          showSymbol: false,
          lineStyle: { color: '#FF6E00', width: 2 },
          areaStyle: { color: 'rgba(255,110,0,0.08)' },
          data: outrageB,
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
              { xAxis: '12', name: 'NAA = 1' },
              { xAxis: '24', name: 'NAA = 2' },
            ],
          },
        },
      ],
    };
  }, []);

  return (
    <div className="w-full" style={{ height }}>
      <ReactECharts option={option} style={{ height: '100%', width: '100%' }} />
    </div>
  );
}

function gauss(x: number, mu: number, sigma: number): number {
  const exponent = -((x - mu) ** 2) / (2 * sigma ** 2);
  return (1 / (sigma * Math.sqrt(2 * Math.PI))) * Math.exp(exponent);
}
