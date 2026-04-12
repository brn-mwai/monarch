# Monarch Backend

FastAPI backend for the Monarch neural processing scanner. Wraps Meta FAIR's
**TRIBE v2** predictive neural encoding model and adds:

- **NAA** (Neural Arousal Asymmetry) — content-level cortical balance index
- **Landau / Ising** mean-field opinion dynamics layer
- **Per-modality multimodal RGB** activation pipeline (text / audio / video)
- **Checkpoint-resume batch** processing for long-running corpora

The frontend brain renderer (`../monarch`) fetches activation vectors from
`GET /api/scan/{id}/activation` as raw `Float32Array` blobs.

## Status

| Component | Status |
|---|---|
| Pure-numpy services (NAA, Landau, ROI, pooling) | ✓ implemented + unit-tested |
| Pydantic schemas + enums | ✓ |
| FastAPI app + `/health` + `/api/scan` | ✓ |
| Inference singleton (`TribeInferenceService`) | ✓ wired (GPU verified on AMD box, not on Windows dev) |
| Multimodal predictor | ✓ |
| Compare / batch / report routers | stubbed (501) |
| `alpha_hat` calibration script | stubbed (uses fallback 0.5) |
| PDF report generator | stubbed |
| Docker / docker-compose | ✓ (targets `rocm/pytorch:latest`) |

## Local dev (CPU, no GPU)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install the TRIBE v2 fork in editable mode (only needed for live ROI lookup;
#    the on-disk ROI cache makes this optional for the API server)
pip install -e ../tribev2

# 3. (Optional) Pre-cache the HCP MMP1.0 ROI indices
python scripts/cache_roi.py

# 4. Run the test suite (pure-numpy services + FastAPI boot smoke test)
pytest

# 5. Boot the API in skip-model-load mode (no GPU required)
MONARCH_SKIP_MODEL_LOAD=1 uvicorn app.main:app --reload --port 8000

# 6. Hit the health endpoint
curl http://localhost:8000/health
```

In skip-model-load mode the `/api/scan` endpoint returns `503`. Everything
else (`/health`, `/api/compare` stub, `/api/batch` stub, `/api/report` stub,
the OpenAPI docs at `/docs`) works.

### Windows dev-box note

If you `pip install -e ../tribev2` on Windows you may hit:

```
ImportError: DLL load failed while importing onnxruntime_pybind11_state
```

This is the onnxruntime native binary failing to load on Windows. The chain
is `tribev2 → neuraltrain → torchmetrics → onnxruntime`. It does not affect
the unit tests (the ROI cache fallback in `app.services.roi` lets the tests
run without `tribev2`) and it does not happen on the Linux ROCm container
(`.so` instead of `.dll`). If you need the live tribev2 lookup on Windows,
use `pip install --force-reinstall onnxruntime` or skip Windows entirely
and run dev inside WSL2.

## Production deploy (AMD MI300X via ROCm)

1. Build the Docker image: `docker compose build`
2. Set `HF_TOKEN` in the host env (must have accepted the LLaMA 3.2 license)
3. Run the smoke test inside the container: `docker compose run monarch-backend python scripts/smoke_test.py`
4. Bring the stack up: `docker compose up -d`
5. Verify: `curl http://localhost:8000/health` -> `{"status": "ok", "model_loaded": true}`

The first scan request triggers TRIBE v2 inference: text → gTTS → WhisperX
(via `uvx`) → LLaMA 3.2-3B + Wav2Vec-BERT 2.0 + fusion transformer →
`(T, 20484)` per-TR cortical activation → mean-pooled to `(20484,)`.

## Repo layout

```
monarch-backend/
├── app/
│   ├── main.py               FastAPI entry point + lifespan
│   ├── config.py             pydantic-settings env config
│   ├── dependencies.py       require_loaded_model
│   ├── routers/              scan.py, compare.py, batch.py, report.py
│   ├── services/             inference, naa, landau, roi, pooling, ...
│   ├── models/               schemas.py, enums.py
│   └── utils/                checkpoint.py, preprocessing.py, file_handling.py
├── scripts/
│   ├── smoke_test.py         Phase 0 environment + model + inference test
│   ├── cache_roi.py          Pre-compute HCP MMP1.0 ROI indices
│   └── calibrate_alpha.py    OLS fit on NELA-GT-2021 (stub)
├── tests/                    pytest suite (pure-numpy + FastAPI boot)
├── data/                     alpha_hat.json (seed), roi_definitions.json (gen)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── pyproject.toml
```

## Frontend integration contract

```
POST /api/scan
  body: { "text": "...", "modality": "text" }
  returns: ScanResponse {
    scan_id, naa, landau, roi_breakdown, modality, n_trs, activation_url
  }

GET /api/scan/{scan_id}/activation
  returns: 81,936 bytes (20484 * 4) raw Float32 binary
  headers: X-Vertex-Count: 20484, X-Dtype: float32
```

The Next.js frontend fetches the activation as `await response.arrayBuffer()`
and passes `new Float32Array(buffer)` directly to `BrainEngine.setActivation`.

## Licensing notes

TRIBE v2 model weights are CC-BY-NC-4.0 (see `monarch-audit/AUDIT_REPORT.md`).
Commercial use of the predictions is restricted by Meta FAIR's license. The
Monarch product copy must respect this constraint.
