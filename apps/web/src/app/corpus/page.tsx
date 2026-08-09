'use client';

import { useEffect, useMemo, useState } from 'react';

interface CategorySummary {
  category: string;
  n: number;
  mean: number;
  median: number;
  sd: number | null;
  min: number;
  max: number;
  aAffMean: number;
  aDelMean: number;
}

interface CorpusItem {
  id: string;
  category: string;
  preview: string;
  wordCount: number | null;
  source: string;
  naaSigned: number | null;
  naaRatio: number | null;
  aAff: number | null;
  aDel: number | null;
}

interface CorpusData {
  corpusTarget: number;
  complete: boolean;
  summary: {
    categories: CategorySummary[];
    nScanned: number;
    nRatioUndefined: number;
    nRatioDefined: number;
    spread: number | null;
    min: number | null;
    max: number | null;
  };
  items: CorpusItem[];
}

const CATEGORY_LABEL: Record<string, string> = {
  fear_activating: 'Fear activating',
  high_outrage: 'High outrage',
  neutral_informational: 'Neutral informational',
  reward_hook: 'Reward hook',
};

function label(category: string): string {
  return CATEGORY_LABEL[category] ?? category;
}

function signed(value: number | null, digits = 4): string {
  if (value === null) return '--';
  return value >= 0 ? `+${value.toFixed(digits)}` : value.toFixed(digits);
}

export default function CorpusPage() {
  const [data, setData] = useState<CorpusData | null>(null);
  const [failed, setFailed] = useState(false);
  const [category, setCategory] = useState<string>('all');

  useEffect(() => {
    fetch('/data/corpus.json')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then(setData)
      .catch(() => setFailed(true));
  }, []);

  const rows = useMemo(() => {
    if (!data) return [];
    const filtered =
      category === 'all' ? data.items : data.items.filter((i) => i.category === category);
    return [...filtered].sort((a, b) => (b.naaSigned ?? 0) - (a.naaSigned ?? 0));
  }, [data, category]);

  if (failed) {
    return (
      <main className="mx-auto max-w-5xl px-6 py-16">
        <p className="text-sm text-white/60">
          The corpus data file could not be loaded. Nothing is shown rather than a placeholder.
        </p>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="mx-auto max-w-5xl px-6 py-16">
        <p className="font-mono text-[11px] uppercase tracking-[0.25em] text-white/40">
          Loading measured corpus
        </p>
      </main>
    );
  }

  const { summary } = data;

  return (
    <main className="mx-auto max-w-5xl px-6 py-16">
      <p className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/45">
        Measured corpus
      </p>
      <h1 className="mt-3 text-3xl font-semibold leading-snug text-white sm:text-4xl">
        {summary.nScanned} items scanned{data.complete ? '' : ` of ${data.corpusTarget}`}
      </h1>
      <p className="mt-5 max-w-2xl text-[15px] leading-relaxed text-white/60">
        Every value here was produced by running the cascade over the item&apos;s text. Nothing
        is illustrative. The index is the signed asymmetry, affective-salience mean minus
        deliberative-control mean, in units of the encoder&apos;s standardised output.
        {!data.complete && ' The scan is still running, so this is a partial corpus.'}
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

      <h2 className="mt-14 text-xl font-semibold text-white">By category</h2>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[640px] text-left text-[13px]">
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
                <td className="py-3 pr-4 text-white">{label(c.category)}</td>
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
        No significance is claimed on this page. Whether these categories separate is decided
        by the analysis over the full corpus, and the design detects an effect down to
        &eta;&sup2; = 0.0268 at 80% power. A difference smaller than that would be missed.
      </p>

      <h2 className="mt-14 text-xl font-semibold text-white">Every item</h2>
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
            {option === 'all' ? 'All' : label(option)}
          </button>
        ))}
      </div>

      <div className="mt-5 overflow-x-auto">
        <table className="w-full min-w-[720px] text-left text-[13px]">
          <thead className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/40">
            <tr className="border-b border-white/10">
              <th className="py-3 pr-4 font-normal">Item</th>
              <th className="py-3 pr-4 font-normal">Category</th>
              <th className="py-3 pr-4 text-right font-normal">Signed</th>
              <th className="py-3 pr-4 text-right font-normal">Ratio</th>
              <th className="py-3 pr-4 text-right font-normal">Affective</th>
              <th className="py-3 text-right font-normal">Deliberative</th>
            </tr>
          </thead>
          <tbody className="text-white/70">
            {rows.map((item, index) => (
              <tr key={`${item.id}-${index}`} className="border-b border-white/5 align-top">
                <td className="max-w-md py-3 pr-4">
                  <span className="text-white/80">{item.preview}</span>
                </td>
                <td className="whitespace-nowrap py-3 pr-4 text-white/50">
                  {label(item.category)}
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
        Items marked <span className="text-white/70">undefined</span> are those where the ratio
        form has no meaning, because a network mean sits below baseline on standardised encoder
        output. They are counted, never dropped or filled in, and the rate at which they occur
        is itself a reported result.
      </p>
    </main>
  );
}
