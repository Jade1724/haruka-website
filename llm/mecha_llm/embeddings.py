"""Async batched Azure OpenAI embeddings.

Embeds chunk text with ``text-embedding-3-large`` (the deployment named in
``settings.azure_openai_embedding_deployment``). Requests are batched and run with
bounded concurrency; each call retries with exponential backoff on transient errors.
The vector width is pinned to ``settings.embedding_dimensions`` so it always matches
the Azure AI Search index schema (see ``index.py``).
"""

from __future__ import annotations

import asyncio
from dataclasses import replace

from openai import (
    APIConnectionError,
    APITimeoutError,
    AsyncAzureOpenAI,
    InternalServerError,
    RateLimitError,
)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from .config import settings
from .documents import Chunk

# Batched embedding inputs per request, and how many requests run concurrently.
EMBED_BATCH_SIZE = 64
EMBED_CONCURRENCY = 4

_TRANSIENT = (RateLimitError, APITimeoutError, APIConnectionError, InternalServerError)


def _client() -> AsyncAzureOpenAI:
    settings.require("azure_openai_endpoint", "azure_openai_api_key")
    return AsyncAzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )


@retry(
    retry=retry_if_exception_type(_TRANSIENT),
    wait=wait_random_exponential(min=1, max=30),
    stop=stop_after_attempt(6),
    reraise=True,
)
async def _embed_batch(client: AsyncAzureOpenAI, batch: list[str]) -> list[list[float]]:
    resp = await client.embeddings.create(
        model=settings.azure_openai_embedding_deployment,
        input=batch,
        dimensions=settings.embedding_dimensions,
    )
    # The API may return items out of order; restore input order via ``index``.
    return [item.embedding for item in sorted(resp.data, key=lambda d: d.index)]


async def embed_texts(
    texts: list[str],
    *,
    batch_size: int = EMBED_BATCH_SIZE,
    concurrency: int = EMBED_CONCURRENCY,
) -> list[list[float]]:
    """Embed ``texts`` and return one vector per input, in order."""
    if not texts:
        return []

    batches = [texts[i : i + batch_size] for i in range(0, len(texts), batch_size)]
    sem = asyncio.Semaphore(concurrency)

    client = _client()
    async with client:

        async def run(batch: list[str]) -> list[list[float]]:
            async with sem:
                return await _embed_batch(client, batch)

        results = await asyncio.gather(*(run(b) for b in batches))

    return [vector for batch in results for vector in batch]


async def embed_chunks(chunks: list[Chunk], **kwargs) -> list[Chunk]:
    """Return copies of ``chunks`` with their ``embedding`` field populated."""
    if not chunks:
        return []
    vectors = await embed_texts([c.text for c in chunks], **kwargs)
    return [replace(chunk, embedding=vector) for chunk, vector in zip(chunks, vectors)]
