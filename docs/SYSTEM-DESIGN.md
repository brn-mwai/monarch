# Monarch - System Design

> Canonical architecture for the Monarch neural processing scanner.
> Built per Claude_brain standards: Phase 0 reasoning gate (Feynman + Musk 5-step),
> system-design-first, explicit trade-offs register + risk register.
> Author: Brian Mwai. Date: 2026-06-11. Status: design-of-record.

---

## 0. One line

**In plain words:** Monarch rates any piece of content - text, audio, or video - for how
strongly it is built to hit your emotions versus make you think, and the physics comes in at the
end to estimate how that emotional pull could spread through a crowd and tip people toward one side.

**Technical:** Monarch feeds a media item (text / audio / video) into Meta FAIR's TRIBE v2
predictive neural encoder, reduces the predicted cortical activation to a single content-level
index (NAA), and interprets that index through a Landau / Ising mean-field model of opinion
dynamics - delivered as an interactive brain-rendering web platform on AMD MI300X.

---

## 0.1 MAIN OUTCOME - rating content across demographics

This is the product's primary purpose. Everything else serves it.

**Monarch rates the content shown to a group, and lets you model what-if crowd scenarios - it
never measures any real person's brain.**

The brain rating is the **same for everyone**: TRIBE was built only from adults, so it cannot
measure how a child, teenager, or older person's brain actually reacts. Demographics therefore
enter in two honest ways, never by measuring real people.

### Way 1 - Rate the content made FOR each group (the core use)
Judge the content aimed at a group, not the group's brains. Like a nutrition label on food made
for different ages.

| Group | What Monarch rates | Who uses it |
|---|---|---|
| **Children** | cartoons, kids' apps, school videos - "calm or built to over-excite?" | parents, teachers, content makers, EdTech |
| **Teenagers** | social-media clips, influencer videos aimed at teens - "how emotionally charged?" | educators, media-literacy programmes, researchers |
| **Elderly** | scam-style messages and forwarded news that target older people - "built to trigger fear?" | safety researchers, family, fact-check groups |
| **A community / language / political audience** | campaign messages pushed at that audience - "leans on outrage?" | journalists, policy researchers, trust & safety |

In every row the rating is a label on the **content**, not on anyone's brain.

### Way 2 - "What-if" crowd scenarios (clearly imagined, not measured)
A separate part of the tool lets the user set dials describing a *type* of crowd - for example a
tightly-knit community that copies each other quickly versus a loose, independent one; or a more
easily-swayed audience versus a skeptical one. You can then ask: "if this emotionally-charged
content reached this kind of crowd, would it likely spread and pull them one way?"

This is the **physics layer** (the opinion-spread model). Its outputs are always labelled
**"imagined scenario you built," not a measurement of real people.** This is the only honest place
where "different groups react differently" lives.

### Way 3 - What Monarch must NOT do
- Never claim to measure any real person's brain.
- Never claim to measure a child's, teen's, or any age group's actual reaction.
- Never use it to test, screen, or profile a real individual - especially a minor.

### Summary table

| Demographic angle | Honest? | What it means |
|---|---|---|
| Rate content aimed at a group | **Yes** | Judging the content, like a food label |
| Imagine how a type of crowd might respond (physics layer) | **Yes, as a what-if** | A scenario the user builds, clearly marked "imagined" |
| Measure a real group's actual brain reaction | **No** | The tool cannot and must not claim this |

So Monarch serves demographics by **rating the content each group is being shown, and modelling
what-if crowd scenarios** - never by measuring real people's brains.

### The value each user gets

The common thread: everyone gets the same gift in a different form - **the invisible made
visible.** "Is this built to provoke me or to inform me?" used to be a feeling. Monarch turns it
into something you can see, measure, compare, and act on.

| User | The value they walk away with |
|---|---|
| **Researchers** | A new measuring stick. They can put a number on "is this built to provoke?" and study it across thousands of items at a scale no human could read by hand - turning a hunch into something testable and publishable. |
| **Teachers / media-literacy** | Proof students can see, not just a lecture. Two versions of the same news, side by side, light up differently on screen. Teaches people to spot manipulation themselves - a skill they keep for life. |
| **Journalists / editors** | A gut-check before publishing. "Are we informing people or fear-baiting them?" answered honestly about their own headline - helping newsrooms stay credible and avoid accidental clickbait. |
| **Parents / EdTech / kids'-content makers** | A sugar-label for children's media. Rate a cartoon or app and see "built to over-excite" before showing it to a child. Checks the content, never the child - like checking a snack's sugar. |
| **Safety researchers / fact-check / elder-protection** | A way to flag manipulation at scale. Scam and outrage-farming content aimed at vulnerable people gets spotted by its emotional fingerprint, fast, across huge volumes. |
| **Students (physics / AI)** | A real, working example that connects brain-AI with the physics of crowds - far more memorable than a textbook. |

