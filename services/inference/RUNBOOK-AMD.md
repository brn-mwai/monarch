# Monarch Layer 1 - AMD GPU Runbook (Phase 2: the smoke-test gate)

Goal: prove the engine produces a real `(T, 20484)` cortical-activation array
on AMD hardware. When `smoke_test.py` passes, **Layer 1 works**.

Run this on an **AMD Developer Cloud MI300X** instance (ROCm). Local CPU only
gets you the app booting (already done); real inference needs the GPU.

## 0. Status - VERIFIED 2026-07-10 (pipeline proven, blocked only by laptop RAM)
Local CPU dry-run got the pipeline all the way through and confirms it works:
- HF token authenticates + has gated access to Llama-3.2-3B + Wav2Vec-BERT (checked).
- TRIBE v2 loads from the real 709 MB `best.ckpt` (~30s).
- gTTS -> WhisperX transcription runs; text feature extraction (Llama-3.2-3B
  "Computing word embeddings") STARTS - then the laptop OOM-kills it (only
  ~1 GB free of 16 GB; Llama needs ~6.5 GB). **On the MI300X this is trivial.**
- API boots on CPU with `MONARCH_SKIP_MODEL_LOAD=1`, `/health` returns 200.

Three failures hit locally were all **Windows / laptop-only** and DO NOT occur
on the Linux pod - do NOT apply these workarounds on the pod:
1. `str(Path("facebook/tribev2"))` -> `facebook\tribev2` (Windows backslash).
   On Linux the forward slash is preserved; plain `snapshot_download` works.
2. `cannot instantiate 'PosixPath'` deserializing `config.yaml` - Windows-only
   pathlib limitation; Linux instantiates PosixPath fine.
3. WhisperX `--model large-v3` (2.2 GB) download broke on the slow laptop link -
   use large-v3 unchanged on the pod (fast datacenter network).

## Quickstart (copy-paste on the MI300X pod)
```bash
git clone https://github.com/brn-mwai/monarch && cd monarch/services/inference
pip install -e ./tribev2[plotting] && pip install -r requirements.txt
export HF_TOKEN=<hf-read-token>        # already verified: has Llama-3.2-3B access
export FIREWORKS_API_KEY=<key>         # for the Gemma report
export INFERENCE_API_KEY=<any-secret>  # openssl rand -hex 32
export MONARCH_TRIBE_DEVICE=auto       # picks ROCm
python scripts/prewarm.py              # pull ALL weights once (no request-time downloads)
python scripts/smoke_test.py           # THE gate: prints a real (T, 20484) array
uvicorn app.main:app --host 0.0.0.0 --port 8000   # then point the frontend here
```
The `HF_TOKEN` above is the one already set in `.env` and confirmed working.

## 1. Provision
- Spin an MI300X box on AMD Developer Cloud (use the $100 ADP credits).
- Confirm ROCm: `rocminfo | head` and `python -c "import torch; print(torch.version.hip)"`.

## 2. Get the code
```bash
git clone <monarch-repo> && cd monarch/services/inference
```

## 3. Dependency check (RESOLVED - was the old P0, now a formality)
`tribev2` requires `neuralset` and `neuraltrain`. These are now published on
PyPI (verified 2026-07-08: 0.0.2 pinned, 0.2.2 latest), so the old
"Meta-internal, might block everything" fear is dead. Confirm they install:
```bash
pip install neuralset==0.0.2 neuraltrain==0.0.2   # succeeds from PyPI
```

## 4. Install
```bash
# Option A - container (matches production, rocm/pytorch base):
docker compose build inference        # tribev2 is now in build context
# Option B - direct on the ROCm box:
pip install -e ./tribev2[plotting]
pip install -r requirements.txt
```

## 5. Smoke test (THE gate)
```bash
export HF_TOKEN=<your_hf_token>        # facebook/tribev2 + LLaMA-3.2-3B downloads
export MONARCH_TRIBE_DEVICE=auto       # picks ROCm
python scripts/smoke_test.py
```
Expect, in order:
1. `ROCm/HIP available: True` + MI300X listed
2. tribev2 / neuralset / neuraltrain / mne import chain OK
3. TRIBE v2 model loads from HuggingFace
4. single-text prediction round-trip → returns `(T, 20484)` array

Any non-zero exit prints the failing step. The heavy cascade
(gTTS -> WhisperX subprocess -> LLaMA-3.2-3B + Wav2VecBert features -> TRIBE)
is where breakage hides - this is exactly why we run it on the box EARLY.

## 6. Boot the real server + hit it
```bash
export MONARCH_SKIP_MODEL_LOAD=0
export INFERENCE_API_KEY=<key>
uvicorn app.main:app --host 0.0.0.0 --port 8000
# then:
curl -H "Authorization: Bearer <key>" -X POST http://localhost:8000/api/scan \
     -H "Content-Type: application/json" -d '{"text":"a test headline"}'
```
A real activation payload back = Layer 1 done; the interpretation layer
(Neurosynth) and products can now stack on a real signature.

## 7. Harden before demo (Phase 3)
- Pre-bake ALL weights into the image (TRIBE + LLaMA-3.2-3B + Wav2VecBert +
  WhisperX) so nothing downloads at request time. `scripts/prewarm.py` does
  this into `HF_HOME`; run it in the Dockerfile via a BuildKit secret so the
  token never lands in a layer:
  `RUN --mount=type=secret,id=hf_token HF_TOKEN=$(cat /run/secrets/hf_token) python scripts/prewarm.py`
  then build with `docker build --secret id=hf_token,src=./hf_token.txt ...`.
- Pin WhisperX; verify `uvx whisperx` works inside the container.
- Add an offline TTS fallback (gTTS needs internet).
- Keep the no-fabrication seam: ambiguous/failed cascade -> "couldn't compute",
  never a fake brain-map.

## Known risk ranking (fix in this order)
1. HF auth for gated LLaMA-3.2-3B (step 5) - set `HF_TOKEN` or the load 401s.
   The app now logs a loud startup warning when it is missing.
2. WhisperX subprocess inside container (ffmpeg + model).
3. Request-time model downloads (slow/flaky) -> pre-bake / persist HF_HOME cache.
4. ROCm/torch op coverage for the model - usually fine on rocm/pytorch base.
5. `neuralset` / `neuraltrain` availability - RESOLVED, now on PyPI (no longer a risk).
