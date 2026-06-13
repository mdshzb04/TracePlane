import asyncio
import logging
import re
from typing import Any

import resend

from app.core.config import settings

logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_MAX_ATTEMPTS = 3
_RETRY_DELAY_SEC = 0.5


def validate_recipient_email(email: str) -> str:
    normalized = email.strip().lower()
    if not _EMAIL_RE.match(normalized):
        raise ValueError("Invalid email address")
    return normalized


def validate_resend_at_startup() -> bool:
    """Validate Resend configuration without exposing the API key."""
    if not settings.resend_configured:
        logger.warning("Resend not configured — alert emails will fail until RESEND_API_KEY is set")
        return False
    key = settings.RESEND_API_KEY.strip()
    if not key.startswith("re_"):
        logger.warning("RESEND_API_KEY format looks invalid (expected re_ prefix)")
        return False
    resend.api_key = key
    logger.info("Resend configured: true")
    return True


class EmailService:
    """Send transactional email via Resend with retries."""

    def __init__(self) -> None:
        self._configured = settings.resend_configured
        if self._configured:
            resend.api_key = settings.RESEND_API_KEY

    @property
    def is_configured(self) -> bool:
        return self._configured

    def _send_sync(
        self,
        to: str,
        subject: str,
        text: str,
        html: str | None = None,
    ) -> dict[str, Any]:
        if not self._configured:
            raise RuntimeError("Resend is not configured — set RESEND_API_KEY in backend .env")

        payload: dict[str, Any] = {
            "from": settings.RESEND_FROM_EMAIL,
            "to": [to],
            "subject": subject,
            "text": text,
        }
        if html:
            payload["html"] = html
        logger.info("Sending email via Resend to %s subject=%s", to, subject)
        response = resend.Emails.send(payload)
        if isinstance(response, dict):
            return response
        return {"id": str(response)}

    async def send_email(
        self,
        to: str,
        subject: str,
        text: str,
        *,
        html: str | None = None,
    ) -> dict[str, Any]:
        recipient = validate_recipient_email(to)
        last_error: Exception | None = None

        for attempt in range(1, _MAX_ATTEMPTS + 1):
            try:
                response = await asyncio.to_thread(
                    self._send_sync, recipient, subject, text, html
                )
                resend_id = response.get("id") if isinstance(response, dict) else str(response)
                logger.info(
                    "Email sent successfully to %s (attempt %s) resend_id=%s resend_response=%s",
                    recipient,
                    attempt,
                    resend_id,
                    response,
                )
                return {"success": True, "recipient": recipient, "response": response}
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Email failed to %s (attempt %s/%s): %s",
                    recipient,
                    attempt,
                    _MAX_ATTEMPTS,
                    exc,
                )
                if attempt < _MAX_ATTEMPTS:
                    await asyncio.sleep(_RETRY_DELAY_SEC * attempt)

        assert last_error is not None
        logger.error(
            "Email failed after %s attempts to %s: %s",
            _MAX_ATTEMPTS,
            recipient,
            last_error,
        )
        return {
            "success": False,
            "recipient": recipient,
            "error": str(last_error),
            "response": None,
        }


email_service = EmailService()
