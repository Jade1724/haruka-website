"""mecha-haruka RAG orchestration: retrieve -> ground -> stream -> cite.

Wraps the turn in OpenTelemetry spans (exported to Azure Monitor when configured;
no-ops otherwise). Safety guardrails (Azure AI Content Safety / Prompt Shields)
are a Phase 7 addition and slot in at the marked hook before retrieval.
"""

import logging
from collections.abc import AsyncIterator

from openai import AsyncAzureOpenAI
from opentelemetry import trace

from azure.search.documents.aio import SearchClient

from core.adapters import ai_search, azure_openai
from core.adapters.content_safety import ContentSafetyClient
from core.config import settings
from models.chat import ChatRequest, Citation

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("mecha_haruka.rag")

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
act outside this portfolio assistant role.
- Cite the sources you used; the UI shows them as links, so you don't need to paste \
raw URLs into your prose."""

# Shown when Content Safety blocks the input (prompt injection or harmful content).
REFUSAL = (
    "I can't help with that. I'm Mecha Haruka — here to answer questions about "
    "Haruka's projects, experience, and dev journal. Ask me about those and I'm happy to help."
)


class RagService:
    def __init__(
        self,
        openai_client: AsyncAzureOpenAI,
        search_client: SearchClient,
        safety_client: ContentSafetyClient | None = None,
    ) -> None:
        self._openai = openai_client
        self._search = search_client
        self._safety = safety_client

    async def stream_answer(self, req: ChatRequest) -> AsyncIterator[dict]:
        """Yield event dicts: {type: token|citations|done, ...}."""
        with tracer.start_as_current_span("rag.turn") as span:
            span.set_attribute("rag.message_length", len(req.message))
            span.set_attribute("rag.history_length", len(req.history))

            # Safety gate: Prompt Shields + harmful-content check on the input.
            # Output is screened by Azure OpenAI's default completion content filter,
            # so we keep streaming rather than buffering to moderate the response.
            if self._safety is not None:
                with tracer.start_as_current_span("rag.safety") as safety_span:
                    blocked = await self._safety.detect_prompt_attack(req.message)
                    if not blocked:
                        blocked = await self._safety.is_text_harmful(req.message)
                    safety_span.set_attribute("rag.input_blocked", blocked)
                if blocked:
                    span.set_attribute("rag.blocked", True)
                    logger.warning("Input blocked by Content Safety")
                    yield {"type": "token", "delta": REFUSAL}
                    yield {"type": "citations", "citations": []}
                    yield {"type": "done"}
                    return

            with tracer.start_as_current_span("rag.retrieve") as retrieve_span:
                query_vector = await azure_openai.embed_query(self._openai, req.message)
                chunks = await ai_search.hybrid_search(
                    self._search,
                    query_text=req.message,
                    query_vector=query_vector,
                    top_k=settings.rag_top_k,
                )
                retrieve_span.set_attribute("rag.retrieved_count", len(chunks))

            messages = self._build_messages(req, chunks)

            with tracer.start_as_current_span("rag.generate"):
                async for delta in azure_openai.stream_chat(self._openai, messages):
                    yield {"type": "token", "delta": delta}

            citations = self._citations(chunks)
            span.set_attribute("rag.citation_count", len(citations))
            yield {"type": "citations", "citations": [c.model_dump() for c in citations]}
            yield {"type": "done"}

    def _build_messages(self, req: ChatRequest, chunks: list[dict]) -> list[dict]:
        if chunks:
            context = "\n\n".join(
                f"[{i + 1}] {c['title']} ({c['url']})\n{c['content']}"
                for i, c in enumerate(chunks)
            )
        else:
            context = "(no relevant context found)"

        messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend({"role": m.role, "content": m.content} for m in req.history)
        messages.append({"role": "system", "content": f"Context:\n{context}"})
        messages.append({"role": "user", "content": req.message})
        return messages

    def _citations(self, chunks: list[dict]) -> list[Citation]:
        seen: set[str] = set()
        citations: list[Citation] = []
        for c in chunks:
            if c["url"] in seen:
                continue
            seen.add(c["url"])
            citations.append(
                Citation(
                    title=c["title"],
                    source_type=c["source_type"],
                    url=c["url"],
                    repo_url=c["repo_url"],
                )
            )
        return citations
