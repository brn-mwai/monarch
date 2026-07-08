"""Unit tests for the externalized blob store (in-memory impl + serde)."""

import numpy as np

from app.services.blob_store import (
    InMemoryBlobStore,
    deserialize_array,
    serialize_array,
)


def test_put_then_get_returns_array():
    store = InMemoryBlobStore(max_entries=4, ttl_seconds=100)
    array = np.arange(10, dtype=np.float32)
    store.put("k", array)
    assert np.array_equal(store.get("k"), array)


def test_get_missing_returns_none():
    store = InMemoryBlobStore(max_entries=4, ttl_seconds=100)
    assert store.get("absent") is None


def test_entry_expires_after_ttl():
    now = {"t": 0.0}
    store = InMemoryBlobStore(max_entries=4, ttl_seconds=10, clock=lambda: now["t"])
    store.put("k", np.zeros(3, dtype=np.float32))
    now["t"] = 5.0
    assert store.get("k") is not None
    now["t"] = 11.0
    assert store.get("k") is None


def test_lru_eviction_beyond_capacity():
    store = InMemoryBlobStore(max_entries=2, ttl_seconds=1000)
    store.put("a", np.zeros(1, dtype=np.float32))
    store.put("b", np.zeros(1, dtype=np.float32))
    store.put("c", np.zeros(1, dtype=np.float32))  # evicts the oldest, "a"
    assert store.get("a") is None
    assert store.get("b") is not None
    assert store.get("c") is not None


def test_serialize_roundtrip_preserves_shape_and_dtype():
    array = np.arange(12, dtype=np.float32).reshape(3, 4)
    recovered = deserialize_array(serialize_array(array))
    assert recovered.dtype == np.float32
    assert recovered.shape == (3, 4)
    assert np.array_equal(recovered, array)
