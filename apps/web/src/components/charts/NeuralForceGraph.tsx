'use client';

import { useMemo } from 'react';

import ReactECharts from './EchartsBase';
import { monarchTheme } from './echarts-theme';

interface NeuralForceGraphProps {
  /** How many nodes to render. Default 55, matching the spec. */
  nodeCount?: number;
  /** Average edge density (probability that any two nodes are connected). */
  edgeDensity?: number;
  className?: string;
}

/**
 * Animated force-directed graph used as the landing-page hero.
 *
 * Pure visual: no scan data, no shared store. Generates a deterministic
 * but plausible network of brain regions and lets ECharts run the
 * built-in force layout. Monochrome (white nodes, low-opacity white
 * edges) so it sits behind the headline without competing with it.
 */
export function NeuralForceGraph({
  nodeCount = 55,
  edgeDensity = 0.06,
  className = '',
}: NeuralForceGraphProps) {
  const option = useMemo(() => {
    // Deterministic pseudo-random so the layout is stable across reloads.
    const rng = mulberry32(0x42c0ffee);

    const nodes = Array.from({ length: nodeCount }, (_, i) => {
      // Importance ~ vertex count (drives node size)
      const importance = 50 + Math.floor(rng() * 350);
      return {
        id: String(i),
        name: `R${i}`,
        symbolSize: 4 + (importance / 400) * 14,
        value: importance,
        // Approximate brain layout: ellipse + small jitter
        x: Math.cos((i / nodeCount) * Math.PI * 2) * 220 + (rng() - 0.5) * 60,
        y: Math.sin((i / nodeCount) * Math.PI * 2) * 140 + (rng() - 0.5) * 40,
      };
    });

    const links: { source: string; target: string; value: number }[] = [];
    for (let i = 0; i < nodeCount; i++) {
      for (let j = i + 1; j < nodeCount; j++) {
        if (rng() < edgeDensity) {
          links.push({
            source: String(i),
            target: String(j),
            value: 0.3 + rng() * 0.7,
          });
        }
      }
    }

    return {
      ...monarchTheme,
      tooltip: { show: false },
      // Force graph has no axes; suppress the inherited theme defaults
      // so axis lines do not render behind the network.
      xAxis: { show: false },
      yAxis: { show: false },
      grid: { show: false, containLabel: false, top: 0, right: 0, bottom: 0, left: 0 },
      animationDurationUpdate: 1500,
      animationEasingUpdate: 'quinticInOut',
      series: [
        {
          type: 'graph',
          layout: 'force',
          force: {
            repulsion: 80,
            edgeLength: [40, 110],
            gravity: 0.06,
            friction: 0.5,
            layoutAnimation: true,
          },
          roam: false,
          draggable: false,
          nodes,
          links,
          itemStyle: {
            color: '#FFFFFF',
            borderColor: 'rgba(255,255,255,0.5)',
            borderWidth: 1,
            shadowBlur: 6,
            shadowColor: 'rgba(255,255,255,0.4)',
          },
          lineStyle: {
            color: 'rgba(255,255,255,0.12)',
            width: 0.6,
            curveness: 0.15,
          },
          emphasis: {
            focus: 'adjacency',
            lineStyle: { color: 'rgba(255,255,255,0.55)', width: 1.2 },
            itemStyle: { shadowBlur: 14, shadowColor: '#FFFFFF' },
          },
        },
      ],
    };
  }, [nodeCount, edgeDensity]);

  return (
    <div className={`h-full w-full ${className}`}>
      <ReactECharts
        option={option}
        style={{ height: '100%', width: '100%' }}
        opts={{ renderer: 'canvas' }}
      />
    </div>
  );
}

/** Tiny seeded PRNG so the network layout is reproducible across renders. */
function mulberry32(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
