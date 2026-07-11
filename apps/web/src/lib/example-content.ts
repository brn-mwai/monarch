// ============================================================
// example-content.ts -- audience-specific example cards
// ============================================================
//
// The Scan tab's example grid switches with the selected audience: a
// journalist sees source-vetting examples, a parent sees kids-content, a
// fact-checker sees a moderation queue. Each set spans the NAA range (calm
// -> reactive) so the demo shows contrast within every audience.
// ============================================================

import type { DemographicId } from './demographics';
import { EXAMPLE_CONTENTS, type ExampleContent } from './mock-data';

const RESEARCHER: ExampleContent[] = [
  { id: 'res-control', label: 'Control stimulus', category: 'neutral', expectedNAA: 0.45,
    text: 'Baseline control condition: a flat, neutral description of a laboratory procedure read without inflection.' },
  { id: 'res-doc-calm', label: 'Low-affect narration', category: 'neutral', expectedNAA: 0.6,
    text: 'A slow documentary voiceover describing a landscape, chosen as a low-arousal reference stimulus.' },
  { id: 'res-mid', label: 'Mid-arousal', category: 'neutral', expectedNAA: 1.5,
    text: 'A human-interest story with mild emotional framing, useful as a graded mid-point condition.' },
  { id: 'res-arousal', label: 'High-arousal', category: 'high-outrage', expectedNAA: 3.6,
    text: 'High-arousal stimulus: an urgent, all-caps alert warning of imminent catastrophe and demanding action NOW.' },
  { id: 'res-threat', label: 'Threat condition', category: 'fear-activating', expectedNAA: 3.9,
    text: 'Threat-conditioning clip: a graphic warning that a common household object may be quietly killing you.' },
  { id: 'res-reward', label: 'Reward cue', category: 'reward-hook', expectedNAA: 3.4,
    text: 'Reward-cue stimulus: a fast-cut montage promising an instant, effortless payoff if you keep watching.' },
];

const EDUCATOR: ExampleContent[] = [
  { id: 'edu-explainer', label: 'Calm explainer', category: 'neutral', expectedNAA: 0.55,
    text: 'A calm classroom explainer walking step by step through how photosynthesis converts light into energy.' },
  { id: 'edu-science-doc', label: 'Science doc', category: 'neutral', expectedNAA: 0.7,
    text: 'A measured science documentary segment on how a vaccine trains the immune system to recognise a virus.' },
  { id: 'edu-debate', label: 'Balanced debate', category: 'neutral', expectedNAA: 1.2,
    text: 'A structured debate clip presenting two sides of a policy question, each backed with evidence.' },
  { id: 'edu-history', label: 'Sensational reel', category: 'high-outrage', expectedNAA: 3.3,
    text: 'A dramatised history reel shouting that everything you were taught in school is a deliberate LIE.' },
  { id: 'edu-ragebait', label: 'Rage-bait short', category: 'high-outrage', expectedNAA: 3.8,
    text: 'A short-form clip engineered to make students furious at an exaggerated strawman opponent.' },
  { id: 'edu-fear-psa', label: 'Shock PSA', category: 'fear-activating', expectedNAA: 3.5,
    text: 'A public-service ad using shock imagery to frighten teens about a danger before explaining anything.' },
];

const JOURNALIST: ExampleContent[] = [
  { id: 'jrn-wire', label: 'Wire report', category: 'neutral', expectedNAA: 0.5,
    text: 'A neutral wire report attributing each claim to a named official source and dated on the record.' },
  { id: 'jrn-press', label: 'Press release', category: 'neutral', expectedNAA: 0.6,
    text: 'A corporate press release stating quarterly results in measured, hedged, factual language.' },
  { id: 'jrn-data', label: 'Data story', category: 'neutral', expectedNAA: 0.65,
    text: 'A data-driven story explaining a trend with charts and a cited, reproducible methodology.' },
  { id: 'jrn-opinion', label: 'Opinion hit-piece', category: 'high-outrage', expectedNAA: 3.4,
    text: 'An opinion column that leans on outrage and loaded adjectives far more than on verifiable facts.' },
  { id: 'jrn-thread', label: 'Outrage thread', category: 'high-outrage', expectedNAA: 3.7,
    text: 'A viral thread stitching unrelated clips into a single narrative of betrayal and grievance.' },
  { id: 'jrn-anon', label: 'Anon-sourced scare', category: 'fear-activating', expectedNAA: 3.6,
    text: 'An anonymously sourced post claiming a hidden threat, heavy on fear and light on evidence.' },
];

