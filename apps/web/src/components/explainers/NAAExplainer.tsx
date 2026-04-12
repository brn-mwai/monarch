'use client';

import { useState } from 'react';

interface NAAExplainerProps {
  naa: number;
  classification: 'LOW' | 'MOD' | 'HIGH';
  aAff: number;
  aDel: number;
}

const VERDICTS = {
  LOW: 'This content is predicted to engage deliberative reasoning systems. The brain\'s executive control regions are expected to dominate processing.',
  MOD: 'This content shows elevated affective engagement with deliberative capacity still partially intact. The brain is emotionally engaged but can still think critically.',
  HIGH: 'This content is predicted to engage affective-salience systems before deliberative reasoning can evaluate the framing. The emotional processing pathway is expected to dominate.',
};

const CONTEXTS: Record<string, (naa: number) => string> = {
  LOW: (naa) =>
    `NAA ${naa.toFixed(2)} - comparable to factual reporting, scientific abstracts, and policy analysis. Content in this range is processed through pathways associated with careful evaluation and rational assessment.`,
  MOD: (naa) =>
    `NAA ${naa.toFixed(2)} - comparable to opinion editorials, persuasive essays, and emotionally framed but substantive journalism. The content triggers some emotional response, but reasoning systems are still active.`,
  HIGH: (naa) =>
    `NAA ${naa.toFixed(2)} - comparable to outrage-driven headlines, fear-based clickbait, and emotionally manipulative content. Content in this range is processed through pathways that bypass careful evaluation.`,
};

const ANALOGIES = {
  LOW: 'Think of this as the brain reading a textbook - it is paying attention, but it is thinking, not reacting.',
  MOD: 'Think of this as the brain watching a compelling documentary - it feels something, but it is still processing the information analytically.',
  HIGH: 'Think of this as the brain reacting to a sudden loud noise - it responds before it can think about whether the noise matters.',
};

/** Reference scale landmarks for the visual comparison strip. */
const LANDMARKS = [
  { naa: 0.5, label: 'PubMed' },
  { naa: 0.85, label: 'Reuters' },
  { naa: 1.2, label: 'Op-Ed' },
  { naa: 1.7, label: 'Persuasive' },
  { naa: 2.4, label: 'Tabloid' },
  { naa: 3.5, label: 'Clickbait' },
];

export function NAAExplainer({ naa, classification, aAff, aDel }: NAAExplainerProps) {
  const [showScience, setShowScience] = useState(false);

  return (
    <div className="mt-4 space-y-3">
      {/* Verdict */}
      <p className="text-[15px] leading-relaxed text-white/85">
        {VERDICTS[classification]}
      </p>

      {/* Context */}
      <p className="text-sm leading-relaxed text-white/55">
        {CONTEXTS[classification](naa)}
      </p>

      {/* Analogy */}
      <p className="text-sm italic text-white/40">{ANALOGIES[classification]}</p>

      {/* Reference scale */}
      <div className="rounded-lg border border-white/5 bg-white/[0.02] p-3">
        <p className="mb-2 font-mono text-[9px] uppercase tracking-wider text-white/35">
          Where this content falls
        </p>
        <div className="relative h-6">
          {/* Track */}
          <div className="absolute inset-x-0 top-1/2 h-px -translate-y-1/2 bg-white/15" />
          {/* Landmarks */}
          {LANDMARKS.map((lm) => {
            const pct = Math.min(100, (lm.naa / 4.5) * 100);
            return (
              <div
                key={lm.label}
                className="absolute top-0 -translate-x-1/2"
                style={{ left: `${pct}%` }}
              >
                <div className="mx-auto h-3 w-px bg-white/20" />
                <span className="block text-center font-mono text-[8px] text-white/30">
                  {lm.label}
                </span>
              </div>
            );
          })}
          {/* This content marker */}
          <div
            className="absolute top-0 -translate-x-1/2"
            style={{ left: `${Math.min(100, (naa / 4.5) * 100)}%` }}
          >
            <div className="mx-auto h-4 w-0.5 bg-white" />
            <span className="mt-0.5 block text-center font-mono text-[9px] font-semibold text-white">
              {naa.toFixed(2)}
            </span>
          </div>
        </div>
        <div className="mt-3 flex justify-between font-mono text-[8px] text-white/25">
          <span>Deliberative</span>
          <span>Mixed</span>
          <span>Reactive</span>
        </div>
      </div>

      {/* Science toggle */}
      <button
        type="button"
        onClick={() => setShowScience(!showScience)}
        className="flex items-center gap-1 text-xs text-white/30 transition-colors hover:text-white/50"
      >
        {showScience ? '▾ Hide technical details' : '▸ How is this calculated?'}
      </button>

      {showScience && (
        <div className="rounded-lg border border-white/5 bg-white/[0.02] p-4 font-mono text-xs leading-relaxed text-white/40">
          <p>NAA = A_aff / (A_del + delta)</p>
          <p className="mt-2">
            A_aff = {aAff.toFixed(4)} (affective-salience mean activation)
          </p>
          <p>A_del = {aDel.toFixed(4)} (deliberative-control mean activation)</p>
          <p>delta = 0.001 (regularisation constant)</p>
          <p className="mt-2">
            Predictions from TRIBE v2 (Meta FAIR, 2026). 20,484 cortical
            vertices, population-averaged across 720 subjects, 1,117.7 hours of
            fMRI training data.
          </p>
        </div>
      )}
    </div>
  );
}
