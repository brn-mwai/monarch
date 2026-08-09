'use client';

import dynamic from 'next/dynamic';
import { useEffect, useMemo, useState } from 'react';

import {
  AffectiveVsDeliberative,
  CategoryMeans,
  SignedByCategory,
} from '@/components/corpus/CorpusCharts';
import {
  categoryLabel,
  CATEGORY_COLORS,
  signed,
  type CorpusData,
  type CorpusItem,
} from '@/lib/corpus-types';
import {
  buildMeasuredRoiActivation,
  loadRoiVertices,
  type RoiVertices,
} from '@/lib/measured-activation';

const BrainViewer = dynamic(
  () => import('@/components/BrainViewer').then((m) => m.BrainViewer),
  { ssr: false, loading: () => <div className="h-[340px] rounded-lg bg-white/[0.03]" /> },
);

function ItemBrain({ item, rois }: { item: CorpusItem; rois: RoiVertices | null }) {
  const activation = useMemo(() => {
    if (!rois || item.aAff === null || item.aDel === null) return null;
    return buildMeasuredRoiActivation(rois, item.aAff, item.aDel);
  }, [rois, item]);

  return (
    <div className="rounded-lg border border-white/10 p-4">
      <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/40">
        {categoryLabel(item.category)}
      </p>
      <p className="mt-2 line-clamp-3 text-[13px] leading-relaxed text-white/70">
        {item.preview}
      </p>
      <div className="mt-3 h-[300px]">
        {activation ? (
          <BrainViewer activation={activation} interactive showOverlays={false} />
        ) : (
          <div className="flex h-full items-center justify-center text-xs text-white/40">
            No measured values for this item
          </div>
        )}
      </div>
      <dl className="mt-3 grid grid-cols-3 gap-3 font-mono text-[11px] tabular-nums">
        <div>
          <dt className="text-white/40">Affective</dt>
          <dd className="text-white">{signed(item.aAff)}</dd>
        </div>
        <div>
          <dt className="text-white/40">Deliberative</dt>
          <dd className="text-white">{signed(item.aDel)}</dd>
        </div>
        <div>
          <dt className="text-white/40">Signed NAA</dt>
          <dd className="text-white">{signed(item.naaSigned)}</dd>
        </div>
      </dl>
    </div>
  );
}

