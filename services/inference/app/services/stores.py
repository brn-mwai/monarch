"""Singleton blob store wired from settings.

In-memory by default; Redis when ``MONARCH_REDIS_URL`` is set. Routers
import ``blob_store`` and key entries by namespace (e.g. ``act:<id>``,
``ts:<id>``) so one backing store can hold both kinds.
"""

from ..config import settings
from .blob_store import BlobStore, create_blob_store

blob_store: BlobStore = create_blob_store(
    redis_url=settings.redis_url,
    max_entries=settings.blob_max_entries,
    ttl_seconds=settings.blob_ttl_seconds,
)
