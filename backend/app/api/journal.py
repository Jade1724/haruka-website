import aiohttp
from fastapi import APIRouter, Depends, HTTPException

from core.factory import get_journal_service
from models.journal import JournalDetail, JournalSummary
from services.journal_service import JournalService

router = APIRouter(prefix="/journals", tags=["journals"])


@router.get("", response_model=list[JournalSummary])
async def get_journals(
    service: JournalService = Depends(get_journal_service),
) -> list[JournalSummary]:
    try:
        return await service.list_journals()
    except aiohttp.ClientResponseError as exc:
        raise HTTPException(status_code=502, detail=f"GitHub API error: {exc.status}")


@router.get("/{journal_id}", response_model=JournalDetail)
async def get_journal(
    journal_id: str,
    service: JournalService = Depends(get_journal_service),
) -> JournalDetail:
    try:
        detail = await service.get_journal(journal_id)
    except aiohttp.ClientResponseError as exc:
        raise HTTPException(status_code=502, detail=f"GitHub API error: {exc.status}")
    if detail is None:
        raise HTTPException(status_code=404, detail="Journal not found")
    return detail
