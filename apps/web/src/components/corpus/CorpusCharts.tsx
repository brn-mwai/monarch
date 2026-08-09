'use client';

import ReactECharts from '@/components/charts/EchartsBase';

import type { CategorySummary, CorpusItem } from '@/lib/corpus-types';
import { CATEGORY_COLORS, categoryLabel } from '@/lib/corpus-types';

const AXIS = {
  axisLine: { lineStyle: { color: 'rgba(255,255,255,0.18)' } },
  axisLabel: { color: 'rgba(255,255,255,0.55)', fontSize: 10 },
  splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
};

const TOOLTIP = {
  backgroundColor: 'rgba(10,10,10,0.95)',
  borderColor: 'rgba(255,255,255,0.15)',
  textStyle: { color: '#fff', fontSize: 11 },
};

/** Every item as a point, so the reader sees the spread rather than a summary of it. */
export function SignedByCategory({ items }: { items: CorpusItem[] }) {
  const categories = Array.from(new Set(items.map((i) => i.category))).sort();

  const series = categories.map((category) => ({
    name: categoryLabel(category),
    type: 'scatter' as const,
    symbolSize: 7,
    itemStyle: { color: CATEGORY_COLORS[category] ?? '#888', opacity: 0.85 },
    data: items
      .filter((i) => i.category === category && i.naaSigned !== null)
      .map((i) => [categories.indexOf(category), i.naaSigned as number]),
  }));

  return (
    <ReactECharts
      style={{ height: 320 }}
      opts={{ renderer: 'canvas' }}
      option={{
        grid: { left: 62, right: 20, top: 20, bottom: 56 },
        tooltip: {
          ...TOOLTIP,
          formatter: (p: { seriesName: string; value: [number, number] }) =>
            `${p.seriesName}<br/>signed NAA ${p.value[1].toFixed(4)}`,
        },
        xAxis: {
          type: 'category',
          data: categories.map(categoryLabel),
          ...AXIS,
          axisLabel: { ...AXIS.axisLabel, interval: 0, rotate: 18 },
        },
        yAxis: {
          type: 'value',
          name: 'signed NAA',
          nameTextStyle: { color: 'rgba(255,255,255,0.45)', fontSize: 10 },
          ...AXIS,
        },
        series: [
          ...series,
          {
            name: 'zero',
            type: 'line',
            markLine: {
              silent: true,
              symbol: 'none',
              lineStyle: { color: 'rgba(255,255,255,0.3)', type: 'dashed' },
              data: [{ yAxis: 0 }],
              label: { show: false },
            },
            data: [],
          },
        ],
      }}
    />
  );
}

/**
 * Affective against deliberative, with the identity line.
 *
 * The index is the distance from that line, so plotting the two means against it shows
 * directly why every item so far falls on the deliberative side.
 */
export function AffectiveVsDeliberative({ items }: { items: CorpusItem[] }) {
  const usable = items.filter((i) => i.aAff !== null && i.aDel !== null);
  const values = usable.flatMap((i) => [i.aAff as number, i.aDel as number]);
  const lo = Math.min(...values);
  const hi = Math.max(...values);
  const categories = Array.from(new Set(usable.map((i) => i.category))).sort();

  return (
    <ReactECharts
      style={{ height: 340 }}
      opts={{ renderer: 'canvas' }}
      option={{
        grid: { left: 66, right: 20, top: 20, bottom: 52 },
        legend: {
          bottom: 0,
          textStyle: { color: 'rgba(255,255,255,0.55)', fontSize: 10 },
          icon: 'circle',
        },
        tooltip: {
          ...TOOLTIP,
          formatter: (p: { seriesName: string; value: [number, number] }) =>
            `${p.seriesName}<br/>affective ${p.value[0].toFixed(4)}<br/>` +
            `deliberative ${p.value[1].toFixed(4)}`,
        },
        xAxis: {
          type: 'value',
          name: 'affective mean',
          nameLocation: 'middle',
          nameGap: 30,
          nameTextStyle: { color: 'rgba(255,255,255,0.45)', fontSize: 10 },
          min: lo,
          max: hi,
          ...AXIS,
        },
        yAxis: {
          type: 'value',
          name: 'deliberative mean',
          nameTextStyle: { color: 'rgba(255,255,255,0.45)', fontSize: 10 },
          min: lo,
          max: hi,
          ...AXIS,
        },
        series: [
          ...categories.map((category) => ({
            name: categoryLabel(category),
            type: 'scatter' as const,
            symbolSize: 8,
            itemStyle: { color: CATEGORY_COLORS[category] ?? '#888', opacity: 0.85 },
            data: usable
              .filter((i) => i.category === category)
              .map((i) => [i.aAff as number, i.aDel as number]),
          })),
          {
            name: 'equal',
            type: 'line' as const,
            showSymbol: false,
            lineStyle: { color: 'rgba(255,255,255,0.28)', type: 'dashed', width: 1 },
            data: [
              [lo, lo],
              [hi, hi],
            ],
          },
        ],
      }}
    />
  );
}

/** Category means with their measured spread, so a difference is read against its noise. */
export function CategoryMeans({ categories }: { categories: CategorySummary[] }) {
  return (
    <ReactECharts
      style={{ height: 300 }}
      opts={{ renderer: 'canvas' }}
      option={{
        grid: { left: 62, right: 20, top: 20, bottom: 60 },
        tooltip: {
          ...TOOLTIP,
          formatter: (p: { name: string; value: number; dataIndex: number }) => {
            const c = categories[p.dataIndex];
            return (
              `${categoryLabel(c.category)}<br/>n = ${c.n}<br/>` +
              `mean ${c.mean.toFixed(4)}<br/>` +
              `sd ${c.sd === null ? '--' : c.sd.toFixed(4)}`
            );
          },
        },
        xAxis: {
          type: 'category',
          data: categories.map((c) => categoryLabel(c.category)),
          ...AXIS,
          axisLabel: { ...AXIS.axisLabel, interval: 0, rotate: 18 },
        },
        yAxis: {
          type: 'value',
          name: 'mean signed NAA',
          nameTextStyle: { color: 'rgba(255,255,255,0.45)', fontSize: 10 },
          ...AXIS,
        },
        series: [
          {
            type: 'bar',
            barWidth: '46%',
            data: categories.map((c) => ({
              value: c.mean,
              itemStyle: { color: CATEGORY_COLORS[c.category] ?? '#888' },
            })),
          },
          {
            type: 'custom',
            renderItem: (
              params: unknown,
              api: { value: (i: number) => number; coord: (p: number[]) => number[] },
            ) => {
              const index = api.value(0);
              const c = categories[index];
              if (!c || c.sd === null) return null;
              const top = api.coord([index, c.mean + c.sd]);
              const bottom = api.coord([index, c.mean - c.sd]);
              const style = { stroke: 'rgba(255,255,255,0.7)', lineWidth: 1 };
              return {
                type: 'group',
                children: [
                  {
                    type: 'line',
                    shape: { x1: top[0], y1: top[1], x2: bottom[0], y2: bottom[1] },
                    style,
                  },
                  {
                    type: 'line',
                    shape: { x1: top[0] - 6, y1: top[1], x2: top[0] + 6, y2: top[1] },
                    style,
                  },
                  {
                    type: 'line',
                    shape: {
                      x1: bottom[0] - 6,
                      y1: bottom[1],
                      x2: bottom[0] + 6,
                      y2: bottom[1],
                    },
                    style,
                  },
                ],
              };
            },
            data: categories.map((_, index) => [index]),
          },
        ],
      }}
    />
  );
}
