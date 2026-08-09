/**
 * What each corpus category is, and what the scan found for it.
 *
 * These are written from the corpus design, not produced by a language model at runtime.
 * The site has no backend, so any text claiming to be model output would be text somebody
 * typed and labelled as model output. The `definition` describes how items were selected;
 * the reading shown next to it on the page is computed from the scan, not written here.
 */

export interface CategoryNote {
  definition: string;
  whatItTests: string;
}

export const CATEGORY_NOTES: Record<string, CategoryNote> = {
  fear_activating: {
    definition:
      'Items whose framing centres on threat, danger or loss, drawn from news and social sources.',
    whatItTests:
      'Whether threat framing shifts the balance toward the affective network relative to neutral reporting of comparable length.',
  },
  high_outrage: {
    definition:
      'Items built around indignation and blame, typically partisan or conflict-driven.',
    whatItTests:
      'Whether outrage framing separates from neutral reporting, which is the separation the proposal predicted would be largest.',
  },
  neutral_informational: {
    definition:
      'Plain reporting and explanatory writing, matched to the other categories on length and source mix.',
    whatItTests:
      'The baseline. Every other category is read against this one, so any effect is a difference from it rather than an absolute value.',
  },
  reward_hook: {
    definition:
      'Items promising benefit, novelty or gain, including clickbait and promotional framing.',
    whatItTests:
      'Whether anticipation of reward moves the index in the same direction as threat and outrage, or in the opposite one.',
  },
};

export function categoryNote(category: string): CategoryNote | null {
  return CATEGORY_NOTES[category] ?? null;
}
