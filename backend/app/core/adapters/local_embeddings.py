"""Thin wrapper around a local sentence-transformers model: query embeddings.

Replaces ``azure_openai.embed_query`` on the retrieval path. The model
(``bge-small-en-v1.5``, 384 dims) is loaded once in ``main.py``'s lifespan and
shared via ``app.state`` — same lifecycle as the other adapter clients.

bge is asymmetric: search queries must be prefixed with a retrieval
instruction, stored passages must not. This module only embeds queries, so it
always applies the prefix; the passage side lives in the offline
``llm/mecha_llm/embeddings_local.py`` and leaves it off. Vectors are
L2-normalized so pgvector's cosine distance matches the offline index.
"""

import asyncio
import logging

from sentence_transformers import SentenceTransformer

from core.config import settings

logger = logging.getLogger(__name__)


def create_client() -> SentenceTransformer:
    """Load the embedding model once (downloads on first run, then cached)."""
    return SentenceTransformer(settings.local_embedding_model)


def _encode(model: SentenceTransformer, text: str) -> list[float]:
    vector = model.encode(
        settings.local_embedding_query_prefix + text,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return vector.tolist()


async def embed_query(model: SentenceTransformer, text: str) -> list[float]:
    """Embed a search query as a 384-dim unit vector (bge prefix applied)."""
    # encode() is sync and CPU-bound; keep it off the event loop.
    return await asyncio.to_thread(_encode, model, text)
