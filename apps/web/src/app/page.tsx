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
import { buildDenseActivation } from '@/lib/roi-activation';

const FEATURES = [
  {
    title: 'One clear score',
    body: 'A single number for how much a piece of media leans on emotion versus reasoning. Higher means it pushes feeling before thought.',
    Icon: Brain,
  },
  {
    title: 'Backed by physics',
    body: 'A model borrowed from how opinions spread through a crowd estimates how far the content could tip a group, not just one person.',
    Icon: Atom,
  },
  {
    title: 'Text, audio, or video',
    body: 'Scan a headline, a voice clip, or a video. The same model reads all three, and can show which one is doing the pulling.',
    Icon: Waveform,
  },
  {
    title: 'Score in bulk',
    body: 'Upload a spreadsheet of up to 1,500 items and get them all scored, ranked, and exportable in one pass.',
    Icon: Stack,
  },
  {
    title: 'See it in a 3D brain',
    body: 'Watch the predicted response light up a real 3D brain surface you can rotate and explore region by region.',
    Icon: CubeFocus,
  },
  {
    title: 'Open and free',
    body: "Built on Meta's TRIBE v2 brain model. Monarch's own code is open source and free to use.",
    Icon: GithubLogo,
  },
];

// Both brains light the same real ROIs the NAA index is computed over;
// only the affective/deliberative balance differs. Neutral content (low
// NAA) lights the deliberative-control network; reactive content (high
// NAA) lights the affective-salience network.
const WHO_ITS_FOR = [
  {
    title: 'Researchers',
    value:
      'A measuring stick for "is this built to provoke?" - run it across thousands of items and study the pattern at a scale no one could read by hand.',
    Icon: ChartLineUp,
  },
  {
    title: 'Educators',
    value:
      'Show students the same story written two ways and watch the score and the brain view diverge. Manipulation becomes something they can see, not just be told about.',
    Icon: Brain,
  },
  {
    title: 'Journalists & editors',
    value:
      'A gut-check before you publish: are we informing people, or fear-baiting them? Answered honestly about your own headline.',
    Icon: Waveform,
  },
  {
    title: 'Parents & EdTech',
    value:
      "A sugar-label for children's media - rate a clip and see whether it is calm or built to over-excite. It checks the content, never the child.",
    Icon: CubeFocus,
  },
  {
    title: 'Safety & fact-check teams',
    value:
      'Flag emotionally manipulative content at scale - scam messages and outrage feeds ranked by their emotional fingerprint, ready for human review.',
    Icon: Stack,
  },
  {
    title: 'Students',
    value:
      'A real, working example that connects brain-AI with the physics of crowds - far more memorable than a textbook.',
    Icon: Atom,
  },
];

