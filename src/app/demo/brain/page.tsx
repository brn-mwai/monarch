'use client';

import { useEffect, useState } from 'react';

import { BatchScatter, type BatchItem } from '@/components/charts/BatchScatter';
import { LandauCurve } from '@/components/charts/LandauCurve';
import { MultimodalBars } from '@/components/charts/MultimodalBars';
import { NAAGauge } from '@/components/charts/NAAGauge';
import { NeuralForceGraph } from '@/components/charts/NeuralForceGraph';
import { ROIBreakdown } from '@/components/charts/ROIBreakdown';
import { SusceptibilityChart } from '@/components/charts/SusceptibilityChart';
import { SplitLayout } from '@/components/SplitLayout';
import {
  DEMO_BLOBS,
  generateSpatialActivation,
  loadBrainCoords,
  type BrainCoords,
} from '@/lib/brain-data';
import {
  getActiveResult,
  useScanState,
  type ScanResult,
} from '@/lib/scan-store';

const HEMI_VERTS = 10242;
const TOTAL_VERTS = 2 * HEMI_VERTS;

// === Synthetic data generators ==============================================

/** Build a synthetic ScanResult for the demo (no backend round-trip needed). */
function buildSyntheticScan(
  scanId: string,
  inputContent: string,
  naaValue: number,
  activationVector: Float32Array | null,
): ScanResult {
  const a_del = 0.6;
  const a_aff = a_del * naaValue;

  // Landau curve sampled on a 200-point grid (matches backend)
  const m: number[] = [];
  const F: number[] = [];
  const beta_j = 0.7;
  const alpha_hat = 0.5;
  const a_lan = 1 - beta_j;
  const b_lan = (beta_j ** 3) / 3;
  const h = alpha_hat * naaValue;
  for (let i = 0; i < 200; i++) {
    const mi = -1 + (2 * i) / 199;
    m.push(mi);
    F.push(a_lan * mi * mi + b_lan * Math.pow(mi, 4) - h * mi);
  }

  // Equilibrium m* via fixed-point iteration
  let mStar = 0;
  for (let k = 0; k < 200; k++) {
    const next = Math.tanh(beta_j * mStar + h);
    if (Math.abs(next - mStar) < 1e-9) {
      mStar = next;
      break;
    }
    mStar = next;
  }

  return {
    scanId,
    inputContent,
    modality: 'text',
    nTrs: 24,
    activationVector,
    naa: {
      naa: naaValue,
      a_aff,
      a_del,
      classification: naaValue < 1 ? 'LOW' : naaValue <= 2 ? 'MOD' : 'HIGH',
    },
    landau: {
      free_energy_m: m,
      free_energy_F: F,
      equilibrium_m: mStar,
      susceptibility: 1 / (1 - beta_j),
      external_field_h: h,
      beta_j,
      alpha_hat,
    },
    roiBreakdown: [
      { name: 'OFC', activation: 0.65 * naaValue * 0.5, system: 'affective', vertexCount: 312 },
      { name: 'AAIC', activation: 0.72 * naaValue * 0.5, system: 'affective', vertexCount: 198 },
      { name: 'a24', activation: 0.58 * naaValue * 0.5, system: 'affective', vertexCount: 245 },
      { name: 'TGd', activation: 0.81 * naaValue * 0.5, system: 'affective', vertexCount: 167 },
      { name: 'TE1a', activation: 0.69 * naaValue * 0.5, system: 'affective', vertexCount: 203 },
      { name: '46', activation: 0.42, system: 'deliberative', vertexCount: 289 },
      { name: '9-46v', activation: 0.38, system: 'deliberative', vertexCount: 234 },
      { name: 'd32', activation: 0.45, system: 'deliberative', vertexCount: 178 },
      { name: '10p', activation: 0.35, system: 'deliberative', vertexCount: 156 },
      { name: '13l', activation: 0.41, system: 'deliberative', vertexCount: 201 },
    ],
  };
}

