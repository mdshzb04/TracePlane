import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel


class Execution(BaseModel):
    __tablename__ = "executions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    input: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="running"
    )
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    token_usage: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True, default=dict)
    estimated_cost: Mapped[Optional[float]] = mapped_column(Numeric(10, 6), nullable=True, default=0)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    replay_of_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("executions.id", ondelete="SET NULL"), nullable=True
    )
    is_replay: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    agent: Mapped["Agent"] = relationship(  # noqa: F821
        "Agent", back_populates="executions"
    )

    events: Mapped[list["ExecutionEvent"]] = relationship(
        "ExecutionEvent", back_populates="execution", cascade="all, delete-orphan"
    )
    spans: Mapped[list["TraceSpan"]] = relationship(
        "TraceSpan", back_populates="execution", cascade="all, delete-orphan"
    )

    __table_args__ = (
        {"comment": "Agent execution tracking"},
    )