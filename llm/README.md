# mecha-llm

Offline RAG pipeline and evaluation harness for **mecha-haruka**, the portfolio
chatbot. This package contains **only** the asynchronous setup/batch logic:

- **ingest** content (journals, projects, experience, site routes),
- **chunk** it (markdown-aware, token-bounded),
- **embed** the chunks with Azure OpenAI, and
- **index** them into Azure AI Search.

Plus an **evaluation** harness (RAGAS + DeepEval). Real-time chat lives in the
backend (`backend/app`) and frontend (`frontend/components/chat`), not here.

See the design doc: [`docs/mecha-haruka-rag-chatbot.md`](../docs/mecha-haruka-rag-chatbot.md).

## Setup

```bash
cd llm
uv sync                 # core pipeline deps
uv sync --extra eval    # + RAGAS / DeepEval for the eval harness
cp .env.example .env     # then fill in the values
```

## Commands

```bash
# Build / refresh the Azure AI Search index from all content sources.
uv run python -m mecha_llm.build

# Run the offline unit tests (sources + chunking; no Azure required).
uv run pytest

# Evaluation (requires --extra eval and Azure judge model configured).
uv run pytest mecha_llm/eval/deepeval_tests.py
uv run python -m mecha_llm.eval.ragas_eval
```

## Layout

```
mecha_llm/
  config.py          # pydantic-settings (Azure OpenAI, AI Search, Langfuse)
  sources/           # journals, content.json (projects/experience), site routes
  chunking.py        # markdown-aware, token-bounded chunker
  embeddings.py      # async Azure OpenAI embeddings
  index.py           # Azure AI Search index create + idempotent upsert
  build.py           # orchestration: ingest -> chunk -> embed -> upsert
  eval/              # RAGAS + DeepEval + red-team
tests/               # offline unit tests
```