export default function CorpusPage() {
  const [data, setData] = useState<CorpusData | null>(null);
  const [rois, setRois] = useState<RoiVertices | null>(null);
  const [failed, setFailed] = useState(false);
  const [category, setCategory] = useState('all');
  const [leftId, setLeftId] = useState<number>(0);
  const [rightId, setRightId] = useState<number>(1);

  useEffect(() => {
    fetch('/data/corpus.json')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then(setData)
      .catch(() => setFailed(true));
    loadRoiVertices().then(setRois).catch(() => setRois(null));
  }, []);

  const sorted = useMemo(() => {
    if (!data) return [];
    return [...data.items]
      .map((item, index) => ({ item, index }))
      .sort((a, b) => (b.item.naaSigned ?? 0) - (a.item.naaSigned ?? 0));
  }, [data]);

  const rows = useMemo(
    () => (category === 'all' ? sorted : sorted.filter((r) => r.item.category === category)),
    [sorted, category],
  );

  useEffect(() => {
    if (sorted.length > 1) {
      setLeftId(sorted[0].index);
      setRightId(sorted[sorted.length - 1].index);
    }
  }, [sorted]);

  if (failed) {
    return (
      <main className="mx-auto max-w-6xl px-6 py-16">
        <p className="text-sm text-white/60">
          The corpus data file did not load. Nothing is shown rather than a placeholder.
        </p>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="mx-auto max-w-6xl px-6 py-16">
        <p className="font-mono text-[11px] uppercase tracking-[0.25em] text-white/40">
          Loading measured corpus
        </p>
      </main>
    );
  }

  const { summary, items } = data;
  const left = items[leftId];
  const right = items[rightId];

  return (
    <main className="mx-auto max-w-6xl px-6 py-16">
      <p className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/45">
        Measured corpus
      </p>
      <h1 className="mt-3 text-3xl font-semibold leading-snug text-white sm:text-4xl">
        {summary.nScanned} items scanned{data.complete ? '' : ` of ${data.corpusTarget}`}
      </h1>
      <p className="mt-5 max-w-2xl text-[15px] leading-relaxed text-white/60">
        Every value on this page came from running the cascade over that item&apos;s text.
        The index is the signed asymmetry: affective-salience mean minus deliberative-control
        mean, in units of the encoder&apos;s standardised output.
        {!data.complete && ' The scan is unfinished, so this is a partial corpus.'}
      </p>

      <div className="mt-10 grid grid-cols-2 gap-4 sm:grid-cols-4">
        {[
          { k: 'Items', v: String(summary.nScanned) },
          { k: 'Ratio defined', v: `${summary.nRatioDefined} / ${summary.nScanned}` },
          { k: 'Spread', v: summary.spread === null ? '--' : summary.spread.toFixed(4) },
          {
            k: 'Range',
            v:
              summary.min === null || summary.max === null
                ? '--'
                : `${signed(summary.min, 3)} .. ${signed(summary.max, 3)}`,
          },
        ].map((cell) => (
          <div key={cell.k} className="rounded-lg border border-white/10 p-4">
            <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/40">
              {cell.k}
            </p>
            <p className="mt-2 font-mono text-lg tabular-nums text-white">{cell.v}</p>
          </div>
        ))}
      </div>

      <section className="mt-16">
        <h2 className="text-xl font-semibold text-white">Where every item falls</h2>
        <p className="mt-2 max-w-2xl text-[13px] leading-relaxed text-white/55">
          One point per item, not a summary. The dashed line is zero, where the two networks
          are predicted to respond equally.
        </p>
        <div className="mt-5 rounded-lg border border-white/10 p-4">
          <SignedByCategory items={items} />
        </div>
      </section>

      <section className="mt-14 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div>
          <h2 className="text-xl font-semibold text-white">Category means</h2>
          <p className="mt-2 text-[13px] leading-relaxed text-white/55">
            Whiskers are one standard deviation. Read the gaps against them.
          </p>
          <div className="mt-5 rounded-lg border border-white/10 p-4">
            <CategoryMeans categories={summary.categories} />
          </div>
        </div>
        <div>
          <h2 className="text-xl font-semibold text-white">The two networks directly</h2>
          <p className="mt-2 text-[13px] leading-relaxed text-white/55">
            Affective against deliberative. Points below the dashed line lean deliberative.
          </p>
          <div className="mt-5 rounded-lg border border-white/10 p-4">
            <AffectiveVsDeliberative items={items} />
          </div>
        </div>
      </section>

      <section className="mt-16">
        <h2 className="text-xl font-semibold text-white">Compare two items on the surface</h2>
        <p className="mt-2 max-w-3xl text-[13px] leading-relaxed text-white/55">
          Each network is painted with the one mean the scan produced for it, so the colour is
          uniform inside each region. This is not vertex-level activation: the scan reduces
          every item&apos;s prediction to two numbers and keeps only those, so finer structure
          does not exist to draw.
        </p>

        <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
          {[
            { value: leftId, set: setLeftId, label: 'Left' },
            { value: rightId, set: setRightId, label: 'Right' },
          ].map((picker) => (
            <label key={picker.label} className="block">
              <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/40">
                {picker.label}
              </span>
              <select
                value={picker.value}
                onChange={(e) => picker.set(Number(e.target.value))}
                className="mt-2 w-full rounded-lg border border-white/15 bg-black px-3 py-2 text-[13px] text-white"
              >
                {sorted.map(({ item, index }) => (
                  <option key={index} value={index}>
                    {signed(item.naaSigned)} — {categoryLabel(item.category)} —{' '}
                    {item.preview.slice(0, 60)}
                  </option>
                ))}
              </select>
            </label>
          ))}
        </div>

        <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
          {left && <ItemBrain item={left} rois={rois} />}
          {right && <ItemBrain item={right} rois={rois} />}
        </div>
      </section>

      <section className="mt-16">
        <h2 className="text-xl font-semibold text-white">By category</h2>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[680px] text-left text-[13px]">
            <thead className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/40">
              <tr className="border-b border-white/10">
                <th className="py-3 pr-4 font-normal">Category</th>
                <th className="py-3 pr-4 text-right font-normal">n</th>
                <th className="py-3 pr-4 text-right font-normal">Mean</th>
                <th className="py-3 pr-4 text-right font-normal">Median</th>
                <th className="py-3 pr-4 text-right font-normal">SD</th>
                <th className="py-3 pr-4 text-right font-normal">Affective</th>
                <th className="py-3 text-right font-normal">Deliberative</th>
              </tr>
            </thead>
            <tbody className="text-white/70">
              {summary.categories.map((c) => (
                <tr key={c.category} className="border-b border-white/5">
                  <td className="py-3 pr-4 text-white">
                    <span
                      className="mr-2 inline-block h-2 w-2 rounded-full align-middle"
                      style={{ background: CATEGORY_COLORS[c.category] ?? '#888' }}
                    />
                    {categoryLabel(c.category)}
                  </td>
                  <td className="py-3 pr-4 text-right tabular-nums">{c.n}</td>
                  <td className="py-3 pr-4 text-right tabular-nums">{signed(c.mean)}</td>
                  <td className="py-3 pr-4 text-right tabular-nums">{signed(c.median)}</td>
                  <td className="py-3 pr-4 text-right tabular-nums">
                    {c.sd === null ? '--' : c.sd.toFixed(4)}
                  </td>
                  <td className="py-3 pr-4 text-right tabular-nums">{signed(c.aAffMean)}</td>
                  <td className="py-3 text-right tabular-nums">{signed(c.aDelMean)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-4 max-w-2xl text-[13px] leading-relaxed text-white/50">
          No significance is claimed here. Whether these categories separate is settled by the
          analysis over the full corpus, and the design detects an effect down to
          &eta;&sup2; = 0.0268 at 80% power. Anything smaller would be missed.
        </p>
      </section>

      <section className="mt-16">
        <h2 className="text-xl font-semibold text-white">Every item</h2>
        <div className="mt-4 flex flex-wrap gap-2">
          {['all', ...summary.categories.map((c) => c.category)].map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => setCategory(option)}
              className={`rounded-full border px-4 py-1.5 font-mono text-[10px] uppercase tracking-[0.15em] transition-colors ${
                category === option
                  ? 'border-white/60 text-white'
                  : 'border-white/15 text-white/50 hover:border-white/35'
              }`}
            >
              {option === 'all' ? 'All' : categoryLabel(option)}
            </button>
          ))}
        </div>

        <div className="mt-5 overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-[13px]">
            <thead className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/40">
              <tr className="border-b border-white/10">
                <th className="py-3 pr-4 font-normal">Item</th>
                <th className="py-3 pr-4 font-normal">Category</th>
                <th className="py-3 pr-4 text-right font-normal">Words</th>
                <th className="py-3 pr-4 text-right font-normal">Signed</th>
                <th className="py-3 pr-4 text-right font-normal">Ratio</th>
                <th className="py-3 pr-4 text-right font-normal">Affective</th>
                <th className="py-3 text-right font-normal">Deliberative</th>
              </tr>
            </thead>
            <tbody className="text-white/70">
              {rows.map(({ item, index }) => (
                <tr key={index} className="border-b border-white/5 align-top">
                  <td className="max-w-md py-3 pr-4 text-white/80">{item.preview}</td>
                  <td className="whitespace-nowrap py-3 pr-4 text-white/50">
                    {categoryLabel(item.category)}
                  </td>
                  <td className="py-3 pr-4 text-right tabular-nums text-white/50">
                    {item.wordCount ?? '--'}
                  </td>
                  <td className="py-3 pr-4 text-right tabular-nums text-white">
                    {signed(item.naaSigned)}
                  </td>
                  <td className="py-3 pr-4 text-right tabular-nums">
                    {item.naaRatio === null ? (
                      <span className="text-white/35">undefined</span>
                    ) : (
                      item.naaRatio.toFixed(4)
                    )}
                  </td>
                  <td className="py-3 pr-4 text-right tabular-nums">{signed(item.aAff)}</td>
                  <td className="py-3 text-right tabular-nums">{signed(item.aDel)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-6 max-w-2xl text-[13px] leading-relaxed text-white/50">
          Items marked <span className="text-white/70">undefined</span> are those where the
          ratio form has no meaning, because a network mean sits below baseline on
          standardised output. They are counted, never dropped or filled in, and how often
          that happens is itself a result.
        </p>
      </section>
    </main>
  );
}
