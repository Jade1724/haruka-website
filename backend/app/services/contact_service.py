import asyncio
import logging

from core.adapters.email import send_email
from core.config import settings
from models.contact import ContactRequest

logger = logging.getLogger(__name__)


class ContactService:
    async def send(self, req: ContactRequest) -> None:
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: send_email(
                    subject=f"Portfolio contact from {req.name}",
                    to=settings.contact_recipient,
                    reply_to=req.email,
                    body=f"Name: {req.name}\nEmail: {req.email}\n\n{req.message}",
                ),
            )
            logger.info("Contact email sent from %s", req.email)
        except Exception:
            logger.exception("Failed to send contact email from %s", req.email)
            raise
