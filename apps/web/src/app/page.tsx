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
import { useEffect, useState } from 'react';

import { BrainViewer } from '@/components/BrainViewer';
import { NAADistributionMini } from '@/components/charts/NAADistributionMini';
import { Equation } from '@/components/Equation';
import {
  DEMO_BLOBS,
  generateSpatialActivation,
  loadBrainCoords,
  type BrainCoords,
} from '@/lib/brain-data';

const FEATURES = [
  {
    title: 'Neural bias index',
    body: 'NAA measures the predicted balance between affective-salience and deliberative-control cortical processing for any media item.',
    Icon: Brain,
  },
  {
    title: 'Physics-grounded',
    body: 'A Landau / Ising mean-field layer turns the NAA observable into population susceptibility, free energy, and equilibrium polarisation.',
    Icon: Atom,
  },
  {
    title: 'Tri-modal',
    body: 'Text, audio, and video pass through the same TRIBE v2 fusion encoder; per-modality contributions are recoverable.',
    Icon: Waveform,
  },
  {
    title: 'Batch audit',
    body: 'Process up to 1,500 corpus items with checkpoint-resume, ranked output, and exportable reports.',
    Icon: Stack,
  },
  {
    title: 'Interactive brain',
    body: 'A real fsaverage5 cortical surface lights up the predicted activation, with per-region drill-down on hover.',
    Icon: CubeFocus,
  },
  {
    title: 'Open source',
    body: 'Built on TRIBE v2 (CC BY-NC) by Meta FAIR. The Monarch wrapper, charts, and physics layer are MIT.',
    Icon: GithubLogo,
  },
];

// "Neutral" content lights a tight orbital + lateral-temporal blob;
// "Reactive" content lights a wider, brighter set covering anterior
// insula, anterior cingulate proxies, and ventral OFC. Same anatomy,
// different intensities.
const NEUTRAL_BLOBS = [
  { hemi: 'left' as const,  center: [-50, -18, -8] as [number, number, number], sigma: 14, peak: 0.55 },
  { hemi: 'right' as const, center: [50, -18, -8]  as [number, number, number], sigma: 14, peak: 0.55 },
];

const REACTIVE_BLOBS = DEMO_BLOBS;

