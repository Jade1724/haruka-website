import asyncio
import logging
import smtplib
from email.message import EmailMessage

from core.config import settings
from models.contact import ContactRequest

logger = logging.getLogger(__name__)


class ContactService:
    def _send_smtp(self, req: ContactRequest) -> None:
        msg = EmailMessage()
        msg["Subject"] = f"Portfolio contact from {req.name}"
        msg["From"] = settings.smtp_user
        msg["To"] = settings.contact_recipient
        msg["Reply-To"] = req.email
        msg.set_content(
            f"Name: {req.name}\n"
            f"Email: {req.email}\n\n"
            f"{req.message}"
        )

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
            smtp.starttls()
            smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(msg)

    async def send(self, req: ContactRequest) -> None:
        try:
            await asyncio.get_event_loop().run_in_executor(None, self._send_smtp, req)
            logger.info("Contact email sent from %s", req.email)
        except Exception:
            logger.exception("Failed to send contact email from %s", req.email)
            raise
