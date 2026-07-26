"""Select the embedding backend at runtime from ``settings.embedding_provider``.
Both provider modules expose the same ``embed_texts`` / ``embed_chunks``
interface, so callers (``build.py``, the retrieval path) import from here and
stay ignorant of which backend produced the vectors. Switch providers by
setting ``embedding_provider`` in config/env — no code change.
"""

from __future__ import annotations

from importlib import import_module
from types import ModuleType

from torch import Value

from .config import settings

_PROVIDERS = {
    "local": "mecha_llm.embeddings_local",
    "azure": "mecha_llm.embeddings",
}


def _backend() -> ModuleType:
    try:
        module_name = _PROVIDERS[settings.embedding_provider]
    except KeyError:
        raise ValueError(
            f"unknown embedding_provider {settings.embedding_provider!r}; "
            f"expected one of {sorted(_PROVIDERS)}"
        ) from None
    return import_module(module_name)


async def embed_texts(texts, **kwargs):
    return await _backend().embed_texts(texts, **kwargs)


async def embed_chunks(chunks, **kwargs):
    return await _backend().embed_chunks(chunks, **kwargs)
