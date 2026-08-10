'use client';

import { useEffect, useMemo, useState } from 'react';

import { BrainPanel } from '@/components/corpus/BrainPanel';
import {
  AffectiveVsDeliberative,
  CategoryMeans,
  SignedByCategory,
} from '@/components/corpus/CorpusCharts';
import { InfoHint } from '@/components/corpus/InfoHint';
import { ItemDetail } from '@/components/corpus/ItemDetail';
import { ItemSelect } from '@/components/corpus/ItemSelect';
import { ItemTable } from '@/components/corpus/ItemTable';
import { categoryNote } from '@/lib/category-notes';
import { setChatContext } from '@/lib/chat-context';
import {
  CATEGORY_COLORS,
  categoryLabel,
  signed,
  type CorpusData,
} from '@/lib/corpus-types';
import {
  loadMedialMask,
  loadRoiVertices,
  type RoiVertices,
} from '@/lib/measured-activation';

function SectionHeading({
  index,
  title,
  hint,
  children,
}: {
  index: string;
  title: string;
  hint?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="mb-6">
      <p className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.25em] text-white/45">
        {index} / {title}
        {hint && <InfoHint title={title} body={hint} />}
      </p>
      {children ? (
        <p className="mt-3 max-w-2xl text-[14px] leading-relaxed text-white/60">{children}</p>
      ) : null}
    </div>
  );
}

function Panel({ children }: { children: React.ReactNode }) {
  return (
    <div className="w-full flex-1 rounded-xl border border-white/10 bg-white/[0.015] p-5">
      {children}
    </div>
  );
}

