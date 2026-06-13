import logging
import uuid
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.repositories.audit_log import AuditLogRepository

logger = logging.getLogger(__name__)


class AuditService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.audit_repo = AuditLogRepository(session)

    async def log(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> AuditLog:
        entry = AuditLog(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            details=details or {},
        )
        entry = await self.audit_repo.create(entry)
        logger.info(
            "Audit: %s on %s/%s by %s",
            action,
            resource_type,
            resource_id,
            user_id,
        )
        return entry