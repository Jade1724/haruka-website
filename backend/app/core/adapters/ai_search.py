"""Thin async wrapper around Azure AI Search: one hybrid query.

Hybrid = keyword (``search_text``) + vector (``vector_queries``) with the
semantic reranker (``query_type="semantic"``). The index, vector field, and
semantic config names match those created by the offline ``llm/`` pipeline
(see ``llm/mecha_llm/index.py``).
"""

import logging

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizedQuery

from core.config import settings

logger = logging.getLogger(__name__)

# Must match llm/mecha_llm/index.py.
SEMANTIC_CONFIG = "default-semantic"
VECTOR_FIELD = "embedding"
_SELECT = ["content", "title", "url", "repo_url", "source_type"]


def create_client() -> SearchClient:
    return SearchClient(
        endpoint=settings.azure_search_endpoint,
        index_name=settings.azure_search_index,
        credential=AzureKeyCredential(settings.azure_search_api_key),
    )


async def hybrid_search(
    client: SearchClient, *, query_text: str, query_vector: list[float], top_k: int
) -> list[dict]:
    """Return the top-k chunks (content + citation metadata) for a query."""
    vector_query = VectorizedQuery(
        vector=query_vector, k_nearest_neighbors=top_k, fields=VECTOR_FIELD
    )
    results = await client.search(
        search_text=query_text,
        vector_queries=[vector_query],
        query_type="semantic",
        semantic_configuration_name=SEMANTIC_CONFIG,
        top=top_k,
        select=_SELECT,
    )

    chunks: list[dict] = []
    async for doc in results:
        chunks.append(
            {
                "content": doc["content"],
                "title": doc["title"],
                "url": doc["url"],
                "repo_url": doc.get("repo_url") or None,
                "source_type": doc["source_type"],
                # Reranker score when semantic ranking applied; else the search score.
                "score": doc.get("@search.reranker_score") or doc.get("@search.score"),
            }
        )
    return chunks
