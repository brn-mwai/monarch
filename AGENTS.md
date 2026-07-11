# AGENTS.md - Monarch

Context for AI agents (and humans) working in this repo. Read this first, then
`CODE-GRAPH.md` for the auto-generated structural map of which files cluster
together and what each cluster does.

## What this is

Monarch predicts how strongly a piece of media (text, audio, or video) engages
the brain's emotional circuits versus its reasoning circuits, renders it on a 3D
cortical surface, and explains it in plain language. It wraps Meta's TRIBE v2
brain encoder, derives a single index (NAA = affective vs deliberative
activation), interprets it through a Landau/Ising mean-field layer, and writes a
plain-language audit with an LLM. AMD Developer Hackathon ACT II, Track 3
(Unicorn). B.Sc Physics research project.

## Layout

- `apps/web` - frontend. Next.js 14 (App Router), React 18, TypeScript,
  three.js (BrainViewer), Clerk, Convex (placeholder in dev), Tailwind.
- `services/inference` - backend. FastAPI (Python), TRIBE v2 inference, NAA +
  Landau physics, per-ROI breakdown, PDF + LLM audit report.
- `CODE-GRAPH.md` / `CODE-GRAPH.json` - auto-generated import-cluster map.
- `RUNBOOK-AMD.md` (in `services/inference`) - MI300X / ROCm deployment.

## Build / test / run

Frontend (from `apps/web`):
- Dev: `npm run dev` (port 3001). Synthetic data until `NEXT_PUBLIC_INFERENCE_URL` is set.
- Type gate (run before declaring done): `npx tsc --noEmit`

Backend (from `services/inference`, global Python 3.12):
- Tests: `MONARCH_SKIP_MODEL_LOAD=1 python -m pytest -p no:pytest_ethereum`
  (the `pytest_ethereum` entrypoint is broken; the repo `.venv` is incomplete).
  Route tests send `Authorization: Bearer` when `.env` sets `INFERENCE_API_KEY`.
- Run (dev, no model): `MONARCH_SKIP_MODEL_LOAD=1 uvicorn app.main:app --port 8000`
- Run (pod, real model): set `MONARCH_SKIP_MODEL_LOAD=0` + `HF_TOKEN` + `MONARCH_TRIBE_DEVICE=auto`,
  then `python scripts/prewarm.py && python scripts/smoke_test.py && uvicorn app.main:app --host 0.0.0.0 --port 8000`

## Key configuration (env)

- `NEXT_PUBLIC_INFERENCE_URL` (frontend) - backend URL; unset = synthetic demo.
- `HF_TOKEN` - gated TRIBE + Llama-3.2-3B downloads. Missing = 401 / 503.
- `MONARCH_SKIP_MODEL_LOAD` - `1` boots without weights (`/api/scan` -> 503).
- `MONARCH_TRIBE_DEVICE` - `auto` picks ROCm/CUDA.
- `INFERENCE_API_KEY` - Bearer auth; empty disables auth (dev only).
- `FIREWORKS_API_KEY` / `MONARCH_FIREWORKS_BASE_URL` / `MONARCH_GEMMA_MODEL` -
  the report LLM. The endpoint is OpenAI-compatible, so point it at Fireworks or
  a self-hosted Gemma (vLLM / Ollama) on AMD. Empty key = deterministic template.
- `MONARCH_CORS_ORIGINS` - comma-separated frontend origins.

## Gotchas

- Secrets live in `services/inference/.env` and `apps/web/.env.local` (both
  gitignored). Never commit real keys; `.env.example` is the template.
- On the MI300X pod the image ships ROCm PyTorch - do NOT let `pip install -r
  requirements.txt` downgrade `torch` (the pin is conservative); install deps
  without torch to preserve the ROCm build.
- Data-in endpoints (`/api/report/pdf`, `/api/report/audit`) render from
  client-supplied numbers, so the report and PDF work for any scan without a
  server-side cached activation.
- Multimodal RGB convention (TRIBE paper Fig 7): red=text, green=audio, blue=video.

## Coding standards

Follow the standards in `C:\Users\Windows\Claude_brain\_standards\` (BEST-PRACTICES,
NAMING, NEVER-DO, CODE-STRUCTURE). In short: Phase-0 reason gate before code;
descriptive names, no banned generic names; comments only for non-obvious WHY;
validate external input at boundaries; one job per function; type gate + tests
before declaring done. Commits: Conventional Commits, no "Co-Authored-By",
no em-dashes (use `-`).