function buildSyntheticBatchItems(): BatchItem[] {
  const items: BatchItem[] = [];
  const categories: BatchItem['category'][] = [
    'high-outrage',
    'fear-activating',
    'reward-hook',
    'neutral',
  ];
  // Deterministic-ish synthetic distribution. Note the bare `seed /
  // 0x100000000` -- using `(seed & 0xffffffff)` here would coerce the
  // already-unsigned seed back to a signed int and produce negative
  // rng() values, which then breaks Math.floor(rng()*4) -> negative
  // category index -> undefined item.category at render time.
  let seed = 0xdeadbeef;
  const rng = () => {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return seed / 0x100000000;
  };
  for (let i = 0; i < 80; i++) {
    const cat = categories[Math.floor(rng() * 4)];
    const baseNaa =
      cat === 'high-outrage'
        ? 2.6
        : cat === 'fear-activating'
        ? 2.2
        : cat === 'reward-hook'
        ? 1.7
        : 0.85;
    const naa = Math.max(0.1, baseNaa + (rng() - 0.5) * 0.9);
    items.push({
      id: `item-${i.toString().padStart(3, '0')}`,
      index: i,
      naa,
      category: cat,
      label: `corpus item ${i}`,
    });
  }
  return items;
}

const DEMO_NAA_PRESETS = [
  { label: 'Low (deliberative)', naa: 0.7 },
  { label: 'Moderate', naa: 1.5 },
  { label: 'High (affective)', naa: 3.1 },
];

// === Page ===================================================================

