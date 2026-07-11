# Monarch — a neural processing scanner for media

**Monarch predicts whether a piece of media is built to trigger your emotions or your reasoning — and models how that could move a crowd's opinion.**

Give it a headline, a post, or a video. Monarch runs it through an AI model of the human brain (Meta's TRIBE v2) on AMD hardware, shows the predicted activation on a 3D cortical surface, scores it, and writes a plain-language audit with Google's Gemma. Then it goes one step further with physics — a Landau/Ising mean-field model of how that emotional pull could shift collective opinion.

> Built for the **AMD Developer Hackathon: ACT II — Track 3 (Unicorn)**.
> Runs on **AMD Instinct MI300X + ROCm**; language reports via **Gemma on Fireworks AI**.

---

## The problem

Media is increasingly engineered to trigger emotion before reasoning — and there's no objective way to measure it. Two stories can report the same fact: one to inform you, one to enrage you. That difference is invisible to the reader, and it drives polarization, misinformation, and over-stimulation (especially for children). Existing tools measure sentiment or toxicity at the word level. None measure how content engages the *brain* — emotional vs reasoning systems — or connect that to how opinion spreads.

Monarch makes that measurable.

## How it works

1. **Predict brain response** — TRIBE v2 (Meta FAIR), trained on real fMRI, predicts cortical activation from text / audio / video. Runs on the AMD MI300X via ROCm.
2. **NAA index** — the Neural Arousal Asymmetry: the ratio of predicted activation in affective-salience regions to deliberative-control regions. Above 1 = engages emotion over reasoning.
3. **Physics layer** — a Landau/Ising mean-field model maps NAA to a prediction of collective opinion shift (`m = tanh(β_j·m + α̂·NAA)`).
4. **Plain-language audit** — Gemma (via Fireworks AI, AMD-hosted) writes a Summary / Key findings / Caveats report grounded in the numbers.

## Use of AMD platforms

- **AMD Instinct MI300X + ROCm** run TRIBE v2 inference (`services/inference`, `rocm/pytorch` base image).
- **Gemma via Fireworks AI** (AMD-hosted) writes the audit reports (`services/inference/app/services/gemma_report.py`) — also Monarch's "Best AMD-Hosted Gemma Project" entry.

## Honesty (what's validated vs proposed)

Monarch is a **working instrument plus a proposed physics framework**, and it says so:
- The **measurement half** (TRIBE prediction + NAA) is real and built on Meta's validated model.
- NAA is a **proposed** content-level observable, not yet validated against ground truth.
- The **opinion-dynamics layer is a model, not a proven result** — the coupling `α̂` is calibrated by `services/inference/scripts/calibrate_alpha.py` (OLS on a labeled corpus, with a confidence interval); until run on real data it is illustrative.
- Monarch predicts an **average** brain's response to **content** — it never scans a real person.

## Run it

### Frontend (works standalone in synthetic-demo mode)
```bash
cd apps/web
npm install
npm run dev            # http://localhost:3000
```
No keys required — with no inference server configured, the app runs on synthetic data so the full experience (scan → 3D brain → report → export) is always usable.

### Container (linux/amd64 — hackathon gate)
```bash
# Frontend
docker build --platform linux/amd64 -t monarch-web apps/web
docker run -p 3000:3000 monarch-web

# Inference (needs an AMD ROCm GPU)
docker build --platform linux/amd64 -t monarch-inference services/inference
docker run -p 8000:8000 -e HF_TOKEN=<hf-token> -e FIREWORKS_API_KEY=<key> monarch-inference
```

### Live TRIBE + Gemma
Set two env vars and the app switches from synthetic to real with no code change:
- Backend: `HF_TOKEN` (gated LLaMA-3.2-3B), `FIREWORKS_API_KEY` (Gemma reports).
- Frontend: `NEXT_PUBLIC_INFERENCE_URL=http://localhost:8000`.

See `services/inference/RUNBOOK-AMD.md` for the MI300X pod setup and the smoke test.

## Repo structure

```
monarch/
├── apps/web/              Next.js 14 frontend (3D brain viewer, report, scanner)
├── services/inference/    FastAPI TRIBE v2 server (AMD MI300X / ROCm)
│   └── scripts/           smoke_test.py, calibrate_alpha.py
├── docs/investigation/    TRIBE v2 audit (read SYNTHESIS.md first)
├── CITATIONS.md           TRIBE v2, extractors, physics references + licenses
└── docker-compose.yml     Inference + frontend
```

## Stack

Next.js 14 · React 18 · TypeScript · Tailwind · Three.js (custom fsaverage7 cortical renderer) · ECharts · KaTeX · FastAPI · PyTorch/ROCm · TRIBE v2 · Gemma (Fireworks) · numpy (NAA + Landau/Ising).

## Licensing

**Built with Llama.** Monarch uses Meta's Llama 3.2-3B (as a text feature extractor inside TRIBE v2) under the Llama 3.2 Community License. TRIBE v2 weights are CC-BY-NC-4.0 (Meta FAIR) — used for research/non-commercial only. See [CITATIONS.md](CITATIONS.md) for all component licenses and citations. The Monarch wrapper, 3D viewer, and physics layer are the authors' own work.
