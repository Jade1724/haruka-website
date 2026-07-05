# mecha-haruka — RAG Chatbot Design

## Context

The portfolio site (Next.js frontend + FastAPI backend, live on Vercel) showcases projects, a
career timeline, and a dev journal scraped from a private Obsidian repo. **mecha-haruka** is an
"AI version of Haruka" — a RAG chatbot that:

- answers questions about Haruka as an engineer,
- points users to the right page on the site ("which page should I look at?"), and
- surfaces relevant links — public GitHub repos and specific journal entries.

Example interactions:

- *"Does Haruka have a project building a VR game?"* → describes the Apple Thinning VR project and
  links the public repo `https://github.com/uc-vision/apple-thinning`.
- *"What has Haruka written about setting up Next.js with FastAPI?"* → links the matching journal
  entry at `/journal/{id}`.
- *"Where can I see Haruka's work history?"* → suggests navigating to `/experience`.

The aim is to demonstrate **production-grade AI engineering**: a real RAG pipeline, safety/ethics
guardrails, observability, and evaluation — using popular, open-source, industry-standard tooling.

## Decisions

| Concern | Choice | Why |
|---|---|---|
| Hosting | Frontend + backend stay on **Vercel**; they call Azure AI over HTTPS | Vercel is the live host; RAG resources are just APIs reachable with endpoint+key — the app need not run inside Azure |
| LLM + embeddings | **Azure OpenAI** via **Azure AI Foundry** | Required; mirrors Haruka's day-job Azure OpenAI experience |
| Vector store / retrieval | **Azure AI Search** (hybrid vector + keyword, semantic reranker) | AI Foundry-native, managed, supports hybrid + reranking out of the box |
| Observability | **OpenTelemetry → Azure Monitor / Application Insights** | Vendor-neutral OTel GenAI instrumentation exported to App Insights; Azure-native (fits the all-Azure design), managed, queryable with KQL; captures traces, token usage, latency |
| Evaluation | **RAGAS** + **DeepEval** | RAGAS for RAG-quality metrics; DeepEval for pytest-style assertions, bias/toxicity, and red-teaming |
| Safety | **Azure AI Content Safety** (Prompt Shields + harmful-category checks) + grounding/citations | Blocks jailbreaks/prompt-injection and harmful content; grounding curbs hallucination |
| IaC | **No Terraform** for LLM resources for now | Resources provisioned by hand via `az`/Foundry; app reads endpoint+key from config |

> **Hosting rationale.** The RAG capability is hosting-agnostic — the app only needs to *call*
> Azure, not live in it. Vercel is the live host (`main` deploys to Vercel; the AKS path under
> `k8s/` + `infra/` is manual-only on the `azure-migration` branch). We keep frontend+backend on
> Vercel and add Azure AI as an external dependency. The `llm/` pipeline is an offline batch job
> (local or GitHub Actions), independent of where the app is hosted.
>
> **Vercel caveats.** (1) FastAPI `StreamingResponse` SSE may be buffered on Vercel's Python
> runtime — verify on a preview deploy; fallback is a Node/Edge proxy route or a non-streamed
> response. (2) Pick an Azure region near the Vercel deploy region (payloads are small, so latency
> impact is minor). (3) Secrets via Vercel environment variables, not the AKS CSI secret store.

## Architecture

```
                  ┌──────────────────── OFFLINE  (llm/ folder, async batch) ────────────────────┐
 Content sources  │  ingest → normalize → chunk → embed (Azure OpenAI) → upsert to AI Search     │
 ├─ Journals (GitHub/Obsidian, mirrors backend GithubDAO)                                         │
 ├─ Projects + Experience (frontend/lib/content.json)                                             │
 └─ Site routes ("/", "/experience", "/journal", "/journal/{id}") + repo links as metadata        │
                  └─────────────────────────────────────────────────────────────────────────────┘
                                              │ writes
                                              ▼
                                  ┌────────────────────────┐
                                  │     Azure AI Search     │  hybrid + semantic rerank
                                  └────────────────────────┘
                                              ▲ retrieve (top-k)
 REAL-TIME                                    │
 Browser ── POST /chat (SSE) ──► FastAPI backend (Vercel)
   floating chat widget          rag_service: guardrails → retrieve → grounded prompt
   (Next.js)                      → Azure OpenAI chat (stream) → citations (links/routes)
                                      │                 │
                             Azure AI Content     OTel span → App Insights
                             Safety (Prompt        (retrieval, prompt, completion,
                             Shields + categories) tokens, latency, safety verdicts)
```

