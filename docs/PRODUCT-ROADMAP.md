# Product roadmap

What Monarch becomes after submission, in dependency order. Nothing here is thesis work, and
nothing here starts before `corpus_naa.csv` exists.

The governing constraint, stated once: **until held-out vertex `r` is measured (Paper 3), no
surface may claim to report what a brain does.** The defensible claim is a percentile against
a documented corpus, with the validation status printed on the page. A competitor currently
sells the brain claim with validation pending; the difference is the product.

---

## 1. Static results, no GPU

**Blocked by:** the scan.

Today the site reaches for an inference server that is not there and shows SCAN FAILED. The
fix is not to host a GPU, it is to ship the measurements.

| Ships as | Size |
|---|---|
| 400 items: NAA, category, ROI means, classification | ~50 KB JSON |
| Full activation maps for the six example items | ~500 KB |
| Ranked table, per-category violins, free-energy atlas | static images |

The example cards become real measurements rather than the authored constants removed in
`f886a1f`, and the corpus browser becomes objective (vii) delivered on the web. No server, no
running cost, nothing to keep alive during a viva.

**Needs:** `scripts/export_web_results.py`, and a results route in `apps/web`.

## 2. The percentile base

**Blocked by:** the scan.

A scan reporting `naa_signed = −0.039` says nothing. The same scan positioned against 400
balanced, leak-checked items is a product. This is the asset that compounds and the one a
competitor cannot copy.

**Honest limits, to be printed beside any percentile:** English news-style text, four
categories, n = 400. A 99th percentile claim off 400 items rests on four items, and nothing
here transfers to video.

## 3. Multimodal

**Blocked by:** nothing in code.

`app/services/inference.py` already implements `predict_audio`, `predict_video` and
`predict_multimodal`, which returns per-modality vectors plus a combined average for the RGB
brain view. The amendment drops audio and video from the thesis on scope, not capability.

**Costs:** a video item is slower than the 210 s/item measured for text on a P100, and the
percentile base is text-only, so a video cannot be ranked against it until a video corpus
exists.

## 4. Per-second read-out

**Blocked by:** nothing.

`predict_text` already returns `raw_preds` at `(T, 20484)` and `mean_pool` throws the time
axis away. Keeping the series gives the per-second trace that is the whole visual language of
this category of tool.

**Design note worth stealing:** z-score within the item. Each item becomes its own control,
which sidesteps cross-item calibration entirely and stays defined where a ratio does not.

## 5. Explanation, grounded

**Blocked by:** 1 and 2.

`gemma_report.py` and `report_generator.py` already narrate a scan with an LLM and fall back
to a deterministic template. The shape is right: **the model never computes a number, it only
narrates one.**

Grounding is structural, not a prompt:

- **Typed entities:** `Scan`, `Item`, `ROIGroup`, `YeoNetwork`, `Category`, `Threshold`,
  `Limitation`, `Citation`
- **The model sees only** the result object, the corpus percentiles and the limitation list.
  Never free text, never the corpus itself
- **A validator rejects before display:** any mention of the amygdala, any purchase or intent
  claim, "measured" without a ceiling, any value of `α`
- **Refusal is the default** when a question falls outside the object

The failure this prevents is visible in a competitor's published JSON, where the
purchase-intent explanation is the salience gloss recycled: templated prose drifting from the
field it claims to explain. A chat that answers "the data does not support that" is the
differentiator, not a limitation.

## 6. Local model

**Blocked by:** the scan, and ideally Paper 3.

400 `(text -> NAA)` pairs is a distillation set: sentence embeddings plus a regressor,
approximating the cascade in milliseconds on CPU. It is the only route from a 210 s/item
pipeline to an interactive tool.

**Reported honestly it is an approximation of a proxy**, with held-out R² published. If
Paper 3 finds the sign inverted, this step is where that finding lands: distilling an
inverted signal reproduces the inversion faster.

---

## Not on the roadmap

**Per-second "buy intent".** No purchase ground truth exists in this project, and the one
calibration attempt returned an interval straddling zero. It would be an unvalidated label on
an unvalidated proxy.

**"Decode what humans think, then control it".** Unsupportable, and it would forfeit the
credibility the null earns.
