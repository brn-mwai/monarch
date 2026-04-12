FROM rocm/pytorch:latest

WORKDIR /app

# System deps for WhisperX (invoked via uvx by tribev2)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# uv lets tribev2 spawn WhisperX as a subprocess (uvx whisperx ...)
RUN pip install uv

# Python deps for the FastAPI backend
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --break-system-packages

# Install the forked TRIBE v2 package in editable mode. Mount the fork
# at /tribev2 via volume or copy it in at build time.
COPY tribev2/ /tribev2/
RUN pip install -e /tribev2[plotting] --break-system-packages

# Copy the Monarch backend
COPY . .

# Pre-cache HCP MMP1.0 ROI indices so the API does not need tribev2
# in its hot path. Safe to fail if tribev2 cannot import at build time
# (the API will fall back to a live lookup at first request).
RUN python -c "from app.services.roi import cache_roi_indices, HAS_TRIBEV2; \
    from pathlib import Path; \
    HAS_TRIBEV2 and cache_roi_indices(Path('./data/roi_definitions.json'))" \
    || echo '[Monarch] ROI cache skipped at build time; will resolve at first request.'

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
