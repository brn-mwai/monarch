// ============================================================
// demographics.ts -- audience lenses for niched interpretation
// ============================================================
//
// The NAA index and brain prediction are objective model outputs and do
// NOT change with audience. What changes is the INTERPRETATION: the same
// score means something different to a journalist vetting a source than to
// a parent screening a clip. Each demographic supplies a focus and a
// classification-keyed takeaway so results read as niched guidance without
// altering any measured value.
// ============================================================

import type { NAAData } from './scan-store';

export type DemographicId =
  | 'general'
  | 'researcher'
  | 'educator'
  | 'journalist'
  | 'parent'
  | 'safety'
  | 'student';

export interface Demographic {
  id: DemographicId;
  label: string;
  /** One-line description of the lens, shown under the selector. */
  lens: string;
}

interface Takeaway {
  LOW: string;
  MOD: string;
  HIGH: string;
}

export const DEMOGRAPHICS: Demographic[] = [
  {
    id: 'general',
    label: 'General',
    lens: 'Plain-language read of the processing balance.',
  },
  {
    id: 'researcher',
    label: 'Researcher',
    lens: 'Stimulus framing for affective vs deliberative cortical load.',
  },
  {
    id: 'educator',
    label: 'Educator',
    lens: 'Whether a clip teaches calmly or pushes a reaction first.',
  },
  {
    id: 'journalist',
    label: 'Journalist & editor',
    lens: 'How hard a source leans on emotional framing over substance.',
  },
  {
    id: 'parent',
    label: 'Parent & EdTech',
    lens: 'How reactive a clip is before a child can think it through.',
  },
  {
    id: 'safety',
    label: 'Safety & fact-check',
    lens: 'Manipulation pressure as a triage signal, not a verdict.',
  },
  {
    id: 'student',
    label: 'Student',
    lens: 'Spot when content is built to make you feel before you think.',
  },
];

const TAKEAWAYS: Record<DemographicId, Takeaway> = {
  general: {
    LOW: 'Reads as informational: deliberative regions lead, little affective push.',
    MOD: 'A mix of emotional pull and reasoning. Read it twice before sharing.',
    HIGH: 'Built to hit emotion before reasoning engages. Slow down before reacting.',
  },
  researcher: {
    LOW: 'Low arousal asymmetry: deliberative ROIs dominate. A clean low-affect control stimulus.',
    MOD: 'Balanced affective/deliberative load. Useful as a mid-point condition in a graded set.',
    HIGH: 'High affective-salience drive relative to deliberative control. Strong candidate for an arousal condition.',
  },
  educator: {
    LOW: 'Teaches calmly: invites reasoning rather than a reaction. Good for neutral instruction.',
    MOD: 'Carries some emotional charge. Pair it with a discussion prompt so students reason through it.',
    HIGH: 'Pushes a reaction first. Use it as a worked example of how framing steers feeling before thought.',
  },
  journalist: {
    LOW: 'Leans on substance over emotional framing. Standard informational register.',
    MOD: 'Mixes substance with emotional framing. Check which claims carry the charge.',
    HIGH: 'Leans hard on emotional framing over substance. Verify the underlying claims before amplifying.',
  },
  parent: {
    LOW: 'Calm and informational: room to think before reacting. Low concern.',
    MOD: 'Some reactive pull. Worth watching together and talking it through.',
    HIGH: 'Engineered to provoke a reaction before reflection. Consider co-viewing or skipping for younger kids.',
  },
  safety: {
    LOW: 'Low manipulation pressure. Deprioritise for review.',
    MOD: 'Moderate manipulation pressure. Flag for a second look if the source is unknown.',
    HIGH: 'High manipulation pressure. Triage signal only -- escalate for human review, not an automated verdict.',
  },
  student: {
    LOW: 'This one lets you think. It is making a point, not pushing a feeling.',
    MOD: 'Part information, part feeling. Notice which words are doing the pulling.',
    HIGH: 'This is built to make you feel before you think. Name the emotion, then judge the claim.',
  },
};

export function demographicTakeaway(
  id: DemographicId,
  naa: NAAData,
): string {
  return TAKEAWAYS[id][naa.classification];
}

export function demographicLabel(id: DemographicId): string {
  return DEMOGRAPHICS.find((d) => d.id === id)?.label ?? 'General';
}
