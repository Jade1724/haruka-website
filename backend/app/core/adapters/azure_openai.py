"""Thin async wrapper around Azure OpenAI: query embeddings + streaming chat.

Mirrors the simplicity of ``email.py`` — module-level functions over a client
that ``main.py`` creates once (in the lifespan) and shares via ``app.state``.
The embedding width is pinned to ``embedding_dimensions`` so query vectors match
the Azure AI Search index built by the offline ``llm/`` pipeline.
"""

import logging
from collections.abc import AsyncIterator

from openai import AsyncAzureOpenAI

from core.config import settings

logger = logging.getLogger(__name__)


def create_client() -> AsyncAzureOpenAI:
    return AsyncAzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )


async def embed_query(client: AsyncAzureOpenAI, text: str) -> list[float]:
    resp = await client.embeddings.create(
        model=settings.azure_openai_embedding_deployment,
        input=[text],
        dimensions=settings.embedding_dimensions,
    )
    return resp.data[0].embedding


async def stream_chat(
    client: AsyncAzureOpenAI, messages: list[dict]
) -> AsyncIterator[str]:
    """Yield content deltas from a streamed chat completion."""
    stream = await client.chat.completions.create(
        model=settings.azure_openai_chat_deployment,
        messages=messages,
        stream=True,
        temperature=0.3,
    )
    async for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content