### The boundary that protects the value
This value holds **only** because Monarch rates the content, not people. The moment anyone claims
it reads a real person's brain - especially a child's - trust breaks and every benefit above
collapses. Keeping that line clean is what makes the value believable.

### How TRIBE and the physics deliver this (what is being built, and why)

There are two engines under Monarch doing two different jobs.

**Engine 1 - TRIBE: the "what does this content stir up" engine.**
TRIBE is Meta's tool, built by scanning adults' brains while they watched and listened to things,
learning the pattern between content and brain reaction. Its job for us: hand it a piece of content,
it returns a map of which brain areas that content tends to stir. We need it because without it,
"this feels emotionally charged" is just one person's opinion - TRIBE gives a consistent,
content-based read that is the same every time and does not depend on a human's mood. It is the
**eyes** of the tool.

**Engine 2 - the physics: turns that map into something usable.** It does two jobs.

- **Job A - boil the brain map down to one number.** The map has ~20,000 points, too much to act
  on. The physics compares two groups of those points - the emotion / gut-reaction areas versus the
  calm / thinking areas - and produces one simple score. High = built to hit emotions. *Why:* a map
  nobody can read becomes a rating anyone can rank, stack, and compare. (This is the NAA index.)
- **Job B - estimate how that pull could ripple through a crowd.** The same kind of math that
  describes how magnets line up or how a rumour spreads is used to ask: "if content with this much
  emotional pull reached a crowd, could it tip them toward one side?" The user picks the crowd type
  (tight-knit vs loose, easily-swayed vs skeptical) and sees the likely effect. *Why:* one item's
  pull only matters because of what it does to *groups* - the physics is the bridge from "this
  headline is charged" to "here is how it could move a crowd," always marked as a what-if, never a
  measurement. (This is the Landau / Ising layer.)

**The whole chain in one line:**
content → **TRIBE** turns it into a brain-reaction map → **physics** squeezes that into one
emotion-vs-thinking score → **physics** then estimates how that score could ripple through a chosen
crowd. TRIBE gives the raw read; the physics makes it a number you can rate, compare, and reason
about at the level of crowds.

---

## 0.2 The journey every user shares

Whoever the user is, they follow the **same four steps**:

