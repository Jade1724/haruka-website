# Self-Hosting Migration Plan: Azure → Raspberry Pi 5

## Context

Azure AI Search is the expensive piece of the mecha-haruka RAG chatbot. This plan
replaces it — and the rest of the paid hosting — with a self-hosted stack on an
8GB Raspberry Pi 5: frontend, backend, PostgreSQL + pgvector, and a local
embedding model, all behind a single Cloudflare Tunnel. Azure OpenAI stays only
for chat generation (a local LLM on an 8GB Pi is not practical; revisit later).

This is deliberately a **learning project**. Each phase lists what you'll learn,
the work involved, and a checkpoint to verify before moving on. The centerpiece
is **implementing HNSW from scratch** and eventually serving real queries with it.

## Decisions

1. **Hosting shape**: everything on the Pi behind one Cloudflare Tunnel. Zero
   hosting cost; all services talk over localhost. Tradeoff: site availability
   depends on home power/internet.
2. **Embeddings**: local `BAAI/bge-small-en-v1.5` (384 dims) via
   sentence-transformers, replacing `text-embedding-3-large` (3072 dims — which
   exceeds pgvector's 2000-dim HNSW index limit anyway). Full corpus re-embed
   required; the corpus is small, so this takes minutes.
3. **HNSW scope**: build in pure Python inside `llm/` with tests and benchmarks
   (recall vs brute force, vs pgvector's HNSW), then wire it into the serving
   path for real behind a `VECTOR_BACKEND=hnsw_scratch|pgvector` config flag.
4. **Generation**: stays on Azure OpenAI (`gpt-4o`). Only retrieval and
   embeddings move.

## Current architecture (what's being replaced)

- **Online path**: `backend/app/services/rag_service.py` embeds the query via
  `backend/app/core/adapters/azure_openai.py`, then calls
  `backend/app/core/adapters/ai_search.py:hybrid_search()` — Azure AI Search
  hybrid retrieval (keyword + vector + semantic reranker). Clients are wired in
  app state via `backend/app/core/factory.py`; config in
  `backend/app/core/config.py`.
- **Offline pipeline** (`llm/mecha_llm/`): `build.py` orchestrates ingest
  (`sources/`) → `chunking.py` → `embeddings.py` (Azure OpenAI, batched) →
  `index.py` (Azure AI Search index + upsert). Shared dataclasses in
  `documents.py` (`SourceDoc`, `Chunk`).
- **Eval harness**: `llm/mecha_llm/eval/` (RAGAS, DeepEval) — reused here to
  compare retrieval quality before and after migration.

## RAM budget (8GB Pi 5)

| Service                        | Approx. RSS |
| ------------------------------ | ----------- |
| PostgreSQL + pgvector          | 300–500 MB  |
| FastAPI backend                | ~150 MB     |
| bge-small embedding model      | 300–400 MB  |
| Next.js production server      | 300–500 MB  |
| cloudflared                    | ~50 MB      |
| **Total**                      | **< 3 GB**  |

---

## Phase 0 — Pi preparation

**Goal**: a hardened, containerized base to build on.

**What you'll learn**: headless Linux server setup, SSH hardening, Docker on ARM64.

- Raspberry Pi OS Lite (64-bit), static LAN IP or DHCP reservation.
- SSH key-only auth, disable password login; `ufw` allowing only SSH from LAN.
- Install Docker + Docker Compose plugin. (Compose chosen over k3s for a single
  8GB node — you already know k8s from the Azure migration; k3s is a valid
  alternative if you want to keep exercising it, at the cost of ~500 MB overhead.)

**Checkpoint**: `docker run --rm hello-world` works over SSH; reboot survives.

## Phase 1 — PostgreSQL + pgvector

**Goal**: a vector-capable Postgres running on the Pi.

**What you'll learn**: the `vector` column type, distance operators (`<=>`
cosine, `<->` L2, `<#>` negative inner product), why normalized embeddings make
cosine equivalent to inner product, and pgvector's 2000-dim HNSW index limit.

- Compose service from `pgvector/pgvector:pg17` (arm64 image), volume-backed.
- Create the `chunks` table mirroring the Azure index schema
  (`llm/mecha_llm/documents.py`): `id`, `doc_id`, `chunk_index`, `content`,
  `title`, `source_type`, `url`, `repo_url`, `published_on`,
  `embedding vector(384)`, plus a generated `tsvector` column over
  `title + content` with a GIN index for the keyword leg of hybrid search.
- Add the pgvector HNSW index (`USING hnsw (embedding vector_cosine_ops)`).

**Checkpoint**: `SELECT '[1,2,3]'::vector(3) <=> '[3,2,1]'::vector(3);` returns
a distance from `psql`.

## Phase 2 — Local embeddings

**Goal**: replace Azure OpenAI embeddings with a local model.

**What you'll learn**: embedding dimensions and normalization, quality/size
tradeoffs (MTEB), why bge models want a query prefix
(`"Represent this sentence for searching relevant passages: "`), ONNX runtime
for faster ARM inference.

- New `llm/mecha_llm/embeddings_local.py` alongside the existing Azure module;
  a config field (`embedding_provider`) selects between them, and
  `embedding_dimensions` drops to 384.
- Same `embed_texts` / `embed_chunks` interface so `build.py` doesn't change.

**Checkpoint**: embedding the same sentence twice yields identical normalized
384-dim vectors; a similar pair scores closer than a dissimilar pair.

## Phase 3 — Rebuild pipeline → pgvector

**Goal**: `mecha_llm.build` writes to the Pi's Postgres instead of Azure AI Search.

**What you'll learn**: idempotent SQL upserts, asyncpg, schema-as-code.

- New `llm/mecha_llm/pg_store.py` taking over `index.py`'s role: ensure schema,
  `INSERT ... ON CONFLICT (id) DO UPDATE` keyed on chunk id.
- Run the build from the laptop against the Pi over LAN (`DATABASE_URL`
  pointing at the Pi).

**Checkpoint**: row count in `chunks` matches the chunk count logged by the
build; spot-check a journal chunk's content and metadata in `psql`.

## Phase 4 — Backend retrieval swap

**Goal**: the chatbot retrieves from pgvector instead of Azure AI Search.

**What you'll learn**: hybrid search without a managed reranker — vector
similarity + Postgres full-text (`websearch_to_tsquery`) fused with
**Reciprocal Rank Fusion (RRF)**; what Azure's semantic reranker was doing and
what is lost without it.

- New adapter `backend/app/core/adapters/pgvector_search.py` exposing the same
  chunk-dict shape as `ai_search.hybrid_search()` so `rag_service.py` barely
  changes; query embedding comes from the local model instead of
  `azure_openai.embed_query`.
- Rewire `main.py` app state + `factory.py`; update `config.py`
  (`database_url`, `chat_configured` no longer gates on Azure Search creds).

**Checkpoint**: run backend locally against the Pi's DB; `/chat` answers with
correct citations. Run the `llm/mecha_llm/eval/` RAGAS suite and compare
retrieval metrics against the Azure baseline (record the baseline **before**
tearing anything down).

## Phase 5 — Apps onto the Pi + Cloudflare Tunnel

**Goal**: the whole site served from the Pi, no open router ports.

**What you'll learn**: arm64 Docker builds, Next.js standalone output, DNS,
zero-open-port ingress via tunnels, deploying without a PaaS.

- Dockerfiles: Next.js (standalone) + FastAPI, built for arm64.
- Compose stack: `frontend`, `backend`, `postgres`, `cloudflared`.
- Cloudflare Tunnel: move the domain's DNS to Cloudflare, create a tunnel,
  public hostnames for the site and API routed to the local containers.
- Secrets via an env file on the Pi; restart policies; a simple `deploy.sh`
  (git pull → build → `docker compose up -d`).

**Checkpoint**: the site loads over the public domain with the tunnel as the
only ingress; chat works end-to-end; pulling the Pi's Ethernet and restoring it
recovers without intervention.

## Phase 6 — HNSW from scratch (the centerpiece)

**Goal**: understand, implement, validate, and finally serve with your own
approximate-nearest-neighbor index.

**6a. Study.** Malkov & Yashunin (2016), and the lineage: skip lists → NSW →
HNSW. Understand `M`, `ef_construction`, `ef_search`, layer assignment
(`floor(-ln(U) * mL)`), greedy `search_layer`, and the neighbor-selection
heuristic (why plain "closest M" degrades the graph).

**6b. Implement.** `llm/mecha_llm/hnsw/` in pure Python + numpy distances:
`graph.py` (structure, insert), `search.py` (layered greedy search). No FAISS,
no shortcuts.

**6c. Test.** Recall@k against brute-force exact search on the real corpus;
edge cases: empty index, k > n, duplicate vectors, single-layer graphs.

**6d. Benchmark.** Recall/latency curves vs exact scan and vs pgvector's HNSW;
a parameter-tuning table (`M`, `ef_construction`, `ef_search`). This is where
the paper's tradeoffs become tangible.

**6e. Serve for real.** The backend loads all vectors from Postgres at startup
into the scratch HNSW and serves ANN queries from it — Postgres stays the
source of truth, rebuild-on-boot is the honest persistence story for a small
corpus. `VECTOR_BACKEND=hnsw_scratch|pgvector` selects the backend; pgvector
remains the fallback.

**Checkpoint**: scratch HNSW serves production chat with recall@5 ≥ 0.95 vs
exact search, and the eval suite shows no quality regression vs pgvector.

## Phase 7 — Cutover & decommission

**Goal**: stop paying.

- Repoint DNS from Vercel to the tunnel (done in Phase 5); pause/remove the
  Vercel projects once stable.
- Re-run the eval suite one final time against production; archive results
  next to the Azure-baseline run.
- Decommission Azure AI Search; remove Azure OpenAI *embedding* deployment
  (keep the chat deployment); delete unused Azure resources from the earlier
  AKS migration if still running.
- Observability: the OpenTelemetry → Azure Monitor export can stay (free tier)
  or move to self-hosted Grafana/Prometheus later — out of scope here.

---

## Cost before / after

| Item                 | Before                    | After                     |
| -------------------- | ------------------------- | ------------------------- |
| Azure AI Search      | ~basic tier $$            | $0                        |
| Embeddings           | per-token (small)         | $0 (local)                |
| Chat generation      | per-token                 | per-token (unchanged)     |
| Hosting              | Vercel free tier          | $0 + Pi power (~2–5 W)    |
| Cloudflare Tunnel    | —                         | $0 (free plan)            |

## Suggested order of work

Phases 0→5 are the migration (each independently verifiable; the site keeps
running on Vercel until Phase 5's cutover). Phase 6 can start any time after
Phase 3 (it only needs vectors in Postgres) and is the deep-learning arc.
Phase 7 only after the eval comparison is recorded.
