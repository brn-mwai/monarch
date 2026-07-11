'use client';

import { UploadSimple } from '@phosphor-icons/react/dist/ssr';
import { useMemo, useRef, useState } from 'react';

import { BatchScatter, type BatchItem } from '@/components/charts/BatchScatter';
import { ScientificDisclaimer } from '@/components/explainers/ScientificDisclaimer';
import { BATCH_CORPUS } from '@/lib/example-content';
import { scanText } from '@/lib/inference-client';
import { type ContentCategory } from '@/lib/mock-data';
import { useScanState, type ScanResult } from '@/lib/scan-store';

const KNOWN_CATEGORIES = new Set<ContentCategory>([
  'neutral',
  'high-outrage',
  'fear-activating',
  'reward-hook',
]);

function coerceCategory(raw: string | undefined): ContentCategory {
  const value = (raw ?? '').trim().toLowerCase() as ContentCategory;
  return KNOWN_CATEGORIES.has(value) ? value : 'neutral';
}

interface CorpusRow {
  id: string;
  text: string;
  category: ContentCategory;
  label: string;
}

const DEFAULT_ROWS: CorpusRow[] = BATCH_CORPUS.map((item) => ({
  id: item.id,
  text: item.text,
  category: item.category,
  label: item.label,
}));

// Minimal CSV parse: one record per line, columns id,text,category, with
// support for double-quoted fields that contain commas. Good enough for the
// corpus manifests users paste in; not a full RFC-4180 parser.
function parseCsv(raw: string): CorpusRow[] {
  const lines = raw.split(/\r?\n/).filter((line) => line.trim().length > 0);
  if (lines.length === 0) return [];

  const splitLine = (line: string): string[] => {
    const cells: string[] = [];
    let cur = '';
    let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (ch === '"') {
        if (inQuotes && line[i + 1] === '"') {
          cur += '"';
          i++;
        } else {
          inQuotes = !inQuotes;
        }
      } else if (ch === ',' && !inQuotes) {
        cells.push(cur);
        cur = '';
      } else {
        cur += ch;
      }
    }
    cells.push(cur);
    return cells.map((c) => c.trim());
  };

  const header = splitLine(lines[0]).map((h) => h.toLowerCase());
  const hasHeader = header.includes('text') || header.includes('id');
  const idCol = hasHeader ? header.indexOf('id') : 0;
  const textCol = hasHeader ? header.indexOf('text') : 1;
  const catCol = hasHeader ? header.indexOf('category') : 2;

  const rows: CorpusRow[] = [];
  const body = hasHeader ? lines.slice(1) : lines;
  body.forEach((line, i) => {
    const cells = splitLine(line);
    const text = (textCol >= 0 ? cells[textCol] : cells[0]) ?? '';
    if (!text.trim()) return;
    rows.push({
      id: (idCol >= 0 ? cells[idCol] : '') || `row-${i + 1}`,
      text,
      category: coerceCategory(catCol >= 0 ? cells[catCol] : undefined),
      label: text.slice(0, 48),
    });
  });
  return rows;
}

interface BatchTabProps {
  /** Called after a clicked item is loaded as the active scan (e.g. to
   *  navigate to its full report). The brain is already updated by then. */
  onInspect?: () => void;
}

/**
 * "Batch Audit" panel. Scores a corpus of text items by NAA: a labelled sample
 * corpus by default, or a CSV you upload. Each item is run through the same
 * scan path as a single item (real model when connected, synthetic fallback
 * otherwise), plotted, ranked, click-to-inspect, and exportable back to CSV.
 * Rendered both as the scanner's Batch tab and as the standalone /batch page.
 */
