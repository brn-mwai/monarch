# Monarch

Neural processing scanner for media. Predicts cortical processing balance using TRIBE v2 and maps the result through a Landau / Ising mean-field opinion dynamics layer.

## Monorepo structure

```
monarch/
├── apps/web/              Next.js 14 frontend (Vercel)
├── services/inference/    FastAPI TRIBE v2 server (AMD MI300X Docker)
├── docs/investigation/    9 research documents from the TRIBE v2 audit
├── packages/shared/       Shared types (TODO)
└── docker-compose.yml     Inference server deployment
```

## Quick start (frontend)

```bash
cd apps/web
npm install
# Set up .env.local (copy from .env.example, fill in keys)
npx convex dev   # Deploys schema + generates types
npm run dev      # Next.js dev server
```

## Stack

- **Frontend:** Next.js 14, React 18, TypeScript, Tailwind, Three.js, ECharts, KaTeX
- **Auth:** Clerk
- **Database:** Convex (scans, users, batch jobs, activation file storage)
- **Inference:** FastAPI + TRIBE v2 on AMD Instinct MI300X via ROCm
- **Physics:** NAA index + Landau / Ising mean-field theory (pure numpy)

## Architecture

```
User -> Clerk auth -> Next.js -> Convex mutation (createScan)
                                       |
                               Convex action (triggerInference)
                                       |
                               FastAPI on AMD MI300X
                               (TRIBE v2 inference)
                                       |
                               Returns NAA + Landau + activation binary
                                       |
                               Convex stores results + binary blob
                                       |
                               Frontend reactively updates:
                               - Brain renderer (Float32Array)
                               - NAA gauge, Landau curve, ROI breakdown
                               - Susceptibility chart
```

## Licensing

TRIBE v2 model weights are CC-BY-NC-4.0 (Meta FAIR). The Monarch wrapper,
charts, and physics layer are open source.
