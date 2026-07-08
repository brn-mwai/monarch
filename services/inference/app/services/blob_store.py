"""Externalized blob storage for activation vectors and time series.

Routes depend on the ``BlobStore`` protocol, not a concrete dict, so the
backing store swaps by configuration:

- ``InMemoryBlobStore``: bounded (TTL + LRU) process-local cache. Default
  for single-process dev. Bounded so it cannot leak.
- ``RedisBlobStore``: shared external store for multi-worker / multi-pod
  production. Enabled by setting ``MONARCH_REDIS_URL``.

Both hold numpy arrays; the Redis impl serializes with ``numpy.save`` so
shape and dtype survive the round trip.
"""

import io
import time
from collections import OrderedDict
from typing import Callable, Optional, Protocol

import numpy as np


def serialize_array(array: np.ndarray) -> bytes:
    buffer = io.BytesIO()
    np.save(buffer, np.ascontiguousarray(array), allow_pickle=False)
    return buffer.getvalue()


def deserialize_array(data: bytes) -> np.ndarray:
    return np.load(io.BytesIO(data), allow_pickle=False)


class BlobStore(Protocol):
    def put(self, key: str, array: np.ndarray) -> None: ...
    def get(self, key: str) -> Optional[np.ndarray]: ...


class InMemoryBlobStore:
    """Bounded in-memory store: entries expire after ``ttl_seconds`` and the
    oldest are evicted once ``max_entries`` is exceeded. The clock is
    injectable so TTL behaviour is deterministically testable."""

    def __init__(
        self,
        max_entries: int,
        ttl_seconds: int,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._max_entries = max_entries
        self._ttl_seconds = ttl_seconds
        self._clock = clock
        self._entries: "OrderedDict[str, tuple[float, np.ndarray]]" = OrderedDict()

    def put(self, key: str, array: np.ndarray) -> None:
        now = self._clock()
        self._evict_expired(now)
        self._entries[key] = (now, array)
        self._entries.move_to_end(key)
        while len(self._entries) > self._max_entries:
            self._entries.popitem(last=False)

    def get(self, key: str) -> Optional[np.ndarray]:
        entry = self._entries.get(key)
        if entry is None:
            return None
        stored_at, array = entry
        if self._clock() - stored_at > self._ttl_seconds:
            self._entries.pop(key, None)
            return None
        self._entries.move_to_end(key)
        return array

    def _evict_expired(self, now: float) -> None:
        expired = [
            key
            for key, (stored_at, _) in self._entries.items()
            if now - stored_at > self._ttl_seconds
        ]
        for key in expired:
            self._entries.pop(key, None)


class RedisBlobStore:
    """Shared external store. Requires the ``redis`` package and a reachable
    server; values expire via Redis' own TTL so it cannot leak."""

    def __init__(self, url: str, ttl_seconds: int) -> None:
        import redis  # optional dependency, only imported when configured

        self._client = redis.Redis.from_url(url)
        self._ttl_seconds = ttl_seconds

    def put(self, key: str, array: np.ndarray) -> None:
        self._client.setex(key, self._ttl_seconds, serialize_array(array))

    def get(self, key: str) -> Optional[np.ndarray]:
        data = self._client.get(key)
        return deserialize_array(data) if data is not None else None


def create_blob_store(
    redis_url: str,
    max_entries: int,
    ttl_seconds: int,
) -> BlobStore:
    if redis_url:
        return RedisBlobStore(redis_url, ttl_seconds)
    return InMemoryBlobStore(max_entries=max_entries, ttl_seconds=ttl_seconds)