export function BatchTab({ onInspect }: BatchTabProps = {}) {
  const { dispatch } = useScanState();
  const fileRef = useRef<HTMLInputElement | null>(null);

  const [rows, setRows] = useState<CorpusRow[]>(DEFAULT_ROWS);
  const [scores, setScores] = useState<Record<string, number>>(() =>
    Object.fromEntries(BATCH_CORPUS.map((c) => [c.id, c.expectedNAA])),
  );
  const [results, setResults] = useState<Record<string, ScanResult>>({});
  const [source, setSource] = useState<'sample' | 'uploaded'>('sample');
  const [progress, setProgress] = useState<{ done: number; total: number } | null>(
    null,
  );

  const items: BatchItem[] = useMemo(
    () =>
      rows.map((row, index) => ({
        id: row.id,
        index,
        naa: scores[row.id] ?? 0,
        category: row.category,
        label: row.label,
      })),
    [rows, scores],
  );

  const ranked = useMemo(
    () => [...items].sort((a, b) => b.naa - a.naa),
    [items],
  );

  const scoreCorpus = async (corpus: CorpusRow[]) => {
    setProgress({ done: 0, total: corpus.length });
    const nextScores: Record<string, number> = {};
    const nextResults: Record<string, ScanResult> = {};
    // Sequential keeps the progress readable and avoids hammering the server
    // with the whole corpus at once; each item is a fast call either way.
    for (let i = 0; i < corpus.length; i++) {
      const row = corpus[i];
      try {
        const result = await scanText(row.text);
        nextScores[row.id] = result.naa.naa;
        nextResults[row.id] = result;
      } catch {
        nextScores[row.id] = 0;
      }
      setProgress({ done: i + 1, total: corpus.length });
    }
    setScores(nextScores);
    setResults(nextResults);
    setProgress(null);
  };

  const handleUpload = (file: File) => {
    const reader = new FileReader();
    reader.onload = () => {
      const parsed = parseCsv(String(reader.result ?? ''));
      if (parsed.length === 0) return;
      setRows(parsed);
      setSource('uploaded');
      setResults({});
      void scoreCorpus(parsed);
    };
    reader.readAsText(file);
  };

  const handleItemClick = async (item: BatchItem) => {
    const cached = results[item.id];
    if (cached) {
      dispatch({ type: 'SCAN_COMPLETE_A', result: cached });
      dispatch({ type: 'SET_COLOR_MODE', mode: 'activation' });
      onInspect?.();
      return;
    }
    const row = rows.find((r) => r.id === item.id);
    if (!row) return;
    try {
      const result = await scanText(row.text);
      setResults((prev) => ({ ...prev, [item.id]: result }));
      setScores((prev) => ({ ...prev, [item.id]: result.naa.naa }));
      dispatch({ type: 'SCAN_COMPLETE_A', result });
      dispatch({ type: 'SET_COLOR_MODE', mode: 'activation' });
      onInspect?.();
    } catch (err) {
      dispatch({ type: 'ERROR', message: String(err) });
    }
  };

  const exportCsv = () => {
    const escape = (value: string) => `"${value.replace(/"/g, '""')}"`;
    const header = 'id,text,category,naa,classification';
    const body = ranked
      .map((item) => {
        const row = rows.find((r) => r.id === item.id);
        const naa = item.naa;
        const cls = naa < 1 ? 'LOW' : naa <= 2 ? 'MOD' : 'HIGH';
        return [
          escape(item.id),
          escape(row?.text ?? ''),
          escape(item.category),
          naa.toFixed(3),
          cls,
        ].join(',');
      })
      .join('\n');
    const blob = new Blob([`${header}\n${body}\n`], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `monarch-batch-${source}-${rows.length}.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  const scoring = progress !== null;

  return (
    <div className="space-y-5">
      <div className="space-y-3 text-[15px] leading-relaxed text-white/75">
        <p>
          Score a corpus of text items by NAA. Below is a {DEFAULT_ROWS.length}-item
          sample corpus spanning calm to reactive content; upload your own CSV
          (columns <span className="font-mono text-white/60">id, text, category</span>)
          to audit up to 1,500 items. Each item runs through the same encoder as a
          single scan.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          disabled={scoring}
          className="flex items-center gap-2 rounded-lg border border-dashed border-white/15 px-4 py-2 text-xs text-white/60 transition-colors hover:border-white/30 hover:text-white/80 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <UploadSimple size={16} className="text-white/40" />
          Upload CSV corpus
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".csv,text/csv"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleUpload(file);
            e.target.value = '';
          }}
        />
        <button
          type="button"
          onClick={() => void scoreCorpus(rows)}
          disabled={scoring}
          className="rounded-full border border-white/25 px-4 py-1.5 font-mono text-[11px] uppercase tracking-wider text-white/75 transition-colors hover:border-white/50 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
        >
          {scoring ? `Scoring ${progress?.done}/${progress?.total}` : 'Score corpus'}
        </button>
        <button
          type="button"
          onClick={exportCsv}
          disabled={scoring}
          className="rounded-full border border-white/25 px-4 py-1.5 font-mono text-[11px] uppercase tracking-wider text-white/75 transition-colors hover:border-white/50 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
        >
          Export CSV
        </button>
        <span className="font-mono text-[10px] uppercase tracking-wider text-white/35">
          {source === 'sample' ? 'Sample corpus' : 'Uploaded corpus'} - {rows.length} items
        </span>
      </div>

      <div className="rounded-lg border border-white/10 p-4">
        <BatchScatter items={items} onItemClick={handleItemClick} />
      </div>

      {/* Ranked table */}
      <section className="rounded-lg border border-white/10">
        <header className="flex items-center justify-between border-b border-white/10 px-4 py-2 font-mono text-[10px] uppercase tracking-wider text-white/50">
          <span>Ranked by NAA</span>
          <span>{ranked.length} items</span>
        </header>
        <div className="max-h-80 overflow-y-auto">
          <table className="w-full table-fixed text-xs">
            <colgroup>
              <col className="w-12" />
              <col />
              <col className="w-36" />
              <col className="w-20" />
            </colgroup>
            <thead className="sticky top-0 bg-black/90 backdrop-blur">
              <tr className="text-left text-white/40">
                <th className="px-4 py-2 font-mono text-[10px] uppercase tracking-wider">#</th>
                <th className="px-4 py-2 font-mono text-[10px] uppercase tracking-wider">Item</th>
                <th className="px-4 py-2 font-mono text-[10px] uppercase tracking-wider">Category</th>
                <th className="px-4 py-2 text-right font-mono text-[10px] uppercase tracking-wider">NAA</th>
              </tr>
            </thead>
            <tbody>
              {ranked.map((item, i) => (
                <tr
                  key={item.id}
                  onClick={() => handleItemClick(item)}
                  className="cursor-pointer border-t border-white/[0.04] text-white/80 transition-colors hover:bg-white/5 hover:text-white"
                >
                  <td className="px-4 py-2 font-mono text-white/30">{i + 1}</td>
                  <td className="truncate px-4 py-2" title={item.label}>{item.label}</td>
                  <td className="truncate px-4 py-2 text-white/50">{item.category}</td>
                  <td className="px-4 py-2 text-right font-mono">
                    {item.naa.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <ScientificDisclaimer />
    </div>
  );
}
