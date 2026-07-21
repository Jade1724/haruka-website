"""Local sentence-transformers embeddings (bge-small-en-v1.5, 384 dims).

Drop-in replacement for the Azure ``embeddings`` module: same
``embed_texts`` / ``embed_chunks`` interface, so the build orchestrator does
not care which provider produced the vectors. Runs on CPU. Vectors are
L2-normalized, so pgvector's cosine distance (``<=>``) ranks identically to
inner product — see ``sql/001_chunks.sql`` (``vector_cosine_ops``).

bge models expect a retrieval instruction prefixed to *queries* only, never to
the stored passages; ``embed_texts(..., is_query=True)`` applies it.
"""

from __future__ import annotations

import asyncio
from dataclasses import replace
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from .config import settings
from .documents import Chunk

EMBED_BATCH_SIZE = 64

@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    """Load the model once and reuse it"""
    return SentenceTransformer(settings.local_embedding_model)


def _encode(texts: list[str], *, batch_size: int) -> list[list[float]]:
    vectors = _model().encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return vectors.tolist()


async def embed_texts(
    texts: list[str],
    *,
    batch_size: int = EMBED_BATCH_SIZE,
    is_query: bool = False,
) -> list[list[float]]:
    """Embed ``texts``; return on 384-dim vector per input, in order.

    Pass ``is_query=True`` for a search query so the bge instruction prefix is applied. 
    Leave it False (the default) for stored passages.
    """
    if not texts:
        return []
    if is_query:
        texts = [settings.local_embedding_query_prefix + t for t in texts]
    # encode() is sync and CPU-bound; keep it off the event loop.
    return await asyncio.to_thread(_encode, texts, batch_size=batch_size)


async def embed_chunks(chunks: list[Chunk], **kwargs) -> list[Chunk]:
    """Return copies of ``chunks`` with their ``embedding`` field populated."""
    if not chunks:
        return []
    kwargs.pop("is_query", None)    # chunks are always passages, never queries
    vectors = await embed_texts([c.text for c in chunks], **kwargs)
    return [replace(chunk, embedding=v) for chunk, v in zip(chunks, vectors)]

