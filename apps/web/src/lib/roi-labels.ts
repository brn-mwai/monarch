// ============================================================
// roi-labels.ts - ROI metadata + plain-language descriptions
// ============================================================
//
// The 17 brain regions Monarch surfaces in the "Show Guide" overlay,
// each with a hackathon-friendly description. The IDs match the keys
// used by ROILabelManager so the description panel can look the
// matching entry up by name.
// ============================================================

export type ROISystem = 'affective' | 'deliberative' | 'sensory' | 'social';

export interface ROIDescription {
  id: string;
  name: string;
  shortName: string;
  hcpParcels: string[];
  system: ROISystem;
  description: string;
}

export interface ROISystemInfo {
  label: string;
  sublabel: string;
  color: string;
}

export const SYSTEM_INFO: Record<ROISystem, ROISystemInfo> = {
  affective: {
    label: 'Affective-Salience System',
    sublabel: 'Drives the NAA numerator (A_aff) - emotional processing',
    color: '#FF6E00',
  },
  deliberative: {
    label: 'Deliberative-Control System',
    sublabel: 'Drives the NAA denominator (A_del) - rational evaluation',
    color: '#FFFFFF',
  },
  sensory: {
    label: 'Sensory Processing',
    sublabel: 'Input pathways - what the brain receives',
    color: '#9CDCB6',
  },
  social: {
    label: 'Social Cognition',
    sublabel: 'Social interpretation - understanding other minds',
    color: '#FFD60A',
  },
};

// === Affective-salience (NAA numerator) ===

export const AFFECTIVE_DESCRIPTIONS: ROIDescription[] = [
  {
    id: 'OFC',
    name: 'Orbitofrontal Cortex',
    shortName: 'OFC',
    hcpParcels: ['OFC'],
    system: 'affective',
    description:
      "Evaluates reward value and emotional significance. When this region activates strongly, the brain is assigning emotional weight to content before conscious evaluation begins.",
  },
  {
    id: 'Insula',
    name: 'Anterior Insular Cortex',
    shortName: 'Insula',
    hcpParcels: ['AAIC'],
    system: 'affective',
    description:
      "The brain's salience detector. Flags stimuli as worthy of immediate attention. This is the cortical hub of the gut feeling - when content triggers it, the brain shifts from passive processing to alert engagement.",
  },
  {
    id: 'ACC',
    name: 'Anterior Cingulate Cortex',
    shortName: 'ACC',
    hcpParcels: ['a24', 'p24'],
    system: 'affective',
    description:
      "Monitors urgency and drives the feeling that you must react now. In the affective context it generates the sense of alarm or outrage that overrides careful thinking.",
  },
  {
    id: 'TP',
    name: 'Temporal Pole',
    shortName: 'Temporal Pole',
    hcpParcels: ['TGd'],
    system: 'affective',
    description:
      "Binds emotional associations to concepts and social situations. Active when content triggers social-emotional processing - outrage about a person, fear about a group, empathy for a victim.",
  },
  {
    id: 'ATC',
    name: 'Anterior Temporal Cortex',
    shortName: 'Ant. Temporal',
    hcpParcels: ['TE1a', 'TE1p'],
    system: 'affective',
    description:
      "Cortical correlate of amygdala-driven emotional processing. Responds to threat, disgust, and fear signals before the prefrontal cortex can evaluate them. The cortex's fastest emotional responder.",
  },
];

// === Deliberative-control (NAA denominator) ===

export const DELIBERATIVE_DESCRIPTIONS: ROIDescription[] = [
  {
    id: 'DLPFC',
    name: 'Dorsolateral Prefrontal Cortex',
    shortName: 'DLPFC',
    hcpParcels: ['46', '9-46v'],
    system: 'deliberative',
    description:
      "The brain's executive control center. Working memory, rational evaluation, deliberate decision-making. When DLPFC is active the brain is thinking ABOUT content rather than reacting to it.",
  },
  {
    id: 'VMPFC',
    name: 'Ventromedial Prefrontal Cortex',
    shortName: 'VMPFC',
    hcpParcels: ['11l', '13l'],
    system: 'deliberative',
    description:
      "The bridge between emotion and reason. Integrates emotional signals with rational evaluation for value-based decisions. Active VMPFC means the brain is weighing evidence, not just reacting.",
  },
  {
    id: 'FPC',
    name: 'Frontopolar Cortex',
    shortName: 'Frontopolar',
    hcpParcels: ['10p', '10pp'],
    system: 'deliberative',
    description:
      "Supports abstract reasoning, future planning, and metacognition - thinking about thinking. Active when evaluating information reliability or considering alternative interpretations.",
  },
  {
    id: 'dACC',
    name: 'Dorsal Anterior Cingulate',
    shortName: 'dACC',
    hcpParcels: ['d32', 'p32'],
    system: 'deliberative',
    description:
      "Cognitive control hub. Detects conflicts between automatic emotional responses and deliberate goals. When dACC is active the brain is actively choosing to think rather than react.",
  },
];

export const ALL_ROI_DESCRIPTIONS: ROIDescription[] = [
  ...AFFECTIVE_DESCRIPTIONS,
  ...DELIBERATIVE_DESCRIPTIONS,
];

/** Look up the description record for an ROI by its short name (e.g. "OFC"). */
export function getROIDescription(name: string): ROIDescription | undefined {
  return ALL_ROI_DESCRIPTIONS.find((r) => r.id === name || r.shortName === name);
}
