# Monarch - Client-Facing User Flows

> How real people use Monarch, step by step, with NO science jargon on screen.
> This is the product/UX source of truth for the interface. The science lives in
> SYSTEM-DESIGN.md; none of those words (NAA, cortical, Landau, Ising, fMRI) appear
> to the user. Author: Brian Mwai. Date: 2026-06-11.

---

## 1. Design rules (non-negotiable)

1. **No jargon on screen.** Never show "NAA", "cortical", "Landau", "Ising", "fMRI",
   "affective-salience". Use the plain words in section 2.
2. **Every step is visible.** The user always knows where they are, what just happened,
   and what to do next. No hidden state, no surprise.
3. **One decision per screen.** Don't ask for two things at once.
4. **The boundary is always shown.** Every result repeats, in one quiet line: "This rates
   the content, not any real person."
5. **Plain results.** Every number comes with a word and a one-sentence meaning.

---

## 2. Plain vocabulary (what we show instead of the science)

| Science term (internal) | What the user sees |
|---|---|
| NAA index | **Pull Score** - a meter from Calm to Charged |
| LOW / MOD / HIGH | **Calm** / **Mixed** / **Charged** |
| UNDEFINED (invalid reading) | **Unclear reading** - "we couldn't get a clear result for this" |
| Predicted cortical activation map | **Heat view** - "where this content tends to land" |
| ROI breakdown | **What drove the score** |
| Landau / Ising opinion model | **Crowd Preview** - a what-if of how a crowd might react |
| Susceptibility | **How easily a crowd could be swayed** |
| Compare mode | **Side-by-side** |
| Batch mode | **Bulk check** |
| Calibrated alpha-hat / physics params | hidden; never shown to the user |

**The Pull Score, in words:**
- **Calm** - built to make you think.
- **Mixed** - some emotional pull, thinking still in play.
- **Charged** - built to hit emotions before you can reason.
- **Unclear** - the content didn't give a clean reading (we don't guess).

---

## 3. The universal result card (what every user sees)

Every scan, for every user, returns the same simple card. Only the wording around it changes.

```
┌─────────────────────────────────────────────┐
│  PULL SCORE:        ●────────────○   CHARGED │   <- meter + word
│                     Calm        Charged       │
│                                               │
│  "This content is built to hit emotions more  │   <- one plain sentence
│   than to make you think."                    │
│                                               │
│  [ Heat view ]  shows where it tends to land  │   <- the brain picture, optional
│  [ What drove it ]  the parts behind the score│   <- expandable detail
│  [ Crowd Preview ]  how a crowd might react   │   <- the what-if, opt-in
│                                               │
│  Rates the content, not any real person.      │   <- the quiet boundary line
└─────────────────────────────────────────────┘
```

**The Unclear state** (this is the brick-1 honesty fix, in plain words):
```
┌─────────────────────────────────────────────┐
│  PULL SCORE:        Unclear reading            │
│                                               │
│  "We couldn't get a clear result for this     │
│   content. Rather than guess, we're telling    │
│   you it's unclear. Try a longer or different  │
│   piece of content."                           │
└─────────────────────────────────────────────┘
```

---

## 4. First-time onboarding (any user, under 60 seconds)

1. **Welcome screen** - one line: "See whether a piece of content is built to hit your
   emotions or to make you think." One button: **Try it**.
2. **Pick what you do** (sets the default mode + wording): Researcher · Teacher · Journalist ·
   Parent/Educator · Safety/Fact-check · Just exploring. (Changeable later in Settings.)
3. **One worked example, pre-loaded** - two versions of the same news already filled in.
   Button: **See the difference**. The result card animates in. No typing required to learn.
4. **"Now try your own"** - drops them into their role's default flow (section 5).

The boundary line appears on the example result, so the user learns it from second one.

---

## 5. Per-demographic flows (step by step)

Each flow names: entry → steps → the result they get → what they do next. Plain words throughout.

### 5.1 Researcher - "study a lot of content"
Default mode: **Bulk check**.
1. **Start** - "Check a batch of content." Button: **Upload a file**.
2. **Upload** - drop a CSV/spreadsheet. Screen shows: "We found 480 items. Ready to check?"
   with a clear count and a **Start** button.
3. **Progress** - a live bar: "Checking 480 items… 120 done." Can leave and come back
   (it resumes). Plain status, never a frozen screen.
4. **Results table** - every item with its Pull Score word (Calm/Mixed/Charged/Unclear),
   sortable. A simple chart shows the spread.
5. **What they get** - a **Bulk Report** (download): the table + the spread chart + a plain
   summary ("62% of these lean Charged"). Exportable as data for their own analysis.
6. **Next** - filter to the Charged items, open any one to see its full card, or export.

