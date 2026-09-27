## Summary
A new /research page on the Monarch site holds a real 3D, flippable copy of the dissertation: a
maroon cloth hardcover with gold CUEA lettering, pages that bend as they turn, stacked page edges,
soft shadows, synthesized page-flip sounds, a contents drawer, and a flat reading view. The
header's Research link now points to it instead of cuea.edu.

Protection: only the preview pages (title, abstract, contents: PDF pages 1, 5, 6, 11-14) are
exported to the site. Every other page is never uploaded. The browser draws those pages as
"locked" from nothing but their page number, so there is no content to extract, whatever someone
changes in the front end. Rate limiting is unnecessary, because nothing protected is served.

## docs/submission/export_book_assets.py
Builds the book's static assets from `docs/thesis/dissertation.pdf` into
`apps/web/public/research/book/`.
- `is_blank(page)`: marks pages with no text, images or drawings, so the book shows them as plain paper.
- `export_pages(doc)`: renders only `PREVIEW_PAGES` to WebP at 1240 px wide. This allow-list is the security boundary.
- `cloth(width, height, seed)`: procedural maroon bookcloth (weave, speckle, soft blotches).
- `gold_text(...)`: gold-foil lettering with a vertical gradient and a small drop shadow, optionally rotated for the spine.
- `make_covers(aspect)`: the front cover in the CUEA layout, a plain back cover, and the spine text.
- `outline(doc)`: chapter and section entries (levels 1 and 2) from the PDF bookmarks.
- `main()`: writes `book.json` (page count, aspect, roman or arabic page labels, preview and blank lists, outline).

## apps/web/src/components/research/bookEngine.ts
The plain Three.js engine.
- The book lies in the XY plane, tilted back like a book on a desk. Leaf 0 is the rigid front cover (a box, hinged at the spine). Leaves 1-41 are paper, each two pages (front = odd PDF page, back = even), which matches a bound book.
- `shapeLeaf`: writes each paper leaf's vertices directly. Each column of the plane is placed by accumulating unit steps at angle `angle - curl * along^2`, so mid-turn the tip lags behind and the page curls. The front mesh uses FrontSide, and the back mesh BackSide with a mirrored texture, so the verso reads correctly on the left.
- `restZ`: stacking heights. The right stack counts down from the cover, the left stack builds up from the front cover.
- `layoutBlocks` and `setBlock`: two boxes with a striped edge texture stand in for the page stacks on each side, sized to the number of leaves, with the top just below the top leaf to avoid z-fighting.
- `enqueue` and `drain`: queue of single-leaf flips. Jumps play as fast staggered flips with quieter sounds.
- `ensureTextures` and `applyPage`: lazy-loads textures for leaves within 3 of the current spread. Preview pages load their WebP; other non-blank pages get a locked canvas.
- `placeCamera`: eases the camera to fit the closed cover, the open spread, or the back cover to the viewport, with a slight pointer-driven sway and a pinch or ctrl-wheel zoom.
- `goToPage(page)`: maps a PDF page to the spread that shows it (odd = recto on the right, even = verso on the left).

## apps/web/src/components/research/bookTextures.ts
- `paperGrain`: a noise bump map for paper and endpapers.
- `stripeEdge`: page-edge stripes for the stack blocks.
- `drawLockedPage(page, label, aspect)`: faint blurred "ghost" text lines, a card with a lock icon, the CUEA Library notice, and the page label. It uses only the page number, never content.

## apps/web/src/components/research/flipSound.ts
- `playFlip(fast)`: a synthesized flip, with no audio file to license or download. Brown-tinted noise through a bandpass sweeping from 3.2 kHz down to 900 Hz, a quick attack and decay, and a soft low thump as the page lands. Fast flips are shorter and quieter.

## apps/web/src/components/research/Book3D.tsx
The React wrapper.
- It loads `book.json`, creates and disposes the engine, and handles keyboard arrows, click on the right or left half, swipe (over 40 px), pinch and ctrl-wheel zoom.
- Controls: close, previous, the spread label (such as "v – vi"), next, back cover, Contents (a bottom sheet on phones), Read this spread (a flat, readable overlay), and a sound toggle. The sound setting is remembered in localStorage inside try/catch.
- Locked pages in the reader show the same library notice.

## apps/web/src/app/research/page.tsx and Header.tsx
- `research/page.tsx`: title, the book, an access note, the three papers (described, not linked), and a link to the corpus.
- `Header.tsx`: Research now goes to /research.
