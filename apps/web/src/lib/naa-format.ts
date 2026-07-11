import { NAA_COLORS } from '@/components/charts/echarts-theme';

export type NAAClass = 'LOW' | 'MOD' | 'HIGH';

/** Human label for a classification, shared by the scanner and report. */
export const NAA_LABEL: Record<NAAClass, string> = {
  LOW: 'Neutral',
  MOD: 'Mixed',
  HIGH: 'Reactive',
};

/** One-line plain-language verdict for the report hero. */
export const NAA_VERDICT: Record<NAAClass, string> = {
  LOW: 'Predicted to engage deliberative reasoning before an emotional reaction forms.',
  MOD: 'Predicted to engage emotion and reasoning in roughly equal measure.',
  HIGH: 'Predicted to engage emotional circuits before reasoning can evaluate the framing.',
};

export function naaColor(cls: NAAClass): string {
  return NAA_COLORS[cls];
}
