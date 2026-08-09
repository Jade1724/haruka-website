-- Phase 1 schema for the mecha-haruka RAG store (pgvector).
-- Mirrors llm/mecha_llm/documents.py::Chunk

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
    id text PRIMARY KEY,
    doc_id text NOT NULL,
    chunk_index int NOT NULL,
    content text NOT NULL,
    title text NOT NULL,
    source_type text NOT NULL
    CHECK (source_type IN ('journal', 'project', 'experience', 'page')),
    url text NOT NULL,
    repo_url text,
    published_on date,
    embedding vector(384),
    content_tsv tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(title, '')), 'A')
        || setweight(to_tsvector('english', coalesce(content, '')), 'B')
    ) STORED
);

CREATE INDEX IF NOT EXISTS chunks_tsv_gin
ON chunks USING gin (content_tsv);

CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw
ON chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
