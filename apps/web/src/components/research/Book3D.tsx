'use client';

import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  CaretDoubleLeft,
  CaretDoubleRight,
  ListBullets,
  LockSimple,
  MagnifyingGlassPlus,
  SpeakerHigh,
  SpeakerSlash,
  X,
} from '@phosphor-icons/react';
import { useCallback, useEffect, useRef, useState } from 'react';

import { BookEngine, type BookMeta, type BookState } from './bookEngine';

const SWIPE_PX = 40;
const MUTE_KEY = 'monarch.book.muted';

function readMuted() {
  try {
    return window.localStorage.getItem(MUTE_KEY) === '1';
  } catch {
    return false;
  }
}

function writeMuted(muted: boolean) {
  try {
    window.localStorage.setItem(MUTE_KEY, muted ? '1' : '0');
  } catch {
    return;
  }
}

function spreadLabel(meta: BookMeta, state: BookState) {
  if (state.flipped === 0) return 'Front cover';
  if (state.flipped === state.total) return 'Back cover';
  const shown = state.side === 'left' ? [state.left] : state.side === 'right' ? [state.right] : [state.left, state.right];
  const pages = shown.filter((page): page is number => page !== null);
  if (!pages.length) return 'Inside cover';
  return pages.map((page) => meta.labels[page - 1] ?? String(page)).join(' – ');
}

function PagePane({ meta, page }: { meta: BookMeta; page: number | null }) {
  if (page === null || meta.blank.includes(page)) {
    return <div className="aspect-[1/1.414] w-full rounded-sm bg-[#f6f2e8]" />;
  }
  if (meta.preview.includes(page)) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={`/research/book/pages/p${String(page).padStart(3, '0')}.webp`}
        alt={`Dissertation page ${meta.labels[page - 1] ?? page}`}
        className="aspect-[1/1.414] w-full rounded-sm bg-[#f6f2e8] object-contain"
      />
    );
  }
  return (
    <div className="flex aspect-[1/1.414] w-full flex-col items-center justify-center gap-3 rounded-sm bg-[#f6f2e8] px-6 text-center text-[#2a2420]">
      <LockSimple size={36} weight="fill" className="text-[#6b1c2a]" />
      <p className="font-serif text-base">Available in full at the CUEA Library</p>
      <p className="text-sm text-[#6f675d]">Page {meta.labels[page - 1] ?? page}</p>
    </div>
  );
}

