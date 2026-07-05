"""Azure AI Search index: definition, idempotent create, and chunk upsert.

The index backs hybrid retrieval (vector + keyword) with a semantic reranker:

- ``content`` / ``title`` are searchable for the keyword + semantic legs;
- ``embedding`` is the vector field (width pinned to ``embedding_dimensions``);
- ``source_type`` / ``doc_id`` / ``published_on`` are filterable for citations.

``ensure_index`` is create-or-update (safe to re-run), and ``upsert_chunks`` uses
merge-or-upload keyed on the deterministic chunk ``id`` so rebuilds are incremental.
"""

from __future__ import annotations

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.indexes.aio import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)

from .config import settings
from .documents import Chunk

# Stable names referenced by both the index schema and query time (backend adapter).
HNSW_ALGORITHM = "default-hnsw-algo"
VECTOR_PROFILE = "default-hnsw"
SEMANTIC_CONFIG = "default-semantic"

# Azure AI Search accepts up to 1000 documents per indexing batch.
UPSERT_BATCH_SIZE = 1000


def index_definition() -> SearchIndex:
    """Build the ``SearchIndex`` schema for the chunk store."""
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SimpleField(name="doc_id", type=SearchFieldDataType.String, filterable=True),
        SimpleField(
            name="chunk_index",
            type=SearchFieldDataType.Int32,
            filterable=True,
            sortable=True,
        ),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SearchableField(name="title", type=SearchFieldDataType.String),
        SimpleField(
            name="source_type",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True,
        ),
        SimpleField(name="url", type=SearchFieldDataType.String),
        SimpleField(name="repo_url", type=SearchFieldDataType.String),
        SimpleField(
            name="published_on",
            type=SearchFieldDataType.String,
            filterable=True,
            sortable=True,
        ),
        SearchField(
            name="embedding",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=settings.embedding_dimensions,
            vector_search_profile_name=VECTOR_PROFILE,
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name=HNSW_ALGORITHM)],
        profiles=[
            VectorSearchProfile(
                name=VECTOR_PROFILE,
                algorithm_configuration_name=HNSW_ALGORITHM,
            )
        ],
    )

    semantic_search = SemanticSearch(
        configurations=[
            SemanticConfiguration(
                name=SEMANTIC_CONFIG,
                prioritized_fields=SemanticPrioritizedFields(
                    title_field=SemanticField(field_name="title"),
                    content_fields=[SemanticField(field_name="content")],
                ),
            )
        ]
    )

    return SearchIndex(
        name=settings.azure_search_index,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search,
    )


def _credential() -> AzureKeyCredential:
    settings.require("azure_search_endpoint", "azure_search_api_key")
    return AzureKeyCredential(settings.azure_search_api_key)


def _index_client() -> SearchIndexClient:
    return SearchIndexClient(settings.azure_search_endpoint, _credential())


def _search_client() -> SearchClient:
    return SearchClient(
        settings.azure_search_endpoint, settings.azure_search_index, _credential()
    )


async def ensure_index() -> None:
    """Create or update the index so it matches ``index_definition()``."""
    client = _index_client()
    async with client:
        await client.create_or_update_index(index_definition())


async def upsert_chunks(chunks: list[Chunk], *, batch_size: int = UPSERT_BATCH_SIZE) -> int:
    """Merge-or-upload embedded chunks; return the number successfully indexed."""
    if not chunks:
        return 0

    documents = [chunk.to_search_document() for chunk in chunks]
    uploaded = 0
    client = _search_client()
    async with client:
        for i in range(0, len(documents), batch_size):
            results = await client.merge_or_upload_documents(
                documents=documents[i : i + batch_size]
            )
            uploaded += sum(1 for r in results if r.succeeded)
    return uploaded
