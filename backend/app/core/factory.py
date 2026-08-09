from typing import TYPE_CHECKING

from fastapi import HTTPException, Request

from dao.github_dao import GithubDAO
from services.journal_service import JournalService

if TYPE_CHECKING:
    from services.rag_service import RagService


def get_journal_service(request: Request) -> JournalService:
    dao = GithubDAO(request.app.state.github_session)
    return JournalService(dao)


def get_rag_service(request: Request) -> "RagService":
    # Lazy import: pulls the heavy RAG deps (asyncpg, torch, ...) which are only
    # installed in "local" mode on the Pi, never on the Vercel proxy deployment.
    from services.rag_service import RagService

    openai_client = request.app.state.openai_client
    search_client = request.app.state.search_client
    embed_client = request.app.state.embed_client
    if openai_client is None or search_client is None or embed_client is None:
        raise HTTPException(
            status_code=503, detail="Chat is not configured on this deployment."
        )
    # Content Safety is optional; None when not configured.
    return RagService(
        openai_client,
        search_client,
        embed_client,
        request.app.state.content_safety_client,
    )