export default function BrainDemoPage() {
  const { state, dispatch } = useScanState();
  const [coords, setCoords] = useState<BrainCoords | null>(null);
  const [batchItems] = useState<BatchItem[]>(() => buildSyntheticBatchItems());

  // Load fsaverage5 coords once so generateSpatialActivation can run
  useEffect(() => {
    let cancelled = false;
    loadBrainCoords()
      .then((c) => {
        if (!cancelled) setCoords(c);
      })
      .catch((err: unknown) => {
        console.error('demo: failed to load brain coords', err);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const loadPreset = (label: string, naaValue: number) => {
    if (!coords) return;
    const activation = generateSpatialActivation(coords, DEMO_BLOBS);
    const result = buildSyntheticScan(
      `demo-${label.toLowerCase().replace(/\s+/g, '-')}`,
      label,
      naaValue,
      activation,
    );
    dispatch({ type: 'SCAN_COMPLETE_A', result });
  };

  const loadCompare = () => {
    if (!coords) return;
    const aActivation = generateSpatialActivation(coords, DEMO_BLOBS);
    const bActivation = generateSpatialActivation(coords, DEMO_BLOBS);
    dispatch({
      type: 'SCAN_COMPLETE_A',
      result: buildSyntheticScan('demo-compare-a', 'Article A', 0.9, aActivation),
    });
    dispatch({
      type: 'SCAN_COMPLETE_B',
      result: buildSyntheticScan('demo-compare-b', 'Article B', 2.7, bActivation),
    });
  };

  const loadMultimodal = () => {
    if (!coords) return;
    const text = new Float32Array(TOTAL_VERTS);
    const audio = new Float32Array(TOTAL_VERTS);
    const video = new Float32Array(TOTAL_VERTS);
    for (let i = 0; i < TOTAL_VERTS; i++) {
      if (i < 3000 || (i >= HEMI_VERTS && i < HEMI_VERTS + 3000)) {
        text[i] = 0.5 + Math.random() * 0.5;
      } else {
        text[i] = Math.random() * 0.15;
      }
      if (
        (i >= 3000 && i < 5500) ||
        (i >= HEMI_VERTS + 3000 && i < HEMI_VERTS + 5500)
      ) {
        audio[i] = 0.5 + Math.random() * 0.5;
      } else {
        audio[i] = Math.random() * 0.15;
      }
      if ((i >= 7000 && i < HEMI_VERTS) || (i >= HEMI_VERTS + 7000 && i < TOTAL_VERTS)) {
        video[i] = 0.5 + Math.random() * 0.5;
      } else {
        video[i] = Math.random() * 0.15;
      }
    }

    const result: ScanResult = {
      ...buildSyntheticScan('demo-multimodal', 'Multimodal sample', 1.8, null),
      multimodal: { text, audio, video },
    };
    dispatch({ type: 'SCAN_COMPLETE_A', result });
    dispatch({ type: 'SET_COLOR_MODE', mode: 'multimodal' });
  };

  const handleBatchItemClick = (item: BatchItem) => {
    if (!coords) return;
    const activation = generateSpatialActivation(coords, DEMO_BLOBS);
    const result = buildSyntheticScan(item.id, item.label, item.naa, activation);
    dispatch({ type: 'SCAN_COMPLETE_A', result });
    dispatch({ type: 'SET_COLOR_MODE', mode: 'activation' });
  };

  const handleClear = () => {
    dispatch({ type: 'CLEAR' });
  };

  const active = getActiveResult(state);

  return (
    <SplitLayout>
      <div className="flex h-full min-h-full flex-col">
      {/* Header */}
      <header className="mb-6">
        <h1 className="font-mono text-xl font-light tracking-wider text-white">
          MONARCH demo
        </h1>
        <p className="mt-1 font-mono text-[11px] uppercase tracking-wider text-white/40">
          ECharts visualizations + brain renderer, shared state
        </p>
      </header>

      {/* Controls */}
      <section className="mb-6 flex flex-wrap gap-2">
        {DEMO_NAA_PRESETS.map((p) => (
          <button
            key={p.label}
            type="button"
            onClick={() => loadPreset(p.label, p.naa)}
            disabled={!coords}
            className="rounded-full border border-white/30 bg-black/50 px-3 py-1.5 font-mono text-xs text-white outline-none backdrop-blur transition-colors hover:border-white/60 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {p.label} (NAA {p.naa})
          </button>
        ))}
        <button
          type="button"
          onClick={loadCompare}
          disabled={!coords}
          className="rounded-full border border-white/30 bg-black/50 px-3 py-1.5 font-mono text-xs text-white outline-none backdrop-blur transition-colors hover:border-white/60 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Compare A / B
        </button>
        <button
          type="button"
          onClick={loadMultimodal}
          disabled={!coords}
          className="rounded-full border border-white/30 bg-black/50 px-3 py-1.5 font-mono text-xs text-white outline-none backdrop-blur transition-colors hover:border-white/60 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Multimodal
        </button>
        <button
          type="button"
          onClick={handleClear}
          className="rounded-full border border-white/30 bg-black/50 px-3 py-1.5 font-mono text-xs text-white outline-none backdrop-blur transition-colors hover:border-white/60"
        >
          Clear
        </button>
      </section>

      {/* Compare A/B selector when in compare mode */}
      {state.mode === 'compare' && (
        <section className="mb-4 flex items-center gap-2 font-mono text-[11px] uppercase tracking-wider">
          <span className="text-white/50">Brain shows:</span>
          {(['A', 'B'] as const).map((v) => (
            <button
              key={v}
              type="button"
              onClick={() => dispatch({ type: 'SET_ACTIVE', active: v })}
              className={`rounded-full border px-3 py-1 transition-colors ${
                state.activeContent === v
                  ? 'border-white bg-white text-black'
                  : 'border-white/30 text-white/70 hover:border-white/60'
              }`}
            >
              Content {v}
            </button>
          ))}
        </section>
      )}

      {/* Empty / hero state -- show the force graph */}
      {state.mode === 'idle' && (
        <section className="mb-6 flex flex-1 flex-col">
          <div className="min-h-[320px] flex-1 overflow-hidden rounded-lg border border-white/10 bg-white/[0.02]">
            <NeuralForceGraph nodeCount={55} edgeDensity={0.06} />
          </div>
          <p className="mt-2 font-mono text-[10px] uppercase tracking-wider text-white/40">
            Pick a preset above to load a synthetic scan
          </p>
        </section>
      )}

      {/* Result charts -- visible whenever a scan exists */}
      {active && (
        <>
          <section className="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
            <NAAGauge
              naa={active.naa.naa}
              classification={active.naa.classification}
              title={
                state.mode === 'compare' ? `NAA - Content ${state.activeContent}` : 'NAA'
              }
            />
            <SusceptibilityChart naa={active.naa.naa} />
          </section>

          <section className="mb-4">
            <LandauCurve
              data={active.landau}
              comparisonData={
                state.mode === 'compare'
                  ? state.activeContent === 'A'
                    ? state.contentB?.landau
                    : state.contentA?.landau
                  : null
              }
            />
          </section>

          <section className="mb-4">
            <ROIBreakdown roiData={active.roiBreakdown} />
          </section>

          {active.multimodal && (
            <section className="mb-4">
              <MultimodalBars
                videoNAA={active.naa.naa * 1.1}
                textNAA={active.naa.naa * 0.7}
                audioNAA={active.naa.naa * 0.9}
                combinedNAA={active.naa.naa}
              />
            </section>
          )}

          <section className="mb-12">
            <BatchScatter items={batchItems} onItemClick={handleBatchItemClick} />
          </section>
        </>
      )}
      </div>
    </SplitLayout>
  );
}
