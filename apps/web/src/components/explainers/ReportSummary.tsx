'use client';

import type { ScanResult } from '@/lib/scan-store';

interface ReportSummaryProps {
  result: ScanResult;
}

/**
 * One-paragraph executive summary at the top of the /report page.
 * Every value is dynamically generated from the actual scan result.
 */
export function ReportSummary({ result }: ReportSummaryProps) {
  const { naa, landau, roiBreakdown } = result;

  const sorted = [...roiBreakdown].sort((a, b) => b.activation - a.activation);
  const top3 = sorted.slice(0, 3).map((r) => r.name);
  const topROINames = top3.join(', ');

  const affSum = roiBreakdown
    .filter((r) => r.system === 'affective')
    .reduce((s, r) => s + r.activation, 0);
  const delSum = roiBreakdown
    .filter((r) => r.system === 'deliberative')
    .reduce((s, r) => s + r.activation, 0);
  const dominantSystem =
    affSum > delSum ? 'affective-salience' : 'deliberative-control';

  let summary: string;

  if (naa.classification === 'HIGH') {
    summary =
      `This content scores ${naa.naa.toFixed(2)} on the Neural Arousal Asymmetry index, ` +
      `placing it in the HIGH processing-bias category. The ${dominantSystem} system ` +
      `is predicted to dominate the neural response, with strongest activation in ` +
      `${topROINames}. Under the Landau mean-field model, this NAA value produces ` +
      `an equilibrium opinion shift of m* = ${landau.equilibrium_m.toFixed(2)} toward ` +
      `the reactive-processing pole. In populations near their critical social ` +
      `temperature, this content could contribute to rapid collective opinion shifts.`;
  } else if (naa.classification === 'MOD') {
    summary =
      `This content scores ${naa.naa.toFixed(2)} on the Neural Arousal Asymmetry index, ` +
      `placing it in the MODERATE processing-bias category. Both affective and ` +
      `deliberative systems are predicted to engage, with the ${dominantSystem} system ` +
      `showing slightly higher activation. The most active regions are ${topROINames}. ` +
      `The Landau model predicts a moderate equilibrium shift of ` +
      `m* = ${landau.equilibrium_m.toFixed(2)}.`;
  } else {
    summary =
      `This content scores ${naa.naa.toFixed(2)} on the Neural Arousal Asymmetry index, ` +
      `placing it in the LOW processing-bias category. Deliberative-control regions ` +
      `are predicted to dominate, with strongest activation in ${topROINames}. ` +
      `The Landau model predicts minimal equilibrium displacement ` +
      `(m* = ${landau.equilibrium_m.toFixed(2)}), suggesting this content would not ` +
      `significantly bias collective opinion under the mean-field approximation.`;
  }

  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.02] p-5">
      <p className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/40">
        Executive summary
      </p>
      <p className="mt-3 text-[14px] leading-relaxed text-white/75">{summary}</p>
    </div>
  );
}
