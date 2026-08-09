"""Thin async wrapper around Azure OpenAI: streaming chat generation.

Mirrors the simplicity of ``email.py`` — module-level functions over a client
that ``main.py`` creates once (in the lifespan) and shares via ``app.state``.
Query embeddings moved to ``local_embeddings`` (bge, on-device); this module now
only handles chat generation.
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
