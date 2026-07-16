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
        proxy observable, not a direct neural measurement of any individual&apos;s
        brain response. The released TRIBE v2 checkpoint predicts cortical
        surface vertices only: the affective-salience and deliberative-control
        regions here are cortical proxies, and the amygdala and nucleus
        accumbens are not measured. The Landau mean-field analysis is a
        theoretical interpretation of the measured NAA value, not direct
        evidence of real-world opinion dynamics. The coupling constant
        alpha-hat is an uncalibrated default, not an empirical estimate: an
        attempted calibration against human arousal ratings returned a null
        result. The NAA index has not been validated against any labelled
        corpus. Monarch is a research instrument, not a diagnostic.
      </p>
    </div>
  );
}