### 5.2 Teacher / media-literacy - "show students the difference"
Default mode: **Side-by-side**.
1. **Start** - "Compare two pieces of content." Two boxes: **Version A**, **Version B**.
2. **Fill in** - paste or pick from a library of classroom-safe examples.
3. **Compare** - one button. Both result cards appear side by side, on the same scale so the
   brighter one really is more charged.
4. **What they get** - a **Side-by-side view** built for a screen/projector: two scores, two
   heat views, and one line: "Same story, built two ways." A **Present mode** hides all
   controls for a clean classroom display.
5. **Next** - swap in a new pair, or save the comparison to reuse in a lesson.
   The boundary line ("rates the content, not your students") stays visible - it IS the lesson.

### 5.3 Journalist / editor - "check before I publish"
Default mode: **Single check**.
1. **Start** - "Check your headline or draft." One box. Paste it.
2. **Check** - one button.
3. **What they get** - a **Single check**: the Pull Score word + one plain line
   ("This leans Charged - consider softening if you meant to inform"). Fast, no clutter.
4. **Next** - edit the text right there and re-check to see the score move. A small note
   reminds them: "This is about how it's worded, not whether it's true."

### 5.4 Parent / EdTech / kids'-content maker - "is this kids' content over-stimulating?"
Default mode: **Single check**, framed as content rating.
1. **Start** - "Rate a piece of children's content." Box for text, or upload a clip.
2. **Check** - one button.
3. **What they get** - a **Content rating card**: Calm / Mixed / Charged, like a label on a
   snack. Plain line: "This clip is built to over-excite" or "This one is calm."
4. **The boundary, said loudly here** - a clear, friendly line at the top of the result:
   **"This rates the video, not your child. It can't and doesn't measure how a child reacts."**
5. **Next** - rate the next clip, or build a calm/charged shortlist.

### 5.5 Safety / fact-check / elder-protection - "flag manipulation at scale"
Default mode: **Bulk check**, sorted by most charged.
1. **Start** - "Scan a pile of messages for emotional manipulation."
2. **Upload** - a batch of suspect messages/articles.
3. **Progress** - resumable live bar (same as researcher).
4. **What they get** - a **Flag report**: the items ranked most-Charged first, so the worst
   offenders are at the top, ready for a human to review. Plain summary ("18 items flagged
   as strongly Charged").
5. **Next** - export the flagged list, or open any item's full card.
   A clear note: "Use this to decide what to review, not as a final verdict."

### 5.6 Student (physics / AI) - "learn how it works"
Default mode: **Single check**, with the deeper panels open.
1. **Start** - "Check any content and see everything." One box.
2. **Check** - one button.
3. **What they get** - the full card with every panel expanded: score, heat view, what drove
   it, and the **Crowd Preview**. A "How this works" link reveals the plain explanation
   (still no heavy jargon - it teaches the ideas, then names the real terms in a footnote).
4. **Next** - tweak the Crowd Preview dials and watch the what-if change.

---

## 6. The Crowd Preview flow (shared, opt-in)

This is the physics/what-if, made plain and clearly imaginary.
1. **Open** - on any result, the user taps **Crowd Preview**.
2. **Pick a crowd** - simple sliders with plain labels, not Greek letters:
   - "How tightly does this crowd copy each other?" (loose ←→ tight)
   - "How easily is this crowd swayed?" (skeptical ←→ easily swayed)
3. **See the what-if** - a simple animation/curve: "If content this charged reached this kind
   of crowd, here's how it could spread." Plus the plain readout: "This crowd could be swayed
   easily / with difficulty."
4. **The label that never leaves** - a banner across the whole panel:
   **"This is a what-if scenario you built. It is NOT a measurement of real people."**
5. **Next** - change the crowd and compare scenarios.

---

## 7. Empty / error / unclear states (always plain, never scary)

| State | What the user sees |
|---|---|
| Content too short | "That's a bit short for a clear reading. Try a longer piece." |
| Unclear reading (brick-1 invalid) | "We couldn't get a clear result. Rather than guess, we're calling it Unclear." |
| Server busy / cold start | "Warming up - first check can take a moment. Hang tight." (with a live spinner, never a frozen screen) |
| Upload too big | "That file's over the limit (1,500 items). Split it and try again." |
| Something failed | "That didn't go through. Nothing was saved. Try again?" - one retry button, no stack traces. |

---

## 8. Microcopy do / don't

| Don't write | Write instead |
|---|---|
| "NAA: 3.71 (HIGH)" | "Charged - built to hit emotions" |
| "Predicted cortical activation map" | "Where this content tends to land" |
| "Landau free-energy susceptibility curve" | "How easily a crowd could be swayed" |
| "Invalid: ROI mean below baseline" | "Unclear reading - we couldn't get a clean result" |
| "This is your brain on outrage" | "This rates the content, not any real person" |
| "Affective-salience dominant" | "This leans emotional" |

---

## 9. The one rule that ties it together
Every screen answers three questions without the user asking: **Where am I? What just
happened? What do I do next?** If a screen can't answer all three in plain words, it isn't done.
