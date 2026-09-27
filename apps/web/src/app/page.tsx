'use client';

import {
  ArrowRight,
  Atom,
  Brain,
  ChartLineUp,
  CubeFocus,
  GithubLogo,
  Stack,
  Waveform,
} from '@phosphor-icons/react/dist/ssr';
import Image from 'next/image';
import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';

import { BrainViewer } from '@/components/BrainViewer';
import { NAADistributionMini } from '@/components/charts/NAADistributionMini';
import { Equation } from '@/components/Equation';
import type { CorpusData, CorpusItem } from '@/lib/corpus-types';

/** Maps pulled from each end of the ranking for the hero. Bounds the hero's download. */
const HERO_ITEMS_PER_END = 6;
import { loadItemVector, loadMedialMask } from '@/lib/measured-activation';

const FEATURES = [
  {
    title: 'One number per item',
    body: "The affective-salience mean minus the deliberative-control mean, in units of the encoder's standardised output. Positive means affective leads.",
    Icon: Brain,
  },
  {
    title: 'A measured corpus, not a demo',
    body: '400 items across four categories, each scanned twice on a GPU. Every value on this site came from those runs.',
    Icon: Stack,
  },
  {
    title: 'Physics that is swept, not fitted',
    body: 'A mean-field model of coupled opinion states, evaluated across a range of couplings. No coupling value is fitted or quoted.',
    Icon: Atom,
  },
  {
    title: 'Open source',
    body: "Built on Meta's TRIBE v2. The pipeline, the analysis scripts and the corpus builder are public.",
    Icon: GithubLogo,
  },
];


// Both brains light the same real ROIs the NAA index is computed over;
// only the affective/deliberative balance differs. Neutral content (low
// NAA) lights the deliberative-control network; reactive content (high
// NAA) lights the affective-salience network.

