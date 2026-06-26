from fastapi import HTTPException, Request

from dao.github_dao import GithubDAO
from services.journal_service import JournalService
from services.rag_service import RagService


def get_journal_service(request: Request) -> JournalService:
    dao = GithubDAO(request.app.state.github_session)
    return JournalService(dao)


def get_rag_service(request: Request) -> RagService:
    openai_client = request.app.state.openai_client
    search_client = request.app.state.search_client
    if openai_client is None or search_client is None:
        raise HTTPException(
            status_code=503, detail="Chat is not configured on this deployment."
        )
    # Content Safety is optional; None when not configured.
    return RagService(openai_client, search_client, request.app.state.content_safety_client)
