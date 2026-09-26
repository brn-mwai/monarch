## Summary
Turned the supervisor-meeting deck into the defence deck for 25 September 2026. Words like "weak",
"high" and "large" are gone from the slides; each claim now carries its number, and every number is
labelled with what it means. A new slide 6 explains the corpus page column by column. Every slide
ends with a gold "Next: ..." line, and every script ends with the sentence that leads into the next
slide. The script is conversational, about 16 minutes in total, and is also written to a printable
text file.

## docs/defence/build_plain_decks.py
Builds the deck twice from one source: `Monarch_Defence_Deck.pptx` (clean) and
`Monarch_Defence_Deck_Script.pptx` (the script in the speaker notes). It now also writes
`Monarch_Defence_Script.txt`.

What changed:
- `SLIDES`: 16 entries of (title, section, minutes, script, numbers, questions). Scripts were
  rewritten short and spoken-style, each ending with the lead into the next slide. "Numbers" now
  lists each on-slide number with its meaning.
- `QUESTIONS`: added the six topics from the supervisor session: eta squared as a dimensionless
  share, why one-way ANOVA, beta J and the sign of `a`, difference vs ratio (69 of 400, not 49),
  writing style vs source, and ethics (no new human data).
- `GROUP_MEANS`: category averages of X, taken from `apps/web/public/data/corpus.json`, so the corpus
  slide matches the live page.
- `next_line(s, text)`: new helper that draws the gold "Next: ... →" line above the footer.
- `stat(...)`: gained `label_size` so longer definitions fit under a number.
- `write_script()`: new; joins `notes_for(i)` for all slides into one text file with total minutes.
- Slide changes: the title now says "Dissertation defence" and is dated 25 Sep. The group names
  match the corpus page (fear-activating, high outrage, reward hook, neutral), and "emotion/reasoning"
  became "emotional/deliberate" to match its columns. "Within 5 words" (false: the spread is 5.2)
  became "162–167". "1 in a billion chance it is luck" (a p-value misreading) became
  "p = 1.0 × 10⁻⁹" with its correct meaning. The Cohen's d scale now shows 0.2/0.5/0.8 instead of
  small/medium/large. The real-brains title "Weakly, yes" became "r = +0.028, p = 0.048". The alpha
  box shows the arithmetic, 0.533 ÷ 0.124 = 4.29. The requests slide was replaced with numbered
  conclusions and "Thank you. Questions welcome."
- Layout fixes after rendering: the clipped "1 = identical" label, a literal "h_c" in a label, and
  a caption that wrapped.

Why this shape: one data list drives both decks and the text file, so the slides, the notes and the
printout cannot disagree.

## Verification
- Built 16 slides, rendered through PowerPoint, and checked every slide visually.
- h_c(2) recomputed as 0.5328, and 0.5328 / 0.1241 = 4.29.
- The group means match `corpus.json` summary.

## Update 2026-09-25: plain-language script
`SLIDES`, `QUESTIONS` and `KEY_POINTS` in `docs/defence/build_plain_decks.py` were rewritten for a
non-specialist audience. Each number is explained in everyday terms: "10.7% of the differences come
from the group", "about once in a billion tries if the groups were the same", "63 out of 100 random
pairs ranked correctly, 50 = coin toss", "a coin balanced on its edge" for the sign flips, and "a room
full of people" for the Ising model. The notes heading is now "WHAT THE NUMBERS MEAN". Slides are
unchanged, and every number is identical to before. The script is about 1,730 words, roughly 12
minutes at 140 words per minute.

## PROJECT.md (2026-09-25)
A new plain-language overview of the dissertation at the repo root. It covers the question, the
Ising idea with a symbol table, the five-step pipeline, the corpus and how to read the corpus page,
the five results with a plain meaning for every number, the α ≥ 4.29 bound, what is supported and
what is not, the amendment, the limits, next steps, ethics, a repo map and references. The numbers
are the same ones used in the defence deck and the thesis. It exists because README.md still
describes the hackathon-era ratio score and a calibrated α, which contradict the dissertation.

## Equation side notes (2026-09-25)
`docs/defence/build_plain_decks.py`: a new `EQUATIONS` dict maps each slide index to (law, how it is
used) pairs. `notes_for` prints them under "EQUATION SIDE NOTE", between the numbers and the
definitions. They cover the Ising energy and the mean-field equation (slide 2), the score (4), power
(5), the spread (6), η² and F (7), Cohen's d (8), ICC and the noise model (9), AUC (10), Pearson r
and the noise ceiling (11), and the Landau free energy, critical-field derivation and bound (12).
h_c(2) = 0.5328 was re-derived, and 0.5328 / 0.1241 = 4.293. `PROJECT.md` gained a matching
"Equations used, and how" table. The slides are unchanged.

## Papers 1-3 made submission-ready (2026-09-26)
- `docs/paper1/paper1.tex`: restructured for a journal, with highlights, declarations and a data statement. The bound now states its assumptions (no background field; the range of X contains 0) and uses |α|. It adds the closed-form spinodal h_c = βJ·m_s − artanh(m_s), fixes a doubled β in the field and χ, and corrects the stated reason for the error in the fitted β. All 11 references were checked. `figures/`, `numbers.tex` and `highlights.txt` were copied in so the folder builds on its own.
- `docs/paper2/paper2.tex`: rewritten, now with 34 references, all checked. It uses one thirds split for the scan-order χ² (2.773, p = 0.837), states that the SemEval label is per publisher, and states that α̂ is proportional to (1 − βJ). It adds a paired bootstrap of Δη² and run B's ΔX (α ≥ 4.530). Dr. Songa is credited for the signed-difference form, and a one-line `\coauthortrue` switch adds her as co-author. The new `verify_numbers.py` re-checks 58 numbers against the data files, with 0 mismatches.
- `docs/paper3/paper3.tex`: retargeted to the Journal of Neuroscience Methods with a structured abstract. It now cites TRIBE v2 (arXiv:2605.04326) and TRIBE v1 correctly. The noise ceiling is worded as a reference level, and withdrawn numbers with no saved output are removed. Limits are added, and 6 verified references are added.
All three are built with `\journal{Preprint}` so they can go to any journal. The per-journal format is pending Brian's choice.