**Retrieval-and-cite contract.** Every indexed chunk carries metadata
`{ source_type: journal | project | experience | page, title, url | route, repo_url? }`. The chat
response streams the answer text, then emits a structured `citations[]` array that the frontend
renders as clickable links and route suggestions. The system prompt instructs the model to ground
answers only in retrieved context and to cite.

## Repository layout

```
llm/                                  # NEW — offline async pipeline + eval ONLY
  pyproject.toml                      # standalone uv project (Python 3.13)
  README.md
  .env.example
  mecha_llm/
    config.py                         # pydantic-settings (Azure OpenAI, AI Search, Azure Monitor/OTel)
    sources/
      journals.py                     # pull journal markdown (mirrors backend GithubDAO)
      content_json.py                 # load frontend/lib/content.json (projects + experience)
      routes.py                       # static site routes -> navigation docs
    chunking.py                       # markdown-aware chunking (headings, token-bounded, overlap)
    embeddings.py                     # async Azure OpenAI embeddings (text-embedding-3-large)
    index.py                          # create/refresh AI Search index + idempotent upsert
    build.py                          # async orchestration: ingest -> chunk -> embed -> upsert
    eval/
      dataset.py                      # golden Q/A set + RAGAS synthetic test-set generation
      ragas_eval.py                   # RAG quality metrics, emits scores as App Insights custom events
      deepeval_tests.py               # pytest: G-Eval, bias, toxicity, hallucination
      redteam.py                      # DeepEval red-team / jailbreak suite
  tests/

backend/app/                          # CHANGED — real-time chat
  core/adapters/azure_openai.py       # NEW adapter (mirrors email.py): chat (stream) + embeddings
  core/adapters/ai_search.py          # NEW adapter: async hybrid query against Azure AI Search
  core/adapters/content_safety.py     # NEW adapter: Prompt Shields + harmful-content check
  services/rag_service.py             # NEW: guardrails -> retrieve -> prompt -> stream -> cite
  api/chat.py                         # NEW: POST /chat (SSE StreamingResponse)
  models/chat.py                      # NEW: ChatRequest, ChatChunk, Citation
  core/config.py                      # add Azure OpenAI / AI Search / App Insights / safety settings
  core/factory.py                     # add get_rag_service(request)
  observability.py                    # NEW: configure_azure_monitor() + OpenAI/FastAPI instrumentation + tracer
  main.py                             # register chat_router; init clients + OTel/Azure Monitor in lifespan

frontend/                             # CHANGED — chat widget
  components/chat/
    chat-widget.tsx                   # floating launcher + panel (client component)
    chat-message.tsx                  # message bubble + citation links
    use-chat.ts                       # fetch + ReadableStream SSE consumer (not React Query)
  components/ui/                       # add shadcn primitives as needed
  app/layout.tsx                      # mount <ChatWidget/> globally (inside QueryProvider)
```

## The `llm/` folder (offline pipeline + eval)

Standalone **uv** Python 3.13 project, independent of the backend so it can run in CI or locally as
a batch job.

1. **Sources** (`sources/`)
   - `journals.py` — mirrors the existing GitHub access pattern (`backend/app/dao/github_dao.py`:
     recursive tree → `.md` blobs → base64 contents; ID format `YYYY-MM-DD-slug` and route
     `/journal/{id}` from `journal_service.py`). Self-contained but uses the same ID scheme so
     citations link correctly.
   - `content_json.py` — reads `frontend/lib/content.json` (`projects[]`, `work[]`, `education[]`);
     captures `links[].url` (GitHub repos) into chunk metadata.
   - `routes.py` — hand-authored navigation docs (one per route) so "which page?" retrieves a route.
2. **Chunking** (`chunking.py`) — markdown-aware: split on headings then token-bounded windows
   (~300–500 tokens, ~15% overlap). Each chunk → `{ id, text, source_type, title, url/route,
   repo_url?, published_on? }`.
3. **Embeddings** (`embeddings.py`) — async batched Azure OpenAI `text-embedding-3-large`, with
   retry/backoff.
4. **Index** (`index.py`) — define the AI Search index (vector field + semantic config + filterable
   metadata); idempotent create-or-update; upsert by deterministic chunk id so re-runs are
   incremental.
5. **Orchestrator** (`build.py`) — `asyncio` pipeline `ingest → chunk → embed → upsert`; CLI entry
   `uv run python -m mecha_llm.build`. Future: schedule after journal changes.
