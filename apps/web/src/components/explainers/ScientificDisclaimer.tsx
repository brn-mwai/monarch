'use client';

/**
 * Appears at the bottom of every result view (Scanner, Report,
 * Compare, Batch). Concise, always visible, no toggle.
 */
export function ScientificDisclaimer() {
  return (
    <div className="mt-8 border-t border-white/5 pt-4">
      <p className="text-[11px] leading-relaxed text-white/25">
        Monarch estimates predicted population-level cortical processing
        balance using TRIBE v2 (Meta FAIR, 2026). The NAA index is a derived
        proxy observable, not a direct neural measurement of any individual's
        brain response. The Landau mean-field analysis is a theoretical
        interpretation of the measured NAA value, not direct evidence of
        real-world opinion dynamics. Validation is convergent (SemEval-2020
        Task 11), not criterion. The coupling constant alpha-hat is a heuristic
        field-scale estimate calibrated on NELA-GT-2021 source-level
        credibility scores.
      </p>
    </div>
  );
}