export default function HomePage() {
  const [pair, setPair] = useState<{
    left: { item: CorpusItem; map: Float32Array } | null;
    right: { item: CorpusItem; map: Float32Array } | null;
  }>({ left: null, right: null });
  const pairRef = useRef(pair);
  pairRef.current = pair;

  // Real scanned items, cycled. Each frame is one item's own predicted response, so the
  // hero shows measurements from the corpus rather than a generated field.
  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setInterval> | undefined;
    let cleanupFrame: (() => void) | undefined;

    fetch('/data/corpus.json')
      .then((r) => r.json())
      .then(async (data: CorpusData) => {
        const withMap = data.items.filter((i) => i.hasVector);
        if (withMap.length < 2 || cancelled) return;

        const ranked = [...withMap].sort(
          (a, b) => (b.naaSigned ?? 0) - (a.naaSigned ?? 0),
        );

        // The hero pairs the highest-scoring item against the lowest, so it only ever needs
        // the two ends of the ranking. Loading every map instead would pull one 82 KB file
        // per item: fine at the 12 the scan had first kept, 30 MB once 375 exist.
        const perEnd = Math.min(HERO_ITEMS_PER_END, Math.floor(ranked.length / 2));
        const sampled = [...ranked.slice(0, perEnd), ...ranked.slice(-perEnd)];

        const mask = await loadMedialMask();
        const scale = data.vectorScale ?? null;
        const loaded = await Promise.all(
          sampled.map(async (item) => {
            const map = await loadItemVector(item.id, scale, mask);
            return map ? { item, map } : null;
          }),
        );
        const usable = loaded.filter(Boolean) as { item: CorpusItem; map: Float32Array }[];
        if (usable.length < 2 || cancelled) return;

        let index = 0;
        let frame: number | undefined;

        // Ease between one item's map and the next rather than cutting. Intermediate
        // frames are a blend of two real predictions, shown only while the transition
        // runs; the caption names the item the view is settling on.
        const blend = (
          from: Float32Array | null,
          to: Float32Array,
          t: number,
        ): Float32Array => {
          if (!from || from.length !== to.length) return to;
          const out = new Float32Array(to.length);
          for (let i = 0; i < to.length; i++) out[i] = from[i] + (to[i] - from[i]) * t;
          return out;
        };

        const easeInOut = (t: number) =>
          t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2;

        const show = () => {
          const nextLeft = usable[index % usable.length];
          const nextRight = usable[usable.length - 1 - (index % usable.length)];
          index += 1;

          const fromLeft = pairRef.current.left?.map ?? null;
          const fromRight = pairRef.current.right?.map ?? null;
          const start = performance.now();
          const DURATION = 1400;

          const step = (now: number) => {
            const t = Math.min(1, (now - start) / DURATION);
            const e = easeInOut(t);
            setPair({
              left: { item: nextLeft.item, map: blend(fromLeft, nextLeft.map, e) },
              right: { item: nextRight.item, map: blend(fromRight, nextRight.map, e) },
            });
            if (t < 1) frame = requestAnimationFrame(step);
          };
          frame = requestAnimationFrame(step);
        };

        show();
        timer = setInterval(show, 6000);
        cleanupFrame = () => {
          if (frame) cancelAnimationFrame(frame);
        };
      })
      .catch(() => undefined);

    return () => {
      cancelled = true;
      if (timer) clearInterval(timer);
      cleanupFrame?.();
    };
  }, []);

  return (
    <div className="bg-black text-white">
      {/* === Section 1 - Hero ================================================ */}
      <section className="relative flex min-h-[calc(100vh-4rem)] flex-col items-center justify-center px-4 py-8 sm:px-6">
        {/* On a phone the three cells stack, so the headline is ordered first: otherwise a
            reader meets a brain canvas before being told what the page is. */}
        <div className="grid w-full max-w-[1600px] grid-cols-1 items-center gap-8 sm:gap-10 md:grid-cols-[1fr_minmax(320px,500px)_1fr]">
          {/* LEFT brain - calm wording */}
          <figure className="order-2 flex flex-col items-center md:order-none">
            <p className="mb-4 font-mono text-[11px] uppercase tracking-[0.25em] text-white/50">
              Predicted activity
            </p>
            <div className="relative h-[300px] w-full max-w-[540px] sm:h-[380px] md:h-[480px]">
              <BrainViewer
                activation={pair.left?.map ?? null}
                activationPreNormalized
                colorMode="activation"
                initialView="left"
                showOverlays={false}
                interactive={false}
                className="absolute inset-0"
              />
            </div>
            <p className="mt-4 font-mono text-[11px] uppercase tracking-[0.2em] text-white/40">
              {pair.left ? pair.left.item.category.replace(/_/g, ' ') : 'loading'}
            </p>
          </figure>

          {/* CENTER - headline + CTAs */}
          <div className="order-1 text-center md:order-none">
            <p className="font-mono text-[11px] uppercase tracking-[0.3em] text-white/45">
              Monarch
            </p>
            <h1 className="mt-4 text-balance text-4xl font-semibold leading-[1.1] text-white sm:text-5xl">
              Is this media built
              <br />
              to make you feel,
              <br />
              or to make you think?
            </h1>
            <p className="mx-auto mt-5 max-w-md text-balance text-[15px] leading-relaxed text-white/65">
              Predicting how cortex responds to written media.
            </p>

            <div className="mx-auto mt-9 flex max-w-[260px] flex-col gap-3">
              <Link
                href="/research"
                className="inline-flex items-center justify-between rounded-full bg-white px-6 py-3 text-sm font-semibold text-black transition-colors hover:bg-white/85"
              >
                Read the research
                <ArrowRight size={13} weight="bold" className="opacity-70" />
              </Link>
              <Link
                href="/corpus"
                className="inline-flex items-center justify-between rounded-full border border-white/30 px-6 py-3 text-sm font-semibold text-white transition-colors hover:border-white/70 hover:bg-white/5"
              >
                See the measured corpus
                <ArrowRight size={13} weight="bold" className="opacity-70" />
              </Link>
              <a
                href="https://github.com/brn-mwai/monarch"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-between rounded-full border border-white/30 px-6 py-3 text-sm font-semibold text-white transition-colors hover:border-white/70 hover:bg-white/5"
              >
                See the code
                <ArrowRight size={13} weight="bold" className="opacity-70" />
              </a>
              <a
                href="https://huggingface.co/facebook/tribev2"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-between rounded-full border border-white/30 px-6 py-3 text-sm font-semibold text-white transition-colors hover:border-white/70 hover:bg-white/5"
              >
                Download the model
                <ArrowRight size={13} weight="bold" className="opacity-70" />
              </a>
            </div>

            <p className="mt-9 font-mono text-[10px] uppercase tracking-[0.25em] text-white/35">
              Built on TRIBE v2 / fsaverage5 cortical surface / Open source
            </p>
          </div>

          {/* RIGHT brain - charged wording */}
          <figure className="order-3 flex flex-col items-center md:order-none">
            <p className="mb-4 font-mono text-[11px] uppercase tracking-[0.25em] text-white/50">
              Predicted activity
            </p>
            <div className="relative h-[300px] w-full max-w-[540px] sm:h-[380px] md:h-[480px]">
              <BrainViewer
                activation={pair.right?.map ?? null}
                activationPreNormalized
                colorMode="activation"
                initialView="right"
                showOverlays={false}
                interactive={false}
                className="absolute inset-0"
              />
            </div>
            <p className="mt-4 font-mono text-[11px] uppercase tracking-[0.2em] text-white/40">
              {pair.right ? pair.right.item.category.replace(/_/g, ' ') : 'loading'}
            </p>
          </figure>
        </div>
      </section>

      {/* === Section 1.5 - What it does ===================================== */}
      <section className="border-t border-white/10 px-6 py-24">
        <div className="mx-auto max-w-5xl">
          <p className="font-mono text-[11px] uppercase tracking-[0.3em] text-white/45">
            What it does
          </p>
          <h2 className="mt-4 max-w-3xl text-balance text-3xl font-semibold leading-tight text-white sm:text-4xl">
            It measures how far a piece of text leans on emotion rather than
            reasoning, and reports the number it gets.
          </h2>
          <p className="mt-5 max-w-2xl text-[15px] leading-relaxed text-white/65">
            The text is spoken, transcribed, embedded, and passed to an encoder
            trained to predict cortical responses. Two networks are averaged, one
            associated with affective salience and one with deliberative control,
            and the index is the difference between them. It rates the content,
            never a person, and it predicts a response rather than recording one.
          </p>
        </div>
      </section>

      {/* === Section 2 - The challenge ======================================= */}
      <section className="border-y border-white/10 px-6 py-24">
        <div className="mx-auto grid max-w-6xl grid-cols-1 items-start gap-12 lg:grid-cols-[1.1fr_1fr]">
          <div>
            <p className="font-mono text-[11px] uppercase tracking-[0.3em] text-white/45">
              01 / The idea
            </p>
            <h2 className="mt-4 text-balance text-3xl font-semibold leading-tight text-white sm:text-4xl">
              Most tools check what
              <br className="hidden sm:inline" />
              media says. Monarch
              <br className="hidden sm:inline" />
              checks how it lands.
            </h2>
            <div className="mt-6 space-y-4 text-[15px] leading-relaxed text-white/70">
              <p>
                Sentiment tools, fact-checkers, and credibility scores all read
                the words. None of them tell you whether a piece of media is
                wired to trigger a gut reaction before you get a chance to think
                it through.
              </p>
              <p>
                Monarch uses Meta&rsquo;s TRIBE v2, an AI trained to predict how
                the brain responds to media, and turns that into one plain score:
                how much this content leans on feeling versus reasoning.
              </p>
            </div>

            {/* Inline contrast cards. The bands illustrate the contrast the index is
                built to expose; they are not scores measured on these two passages. */}
            <div className="mt-8 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <article className="rounded-lg border border-white/10 p-4">
                <header className="mb-2 flex items-center justify-between">
                  <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/40">
                    Reuters wire
                  </span>
                  <span className="rounded-sm border border-emerald-300/30 px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wider text-emerald-200">
                    LOW
                  </span>
                </header>
                <p className="text-[13px] leading-relaxed text-white/80">
                  Federal Reserve holds interest rates steady, citing stable
                  inflation outlook.
                </p>
              </article>
              <article className="rounded-lg border border-white/10 p-4">
                <header className="mb-2 flex items-center justify-between">
                  <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/40">
                    Outrage feed
                  </span>
                  <span className="rounded-sm border border-orange-300/40 px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wider text-orange-300">
                    HIGH
                  </span>
                </header>
                <p className="text-[13px] leading-relaxed text-white/80">
                  FED DESTROYS AMERICA. Your savings are GONE. The collapse
                  they hid from you!
                </p>
              </article>
            </div>
            <p className="mt-3 font-mono text-[10px] text-white/35">
              illustrative, not measured
            </p>
          </div>

          {/* Right column: distribution chart */}
          <figure className="rounded-lg border border-white/10 bg-white/[0.02] p-5">
            <p className="mb-1 font-mono text-[10px] uppercase tracking-[0.25em] text-white/45">
              Two sets of stories, scored
            </p>
            <p className="mb-4 text-[12px] text-white/55">
              Straight news coverage clusters at the calm end. The same facts
              re-written to grab attention push the whole set to the charged end.
            </p>
            <NAADistributionMini height={240} />
            <p className="mt-3 font-mono text-[10px] text-white/35">
              synthetic, illustrative
            </p>
          </figure>
        </div>
      </section>

      {/* === Section 3 - How it works ========================================= */}
      <section className="px-6 py-24">
        <div className="mx-auto max-w-6xl">
          <p className="font-mono text-[11px] uppercase tracking-[0.3em] text-white/45">
            02 / How it works
          </p>
          <h2 className="mt-4 text-balance text-3xl font-semibold leading-tight text-white sm:text-4xl">
            From a piece of media to a
            <br className="hidden sm:inline" />
            score, in three steps.
          </h2>

          <div className="mt-12 grid grid-cols-1 gap-4 md:grid-cols-3">
            {[
              {
                step: '01',
                Icon: Waveform,
                title: 'Read the content',
                body: 'The item is spoken, transcribed for word timings, and embedded, then passed to TRIBE v2, an encoder trained to predict cortical responses to naturalistic media.',
                tag: 'TRIBE v2 brain model',
              },
              {
                step: '02',
                Icon: Brain,
                title: 'Predict the brain response',
                body: 'The encoder returns a predicted response for 20,484 points on the cortical surface. Two networks are averaged from it, one affective, one deliberative.',
                tag: 'Whole-brain prediction',
              },
              {
                step: '03',
                Icon: Atom,
                title: 'Ask what it would take to matter',
                body: 'A mean-field model states how strong the coupling between this index and a population would have to be before content of this spread could shift a consensus at all.',
                tag: 'Mean-field bound',
              },
            ].map(({ step, Icon, title, body, tag }, i) => (
              <article
                key={step}
                className="relative flex flex-col rounded-lg border border-white/10 p-6 transition-colors hover:border-white/25"
              >
                <div className="mb-4 flex items-center justify-between">
                  <div className="flex h-9 w-9 items-center justify-center rounded-full border border-white/15 bg-white/[0.03]">
                    <Icon size={18} weight="duotone" className="text-white/85" />
                  </div>
                  <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/35">
                    Step {step}
                  </span>
                </div>
                <h3 className="text-lg font-semibold text-white">{title}</h3>
                <p className="mt-3 flex-1 text-[13px] leading-relaxed text-white/60">
                  {body}
                </p>
                <p className="mt-4 border-t border-white/[0.06] pt-3 font-mono text-[10px] uppercase tracking-[0.2em] text-white/35">
                  {tag}
                </p>
                {i < 2 && (
                  <ArrowRight
                    size={14}
                    weight="bold"
                    className="absolute -right-3 top-1/2 hidden -translate-y-1/2 rounded-full bg-black p-0.5 text-white/40 md:block"
                  />
                )}
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* === Section 4 - Features ============================================= */}
      <section className="border-t border-white/10 px-6 py-24">
        <div className="mx-auto max-w-5xl">
          <p className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/45">
            03 / Capabilities
          </p>
          <h2 className="mt-3 text-balance text-3xl font-semibold leading-snug text-white sm:text-4xl">
            What Monarch does
          </h2>
          <div className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map(({ title, body, Icon }) => (
              <article
                key={title}
                className="rounded-lg border border-white/10 p-6 transition-colors hover:border-white/25"
              >
                <Icon size={24} weight="duotone" className="mb-4 text-white/85" />
                <h3 className="mb-2 text-base font-semibold text-white">
                  {title}
                </h3>
                <p className="text-[13px] leading-relaxed text-white/60">{body}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* === Section 5 - Physics ============================================== */}
      <section className="border-y border-white/10 px-6 py-24">
        <div className="mx-auto max-w-3xl">
          <div className="mb-3 flex items-center gap-2">
            <ChartLineUp size={14} className="text-white/55" />
            <p className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/45">
              04 / The physics
            </p>
          </div>
          <h2 className="text-balance text-3xl font-semibold leading-snug text-white sm:text-4xl">
            The maths behind the score
          </h2>

          <p className="mt-6 text-[15px] leading-relaxed text-white/70">
            For the curious. You don&rsquo;t need any of this to use Monarch -
            this is the physics that turns a brain prediction into a score and a
            ripple estimate.
          </p>

          <p className="mt-6 text-[15px] leading-relaxed text-white/70">
            The score compares how active the brain&rsquo;s emotion-related
            regions are against its reasoning-related regions. It is a difference,
            because a ratio of the two was undefined for 69 of the 400 items:
          </p>
          <div className="mt-4 rounded-lg border border-white/10 bg-white/[0.03] px-6 py-5">
            <Equation tex={String.raw`X \;=\; A_{\mathrm{aff}} \;-\; A_{\mathrm{del}}`} />
          </div>

          <p className="mt-8 text-[15px] leading-relaxed text-white/70">
            The Landau free energy of an Ising-style population under the
            content field <em className="not-italic font-semibold">h = &alpha; &middot; X</em> is:
          </p>
          <div className="mt-4 rounded-lg border border-white/10 bg-white/[0.03] px-6 py-5">
            <Equation
              tex={String.raw`F(m) \;=\; \tfrac{1 - \beta J}{2}\,m^{2} \;+\; \tfrac{1}{12}\,m^{4} \;-\; h\,m`}
            />
          </div>

          <p className="mt-8 text-[15px] leading-relaxed text-white/70">
            Equilibrium polarisation <em className="not-italic font-semibold">m*</em> solves the
            self-consistency equation:
          </p>
          <div className="mt-4 rounded-lg border border-white/10 bg-white/[0.03] px-6 py-5">
            <Equation tex={String.raw`m \;=\; \tanh\!\bigl(\beta J\, m \;+\; h\bigr)`} />
          </div>

          <p className="mt-8 text-[15px] leading-relaxed text-white/70">
            The coupling &alpha; cannot be measured from this corpus, so the work
            states the minimum it would need. For content of measured spread
            &Delta;X to tip a consensus, the field must reach the critical field
            h<sub>c</sub>:
          </p>
          <div className="mt-4 rounded-lg border border-white/10 bg-white/[0.03] px-6 py-5">
            <Equation tex={String.raw`\alpha \;\geq\; \dfrac{h_{c}(\beta J)}{\Delta X} \;=\; \dfrac{0.533}{0.124} \;=\; 4.29 \quad (\beta J = 2)`} />
          </div>
          <p className="mt-4 text-[13px] leading-relaxed text-white/50">
            This is a minimum any claim must meet within the mean-field model, not a claim
            that media flips opinion.
          </p>
        </div>
      </section>

      {/* === Section 6 - Research status ====================================== */}
      <section className="border-t border-white/10 px-6 py-24">
        <div className="mx-auto max-w-5xl">
          <p className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/45">
            05 / Research status
          </p>
          <h2 className="mt-3 text-balance text-3xl font-semibold leading-snug text-white sm:text-4xl">
            What was measured, and what is still open
          </h2>
          <p className="mt-5 max-w-2xl text-[15px] leading-relaxed text-white/60">
            The dissertation was submitted in September 2026 and is held by the CUEA Library.
            All 400 items were scanned twice. Three papers, written with Dr. Songa Mutambi,
            are in review before journal submission.
          </p>

          <div className="mt-8 grid grid-cols-2 gap-3 lg:grid-cols-4">
            {[
              { value: '10.7%', label: 'of the variation in the score is explained by the kind of content (η² = 0.107)' },
              { value: 'd = 0.94', label: 'fear-driven content, the largest gap from neutral' },
              { value: '0.87', label: 'agreement between the two runs (ICC)' },
              { value: 'α ≥ 4.29', label: 'minimum media strength to tip opinion at βJ = 2' },
            ].map((stat) => (
              <div key={stat.value} className="rounded-lg border border-white/10 p-4">
                <p className="font-mono text-xl font-semibold tabular-nums text-white sm:text-2xl">{stat.value}</p>
                <p className="mt-2 text-[12px] leading-relaxed text-white/55">{stat.label}</p>
              </div>
            ))}
          </div>

          <div className="mt-10 grid grid-cols-1 gap-4 md:grid-cols-3">
            <article className="rounded-lg border border-white/10 p-6">
              <h3 className="mb-2 font-mono text-[10px] uppercase tracking-[0.25em] text-white/40">
                Paper 1 / theory
              </h3>
              <p className="text-[13px] leading-relaxed text-white/60">
                For any content observable used as a field through h = αX, no media-driven
                transition is possible unless α ≥ h<sub>c</sub>(βJ) / ΔX. The bound states
                what the coupling would have to be for the mechanism to work at all, and can
                be checked before any data are collected. In review.
              </p>
            </article>
            <article className="rounded-lg border border-white/10 p-6">
              <h3 className="mb-2 font-mono text-[10px] uppercase tracking-[0.25em] text-white/40">
                Paper 2 / the corpus
              </h3>
              <p className="text-[13px] leading-relaxed text-white/60">
                The four categories separate at η² = 0.107 (p ≈ 10<sup>-9</sup>), carried by
                fear-driven content. Outrage raises emotion and reasoning equally, so its score
                stays flat. The measured spread ΔX = 0.124 gives α ≥ 4.29 at βJ = 2. In review.
              </p>
            </article>
            <article className="rounded-lg border border-white/10 p-6">
              <h3 className="mb-2 font-mono text-[10px] uppercase tracking-[0.25em] text-white/40">
                Paper 3 / validation
              </h3>
              <p className="text-[13px] leading-relaxed text-white/60">
                Against public brain recordings of people watching Friends, the brain model
                reaches r = +0.028 on a 2-minute clip, 30% of the best possible (0.096), with a
                positive sign. The full-episode test is next. In review.
              </p>
            </article>
          </div>

          <div className="mt-8 rounded-lg border border-white/10 p-6">
            <h3 className="mb-3 font-mono text-[10px] uppercase tracking-[0.25em] text-white/40">
              Stated limits
            </h3>
            <ul className="space-y-2 text-[13px] leading-relaxed text-white/60">
              <li>
                The observable is a cortical proxy. The checkpoint is cortical-only and cannot
                speak to subcortical structures.
              </li>
              <li>
                Monarch predicts an average brain&apos;s response to content. It never scans a
                person, and predicted activation is not measured activation.
              </li>
              <li>
                The coupling α is not measured. The site quotes only its minimum, α ≥ 4.29 at
                βJ = 2, within the mean-field model.
              </li>
              <li>
                Each content category came from one source collection, so category and source
                are mixed. A word-counting baseline separates the labels better (AUC 0.98 against
                0.63), which is why the score is reported as a measurement, not a detector.
              </li>
              <li>
                Group averages are reliable; single-item scores are not, since 51 of 400 items
                changed sign between runs, as measurement noise predicts.
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* === Section 7 - Attribution ========================================== */}
      <section className="px-6 py-24">
        <div className="mx-auto max-w-5xl">
          <p className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/45">
            06 / Attribution
          </p>
          <h2 className="mt-3 text-balance text-3xl font-semibold leading-snug text-white sm:text-4xl">
            Who is building this
          </h2>
          <div className="mt-10 grid grid-cols-1 gap-4 md:grid-cols-2">
            <article className="rounded-lg border border-white/10 p-6">
              <h3 className="mb-2 font-mono text-[10px] uppercase tracking-[0.25em] text-white/40">
                Research project
              </h3>
              <p className="text-base font-semibold text-white">
                B.Sc. Physics dissertation, 2026
              </p>
              <p className="mt-2 text-[13px] leading-relaxed text-white/60">
                Brian Mwai, The Catholic University of Eastern Africa, Nairobi.
                <br />
                Supervised by Dr. Songa Mutambi.{' '}
                <Link href="/research" className="text-white underline-offset-4 hover:underline">
                  Preview the dissertation
                </Link>
              </p>
            </article>
            <article className="rounded-lg border border-white/10 p-6">
              <h3 className="mb-2 font-mono text-[10px] uppercase tracking-[0.25em] text-white/40">
                Apparatus
              </h3>
              <p className="text-base font-semibold text-white">
                Open-source measurement pipeline
              </p>
              <p className="mt-2 text-[13px] leading-relaxed text-white/60">
                Built on Meta&apos;s TRIBE v2, released under the project&apos;s own
                open-source licence.
                <br />
                The 400-item corpus was scanned twice on a Tesla P100.
              </p>
            </article>
          </div>
        </div>
      </section>

      {/* === Footer ============================================================ */}
      <footer className="border-t border-white/10 px-6 py-12">
        <div className="mx-auto flex max-w-5xl flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
          <Image
            src="/monarch-logo.svg"
            alt="Monarch"
            width={140}
            height={34}
            className="h-7 w-auto opacity-70"
          />
          <nav className="flex flex-wrap gap-5 text-xs font-semibold text-white/55">
            <Link href="/corpus" className="hover:text-white">Corpus</Link>
            <Link href="/research" className="hover:text-white">Research</Link>
          </nav>
          <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/35">
            (c) 2026 Brian Mwai / CUEA Department of Natural Sciences
          </p>
        </div>
      </footer>
    </div>
  );
}
