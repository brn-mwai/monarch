'use client';

import { useEffect, useState } from 'react';

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
  confine: true,
};

/** Axis names on a phone, where the full category names collide under each other. */
const SHORT_LABELS: Record<string, string> = {
  fear_activating: 'Fear',
  high_outrage: 'Outrage',
  neutral_informational: 'Neutral',
  reward_hook: 'Reward',
};

function axisCategory(category: string, narrow: boolean): string {
  return narrow ? (SHORT_LABELS[category] ?? categoryLabel(category)) : categoryLabel(category);
}

/** True below the Tailwind `sm` breakpoint, where the charts switch to a compact layout. */
function useNarrow(): boolean {
  const [narrow, setNarrow] = useState(false);
  useEffect(() => {
    const query = window.matchMedia('(max-width: 639px)');
    const update = () => setNarrow(query.matches);
    update();
    query.addEventListener('change', update);
    return () => query.removeEventListener('change', update);
  }, []);
  return narrow;
}

function axisFor(narrow: boolean) {
  return {
    ...AXIS,
    axisLabel: { ...AXIS.axisLabel, fontSize: narrow ? 11 : 10 },
  };
}

/** Every item as a point, so the reader sees the spread rather than a summary of it. */
export function SignedByCategory({ items }: { items: CorpusItem[] }) {
  const narrow = useNarrow();
  const axis = axisFor(narrow);
  const categories = Array.from(new Set(items.map((i) => i.category))).sort();

  const series = categories.map((category) => ({
    name: categoryLabel(category),
    type: 'scatter' as const,
    symbolSize: narrow ? 6 : 7,
    itemStyle: { color: CATEGORY_COLORS[category] ?? '#888', opacity: 0.85 },
    data: items
      .filter((i) => i.category === category && i.naaSigned !== null)
      .map((i) => [categories.indexOf(category), i.naaSigned as number]),
  }));

  return (
    <ReactECharts
      key={narrow ? 'narrow' : 'wide'}
      style={{ height: narrow ? 280 : 320 }}
      opts={{ renderer: 'canvas' }}
      option={{
        grid: narrow
          ? { left: 8, right: 8, top: 32, bottom: 8, containLabel: true }
          : { left: 62, right: 20, top: 20, bottom: 56 },
        tooltip: {
          ...TOOLTIP,
          formatter: (p: { seriesName: string; value: [number, number] }) =>
            `${p.seriesName}<br/>signed NAA ${p.value[1].toFixed(4)}`,
        },
        xAxis: {
          type: 'category',
          data: categories.map((c) => axisCategory(c, narrow)),
          ...axis,
          axisLabel: { ...axis.axisLabel, interval: 0, rotate: narrow ? 0 : 18 },
        },
        yAxis: {
          type: 'value',
          name: 'signed NAA',
          nameTextStyle: {
            color: 'rgba(255,255,255,0.45)',
            fontSize: 10,
            ...(narrow ? { align: 'left' as const } : {}),
          },
          splitNumber: narrow ? 4 : undefined,
          ...axis,
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
  const narrow = useNarrow();
  const axis = narrow
    ? {
        ...axisFor(true),
        splitNumber: 3,
        axisLabel: {
          ...axisFor(true).axisLabel,
          hideOverlap: true,
          formatter: (v: number) => v.toFixed(3),
        },
      }
    : AXIS;

  return (
    <ReactECharts
      key={narrow ? 'narrow' : 'wide'}
      style={{ height: narrow ? 320 : 340 }}
      opts={{ renderer: 'canvas' }}
      option={{
        grid: narrow
          ? { left: 8, right: 16, top: 32, bottom: 72, containLabel: true }
          : { left: 66, right: 20, top: 20, bottom: 52 },
        legend: {
          bottom: 0,
          textStyle: { color: 'rgba(255,255,255,0.55)', fontSize: narrow ? 11 : 10 },
          icon: 'circle',
          itemGap: narrow ? 12 : 10,
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
          nameGap: narrow ? 26 : 30,
          nameTextStyle: { color: 'rgba(255,255,255,0.45)', fontSize: 10 },
          min: lo,
          max: hi,
          ...axis,
        },
        yAxis: {
          type: 'value',
          name: 'deliberative mean',
          nameTextStyle: {
            color: 'rgba(255,255,255,0.45)',
            fontSize: 10,
            ...(narrow ? { align: 'left' as const } : {}),
          },
          min: lo,
          max: hi,
          ...axis,
        },
        series: [
          ...categories.map((category) => ({
            name: categoryLabel(category),
            type: 'scatter' as const,
            symbolSize: narrow ? 6 : 8,
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
  const narrow = useNarrow();
  const axis = axisFor(narrow);

  return (
    <ReactECharts
      key={narrow ? 'narrow' : 'wide'}
      style={{ height: narrow ? 280 : 300 }}
      opts={{ renderer: 'canvas' }}
      option={{
        grid: narrow
          ? { left: 8, right: 8, top: 32, bottom: 8, containLabel: true }
          : { left: 62, right: 20, top: 20, bottom: 60 },
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
          data: categories.map((c) => axisCategory(c.category, narrow)),
          ...axis,
          axisLabel: { ...axis.axisLabel, interval: 0, rotate: narrow ? 0 : 18 },
        },
        yAxis: {
          type: 'value',
          name: 'mean signed NAA',
          nameTextStyle: {
            color: 'rgba(255,255,255,0.45)',
            fontSize: 10,
            ...(narrow ? { align: 'left' as const } : {}),
          },
          splitNumber: narrow ? 4 : undefined,
          ...axis,
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
              const cap = narrow ? 4 : 6;
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
                    shape: { x1: top[0] - cap, y1: top[1], x2: top[0] + cap, y2: top[1] },
                    style,
                  },
                  {
                    type: 'line',
                    shape: {
                      x1: bottom[0] - cap,
                      y1: bottom[1],
                      x2: bottom[0] + cap,
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
