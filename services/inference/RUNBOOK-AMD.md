# Monarch Layer 1 - AMD GPU Runbook (Phase 2: the smoke-test gate)

Goal: prove the engine produces a real `(T, 20484)` cortical-activation array
on AMD hardware. When `smoke_test.py` passes, **Layer 1 works**.

Run this on an **AMD Developer Cloud MI300X** instance (ROCm). Local CPU only
gets you the app booting (already done); real inference needs the GPU.

## 0. Status before this runbook (already done locally)
- tribev2 fork vendored into `services/inference/tribev2/`.
- API boots on CPU with `MONARCH_SKIP_MODEL_LOAD=1`, `/health` returns 200.

## 1. Provision
- Spin an MI300X box on AMD Developer Cloud (use the $100 ADP credits).
- Confirm ROCm: `rocminfo | head` and `python -c "import torch; print(torch.version.hip)"`.

## 2. Get the code
```bash
git clone <monarch-repo> && cd monarch/services/inference
```

## 3. FIRST, de-risk the one dependency that can block everything
`tribev2` requires `neuralset==0.0.2` and `neuraltrain==0.0.2`. Verify they
install from PyPI BEFORE anything else - if they are Meta-internal, this is the
real blocker, not ROCm:
```bash
pip install neuralset==0.0.2 neuraltrain==0.0.2   # must succeed
```
If this fails, stop and resolve (vendor the wheels / find the source) - the
rest cannot proceed without it.

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
  WhisperX) so nothing downloads at request time.
- Pin WhisperX; verify `uvx whisperx` works inside the container.
- Add an offline TTS fallback (gTTS needs internet).
- Keep the no-fabrication seam: ambiguous/failed cascade -> "couldn't compute",
  never a fake brain-map.

## Known risk ranking (fix in this order)
1. `neuralset` / `neuraltrain` availability (step 3) - hardest blocker.
2. WhisperX subprocess inside container (ffmpeg + model).
3. Request-time model downloads (slow/flaky) -> pre-bake.
4. ROCm/torch op coverage for the model - usually fine on rocm/pytorch base.