export default function HomePage() {
  const [neutralAct, setNeutralAct] = useState<Float32Array | null>(null);
  const [reactiveAct, setReactiveAct] = useState<Float32Array | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([buildDenseActivation(0.84), buildDenseActivation(3.71)])
      .then(([neutral, reactive]) => {
        if (cancelled) return;
        setNeutralAct(neutral);
        setReactiveAct(reactive);
      })
      .catch((err: unknown) => {
        console.error('home: failed to build hero activation', err);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="bg-black text-white">
      {/* === Section 1 - Hero ================================================ */}
      <section className="relative flex min-h-[calc(100vh-4rem)] flex-col items-center justify-center px-6 py-8">
        <div className="grid w-full max-w-[1600px] grid-cols-1 items-center gap-10 md:grid-cols-[1fr_minmax(320px,500px)_1fr]">
          {/* LEFT brain - calm wording */}
          <figure className="flex flex-col items-center">
            <p className="mb-4 font-mono text-[11px] uppercase tracking-[0.25em] text-white/50">
              Calm wording
            </p>
            <div className="relative h-[480px] w-full max-w-[540px]">
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
              Score 0.84 / Calm
            </p>
          </figure>

          {/* CENTER - headline + CTAs */}
          <div className="text-center">
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
              Paste a headline, post, or clip. Monarch scores how strongly it
              pushes emotion over reason, and shows it on a 3D brain. The same
              story, told two ways, looks different inside the head.
            </p>

            <div className="mx-auto mt-9 flex max-w-[260px] flex-col gap-3">
              <Link
                href="/scanner"
                className="inline-flex items-center justify-between rounded-full border border-white/30 px-6 py-3 text-sm font-semibold text-white transition-colors hover:border-white/70 hover:bg-white/5"
              >
                Try it now
                <ArrowRight size={13} weight="bold" className="opacity-70" />
              </Link>
              <Link
                href="/report"
                className="inline-flex items-center justify-between rounded-full border border-white/30 px-6 py-3 text-sm font-semibold text-white transition-colors hover:border-white/70 hover:bg-white/5"
              >
                See a sample report
                <ArrowRight size={13} weight="bold" className="opacity-70" />
              </Link>
              <a
                href="https://github.com/brn-mwai"
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
              Built on TRIBE v2 / AMD Instinct MI300X / Open source
            </p>
          </div>

          {/* RIGHT brain - charged wording */}
          <figure className="flex flex-col items-center">
            <p className="mb-4 font-mono text-[11px] uppercase tracking-[0.25em] text-white/50">
              Charged wording
            </p>
            <div className="relative h-[480px] w-full max-w-[540px]">
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
              Score 3.71 / Charged
            </p>
          </figure>
        </div>
      </section>

      {/* === Section 1.5 - What it does + who it's for ====================== */}
      <section className="border-t border-white/10 px-6 py-24">
        <div className="mx-auto max-w-5xl">
          <p className="font-mono text-[11px] uppercase tracking-[0.3em] text-white/45">
            What it does
          </p>
          <h2 className="mt-4 max-w-3xl text-balance text-3xl font-semibold leading-tight text-white sm:text-4xl">
            It rates a piece of content for how strongly it is built to hit your
            emotions versus make you think.
          </h2>
          <p className="mt-5 max-w-2xl text-[15px] leading-relaxed text-white/65">
            Give it text, audio, or video. You get back a clear score - Calm,
            Mixed, or Charged - a view of where the content tends to land in the
            brain, and a preview of how it could ripple through a crowd. It rates
            the content, not any real person.
          </p>

          <p className="mt-14 font-mono text-[11px] uppercase tracking-[0.3em] text-white/45">
            Who it&rsquo;s for
          </p>
          <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {WHO_ITS_FOR.map(({ title, value, Icon }) => (
              <article
                key={title}
                className="rounded-lg border border-white/10 p-6 transition-colors hover:border-white/25"
              >
                <Icon size={22} weight="duotone" className="mb-4 text-white/85" />
                <h3 className="mb-2 text-base font-semibold text-white">
                  {title}
                </h3>
                <p className="text-[13px] leading-relaxed text-white/60">
                  {value}
                </p>
              </article>
            ))}
          </div>
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
                body: 'Monarch feeds your text, audio, or video into TRIBE v2, an AI that has learned how the brain reacts to each kind of media.',
                tag: 'TRIBE v2 brain model',
              },
              {
                step: '02',
                Icon: Brain,
                title: 'Predict the brain response',
                body: 'It predicts where the content would light up across the whole brain, then boils that down to one score: how much it leans on emotion versus reasoning.',
                tag: 'Whole-brain prediction',
              },
              {
                step: '03',
                Icon: Atom,
                title: 'Model the ripple effect',
                body: 'A physics model of how opinions spread through a crowd estimates how far this content could move a group, not just one person.',
                tag: 'Crowd-dynamics model',
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
            regions are against its reasoning-related regions:
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
                Track 3: multimodal AI.
                <br />
                Runs on AMD Instinct MI300X.
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
