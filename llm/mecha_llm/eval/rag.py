"""System-under-test for evaluation: retrieve -> ground -> generate.

The ``llm/`` package can't import the backend, so this mirrors the backend's
RAG path (``backend/app/services/rag_service.py``) and returns both the answer
and the retrieved contexts that RAGAS needs. Non-streaming (eval wants the full
answer). Keep ``SYSTEM_PROMPT`` in sync with the backend's.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import asyncpg
from openai import AsyncAzureOpenAI
from pgvector.asyncpg import register_vector

from ..config import settings
from ..embeddings_local import embed_texts

# RRF fusion constants; mirror backend/app/core/adapters/pgvector_search.py.
RRF_K = 60
CANDIDATES = 50
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


# Hybrid retrieval mirroring the backend's pgvector_search adapter: vector
# (cosine) + Postgres FTS fused with Reciprocal Rank Fusion.
_HYBRID_SQL = """
WITH vector_search AS (
    SELECT id, row_number() OVER (ORDER BY embedding <=> $1) AS rank
    FROM chunks
    ORDER BY embedding <=> $1
    LIMIT $3
),
keyword_search AS (
    SELECT id, row_number() OVER (ORDER BY ts_rank_cd(content_tsv, query) DESC) AS rank
    FROM chunks, websearch_to_tsquery('english', $2) query
    WHERE content_tsv @@ query
    ORDER BY ts_rank_cd(content_tsv, query) DESC
    LIMIT $3
),
fused AS (
    SELECT
        id,
        COALESCE(1.0 / ($4 + v.rank), 0.0)
        + COALESCE(1.0 / ($4 + k.rank), 0.0) AS score
    FROM vector_search v
    FULL OUTER JOIN keyword_search k USING (id)
)
SELECT c.content
FROM fused f
JOIN chunks c USING (id)
ORDER BY f.score DESC
LIMIT $5;
"""


async def _retrieve(question: str, vector: list[float], top_k: int) -> list[str]:
    conn = await asyncpg.connect(settings.database_url)
    await register_vector(conn)
    try:
        rows = await conn.fetch(
            _HYBRID_SQL, vector, question, CANDIDATES, RRF_K, top_k
        )
    finally:
        await conn.close()
    return [r["content"] for r in rows]


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
        "database_url",
    )
    vector = (await embed_texts([question], is_query=True))[0]
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