export default function CorpusPage() {
  const [data, setData] = useState<CorpusData | null>(null);
  const [rois, setRois] = useState<RoiVertices | null>(null);
  const [mask, setMask] = useState<Uint8Array | null>(null);
  const [failed, setFailed] = useState(false);
  const [compare, setCompare] = useState(false);
  const [filter, setFilter] = useState('all');
  const [primary, setPrimary] = useState(0);
  const [secondary, setSecondary] = useState(0);
  const [detail, setDetail] = useState<number | null>(null);

  useEffect(() => {
    fetch('/data/corpus.json')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then(setData)
      .catch(() => setFailed(true));
    loadRoiVertices()
      .then(setRois)
      .catch(() => setRois(null));
    loadMedialMask().then(setMask);
  }, []);

  const ranked = useMemo(() => {
    if (!data) return [];
    return data.items
      .map((item, index) => ({ item, index }))
      .sort((a, b) => (b.item.naaSigned ?? 0) - (a.item.naaSigned ?? 0));
  }, [data]);

  useEffect(() => {
    if (ranked.length < 2) return;
    // Prefer items with a kept per-vertex map, since those are the ones worth looking at
    // on the surface. 375 of 400 have one; the rest fall back to the region average.
    const withVector = ranked.filter((r) => r.item.hasVector);
    const pool = withVector.length > 1 ? withVector : ranked;
    setPrimary(pool[0].index);
    setSecondary(pool[pool.length - 1].index);
  }, [ranked]);

  // The chat answers about whichever item is on the surface. Only values already on the
  // page go into the scope, so scoping can never widen what the assistant knows.
  useEffect(() => {
    const item = data?.items[primary];
    if (!item) return;
    setChatContext({
      label: `${categoryLabel(item.category)} — ${item.preview.slice(0, 60)}`,
      detail: JSON.stringify({
        category: item.category,
        source_dataset: item.source,
        pre_scan_label_manipulative: item.labelManipulative,
        word_count: item.wordCount,
        emotional_region_mean: item.aAff,
        deliberate_region_mean: item.aDel,
        score_emotional_minus_deliberate: item.naaSigned,
        ratio_form: item.naaRatio ?? 'undefined for this item',
        has_per_vertex_map: Boolean(item.hasVector),
        text: item.text ?? item.preview,
      }),
    });
    return () => setChatContext(null);
  }, [data, primary]);

  const scale = useMemo(() => {
    if (!data) return { lo: 0, hi: 1 };
    const values = data.items.flatMap((i) =>
      i.aAff === null || i.aDel === null ? [] : [i.aAff, i.aDel],
    );
    return values.length
      ? { lo: Math.min(...values), hi: Math.max(...values) }
      : { lo: 0, hi: 1 };
  }, [data]);

  if (failed) {
    return (
      <main className="mx-auto max-w-6xl px-6 py-20">
        <p className="text-sm text-white/60">
          The corpus data did not load. Nothing is shown rather than a placeholder.
        </p>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="mx-auto max-w-6xl px-6 py-20">
        <p className="font-mono text-[11px] uppercase tracking-[0.25em] text-white/40">
          Loading corpus
        </p>
      </main>
    );
  }

  const { summary, items } = data;
  const rows =
    filter === 'all'
      ? ranked
      : filter === 'pervertex'
        ? ranked.filter((r) => r.item.hasVector)
        : ranked.filter((r) => r.item.category === filter);
  const left = items[primary];
  const right = items[secondary];

  return (
    <main className="mx-auto max-w-6xl px-6 py-16">
      <header>
        <p className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/45">
          Measured corpus
        </p>
        <h1 className="mt-3 text-3xl font-semibold leading-snug text-white sm:text-4xl">
          {summary.nScanned} items scanned{data.complete ? '' : ` of ${data.corpusTarget}`}
        </h1>
        <p className="mt-5 max-w-2xl text-[15px] leading-relaxed text-white/60">
          Each item was read aloud, transcribed, and passed to an encoder that predicts how
          cortex responds. Two regions are averaged from that prediction, one linked to
          emotional salience and one to deliberate control, and the score is the difference
          between them. Positive means the emotional side led.
          {!data.complete && ' The scan is unfinished, so this is a partial corpus.'}
        </p>
      </header>

      <section className="mt-10 grid grid-cols-2 gap-4 sm:grid-cols-4">
        {[
          { k: 'Items', v: String(summary.nScanned) },
          { k: 'Usable ratio', v: `${summary.nRatioDefined} / ${summary.nScanned}` },
          { k: 'Spread', v: summary.spread === null ? '--' : summary.spread.toFixed(4) },
          {
            k: 'Range',
            v:
              summary.min === null || summary.max === null
                ? '--'
                : `${signed(summary.min, 3)} to ${signed(summary.max, 3)}`,
          },
        ].map((cell) => (
          <div key={cell.k} className="rounded-xl border border-white/10 p-4">
            <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/40">
              {cell.k}
            </p>
            <p className="mt-2 font-mono text-lg tabular-nums text-white">{cell.v}</p>
          </div>
        ))}
      </section>

      <section className="mt-20">
        <SectionHeading index="01" title="On the surface"
          hint="A 3D cortical surface with the predicted response painted on it. Warmer means a higher predicted value. It shows what the encoder predicts, not what any person’s brain did.">
          Items marked <span className="text-white/80">Per vertex</span> show the prediction
          at every one of the 20,484 surface points, which is what produces a graded map. The
          scan kept that map for 12 items; for the rest it stored only two region averages, so
          those render as flat regions. The panel header says which you are looking at.
        </SectionHeading>

        <div className="mb-5 flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={() => setCompare(false)}
            className={`rounded-full border px-4 py-2 font-mono text-[10px] uppercase tracking-[0.15em] transition-colors ${
              compare
                ? 'border-white/15 text-white/50 hover:border-white/35'
                : 'border-white/60 text-white'
            }`}
          >
            Single item
          </button>
          <button
            type="button"
            onClick={() => setCompare(true)}
            className={`rounded-full border px-4 py-2 font-mono text-[10px] uppercase tracking-[0.15em] transition-colors ${
              compare
                ? 'border-white/60 text-white'
                : 'border-white/15 text-white/50 hover:border-white/35'
            }`}
          >
            Compare two
          </button>
        </div>

        {compare ? (
          <div className="rounded-xl border border-white/10 bg-white/[0.015]">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 px-5 py-4">
              <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/45">
                Two items, one colour scale
              </span>
              <span className="flex flex-col items-center gap-1">
                <span className="flex w-48 items-center justify-between text-[11px] text-white/70">
                  <span>Low</span>
                  <span>High</span>
                </span>
                <span
                  className="h-2 w-48 rounded-sm"
                  style={{
                    background:
                      'linear-gradient(90deg, #000000 0%, #b81d13 35%, #e8730c 62%, #f0c419 82%, #ffffff 100%)',
                  }}
                />
                <span className="text-[11px] text-white/60">Activity</span>
              </span>
            </div>

            <div className="grid grid-cols-1 gap-4 p-4 lg:grid-cols-2">
              <div className="space-y-3">
                <ItemSelect
                  label="Left item"
                  value={primary}
                  options={ranked}
                  onChange={setPrimary}
                />
                {left && (
                  <BrainPanel
                    item={left}
                    rois={rois}
                    mask={mask}
                    scaleLo={scale.lo}
                    scaleHi={scale.hi}
                    vectorScale={data.vectorScale ?? null}
                    height={340}
                    compact
                    chrome={false}
                  />
                )}
              </div>
              <div className="space-y-3 lg:border-l lg:border-white/10 lg:pl-4">
                <ItemSelect
                  label="Right item"
                  value={secondary}
                  options={ranked}
                  onChange={setSecondary}
                />
                {right && (
                  <BrainPanel
                    item={right}
                    rois={rois}
                    mask={mask}
                    scaleLo={scale.lo}
                    scaleHi={scale.hi}
                    vectorScale={data.vectorScale ?? null}
                    height={340}
                    compact
                    chrome={false}
                  />
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <ItemSelect
              label="Item"
              value={primary}
              options={ranked}
              onChange={setPrimary}
            />
            {left && (
              <BrainPanel
                item={left}
                rois={rois}
                mask={mask}
                scaleLo={scale.lo}
                scaleHi={scale.hi}
                    vectorScale={data.vectorScale ?? null}
                height={460}
              />
            )}
          </div>
        )}
      </section>

      <section className="mt-20">
        <SectionHeading index="02" title="Every item, by category"
          hint="One dot per item, grouped by category, so you see the whole spread rather than an average. Wide overlap between groups means the categories are not cleanly separated.">
          One point per item. The dashed line is zero, where both regions respond equally.
        </SectionHeading>
        <Panel>
          <SignedByCategory items={items} />
        </Panel>
      </section>

      <section className="mt-20 grid grid-cols-1 items-stretch gap-6 lg:grid-cols-2">
        <div className="flex flex-col">
          <SectionHeading index="03" title="Category averages"
          hint="The mean score per category with whiskers of one standard deviation. If whiskers overlap heavily, the gap between bars is small next to the variation inside each group.">
            Whiskers are one standard deviation. Read the gaps against them, not on their own.
          </SectionHeading>
          <Panel>
            <CategoryMeans categories={summary.categories} />
          </Panel>
        </div>
        <div className="flex flex-col">
          <SectionHeading index="04" title="The two regions against each other"
          hint="Each item plotted as emotional average against deliberate average. The dashed line is where they respond equally; points above it lean deliberate. The cloud sits above the line for almost every item.">
            Points above the dashed line are items where the deliberate side responded more.
          </SectionHeading>
          <Panel>
            <AffectiveVsDeliberative items={items} />
          </Panel>
        </div>
      </section>

      <section className="mt-20">
        <SectionHeading index="05" title="What each category is"
          hint="How items were chosen for each category, written from the corpus design. The figures beside each description are computed from the scan.">
          Descriptions of how items were selected, written from the corpus design. The numbers
          beside them are computed from the scan.
        </SectionHeading>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {summary.categories.map((c) => {
            const note = categoryNote(c.category);
            return (
              <div key={c.category} className="rounded-xl border border-white/10 p-5">
                <div className="flex items-center gap-2">
                  <span
                    className="inline-block h-2.5 w-2.5 rounded-full"
                    style={{ background: CATEGORY_COLORS[c.category] ?? '#888' }}
                  />
                  <h3 className="text-base font-semibold text-white">
                    {categoryLabel(c.category)}
                  </h3>
                  <span className="ml-auto font-mono text-[11px] tabular-nums text-white/45">
                    n = {c.n}
                  </span>
                </div>
                {note && (
                  <>
                    <p className="mt-3 text-[13px] leading-relaxed text-white/65">
                      {note.definition}
                    </p>
                    <p className="mt-2 text-[13px] leading-relaxed text-white/50">
                      {note.whatItTests}
                    </p>
                  </>
                )}
                <dl className="mt-4 grid grid-cols-3 gap-3 border-t border-white/10 pt-4 font-mono text-[11px] tabular-nums">
                  <div>
                    <dt className="text-white/40">Average</dt>
                    <dd className="mt-1 text-white">{signed(c.mean)}</dd>
                  </div>
                  <div>
                    <dt className="text-white/40">Middle</dt>
                    <dd className="mt-1 text-white">{signed(c.median)}</dd>
                  </div>
                  <div>
                    <dt className="text-white/40">Spread</dt>
                    <dd className="mt-1 text-white">
                      {c.sd === null ? '--' : c.sd.toFixed(4)}
                    </dd>
                  </div>
                </dl>
              </div>
            );
          })}
        </div>
        <p className="mt-5 max-w-2xl text-[13px] leading-relaxed text-white/50">
          No claim of a real difference is made here. Whether the categories separate is
          settled by the analysis over the full corpus, and this design can only detect an
          effect above a stated size. Anything smaller would be missed, and that limit is
          reported alongside the result rather than after it.
        </p>
      </section>

      <section className="mt-20">
        <SectionHeading index="06" title="All items"
          hint="Every scanned item with its score, its two region values, and the labels it carried before scanning. Click a row to open it in full.">
          Sorted from the most emotional-leaning to the least.
        </SectionHeading>
        <div className="mb-4 flex flex-wrap gap-2">
          {['all', 'pervertex', ...summary.categories.map((c) => c.category)].map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => setFilter(option)}
              className={`rounded-full border px-4 py-1.5 font-mono text-[10px] uppercase tracking-[0.15em] transition-colors ${
                filter === option
                  ? 'border-white/60 text-white'
                  : 'border-white/15 text-white/50 hover:border-white/35'
              }`}
            >
              {option === 'all'
                ? `All ${summary.nScanned}`
                : option === 'pervertex'
                  ? `Per vertex ${items.filter((i) => i.hasVector).length}`
                  : categoryLabel(option)}
            </button>
          ))}
        </div>

        <ItemTable
          rows={rows}
          selected={primary}
          onSelect={(index) => {
            setPrimary(index);
            setDetail(index);
          }}
          scaleLo={summary.min ?? 0}
          scaleHi={summary.max ?? 1}
        />

        <p className="mt-4 max-w-2xl text-[13px] leading-relaxed text-white/50">
          Click any row to open it in full and load it into the surface view above. {summary.nRatioUndefined} of{' '}
          {summary.nScanned} items produce no usable ratio, because one region&apos;s average
          falls below its baseline and a ratio then has no meaning. Those items are counted,
          never dropped or filled in.
        </p>
      </section>

      <ItemDetail
        item={detail === null ? null : items[detail]}
        category={
          detail === null
            ? undefined
            : summary.categories.find((c) => c.category === items[detail].category)
        }
        scoreLo={summary.min ?? 0}
        scoreHi={summary.max ?? 1}
        regionLo={scale.lo}
        regionHi={scale.hi}
        rank={detail === null ? null : ranked.findIndex((r) => r.index === detail) + 1}
        total={summary.nScanned}
        onClose={() => setDetail(null)}
      />
    </main>
  );
}
