import type { ReactNode } from 'react';

/**
 * The small subset of Markdown the assistant is told to produce: bold, inline code, and
 * dash bullets. Written here rather than pulled in as a dependency because a full parser
 * would also render images, links and raw HTML from model output, which is a larger
 * surface than this page needs.
 */
function inline(text: string, keyPrefix: string): ReactNode[] {
  const out: ReactNode[] = [];
  const pattern = /(\*\*[^*]+\*\*|`[^`]+`)/g;
  let last = 0;
  let match: RegExpExecArray | null;
  let index = 0;

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > last) out.push(text.slice(last, match.index));
    const token = match[0];
    const key = `${keyPrefix}-${index++}`;

    if (token.startsWith('**')) {
      out.push(
        <strong key={key} className="font-semibold text-white">
          {token.slice(2, -2)}
        </strong>,
      );
    } else {
      out.push(
        <code
          key={key}
          className="rounded bg-white/[0.08] px-1 py-0.5 font-mono text-[11px] text-white/90"
        >
          {token.slice(1, -1)}
        </code>,
      );
    }
    last = match.index + token.length;
  }

  if (last < text.length) out.push(text.slice(last));
  return out;
}

export function Markdown({ text }: { text: string }) {
  const blocks: ReactNode[] = [];
  const lines = text.split('\n');
  let bullets: string[] = [];
  let key = 0;

  const flushBullets = () => {
    if (bullets.length === 0) return;
    blocks.push(
      <ul key={`ul-${key++}`} className="ml-1 list-disc space-y-1 pl-4 marker:text-white/30">
        {bullets.map((item, i) => (
          <li key={i}>{inline(item, `li-${key}-${i}`)}</li>
        ))}
      </ul>,
    );
    bullets = [];
  };

  for (const raw of lines) {
    const line = raw.trimEnd();
    const bullet = line.match(/^\s*[-*]\s+(.*)$/);
    const numbered = line.match(/^\s*\d+[.)]\s+(.*)$/);

    if (bullet) {
      bullets.push(bullet[1]);
      continue;
    }
    if (numbered) {
      bullets.push(numbered[1]);
      continue;
    }

    flushBullets();
    if (line.trim() === '') continue;
    blocks.push(<p key={`p-${key++}`}>{inline(line, `p-${key}`)}</p>);
  }
  flushBullets();

  return <div className="space-y-2">{blocks}</div>;
}
