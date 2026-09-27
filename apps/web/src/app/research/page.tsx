import type { Metadata } from 'next';
import Link from 'next/link';

import { Book3D } from '@/components/research/Book3D';

export const metadata: Metadata = {
  title: 'Research - Monarch',
  description:
    'Measuring the External Field: the B.Sc. Physics dissertation behind Monarch, with a preview of the title, abstract and contents.',
};

const PAPERS = [
  {
    title: 'Bounding the external field in mean-field opinion dynamics',
    body: 'The theory: the minimum strength any measure of media content must reach before it can tip opinion in the model.',
  },
  {
    title: 'A cortical-proxy observable for emotionally manipulative media',
    body: 'The instrument: the score, the 400-article corpus, and the bound it yields.',
  },
  {
    title: 'What does a released average-subject brain encoder actually predict?',
    body: 'The check: how closely the brain model tracks real brain recordings, and three silent failures to avoid.',
  },
];

export default function ResearchPage() {
  return (
    <div className="mx-auto w-full max-w-6xl px-4 pb-24 pt-10 sm:px-10 sm:pt-16">
      <p className="font-mono text-xs uppercase tracking-[0.25em] text-white/50">Research</p>
      <h1 className="mt-3 max-w-3xl text-3xl font-semibold leading-tight text-white sm:text-5xl">
        Measuring the External Field
      </h1>
      <p className="mt-4 max-w-3xl text-base leading-relaxed text-white/65 sm:text-lg">
        A cortical-proxy content observable and the mean-field bound on media-driven opinion change.
        B.Sc. Physics dissertation, The Catholic University of Eastern Africa, 2026. Brian Mwai,
        supervised by Dr. Songa Mutambi.
      </p>

      <div className="mt-10">
        <Book3D />
      </div>

      <p className="mx-auto mt-6 max-w-2xl text-center text-sm leading-relaxed text-white/50">
        This preview shows the title page, the abstract and the contents. The full dissertation is
        held at the CUEA Library. Turn pages by clicking, swiping or using the arrow keys.
      </p>

      <section className="mt-20">
        <p className="font-mono text-xs uppercase tracking-[0.25em] text-white/50">Papers</p>
        <h2 className="mt-3 text-2xl font-semibold text-white sm:text-3xl">Three papers, in review</h2>
        <p className="mt-3 max-w-3xl text-sm leading-relaxed text-white/60 sm:text-base">
          Written with Dr. Songa Mutambi and currently under review before journal submission.
        </p>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {PAPERS.map((paper, index) => (
            <article key={paper.title} className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
              <p className="font-mono text-xs tabular-nums text-white/40">Paper {index + 1}</p>
              <h3 className="mt-3 text-base font-medium leading-snug text-white">{paper.title}</h3>
              <p className="mt-3 text-sm leading-relaxed text-white/60">{paper.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="mt-16 flex flex-col items-start gap-3 rounded-2xl border border-white/10 p-6 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-white/65 sm:text-base">See the measurements behind the dissertation, article by article.</p>
        <Link
          href="/corpus"
          className="inline-flex h-11 items-center rounded-full border border-white/20 px-5 text-sm text-white hover:bg-white/10"
        >
          Explore the corpus
        </Link>
      </section>
    </div>
  );
}