1. **Put content in** - the thing they bring (a headline, a kids' video, a batch of articles).
2. **Get a clear result** - a score, a plain label (LOW / MODERATE / HIGH), and a brain picture.
3. **Compare or rank** - against another version, or across a whole batch.
4. **Act on it** - publish or soften, choose or flag, study or teach.

What changes per person is only the **content they bring** and the **decision they make**. The
boundary never changes: it rates the content, never a real person's brain.

## 0.3 Per-demographic playbook: TRIBE, the physics, and the report each gets

For every user, **TRIBE does the same job** (turn their content into a brain-reaction map) and
**the physics does the same two jobs** (squeeze the map into one score, then model the crowd
what-if). What differs is the content they feed in and the report they walk away with.

| User | What they feed in | What TRIBE does with it | What the physics adds | The report they get |
|---|---|---|---|---|
| **Researchers** | a corpus (hundreds-thousands of items) | reads each item into a brain-reaction map | scores each item; models how each could move a crowd | a **batch audit report**: ranked table + score scatter + summary stats across the whole set, exportable as data + PDF |
| **Teachers / media-literacy** | two versions of one story | reads both into two brain maps | one score per version; shows the gap | a **side-by-side compare report**: two brain pictures + two scores + the difference, for showing on screen |
| **Journalists / editors** | their own draft headline | reads it into a brain map | one score + where it sits on the calm→charged scale | a **single-item check**: score + label + a one-line plain reading ("leans charged - consider softening") |
| **Parents / EdTech / kids'-content** | a children's video, app, or article | reads the content into a brain map | a score + "calm" vs "built to over-excite" | a **content rating card**: score + label + brain picture, framed as a label on the *content* |
| **Safety / fact-check / elder-protection** | a large pile of suspect messages | reads each into a brain map | scores and ranks by emotional fingerprint | a **flagging report**: ranked list of the most charged items, to prioritise human review |
| **Students (physics / AI)** | their own test content | reads it into a brain map | full score + crowd what-if curve | the **full report**: brain map + score + breakdown + crowd model, as a learning artefact |

Read every row the same way: TRIBE is the eyes, the physics is the ruler and the crowd model, and
the report is a **rating of the content** - never an assessment of any person.

## 0.4 The outcome - what the "report" actually is

The outcome of a scan is a **content audit report**. It comes in two forms:

- **On-screen result (instant):** the score, the plain label, the brain picture, and the area
  breakdown - shown live as soon as the scan finishes.
- **Downloadable report (PDF / data):** the same result captured as a document you can save, share,
  cite, or attach to a study.

**What a single-item report contains:**
1. What was scanned (the content, the type, the date).
2. The score and its plain label (LOW / MODERATE / HIGH emotional pull).
3. The brain picture - which areas the content tends to stir (a general prediction, labelled).
4. The breakdown - which areas drove the score, so the "why" is visible, not just the number.
5. The crowd what-if - how this much pull could ripple through a chosen type of crowd.
6. The plain-language reading - one or two sentences anyone can understand.
7. The honesty notes - "predicted, content-level, not a real person's brain."

**What a batch report adds:** a ranked table of every item, a scatter showing the spread of scores,
and summary statistics across the whole set.

**The nature of the report:** it is reproducible (same content gives the same result), timestamped,
and exportable. It is a **label on content**, like a lab report on a food sample - not a profile of
any reader, viewer, or child.

## 0.5 How all of this contributes to a research paper

Monarch is itself a B.Sc. Physics research deliverable, and every part above maps cleanly onto the
sections of a scientific paper:

| Paper section | What Monarch provides |
|---|---|
| **Method** | The pipeline itself: TRIBE turns content into a brain-reaction map; the physics defines the score (the emotion-vs-thinking ratio) and the crowd model (the opinion-spread math). This is a described, reproducible method others can follow. |
| **Data** | The content corpora scanned (news, propaganda, children's media, etc.) and the score each item received - a dataset that did not exist before. |
| **Results** | The headline result is the **validation number**: when you score a labelled set (e.g. propaganda-flagged articles), does the score separate them from neutral ones better than chance? Reported as standard accuracy figures. The per-demographic content audits become case-study results. |
| **Discussion** | What the scores reveal (e.g. "outrage-style content clusters at the high end"), and the crowd model's predictions about when a population is most easily tipped. |
| **Limitations** | The honest boundaries, stated plainly: the brain tool was trained on adults watching movies, so headlines and children's content are outside its original training; it predicts a population pattern, not any individual; the crowd model is a theory layer, not measured opinion change. |

**The single most important contribution** is the validation result. Everything else - the brain
pictures, the crowd model, the demographic audits - is supporting material around one testable
claim: *does this content score actually track an independent, human-labelled signal of charged
content?* A paper that answers that honestly, with the limits stated, is a defensible contribution
whether the answer is strongly yes or only partly.

---

## 1. Phase 0 - Reasoning gate (run before any design)

### 1.1 Feynman - what is this, really?
Strip the physics vocabulary. Monarch is: **a regression model that maps text/audio/video to a
20,484-number vector, from which we take a ratio of two hand-picked subsets of numbers, then
plot that ratio on a tanh curve.** Everything else - "neural," "affective-salience," "Landau
free energy" - is interpretation layered on that core. The interpretation is only as honest as
(a) whether the regression generalises to our inputs and (b) whether the two number-subsets
mean what we say they mean.

### 1.2 Musk 5-step

| Step | Applied to Monarch |
|---|---|
| **Question every requirement** | Do we need subcortical ROIs? (We claim NAcc / striatum - TRIBE can't produce them. Cut from the spec.) Do we need audio+video? (No - text-only is the minimum publishable core. Cut to stretch.) Do we need the Ising layer to ship? (No - it's interpretation, not measurement. It can be a clearly-labelled theory panel.) |
| **Delete** | Subcortical ROIs, the 8,802-voxel claim, the "8-head / 384-dim" architecture claim (all wrong vs the real checkpoint). Multimodal "decomposition" claim (the model can't decompose). |
| **Simplify** | One model, one worker, one forward pass per scan. Static mean-pooled snapshot, not live animation, for MVP. Pure-numpy physics, no extra services. |
| **Accelerate** | Only AFTER the validation experiment passes. Do not optimise a pipeline whose central claim is untested. |
| **Automate** | Batch corpus runner (memmap + resume journal) - but last, once single-scan is proven. |

### 1.3 The gate verdict
The reasoning gate says: **build the smallest honest version first** - text-only, cortical-only,
NAA as a relative index, Landau as a labelled interpretation - and gate everything downstream on
one validation number. Do not build the full 7-visualisation platform before that number exists.

---

## 2. What TRIBE v2 can and cannot do (capability + boundary map)

This is the load-bearing section. Everything in the design follows from it. Grounded in the
TRIBE v2 source audit (`monarch-audit/AUDIT_REPORT.md`) and the 9 investigation docs
(`docs/investigation/`).

### 2.1 CAN do

| Capability | Detail | Source |
|---|---|---|
| Predict cortical fMRI from media | `(T, 20484)` BOLD on fsaverage5, 1 TR = 1 s, T ≈ duration in seconds | `03_inference_pipeline §3` |
| Accept 3 input modalities | text(.txt) / audio(.wav,.mp3,.flac,.ogg) / video(.mp4,.avi,.mkv,.mov,.webm); exactly one per call | `synthesis Q1` |
| Tri-modal fusion | LLaMA-3.2-3B (text) + w2v-BERT-2.0 (audio) + V-JEPA2-giant (video) → 8-layer transformer | `audit §2f` |
| Zero-shot across **subjects** | trained on 25 subjects, validated zero-shot on 695. This is its real, peer-reviewed strength. | paper Table 1 |
| Population-average prediction | `average_subjects=True` collapses the subject dim → one population-typical map | `03 §1.4` |
| Tolerate missing modalities | zero-fills absent channels; text-only / audio-only calls still return `(T, 20484)` | `synthesis Q4` |
| Deterministic inference | `model.eval()` disables modality dropout; reproducible modulo CUDA kernels | `audit §2g` |
| Run on AMD ROCm | nothing CUDA-specific except the availability check; MI300X works | `audit §2i` |

### 2.2 CANNOT do (the boundaries that shape the whole design)

| Limit | Consequence for Monarch | Severity |
|---|---|---|
| **Trained on movie-watching fMRI, not news/headlines** | Our core input (short news headlines) is **out of distribution**. Zero-shot across *subjects* ≠ generalising across *stimulus type*. This is the single biggest scientific risk. | **Critical** |
| **Cortical surface only - no subcortical checkpoint published** | The affective-salience thesis wants insula-deep, nucleus accumbens, ventral striatum, amygdala - these are **subcortical and absent**. NAA can only use cortical proxies (OFC, ACC, temporal pole, AAIC). | **Critical** |
| **Text always routed through synthetic speech** | `text → gTTS robot voice → WhisperX → LLaMA`. You encode "a robot reading the headline aloud," not silent reading. A confound baked into every text scan. | High |
| **No clean modality decomposition** | Zero-filling a channel ≠ "brain response to the other modalities alone." The 8 transformer layers mix non-linearly. The "RGB multimodal" view is illustrative, not a decomposition. | Medium |
| **Output is a *prediction*, not a measurement** | Not an individual brain, not even an averaged real brain - a model's guess at population-typical BOLD. All copy must say "predicted." | High (framing) |
| **License CC-BY-NC-4.0** | No commercial product on these weights or their derived predictions. Research / hackathon / open-source only. | High (legal) |
| **Output units are arbitrary** | raw MSE-trained BOLD-scale floats, not z-scored. Fine for NAA (ratio cancels units) but cross-stimulus comparison needs shared normalisation or calibrated α̂. | Medium |

### 2.3 The honest reframing that *does* work
TRIBE cannot tell you "this headline lights up the amygdala." It **can** give a predicted
cortical activation pattern, from which NAA reads a **relative asymmetry between two cortical
networks**, validated convergently against an independent label. That claim is defensible as
exploratory science. The design below builds exactly that, and draws a hard line at the OOD /
subcortical boundary.

---

## 3. Viability verdict (by definition of "work")

| "Work" means... | Verdict | Why |
|---|---|---|
| Produce NAA numbers + brain renders live | **Yes** | Pipeline runs end-to-end; verified on the AMD box per backend README. |
| A scientifically defensible *relative* cortical-bias index, validated vs propaganda labels | **Yes, if** the validation experiment passes | Convergent-validity design is sound; the number does not yet exist. |
| Measure "the affective-salience brain response to news" | **No** | The construct is largely subcortical (absent) and the input is OOD. Must reframe as cortical-proxy + predicted. |
| A commercial product | **No** | CC-BY-NC license. |

**Bottom line: TRIBE can make the honest version of Monarch work. It cannot make the
oversold version work.** The design's job is to build the honest version and make the boundary
impossible to miss.

---

## 4. Requirements

### 4.1 Functional
- F1. Single scan: accept text/audio/video, return NAA + classification + cortical activation vector.
- F2. A/B compare: two items, shared normalisation, per-item NAA, optional diff map.
- F3. Report: NAA gauge, Landau free-energy curve, susceptibility curve, ROI breakdown, PDF export.
- F4. Batch: CSV of up to 1,500 items → ranked table + scatter, resumable.
- F5. Brain render: interactive fsaverage5 cortical surface, hot colormap, hemisphere/inflate toggles.
- F6. Auth: Clerk-gated scan/report/batch; public landing demo strip.
- F7. **Validation harness**: run NAA over a labelled corpus, report AUC/F1 vs SemEval-2020 propaganda.

### 4.2 Non-functional
- N1. Single-scan latency: cold first request 60-90 s (extractor load); warm ~10 s on MI300X.
- N2. One model instance, one worker - never multi-worker (LLaMA alone ~6 GB VRAM).
- N3. Reproducible inference (deterministic eval mode).
- N4. Offline-capable frontend (mesh + colormap baked at build time; no runtime Python).
- N5. Honest framing enforced in UI copy (see §11).

### 4.3 Hard constraints
- C1. CC-BY-NC-4.0 - non-commercial only.
- C2. Cortical only - no subcortical ROIs in NAA.
- C3. Gated LLaMA-3.2-3B - service account with accepted license in the container.
- C4. `neuralset==0.0.2` + `neuraltrain==0.0.2` must be installable (paper confirms OK on py3.12).
- C5. WhisperX via `uvx` - `uv` on PATH, model cache baked into the image.

---

## 5. Architecture (target state)

Three layers, one direction of data flow. No layer reaches back up.

```
┌──────────────────────────────────────────────────────────────────────────┐
│  PRESENTATION  (apps/web — Next.js 14, Vercel)                            │
│  Landing · Scanner · Report · Batch · sign-in                            │
│  BrainViewer (Three.js, baked fsaverage5 mesh + fire LUT)                 │
│  7 ECharts · Clerk auth gate · inference-client (live | synthetic fallback)│
└───────────────┬──────────────────────────────────────────────────────────┘
                │ HTTPS  POST /api/scan {text|file, modality}
                │        GET  /api/scan/{id}/activation  (Float32 binary)
                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  PHYSICS + API  (services/inference — FastAPI, MI300X Docker)            │
│  routers: scan · compare · batch · report                                │
│  services: naa · landau · susceptibility · roi · pooling · alpha_calib   │
│  pure-numpy, zero TRIBE dependency — unit-tested, deterministic          │
└───────────────┬──────────────────────────────────────────────────────────┘
                │ in-process call (same container, singleton)
                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  INFERENCE  (TribeInferenceService singleton)                            │
│  TribeModel.from_pretrained("facebook/tribev2") loaded once at startup   │
│  text → gTTS → WhisperX(uvx) → LLaMA-3.2-3B + w2v-BERT + V-JEPA2          │
│  → 8-layer fusion transformer → (T, 20484) → mean-pool → (20484,)        │
└──────────────────────────────────────────────────────────────────────────┘

   SIDE STORE (Convex):  scans, users, batch jobs, activation blobs
   CALIBRATION (offline): scripts/calibrate_alpha.py → data/alpha_hat.json
```

### 5.1 Why this shape (and what was rejected)
- **Physics layer holds zero TRIBE dependency.** Deliberate: it boots, tests, and runs on a CPU
  dev box without the GPU stack. The TRIBE import lives only inside `inference.py:load_model`.
- **One container, in-process call** (not a separate inference microservice). Rejected the
  microservice split because the physics layer is cheap and the model is the only heavy thing -
  a network hop buys nothing and adds a failure mode. Revisit only if batch throughput needs a
  separate GPU pool.
- **Convex as side store, not on the hot path.** The activation binary (81,936 bytes) is served
  straight from the inference service as a Float32 blob; Convex stores metadata + results for
  history and reactivity, not the inference itself.

---

## 6. Component specs

### 6.1 Inference service (`services/inference/app/services/inference.py`)
- Singleton `TribeInferenceService`; `load_model()` in FastAPI lifespan at startup.
- **Pre-warm**: run one dummy text scan at startup so the first real request doesn't eat the
  60-90 s extractor cold start (LLaMA + V-JEPA2 + w2v-BERT lazy-load on first `.prepare`).
- Per-modality methods return `{raw_preds (T,20484), item_vector (20484,), n_trs, modality}`.
- Multimodal = three separate passes, simple mean. **Labelled "illustrative," not decomposition.**

### 6.2 NAA (`services/.../naa.py`) - DONE, audit-corrected
- `NAA = mean(A_aff) / (mean(A_del) + δ)`, δ=1e-3.
- Affective-salience ROIs (cortical proxies): `OFC, pOFC, p24, a24, TGd, TE1a, TE1p, IFSa, IFSp, AAIC`.
- Deliberative-control ROIs: `46, 9-46v, 11l, 13l, d32, p32, 10p, 10pp`.
- Subcortical (NAcc, ventral striatum) **intentionally omitted** - not in the cortical checkpoint.
- Classification: LOW <1.0, MOD 1.0-2.0, HIGH >2.0 (heuristic thresholds, flagged as such).

### 6.3 Landau / Ising (`services/.../landau.py`) - DONE
- `m = tanh(βJ·m + β·α̂·NAA)`; `F(m) = (1-βJ)m² + (βJ)³/3·m⁴ - h·m`; χ from implicit diff.
- βJ = 0.7 default. **Labelled as theoretical interpretation, not evidence of real opinion shift.**

### 6.4 α̂ calibration (`services/.../alpha_calibration.py` + `scripts/calibrate_alpha.py`)
- **Currently fallback 0.5 - NOT calibrated.** Must run OLS on NELA-GT-2021 source-credibility
  (sign-reversed, source-aggregated to avoid pseudo-replication, B=1000 bootstrap CI).
- Until calibrated, every Landau number is placeholder. Calibrate before any report ships.

### 6.5 Brain renderer (`apps/web/src/components/BrainViewer/`)
- fsaverage5 mesh baked to JSON/binary at build time (already in `public/mesh/`).
- Port `robust_normalize(p99)` + fire LUT + alpha ramp + sulcal blend to a single shader.
- A/B compare: normalise over the **concatenation** of both vectors so brightness is comparable.

### 6.6 Validation harness (NEW - the make-or-break, F7)
- Run NAA over SemEval-2020 Task 11 propaganda corpus (independent of NELA, which calibrates α̂).
- Report AUC, precision, recall, F1 at Youden-optimal threshold.
- This is convergent validity: does NAA track an independent human-annotated signal related to
  reactive processing? One number decides whether Monarch is an instrument or a visualisation.

---

## 7. End-to-end data flow (single text scan)

```
"FED DESTROYS AMERICA…"
  → POST /api/scan {text, modality:"text"}
  → input validation (length, sanitise)
  → TribeInferenceService.predict_text
      → tmp .txt → get_events_dataframe
          → gTTS synth audio → WhisperX word timings → events DF
      → model.predict → (T≈30, 20484) per-TR cortical BOLD
      → mean_pool → (20484,) item vector
  → naa.compute_naa(vector, aff_idx, del_idx) → {naa, a_aff, a_del, class}
  → landau.compute_landau_analysis(naa, α̂) → {F(m), m*, χ, h}
  → store scan + vector blob (Convex); return ScanResponse + activation_url
  → frontend GET activation_url → Float32Array → BrainEngine.setActivation
  → render brain + NAA gauge + Landau curve + ROI bars
```

---

## 8. Trade-offs register

| Decision | Chosen | Alternative | Why chosen | Revisit when |
|---|---|---|---|---|
| Inference placement | in-process singleton | separate gRPC inference svc | physics is cheap; one failure domain | batch needs its own GPU pool |
| MVP render | static mean-pooled snapshot | live (T,20484) animation | T=1Hz is slow; snapshot proves the claim | after validation passes |
| Modality scope (MVP) | text-only | tri-modal from day 1 | text is the minimum publishable core; audio/video are stretch | text validation passes |
| Subcortical ROIs | omit | train subcortical head | no published checkpoint; retrain infeasible | Meta releases subcortical weights |
| α̂ | OLS on NELA, bootstrap CI | learned per-item function | keep it an order-of-magnitude constant, honest | a real opinion-shift dataset exists |
| Workers | single | multi-worker FastAPI | model is 6 GB+; duplicate loads OOM | queue-based scaling needed |
| Frontend fallback | synthetic when no server | hard-fail | demo always usable | production (must disable synthetic) |
| Text input path | accept gTTS confound | OCR/silent-reading encoder | TRIBE has no text-only-silent path | a reading-fMRI encoder ships |

---

## 9. Risk register

### P0 - blocks a credible result
- **R1 OOD generalisation.** TRIBE trained on movies, scored on headlines. *Mitigation:* scope all
  claims to "predicted, relative, cortical"; report validation AUC honestly; never claim
  individual or subcortical response.
- **R2 Validation unrun.** The AUC/F1 vs SemEval does not exist. *Mitigation:* run F7 before
  building more platform. If near chance → reframe as exploratory visualisation tool.
- **R3 α̂ uncalibrated** (fallback 0.5). *Mitigation:* run `calibrate_alpha.py` before any report ships.
- **R4 neuralset/neuraltrain availability.** *Status:* paper confirms installed on py3.12 - verify in the prod container.
- **R5 Gated LLaMA-3.2-3B.** *Mitigation:* service account + accepted license baked into image.

### P1 - blocks MVP polish
- R6 WhisperX `uvx` cold download - bake cache into Docker image.
- R7 First-scan cold start 60-90 s - pre-warm dummy scan at startup.
- R8 Compare / batch / report routers stubbed (501) - implement.
- R9 PDF generator stubbed.
- R10 Inflated mesh exported with `inflate=True` not `"half"` - lerp 50/50 at load or re-export.

### P2 - operational
- R11 Cache volume growth (batch can reach tens of GB) - mount >100 GB persistent volume.
- R12 `torch.load(mmap=True)` ROCm edge cases - sanity-check on MI300X.
- R13 No integration test asserting `(T, 20484)` shape + range - add one.
- R14 Frontend synthetic fallback can silently mask a dead inference server in prod - add a banner.

---

## 10. The validation experiment (do this first)

Everything downstream is theory on an untested foundation until this runs.

1. Calibrate α̂: `scripts/calibrate_alpha.py` on NELA-GT-2021 (source-aggregated, bootstrap CI).
2. Run NAA (live TRIBE, text-only) over SemEval-2020 Task 11 propaganda corpus.
3. Report AUC / precision / recall / F1 at Youden-optimal threshold.
4. **Decision gate:**
   - AUC comfortably > 0.5 with sane CI → NAA carries signal; continue building the platform.
   - AUC ≈ 0.5 → NAA does not track the construct; reframe Monarch as an exploratory
     visualisation of TRIBE predictions, drop the "instrument" claim, keep the physics as a demo.

This is also the B.Sc. defensible core: one measurement + one validation, with Landau as
clearly-labelled illustrative theory.

---

## 11. Scientific-honesty rules (enforced in UI + paper)

1. Always "**predicted**" cortical activation - never "measured" / "your brain."
2. NAA is **population-level** and **content-level** - not any individual's response.
3. NAA uses **cortical proxies**; the affective-salience construct is largely subcortical and
   **not observed** - say so.
4. Text scans encode **synthesised speech**, not silent reading.
5. The multimodal RGB view is **illustrative**, not a decomposition.
6. Landau / Ising is a **theoretical interpretation**, not evidence of real-world opinion shift.
7. Demo NAA values are **illustrative** unless produced by live TRIBE inference.

---

## 12. Build order (gated)

```
Phase 0  Unblock      verify neuralset/neuraltrain install + gated LLaMA in prod container
Phase 1  Validate     calibrate α̂ → run SemEval validation → DECISION GATE  ← do not skip
Phase 2  Harden core  pre-warm, integration test (T,20484), disable synthetic in prod
Phase 3  Finish API   implement compare / batch / report routers, PDF export
Phase 4  Frontend     A/B shared-normalisation, fix inflated mesh, honesty banners
Phase 5  Batch        memmap + resume journal corpus runner
Phase 6  Polish       landing, docs, deploy hardening
```

The ordering is non-negotiable on one point: **Phase 1 precedes Phase 3+.** Do not finish the
platform before knowing whether the central number means anything.

---

## 13. Who can use it, and for what

The unit Monarch produces is a **property of the content**, not a measurement of any viewer.
Read every persona below through that lens.

### 13.1 The outcome - one sentence (memorise this)
**Monarch outputs a predicted, population-level, relative index (NAA) of how strongly a piece of
content engages affective-salience vs deliberative-control cortical networks - plus a sociophysics
model of how a chosen population cohort would polarise under that content. It is a property of the
content, not a measurement of any individual's brain, and not a truth, accuracy, or sentiment score.**

### 13.2 Personas

| User | What they do with Monarch | Defensible today? |
|---|---|---|
| **Researchers** (media studies, comms, computational social science, sociophysics) | Audit corpora; test whether NAA tracks independent labels; study framing vs predicted neural asymmetry; explore the Ising/Landau population layer | **Yes** - this is the primary, defensible audience. The whole platform is a research instrument. |
| **Educators / media-literacy teachers** | Show students the same event written two ways and watch the predicted brain map + NAA diverge - "same story, different brain." A teaching demonstrator. | **Yes** - as illustration. Strongest, lowest-risk use. |
| **Content curators / parents / EdTech** screening **children's content** | Rank children's media by **predicted (adult) affective load** as a curation/screening signal - "this clip scores HIGH affective asymmetry" | **Partly** - see §15. It scores the *content*, not the child. |
| **Journalists / editors / fact-check orgs** | Pre-publication check: does our headline lean affective vs deliberative? Audit a feed for outrage-skew. | **Yes, with the OOD caveat** - headlines are out-of-distribution for TRIBE; treat as relative signal. |
| **Trust & safety / policy / platform research** | Corpus-scale auditing of misinformation feeds for affective-salience skew | **Research-grade** - useful as a relative lens, not an enforcement oracle. |
| **Students** (physics / neuro-AI) | Learn sociophysics + predictive neural encoding hands-on | **Yes** - it is itself a B.Sc. physics deliverable. |

### 13.3 What Monarch is NOT for (say this plainly)
- Not a lie detector, fact-checker, or accuracy/credibility score.
- Not a sentiment/tone classifier (it predicts processing *pathway*, not valence).
- Not a measurement of what any specific person's brain did or will do.
- Not a clinical, diagnostic, or individual-screening tool.
- Not an enforcement or moderation oracle - a research/relative signal only.

## 14. The outcome, made concrete

What a user actually walks away with, per mode:

| Mode | Input | Output the user receives | How to read it |
|---|---|---|---|
| Single scan | one item | NAA value + LOW/MOD/HIGH + predicted cortical brain map + ROI breakdown + Landau position | "This content is predicted to engage affective-salience networks N× more than deliberative-control, at the population level." |
| Compare | two items | two NAAs + two brain maps + optional diff map | "Same event, these two framings differ by ΔNAA; here is where the predicted activation differs." |
| Report | one scan | gauge + Landau free-energy curve + susceptibility curve + PDF | "Where this item sits on the opinion-dynamics phase diagram for a chosen population." |
| Batch | corpus (≤1500) | ranked table + NAA scatter by category | "Across this feed, these items carry the highest predicted affective skew." |

The outcome is always **relative and predicted**. A single NAA in isolation means little; NAA
*between two framings*, or *across a corpus*, or *vs a validated threshold*, is the product.

## 15. Age groups and children - the honest boundary

This is the part that must not be oversold. TRIBE v2 was trained on **adult** fMRI subjects. It has
**no developmental data**. Therefore:

### 15.1 What Monarch CANNOT do
- It **cannot** predict a child's (or any specific age cohort's) actual brain response. Feeding it
  a children's cartoon does not yield "how a 7-year-old's brain responds" - it yields the
  adult-population prediction for that stimulus. Children's brains differ structurally and
  functionally; this is a second out-of-distribution axis stacked on the stimulus-type one.
- It **cannot** be a screening or assessment tool applied *to* children. No individual, no minor.
- Per-age neural differentiation in the output is **not supported by the model.** Do not ship a
  UI that implies it.

### 15.2 Where "different groups / age cohorts" CAN legitimately live
The honest place to model *different audiences* is **not** the neural layer (fixed, adult,
content-level) but the **social layer** - the Landau / Ising population model, whose parameters
are explicitly modelling assumptions, not measurements:

- **βJ (social coupling / conformity pressure)** and **social temperature T** describe how a
  *population* polarises. A tightly-coupled community polarises more readily than a loosely-coupled
  one. These are tunable **per cohort** as a clearly-labelled scenario, not a measurement.
- **α̂ (field susceptibility)** scales how strongly the population responds to the content's NAA field.
- So "how might a more impressionable / more tightly-networked group respond to this content?" is
  answerable **as a sociophysics scenario** - sliders on the population model - with every output
  labelled *modelled, not measured*.

This gives educators and researchers a real, defensible knob ("model a more susceptible cohort")
without ever claiming TRIBE measured a child's brain.

### 15.3 The genuinely useful children's-content use case
**Audit children's content for predicted (adult-population) affective load as a curation signal.**
An educator or parent ranks clips/articles aimed at kids and sees which ones score HIGH affective
asymmetry. That is useful and honest: it scores the **content** (is this designed to spike
affective-salience processing?), not the child. Frame it as content curation, never as
child-response measurement.

### 15.4 If real developmental work is the goal (future, out of scope)
Predicting children's actual responses would require pediatric fMRI training data (TRIBE has none),
a developmental encoder, and serious ethics approval - child neuroimaging is a heavily regulated
domain. This is a multi-year research programme, not a Monarch feature. Flag it as future direction
and do not imply the current platform approaches it.

### 15.5 UI / copy rules for age (enforce)
1. Never label any output as a child's, teen's, or specific age group's brain response.
2. If audience cohorts are offered, they live on the **social model** and are labelled
   "modelled population scenario," with parameter values visible.
3. Children's-content features are framed as **content auditing / curation**, not response measurement.
4. No use of the platform to assess, screen, or profile any minor.

## Appendix - primary sources
- `monarch-audit/AUDIT_REPORT.md` - TRIBE v2 source audit (read-only).
- `docs/investigation/SYNTHESIS.md` - the nine wiring questions.
- `docs/investigation/03_inference_pipeline.md` - line-by-line forward pass.
- `Monarch_Paper.pdf` - product paper (NAA + Landau definitions, caveats).
```