const PARENT: ExampleContent[] = [
  { id: 'par-cartoon', label: 'Educational cartoon', category: 'neutral', expectedNAA: 0.4,
    text: 'A gentle educational cartoon teaching counting to ten with a calm, friendly narrator.' },
  { id: 'par-nature', label: 'Nature doc', category: 'neutral', expectedNAA: 0.55,
    text: 'A soothing nature documentary segment following a family of animals across a quiet savanna.' },
  { id: 'par-drama', label: 'Drama vlog', category: 'high-outrage', expectedNAA: 2.9,
    text: 'A teen drama vlog escalating a small disagreement into shouting, tears, and dramatic music.' },
  { id: 'par-unboxing', label: 'Unboxing hype', category: 'reward-hook', expectedNAA: 3.5,
    text: 'A hyperactive unboxing video shouting BUY IT NOW before it sells out forever!' },
  { id: 'par-lootbox', label: 'Loot-box hook', category: 'reward-hook', expectedNAA: 3.6,
    text: 'A game ad dangling a rare reward if you just keep tapping to open one more box.' },
  { id: 'par-challenge', label: 'Scary challenge', category: 'fear-activating', expectedNAA: 3.9,
    text: 'A viral challenge clip built to frighten kids into filming a dangerous stunt of their own.' },
];

const SAFETY: ExampleContent[] = [
  { id: 'saf-benign', label: 'Benign post', category: 'neutral', expectedNAA: 0.4,
    text: 'A routine community post sharing a neutral schedule for an upcoming local event.' },
  { id: 'saf-policy', label: 'Policy explainer', category: 'neutral', expectedNAA: 0.6,
    text: 'A calm explainer summarising a platform policy change with links to the full text.' },
  { id: 'saf-threat', label: 'Intimidation tone', category: 'high-outrage', expectedNAA: 3.3,
    text: 'A post using intimidating, threatening language aimed at a named individual.' },
  { id: 'saf-coordinated', label: 'Coordinated outrage', category: 'high-outrage', expectedNAA: 3.8,
    text: 'A copy-pasted outrage script appearing across many accounts within the same few minutes.' },
  { id: 'saf-scam', label: 'Reward scam', category: 'reward-hook', expectedNAA: 3.7,
    text: 'A message promising a large payout if you act immediately and share your account details.' },
  { id: 'saf-misinfo', label: 'Health misinfo', category: 'fear-activating', expectedNAA: 4.0,
    text: 'A post claiming a miracle cure that doctors are supposedly hiding from the public.' },
];

const STUDENT: ExampleContent[] = [
  { id: 'stu-textbook', label: 'Textbook passage', category: 'neutral', expectedNAA: 0.5,
    text: 'A textbook passage explaining supply and demand with a clear, worked numerical example.' },
  { id: 'stu-essay', label: 'Balanced essay', category: 'neutral', expectedNAA: 0.7,
    text: 'A balanced essay weighing arguments for and against a claim before reaching a conclusion.' },
  { id: 'stu-viral', label: 'Viral explainer', category: 'high-outrage', expectedNAA: 2.4,
    text: 'A punchy explainer that oversimplifies a topic to make you feel smart in fifteen seconds.' },
  { id: 'stu-motivation', label: 'Motivational hype', category: 'reward-hook', expectedNAA: 3.1,
    text: 'A high-energy motivational reel promising instant success if you just believe hard enough.' },
  { id: 'stu-exam-scare', label: 'Exam-scare post', category: 'fear-activating', expectedNAA: 3.4,
    text: 'A post warning that one wrong move on this exam will RUIN your entire future.' },
  { id: 'stu-fear-headline', label: 'Fear headline', category: 'fear-activating', expectedNAA: 3.6,
    text: 'A headline built to spike your anxiety before you have read a single supporting fact.' },
];

const EXAMPLES_BY_AUDIENCE: Record<DemographicId, ExampleContent[]> = {
  general: EXAMPLE_CONTENTS,
  researcher: RESEARCHER,
  educator: EDUCATOR,
  journalist: JOURNALIST,
  parent: PARENT,
  safety: SAFETY,
  student: STUDENT,
};

export function examplesForAudience(id: DemographicId): ExampleContent[] {
  return EXAMPLES_BY_AUDIENCE[id] ?? EXAMPLE_CONTENTS;
}

// A single labelled corpus for the Batch Audit tab: every audience set
// flattened and de-duplicated by id, so the default batch shows real,
// varied content across the NAA range instead of placeholder rows.
export const BATCH_CORPUS: ExampleContent[] = (() => {
  const seen = new Set<string>();
  const corpus: ExampleContent[] = [];
  for (const set of [
    EXAMPLE_CONTENTS,
    RESEARCHER,
    EDUCATOR,
    JOURNALIST,
    PARENT,
    SAFETY,
    STUDENT,
  ]) {
    for (const item of set) {
      if (seen.has(item.id)) continue;
      seen.add(item.id);
      corpus.push(item);
    }
  }
  return corpus;
})();
