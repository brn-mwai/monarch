import 'katex/dist/katex.min.css';

import katex from 'katex';

interface EquationProps {
  /** Raw LaTeX source (no surrounding `$$`). */
  tex: string;
  /** When true renders inline (default block / display style). */
  inline?: boolean;
  className?: string;
}

/**
 * Server-rendered KaTeX equation. Pre-renders to HTML at request time
 * so there is no client-side math typesetting flash. Uses KaTeX's CSS
 * (imported once here) for the glyph layout.
 */
export function Equation({ tex, inline = false, className = '' }: EquationProps) {
  const html = katex.renderToString(tex, {
    displayMode: !inline,
    throwOnError: false,
    output: 'html',
    strict: 'ignore',
  });

  return (
    <div
      className={`${inline ? 'inline-block' : 'overflow-x-auto'} text-white ${className}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