export function Book3D() {
  const containerRef = useRef<HTMLDivElement>(null);
  const engineRef = useRef<BookEngine | null>(null);
  const pointerRef = useRef<{ id: number; x: number; y: number }[]>([]);
  const pinchRef = useRef(0);
  const [meta, setMeta] = useState<BookMeta | null>(null);
  const [state, setState] = useState<BookState | null>(null);
  const [error, setError] = useState(false);
  const [muted, setMuted] = useState(false);
  const [outlineOpen, setOutlineOpen] = useState(false);
  const [readerOpen, setReaderOpen] = useState(false);

  useEffect(() => {
    setMuted(readMuted());
    fetch('/research/book/book.json')
      .then((response) => (response.ok ? response.json() : Promise.reject(response.status)))
      .then((data: BookMeta) => setMeta(data))
      .catch(() => setError(true));
  }, []);

  useEffect(() => {
    const container = containerRef.current;
    if (!meta || !container) return;
    let engine: BookEngine;
    try {
      engine = new BookEngine(container, meta, setState);
    } catch {
      setError(true);
      return;
    }
    engine.setMuted(readMuted());
    engineRef.current = engine;
    return () => {
      engine.dispose();
      engineRef.current = null;
    };
  }, [meta]);

  useEffect(() => {
    engineRef.current?.setMuted(muted);
  }, [muted]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) return;
      if (event.key === 'ArrowRight') engineRef.current?.next();
      if (event.key === 'ArrowLeft') engineRef.current?.prev();
      if (event.key === 'Escape') {
        setReaderOpen(false);
        setOutlineOpen(false);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const onPointerDown = useCallback((event: React.PointerEvent<HTMLDivElement>) => {
    pointerRef.current.push({ id: event.pointerId, x: event.clientX, y: event.clientY });
    if (pointerRef.current.length === 2) {
      const [a, b] = pointerRef.current;
      pinchRef.current = Math.hypot(a.x - b.x, a.y - b.y);
    }
  }, []);

  const onPointerMove = useCallback((event: React.PointerEvent<HTMLDivElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    engineRef.current?.setPointer(
      ((event.clientX - rect.left) / rect.width) * 2 - 1,
      -(((event.clientY - rect.top) / rect.height) * 2 - 1),
    );
    const pointers = pointerRef.current;
    const tracked = pointers.find((pointer) => pointer.id === event.pointerId);
    if (!tracked || pointers.length !== 2) return;
    tracked.x = event.clientX;
    tracked.y = event.clientY;
    const [a, b] = pointers;
    const distance = Math.hypot(a.x - b.x, a.y - b.y);
    if (pinchRef.current) engineRef.current?.zoomBy(distance / pinchRef.current);
    pinchRef.current = distance;
  }, []);

  const onPointerUp = useCallback((event: React.PointerEvent<HTMLDivElement>) => {
    const pointers = pointerRef.current;
    const start = pointers.find((pointer) => pointer.id === event.pointerId);
    const wasPinch = pointers.length > 1;
    pointerRef.current = pointers.filter((pointer) => pointer.id !== event.pointerId);
    if (!start || wasPinch) return;
    const engine = engineRef.current;
    if (!engine) return;
    const dx = event.clientX - start.x;
    if (Math.abs(dx) > SWIPE_PX) {
      if (dx < 0) engine.next();
      else engine.prev();
      return;
    }
    const rect = event.currentTarget.getBoundingClientRect();
    if (event.clientX - rect.left > rect.width / 2) engine.next();
    else engine.prev();
  }, []);

  const onPointerCancel = useCallback((event: React.PointerEvent<HTMLDivElement>) => {
    pointerRef.current = pointerRef.current.filter((pointer) => pointer.id !== event.pointerId);
  }, []);

  const onWheel = useCallback((event: React.WheelEvent<HTMLDivElement>) => {
    if (!event.ctrlKey && !event.metaKey) return;
    engineRef.current?.zoomBy(event.deltaY > 0 ? 0.93 : 1.07);
  }, []);

  const toggleMuted = () => {
    setMuted((current) => {
      writeMuted(!current);
      return !current;
    });
  };

  const goTo = (page: number) => {
    engineRef.current?.goToPage(page);
    setOutlineOpen(false);
  };

  if (error) {
    return (
      <div className="flex h-[60vh] items-center justify-center rounded-2xl border border-white/10 text-sm text-white/60">
        The book could not be loaded on this device.
      </div>
    );
  }

  const controlButton =
    'inline-flex h-11 min-w-11 items-center justify-center gap-2 rounded-full border border-white/15 bg-white/5 px-3 text-sm text-white/80 transition-colors hover:bg-white/10 hover:text-white disabled:opacity-35';

  return (
    <div className="relative">
      <div
        ref={containerRef}
        role="application"
        aria-label="Dissertation book. Use the arrow keys, swipe, or click a page to turn it."
        tabIndex={0}
        className="relative h-[62vh] min-h-[380px] w-full cursor-pointer touch-none select-none overflow-hidden rounded-2xl border border-white/10 bg-[radial-gradient(ellipse_at_center,#1c1416_0%,#050505_70%)] outline-none focus-visible:ring-2 focus-visible:ring-white/30 sm:h-[72vh]"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerCancel}
        onWheel={onWheel}
      >
        {!state && (
          <div className="absolute inset-0 flex items-center justify-center text-sm text-white/50">Opening the book…</div>
        )}
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
        <button type="button" className={controlButton} aria-label="Close the book" onClick={() => engineRef.current?.first()} disabled={!state || state.flipped === 0}>
          <CaretDoubleLeft size={16} />
        </button>
        <button type="button" className={controlButton} aria-label="Previous page" onClick={() => engineRef.current?.prev()} disabled={!state || state.flipped === 0}>
          <ArrowLeft size={16} />
        </button>
        <span className="min-w-[8.5rem] text-center font-mono text-sm tabular-nums text-white/70" aria-live="polite">
          {meta && state ? spreadLabel(meta, state) : '…'}
        </span>
        <button type="button" className={controlButton} aria-label="Next page" onClick={() => engineRef.current?.next()} disabled={!state || state.flipped === state.total}>
          <ArrowRight size={16} />
        </button>
        <button type="button" className={controlButton} aria-label="Go to the back cover" onClick={() => engineRef.current?.last()} disabled={!state || state.flipped === state.total}>
          <CaretDoubleRight size={16} />
        </button>
      </div>

      <div className="mt-3 flex flex-wrap items-center justify-center gap-2">
        <button type="button" className={controlButton} onClick={() => setOutlineOpen(true)} disabled={!meta}>
          <ListBullets size={16} /> Contents
        </button>
        <button type="button" className={controlButton} onClick={() => setReaderOpen(true)} disabled={!state || state.flipped === 0 || state.flipped === state.total}>
          <MagnifyingGlassPlus size={16} /> Read this spread
        </button>
        <button type="button" className={controlButton} aria-pressed={!muted} onClick={toggleMuted}>
          {muted ? <SpeakerSlash size={16} /> : <SpeakerHigh size={16} />} {muted ? 'Sound off' : 'Sound on'}
        </button>
      </div>

      {outlineOpen && meta && (
        <div className="fixed inset-0 z-[60] flex items-end justify-center bg-black/70 sm:items-center" onClick={() => setOutlineOpen(false)}>
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Contents"
            className="max-h-[85vh] w-full overflow-hidden rounded-t-2xl border border-white/10 bg-[#0d0d0d] pb-[env(safe-area-inset-bottom)] sm:max-w-lg sm:rounded-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
              <p className="flex items-center gap-2 text-sm font-medium text-white">
                <BookOpen size={18} /> Contents
              </p>
              <button type="button" className="inline-flex h-11 w-11 items-center justify-center rounded-full text-white/70 hover:bg-white/10 hover:text-white" aria-label="Close contents" onClick={() => setOutlineOpen(false)}>
                <X size={18} />
              </button>
            </div>
            <ol className="max-h-[70vh] overflow-y-auto px-2 py-2">
              <li>
                <button type="button" onClick={() => goTo(1)} className="flex min-h-11 w-full items-center justify-between gap-3 rounded-lg px-3 text-left text-sm text-white/85 hover:bg-white/5">
                  <span>Title page</span>
                  <span className="font-mono text-xs tabular-nums text-white/45">{meta.labels[0]}</span>
                </button>
              </li>
              {meta.outline.map((entry) => {
                const locked = !meta.preview.includes(entry.page);
                return (
                  <li key={`${entry.page}-${entry.title}`}>
                    <button
                      type="button"
                      onClick={() => goTo(entry.page)}
                      className={`flex min-h-11 w-full items-center justify-between gap-3 rounded-lg px-3 text-left text-sm hover:bg-white/5 ${
                        entry.level === 1 ? 'text-white/85' : 'pl-7 text-white/60'
                      }`}
                    >
                      <span className="flex items-center gap-2">
                        {locked && <LockSimple size={12} className="shrink-0 text-white/35" aria-label="Library only" />}
                        {entry.title}
                      </span>
                      <span className="font-mono text-xs tabular-nums text-white/45">{meta.labels[entry.page - 1] ?? entry.page}</span>
                    </button>
                  </li>
                );
              })}
            </ol>
          </div>
        </div>
      )}

      {readerOpen && meta && state && (
        <div className="fixed inset-0 z-[60] overflow-y-auto bg-black/85 px-4 pb-10 pt-20" onClick={() => setReaderOpen(false)}>
          <button type="button" className="fixed right-4 top-20 inline-flex h-11 w-11 items-center justify-center rounded-full bg-white/10 text-white hover:bg-white/20" aria-label="Close reader" onClick={() => setReaderOpen(false)}>
            <X size={20} />
          </button>
          <div className="mx-auto grid max-w-5xl gap-4 sm:grid-cols-2" onClick={(event) => event.stopPropagation()}>
            <PagePane meta={meta} page={state.left} />
            <PagePane meta={meta} page={state.right} />
          </div>
        </div>
      )}
    </div>
  );
}
