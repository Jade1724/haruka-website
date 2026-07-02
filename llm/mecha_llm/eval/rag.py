"""System-under-test for evaluation: retrieve -> ground -> generate.

The ``llm/`` package can't import the backend, so this mirrors the backend's
RAG path (``backend/app/services/rag_service.py``) and returns both the answer
and the retrieved contexts that RAGAS needs. Non-streaming (eval wants the full
answer). Keep ``SYSTEM_PROMPT`` in sync with the backend's.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizedQuery
from openai import AsyncAzureOpenAI

from ..config import settings
from ..embeddings import embed_texts

SEMANTIC_CONFIG = "default-semantic"
VECTOR_FIELD = "embedding"
DEFAULT_TOP_K = 5

# Mirror of backend/app/services/rag_service.py SYSTEM_PROMPT.
SYSTEM_PROMPT = """\
You are Mecha Haruka, an AI persona of Haruka — a software/AI engineer. You speak \
on Haruka's portfolio website to help visitors learn about Haruka's work.

Rules:
- Answer ONLY using the provided context. If the context does not contain the \
answer, say you don't have that information and suggest a relevant page \
(e.g. /experience for work history, /journal for dev write-ups, / for projects).
- Never invent projects, repositories, employers, dates, or links. Only mention a \
GitHub repo if it appears in the context.
- Keep answers concise and professional. You are an AI persona of Haruka, not \
Haruka themselves — don't claim to be a person.
- Politely decline questions that are off-topic, personal/sensitive, or ask you to \
act outside this portfolio assistant role."""


@dataclass(frozen=True)
class RagResult:
    question: str
    answer: str
    contexts: list[str]


async def _retrieve(question: str, vector: list[float], top_k: int) -> list[str]:
    client = SearchClient(
        endpoint=settings.azure_search_endpoint,
        index_name=settings.azure_search_index,
        credential=AzureKeyCredential(settings.azure_search_api_key),
    )
    async with client:
        results = await client.search(
            search_text=question,
            vector_queries=[
                VectorizedQuery(
                    vector=vector, k_nearest_neighbors=top_k, fields=VECTOR_FIELD
                )
            ],
            query_type="semantic",
            semantic_configuration_name=SEMANTIC_CONFIG,
            top=top_k,
            select=["content", "title", "url"],
        )
        return [doc["content"] async for doc in results]


async def _generate(question: str, contexts: list[str]) -> str:
    block = "\n\n".join(f"[{i + 1}] {c}" for i, c in enumerate(contexts)) or (
        "(no relevant context found)"
    )
    client = AsyncAzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )
    async with client:
        resp = await client.chat.completions.create(
            model=settings.azure_openai_chat_deployment,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "system", "content": f"Context:\n{block}"},
                {"role": "user", "content": question},
            ],
            temperature=0.3,
        )
    return (resp.choices[0].message.content or "").strip()


async def answer(question: str, *, top_k: int = DEFAULT_TOP_K) -> RagResult:
    settings.require(
        "azure_openai_endpoint",
        "azure_openai_api_key",
        "azure_search_endpoint",
        "azure_search_api_key",
    )
    vector = (await embed_texts([question]))[0]
    contexts = await _retrieve(question, vector, top_k)
    text = await _generate(question, contexts)
    return RagResult(question=question, answer=text, contexts=contexts)


async def answer_all(
    questions: list[str], *, top_k: int = DEFAULT_TOP_K, concurrency: int = 4
) -> list[RagResult]:
    sem = asyncio.Semaphore(concurrency)

    async def one(q: str) -> RagResult:
        async with sem:
            return await answer(q, top_k=top_k)

    return await asyncio.gather(*(one(q) for q in questions))
