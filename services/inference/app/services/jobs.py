"""In-process store for long-running scan jobs.

A cold text scan runs the whole TRIBE cascade (TTS -> WhisperX -> Llama
embeddings -> model) and takes minutes. Any proxy in front of the API will
cut a synchronous request long before that: a Cloudflare quick tunnel kills
the connection at ~100s (HTTP 524), so the browser never sees the result even
though the GPU finished the work. Jobs decouple the two: the request returns
a job id immediately and the caller polls for the result.

The store is per-process and in-memory, which matches how the service is
deployed today (one uvicorn worker holding one model on one GPU). Multiple
workers would each keep their own jobs, so a shared backend (the Redis blob
store is already wired) is the upgrade path if the service is ever scaled out.
"""

from __future__ import annotations

import threading
import time
import uuid
from enum import Enum
from typing import Any, Optional


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


class Job:
    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        self.status = JobStatus.PENDING
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
        self.created_at = time.time()

    def as_dict(self) -> dict:
        out: dict[str, Any] = {"job_id": self.job_id, "status": self.status.value}
        if self.status is JobStatus.DONE:
            out["result"] = self.result
        if self.status is JobStatus.ERROR:
            out["error"] = self.error
        return out


class JobStore:
    """Thread-safe job map with age-based eviction.

    Scans are written from a threadpool worker and read from the event loop,
    so every mutation takes the lock. Finished jobs are evicted once they age
    past ``ttl_seconds`` to stop a long-running server from growing without
    bound; a client that polls slower than the TTL loses its result and must
    rescan, which is why the TTL is generous relative to a scan.
    """

    def __init__(self, ttl_seconds: int = 3600, max_jobs: int = 512) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._ttl_seconds = ttl_seconds
        self._max_jobs = max_jobs

    def create(self) -> Job:
        job = Job(str(uuid.uuid4()))
        with self._lock:
            self._evict_locked()
            self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def mark_running(self, job_id: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is not None:
                job.status = JobStatus.RUNNING

    def mark_done(self, job_id: str, result: Any) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is not None:
                job.status = JobStatus.DONE
                job.result = result

    def mark_error(self, job_id: str, message: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is not None:
                job.status = JobStatus.ERROR
                job.error = message

    def _evict_locked(self) -> None:
        cutoff = time.time() - self._ttl_seconds
        stale = [jid for jid, job in self._jobs.items() if job.created_at < cutoff]
        for jid in stale:
            del self._jobs[jid]

        overflow = len(self._jobs) - self._max_jobs + 1
        if overflow > 0:
            oldest = sorted(self._jobs.values(), key=lambda j: j.created_at)
            for job in oldest[:overflow]:
                del self._jobs[job.job_id]


job_store = JobStore()
