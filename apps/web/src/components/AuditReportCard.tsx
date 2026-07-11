'use client';

import type { AuditReport } from '@/lib/inference-client';

interface AuditReportCardProps {
  report: AuditReport | null;
  loading: boolean;
}

/**
 * Renders the plain-language audit narrative. Splits the Summary / Key
 * findings / Caveats blocks (shared by the Gemma output and the template
 * fallback) and attributes the source honestly: a real Gemma-via-Fireworks
 * generation versus the deterministic template.
 */
export function AuditReportCard({ report, loading }: AuditReportCardProps) {
  if (loading) {
    return (
      <section className="rounded-lg border border-white/10 p-5">
        <SectionHeading />
        <p className="text-xs text-white/50">Generating plain-language audit...</p>
      </section>
    );
  }

  if (!report) return null;

  const blocks = parseBlocks(report.summary);

  return (
    <section className="rounded-lg border border-white/10 p-5">
      <div className="mb-3 flex items-center justify-between gap-3">
        <SectionHeading />
        <SourceBadge source={report.source} model={report.model} />
      </div>

      <div className="space-y-3">
        {blocks.map((block) => (
          <div key={block.heading}>
            <h3 className="mb-1 font-mono text-[10px] uppercase tracking-wider text-white/40">
              {block.heading}
            </h3>
            <p className="whitespace-pre-wrap text-xs leading-relaxed text-white/75">
              {block.body}
            </p>
          </div>
        ))}
      </div>

      <p className="mt-4 border-t border-white/10 pt-3 text-[10px] leading-relaxed text-white/35">
        {report.source === 'gemma'
          ? `Written by ${shortModel(report.model)} via Fireworks AI (runs on AMD). Grounded in the scan numbers above.`
          : 'Deterministic template (no language model configured). Set FIREWORKS_API_KEY on the inference server for the model-written version.'}
      </p>
    </section>
  );
}

function SectionHeading() {
  return (
    <h2 className="font-mono text-[11px] uppercase tracking-wider text-white/45">
      Plain-language audit
    </h2>
  );
}

/** Last path segment of a Fireworks slug, e.g. ".../gpt-oss-120b" -> "gpt-oss-120b". */
function shortModel(model: string): string {
  const segment = model.split('/').pop() ?? model;
  return segment || model;
}

function SourceBadge({ source, model }: { source: AuditReport['source']; model: string }) {
  const isModel = source === 'gemma';
  return (
    <span
      title={model}
      className={`rounded-full border px-2.5 py-0.5 font-mono text-[9px] uppercase tracking-wider ${
        isModel
          ? 'border-emerald-400/40 text-emerald-300/90'
          : 'border-white/20 text-white/45'
      }`}
    >
      {isModel ? `${shortModel(model)} - Fireworks / AMD` : 'Template'}
    </span>
  );
}

interface NarrativeBlock {
  heading: string;
  body: string;
}

function parseBlocks(summary: string): NarrativeBlock[] {
  const chunks = summary
    .split(/\n\s*\n/)
    .map((c) => c.trim())
    .filter(Boolean);

  return chunks.map((chunk) => {
    const newline = chunk.indexOf('\n');
    if (newline === -1) {
      return { heading: 'Summary', body: chunk };
    }
    return {
      heading: chunk.slice(0, newline).trim(),
      body: chunk.slice(newline + 1).trim(),
    };
  });
}
