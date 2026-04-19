from fastapi import Request

from dao.github_dao import GithubDAO
from services.journal_service import JournalService


def get_journal_service(request: Request) -> JournalService:
    dao = GithubDAO(request.app.state.github_session)
    return JournalService(dao)