6. **Eval** (`eval/`) — see [Evaluation](#evaluation-ragas--deepeval).

## Backend (real-time chat)

Follows the existing 4-layer pattern (`api → services → adapters`, DI via `core/factory.py`, shared
clients created in `main.py` lifespan, pydantic-settings config).

- **Adapters** (`core/adapters/`, mirror `email.py` simplicity):
  - `azure_openai.py` — async chat completion **with streaming** + embeddings.
  - `ai_search.py` — async hybrid query (vector + keyword + semantic rerank); returns top-k chunks
    with metadata for citations.
  - `content_safety.py` — Azure AI Content Safety: Prompt Shields on input + harmful-category check
    on input/output.
- **Service** (`services/rag_service.py`):
  1. validate/normalize input; Prompt Shields + length/rate checks;
  2. embed query → AI Search hybrid retrieve (top-k);
  3. build the grounded system prompt (mecha-haruka persona; answer only from context; never invent
     repos/facts; politely decline + suggest a page when off-scope; always cite);
  4. stream the Azure OpenAI completion;
  5. assemble `citations[]` from retrieved metadata;
  6. wrap the turn in an OTel span (exported to Application Insights).
- **Route** (`api/chat.py`) — `POST /chat` → `StreamingResponse` (SSE) of token deltas, terminating
  with a `citations` event; `Depends(get_rag_service)`. Verify SSE streams un-buffered through
  Vercel's Python runtime (`backend/api/index.py` + `vercel.json`); fallback to a non-streamed
  response or a Node/Edge proxy if buffered.
- **Models** (`models/chat.py`) — `ChatRequest{ message, history? }`, `ChatChunk{ delta }`,
  `Citation{ title, url|route, source_type }`.

## Frontend (chat widget)

> Next.js 16 + React 19 (App Router). Read `frontend/node_modules/next/dist/docs/` before writing
> Next-specific code. Streaming is consumed with `fetch` + `ReadableStream` (SSE-over-POST), not
> React Query.

- `components/chat/chat-widget.tsx` — floating launcher + slide-up panel; theme-aware via the
  existing `ThemeProvider`; reuses shadcn `button` and adds `sheet`/`scroll-area` as needed.
- `components/chat/use-chat.ts` — POSTs to `${NEXT_PUBLIC_API_URL}/chat`, reads the SSE stream,
  appends deltas, then renders `citations` as clickable links (`next/link` for internal routes;
  external repos open in a new tab).
- `components/chat/chat-message.tsx` — message bubble + citation chips.
- Mounted globally in `app/layout.tsx` inside `QueryProvider`, after `<main>`.
- A short privacy line ("messages are processed by Azure OpenAI; don't share sensitive info") in the
  panel.

## Safety, ethics, privacy

- **Grounding / anti-hallucination** — answer only from retrieved context; "if unknown, say so and
  suggest a page"; citations required. Validated by RAGAS faithfulness + DeepEval hallucination.
- **Prompt-injection / jailbreak** — Azure AI Content Safety Prompt Shields on input; hardened
  system prompt; DeepEval red-team suite in CI.
- **Harmful content & bias/fairness** — Content Safety harmful-category checks on input+output;
  DeepEval bias/toxicity metrics; persona constrained to professional/portfolio scope; declines
  personal/sensitive or discriminatory requests.
- **Privacy / PII** — no persistence of raw user messages by default; OTel GenAI message-content
  capture left **off** by default (`OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=false`), so
  prompt/completion text is not sent to App Insights unless explicitly enabled; rate limiting +
  input length caps; secrets only via Vercel env vars, never baked into images/builds.
- **Transparency** — UI labels it an AI persona of Haruka, not Haruka.

## Observability (OpenTelemetry → Azure Monitor / Application Insights)

OpenTelemetry is the instrumentation/transport layer only; **Application Insights** is the backing
store + UI (queried with KQL). No separate observability service to run.

- `backend/app/observability.py` — calls `configure_azure_monitor()` (the `azure-monitor-opentelemetry`
  distro) once in the FastAPI lifespan, then instruments the OpenAI SDK
  (`opentelemetry-instrumentation-openai-v2`, GenAI semantic conventions) and FastAPI. Exposes a
  `tracer` for manual spans around `retrieve`, `build_prompt`, `chat_completion`; the OpenAI
  instrumentation auto-captures model, token usage, and latency, and manual spans add retrieved
  chunk ids, safety verdicts, and citations.
- Config via a single `APPLICATIONINSIGHTS_CONNECTION_STRING` (from the App Insights resource);
  `OTEL_SERVICE_NAME` names the service. Prompt/completion text capture is off by default
  (`OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT`).
- **Gaps vs a purpose-built LLM tool (handled deliberately):** (1) dollar **cost** is not
  auto-computed — derive it from `gen_ai.usage.*` token counts via a KQL query or a `cost` span
  attribute from a price map; (2) there is no first-class **eval-score** object — the `llm/` eval
  jobs emit RAGAS/DeepEval scores as App Insights **custom events/metrics** tagged with `trace_id`,
  so offline eval can still be joined to production traces in KQL.

## Evaluation (RAGAS + DeepEval)

Lives in `llm/eval/`.

- **RAGAS** — faithfulness, answer relevancy, context precision/recall over a golden + synthetic
  set; gated on thresholds.
- **DeepEval** — pytest-style G-Eval correctness, bias, toxicity, hallucination, plus
  red-team/jailbreak. Runnable locally (`uv run pytest`) and in CI as a quality gate before index or
  prompt changes ship.

## Configuration & secrets

Added to `backend/app/core/config.py` and `llm/mecha_llm/config.py`; documented in the `CLAUDE.md`
env section and the respective `.env.example` files:

```
AZURE_OPENAI_ENDPOINT=          AZURE_OPENAI_API_KEY=
AZURE_OPENAI_CHAT_DEPLOYMENT=   AZURE_OPENAI_EMBEDDING_DEPLOYMENT=
AZURE_OPENAI_API_VERSION=
AZURE_SEARCH_ENDPOINT=          AZURE_SEARCH_API_KEY=        AZURE_SEARCH_INDEX=
AZURE_CONTENT_SAFETY_ENDPOINT=  AZURE_CONTENT_SAFETY_KEY=
APPLICATIONINSIGHTS_CONNECTION_STRING=  OTEL_SERVICE_NAME=
```

Azure OpenAI deployments, Azure AI Search, Content Safety, and the Application Insights resource are
provisioned by hand via `az` / the Azure portal. Keys/connection strings are stored as Vercel
environment variables (backend project) and in local `.env` files for development. The `llm/`
pipeline reads the same values from its own `.env` / CI secrets.

## Phased implementation

1. **Doc** — this file.
2. **`llm/` scaffold + ingestion + chunking** (offline, testable without Azure).
3. **Azure resources** — Azure OpenAI chat+embedding deployments, Azure AI Search, Content Safety,
   Application Insights (provisioned via `az`/portal).
4. **`llm/` embed + index build** — `build.py` populates Azure AI Search.
5. **Backend** — adapters + `rag_service` + `/chat` SSE + OTel/Azure Monitor tracing.
6. **Frontend** — chat widget with streaming + citations, mounted globally.
7. **Safety hardening** — Prompt Shields + Content Safety wired and tested.
8. **Eval harness** — RAGAS + DeepEval + red-team, with thresholds; scores to App Insights custom events.
9. **Deploy** — env vars on Vercel; confirm SSE behavior (fallback if buffered); update docs;
   optional scheduled GitHub Action for the index build.

## Verification

- **`llm/` pipeline** — `uv run python -m mecha_llm.build` → confirm chunk count and that documents
  (with metadata) exist in Azure AI Search.
- **Retrieval sanity** — query AI Search for "VR game" → returns the Apple Thinning chunk with
  `repo_url = https://github.com/uc-vision/apple-thinning`.
- **Backend (local)** — `uv run uvicorn app.main:app --reload`; `curl -N` `POST /chat` with the
  VR-game question → streamed grounded answer + repo citation; a navigation question → suggests
  `/journal` or `/experience`; the turn appears as a distributed trace in Application Insights with
  token usage (Transaction search / Application map).
- **Backend (Vercel)** — deploy a preview and `curl -N` the deployed `/chat` to confirm SSE is not
  buffered; apply the fallback if it is.
- **Safety** — a prompt-injection/jailbreak attempt is blocked with a safe refusal; off-scope or
  sensitive requests are politely declined.
- **Frontend** — `bun run dev`; the widget floats on every page; example questions stream an answer
  with clickable citations; works in light + dark.
- **Eval gate** — `uv run pytest` (DeepEval) passes thresholds; `ragas_eval.py` reports metrics
  above thresholds and scores appear as custom events in Application Insights.
- **Full stack** — `docker compose up` → widget on `localhost:3000` talks to the backend on `:8000`
  end to end.
