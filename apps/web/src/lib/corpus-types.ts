export interface CategorySummary {
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

export interface CorpusItem {
  id: string;
  category: string;
  preview: string;
  text?: string;
  hasVector?: boolean;
  labelManipulative?: string;
  labelCredibility?: string;
  labelPartisan?: string;
  wordCount: number | null;
  source: string;
  naaSigned: number | null;
  naaRatio: number | null;
  aAff: number | null;
  aDel: number | null;
}

export interface CorpusData {
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
  /** Corpus-wide vertex colour range, present once per-vertex maps are shipped. */
  vectorScale?: {
    lo: number;
    hi: number;
    nVectors: number;
    percentiles: number[];
    cortexOnly: boolean;
  };
}

const LABELS: Record<string, string> = {
  fear_activating: 'Fear activating',
  high_outrage: 'High outrage',
  neutral_informational: 'Neutral informational',
  reward_hook: 'Reward hook',
};

export const CATEGORY_COLORS: Record<string, string> = {
  fear_activating: '#e8730c',
  high_outrage: '#d64545',
  neutral_informational: '#4a9eda',
  reward_hook: '#c9a227',
};

export function categoryLabel(category: string): string {
  return LABELS[category] ?? category;
}

export function signed(value: number | null, digits = 4): string {
  if (value === null || Number.isNaN(value)) return '--';
  return value >= 0 ? `+${value.toFixed(digits)}` : value.toFixed(digits);
}