export default function HomePage() {
  const [neutralAct, setNeutralAct] = useState<Float32Array | null>(null);
  const [reactiveAct, setReactiveAct] = useState<Float32Array | null>(null);

  useEffect(() => {
    let cancelled = false;
    loadBrainCoords()
      .then((c: BrainCoords) => {
        if (cancelled) return;
        setNeutralAct(generateSpatialActivation(c, NEUTRAL_BLOBS, 0.002));
        setReactiveAct(generateSpatialActivation(c, REACTIVE_BLOBS, 0.005));
      })
      .catch((err: unknown) => {
        console.error('home: failed to load brain coords', err);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="bg-black text-white">
      {/* === Section 1 - Hero ================================================ */}
      <section className="relative flex min-h-[calc(100vh-4rem)] flex-col items-center justify-center px-6 py-10">
        <div className="grid w-full max-w-[1600px] grid-cols-1 items-center gap-10 md:grid-cols-[1fr_minmax(320px,500px)_1fr]">
          {/* LEFT brain - Neutral framing */}
          <figure className="flex flex-col items-center">
            <p className="mb-4 font-mono text-[11px] uppercase tracking-[0.25em] text-white/50">
              Neutral framing
            </p>
            <div className="relative h-[560px] w-full max-w-[540px]">
              <BrainViewer
                activation={neutralAct}
                colorMode="activation"
                initialView="left"
                showOverlays={false}
                interactive={false}
                className="absolute inset-0"
              />
            </div>
            <p className="mt-4 font-mono text-[11px] uppercase tracking-[0.2em] text-white/40">
              NAA 0.84 / LOW
            </p>
          </figure>

          {/* CENTER - headline + CTAs */}
          <div className="text-center">
            <p className="font-mono text-[11px] uppercase tracking-[0.3em] text-white/45">
              Neural processing scanner
            </p>
            <h1 className="mt-4 text-balance text-4xl font-semibold leading-[1.1] text-white sm:text-5xl">
              An AI model of the
              <br />
              human brain, applied
              <br />
              to media
            </h1>
            <p className="mx-auto mt-5 max-w-md text-balance text-[15px] leading-relaxed text-white/65">
              Predicting cortical processing balance for sight, sound and
              language. Same story, different brain - now you can see it.
            </p>

            <div className="mx-auto mt-9 flex max-w-[260px] flex-col gap-3">
              <Link
                href="/scanner"
                className="inline-flex items-center justify-between rounded-full border border-white/30 px-6 py-3 text-sm font-semibold text-white transition-colors hover:border-white/70 hover:bg-white/5"
              >
                Explore the demo
                <ArrowRight size={13} weight="bold" className="opacity-70" />
              </Link>
              <Link
                href="/report"
                className="inline-flex items-center justify-between rounded-full border border-white/30 px-6 py-3 text-sm font-semibold text-white transition-colors hover:border-white/70 hover:bg-white/5"
              >
                Read the paper
                <ArrowRight size={13} weight="bold" className="opacity-70" />
              </Link>
              <a
                href="https://github.com/brn-mwai"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-between rounded-full border border-white/30 px-6 py-3 text-sm font-semibold text-white transition-colors hover:border-white/70 hover:bg-white/5"
              >
                Access the code
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
              Built on TRIBE v2 / AMD Instinct MI300X / Open source
            </p>
          </div>

          {/* RIGHT brain - Reactive framing */}
          <figure className="flex flex-col items-center">
            <p className="mb-4 font-mono text-[11px] uppercase tracking-[0.25em] text-white/50">
              Reactive framing
            </p>
            <div className="relative h-[560px] w-full max-w-[540px]">
              <BrainViewer
                activation={reactiveAct}
                colorMode="activation"
                initialView="right"
                showOverlays={false}
                interactive={false}
                className="absolute inset-0"
              />
            </div>
            <p className="mt-4 font-mono text-[11px] uppercase tracking-[0.2em] text-white/40">
              NAA 3.71 / HIGH
            </p>
          </figure>
        </div>
      </section>

      {/* === Section 2 - The challenge ======================================= */}
      <section className="border-y border-white/10 px-6 py-24">
        <div className="mx-auto grid max-w-6xl grid-cols-1 items-start gap-12 lg:grid-cols-[1.1fr_1fr]">
          <div>
            <p className="font-mono text-[11px] uppercase tracking-[0.3em] text-white/45">
              01 / The challenge
            </p>
            <h2 className="mt-4 text-balance text-3xl font-semibold leading-tight text-white sm:text-4xl">
              Sentiment is not the
              <br className="hidden sm:inline" />
              processing pathway.
            </h2>
            <div className="mt-6 space-y-4 text-[15px] leading-relaxed text-white/70">
              <p>
                For decades, media analysis has relied on semantic tools.
                Sentiment classifiers, fact-checkers, credibility scorers.
                None of these measures the predicted neurophysiological
                pathway through which content reaches a brain before
                deliberative evaluation can engage.
              </p>
              <p>
                Monarch wraps Meta FAIR&rsquo;s TRIBE v2, the first
                population-averaged predictor of cortical activation across
                the full surface, and reads its predictions through a
                content-level bias index (NAA) that sits one layer above
                sentiment.
              </p>
            </div>

            {/* Inline contrast cards */}
            <div className="mt-8 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <article className="rounded-lg border border-white/10 p-4">
                <header className="mb-2 flex items-center justify-between">
                  <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/40">
                    Reuters wire
                  </span>
                  <span className="rounded-sm border border-emerald-300/30 px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wider text-emerald-200">
                    LOW 0.84
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
                    HIGH 3.71
                  </span>
                </header>
                <p className="text-[13px] leading-relaxed text-white/80">
                  FED DESTROYS AMERICA. Your savings are GONE. The collapse
                  they hid from you!
                </p>
              </article>
            </div>
          </div>

          {/* Right column: distribution chart */}
          <figure className="rounded-lg border border-white/10 bg-white/[0.02] p-5">
            <p className="mb-1 font-mono text-[10px] uppercase tracking-[0.25em] text-white/45">
              NAA distribution across two corpora
            </p>
            <p className="mb-4 text-[12px] text-white/55">
              Wire-style coverage clusters near LOW. The same factual story
              re-framed for engagement shifts the entire population to HIGH.
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
            02 / Pipeline
          </p>
          <h2 className="mt-4 text-balance text-3xl font-semibold leading-tight text-white sm:text-4xl">
            From media stream to cortical prediction
            <br className="hidden sm:inline" />
            in three stages.
          </h2>

          <div className="mt-12 grid grid-cols-1 gap-4 md:grid-cols-3">
            {[
              {
                step: '01',
                Icon: Waveform,
                title: 'Tri-modal encoding',
                body: 'TRIBE v2 ingests text, audio, and video. Each stream goes through its own pretrained encoder (LLaMA 3.2-3B, Wav2Vec-BERT 2.0, V-JEPA 2) and the fusion transformer aligns them into a shared latent space.',
                tag: 'TRIBE v2 fusion encoder',
              },
              {
                step: '02',
                Icon: Brain,
                title: 'Cortical prediction',
                body: 'The encoder outputs predicted population-averaged activation across 20,484 fsaverage5 cortical vertices, aggregated into NAA across the affective-salience and deliberative-control ROI groups.',
                tag: '20,484 vertices / fsaverage5',
              },
              {
                step: '03',
                Icon: Atom,
                title: 'Physics analysis',
                body: 'NAA becomes the external field of an Ising-style mean-field model. We compute equilibrium polarisation m*, susceptibility chi(NAA), and the Landau free-energy landscape for the population.',
                tag: 'Landau / Ising mean-field',
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
            Equations behind the scanner
          </h2>

          <p className="mt-6 text-[15px] leading-relaxed text-white/70">
            NAA is the ratio of mean predicted activation across the
            affective-salience ROI group to the deliberative-control group:
          </p>
          <div className="mt-4 rounded-lg border border-white/10 bg-white/[0.03] px-6 py-5">
            <Equation tex={String.raw`\mathrm{NAA} \;=\; \dfrac{A_{\mathrm{aff}}}{A_{\mathrm{del}} + \delta}`} />
          </div>

          <p className="mt-8 text-[15px] leading-relaxed text-white/70">
            The Landau free energy of an Ising-style population under the
            NAA-induced field <em className="not-italic font-semibold">h = &alpha;&#770; &middot; NAA</em> is:
          </p>
          <div className="mt-4 rounded-lg border border-white/10 bg-white/[0.03] px-6 py-5">
            <Equation
              tex={String.raw`F(m) \;=\; (1 - \beta J)\,m^{2} \;+\; \tfrac{(\beta J)^{3}}{3}\,m^{4} \;-\; h\,m`}
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
            and the population susceptibility is:
          </p>
          <div className="mt-4 rounded-lg border border-white/10 bg-white/[0.03] px-6 py-5">
            <Equation
              tex={String.raw`\chi \;=\; \dfrac{\beta\,\operatorname{sech}^{2}\!\bigl(\beta J\,m^{*} + h\bigr)}{1 - \beta J\,\operatorname{sech}^{2}\!\bigl(\beta J\,m^{*} + h\bigr)}`}
            />
          </div>
        </div>
      </section>

      {/* === Section 6 - Attribution ========================================== */}
      <section className="px-6 py-24">
        <div className="mx-auto max-w-5xl">
          <p className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/45">
            05 / Attribution
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
                B.Sc. Physics research project
              </p>
              <p className="mt-2 text-[13px] leading-relaxed text-white/60">
                Catholic University of Eastern Africa, Nairobi.
                <br />
                Supervised by Dr. Songa Mutambi.
              </p>
            </article>
            <article className="rounded-lg border border-white/10 p-6">
              <h3 className="mb-2 font-mono text-[10px] uppercase tracking-[0.25em] text-white/40">
                Submission
              </h3>
              <p className="text-base font-semibold text-white">
                AMD Developer Hackathon 2026
              </p>
              <p className="mt-2 text-[13px] leading-relaxed text-white/60">
                Track 3: Vision &amp; multimodal AI.
                <br />
                Deadline 10 May 2026.
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
            <Link href="/scanner" className="hover:text-white">Scanner</Link>
            <Link href="/report" className="hover:text-white">Report</Link>
            <Link href="/batch" className="hover:text-white">Batch</Link>
          </nav>
          <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/35">
            (c) 2026 Brian Mwai / CUEA Department of Physics
          </p>
        </div>
      </footer>
    </div>
  );
}
