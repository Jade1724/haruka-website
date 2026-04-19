import smtplib

from fastapi import APIRouter, HTTPException

from models.contact import ContactRequest
from services.contact_service import ContactService

router = APIRouter(prefix="/contact", tags=["contact"])

_service = ContactService()


@router.post("")
async def post_contact(req: ContactRequest) -> dict:
    try:
        await _service.send(req)
    except smtplib.SMTPException as exc:
        raise HTTPException(status_code=502, detail=f"Failed to send email: {exc}")
    return {"ok": True}
