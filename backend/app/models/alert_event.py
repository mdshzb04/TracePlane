import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True
    )
    rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("alert_rules.id"), nullable=False, index=True
    )
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    metric: Mapped[str] = mapped_column(String(64), nullable=False)
    current_value: Mapped[float] = mapped_column(nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    channel_type: Mapped[str] = mapped_column(String(32), nullable=False)
    recipient: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    resend_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resend_response: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    severity: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    agent_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    provider: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    environment: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_test: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
