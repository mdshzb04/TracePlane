import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel


class TraceSpan(BaseModel):
    __tablename__ = "trace_spans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("executions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_span_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trace_spans.id", ondelete="CASCADE"), nullable=True, index=True
    )
    external_span_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    span_type: Mapped[str] = mapped_column(String(30), nullable=False, default="custom")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="success")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    attributes: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True, default=dict)
    token_usage: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True, default=dict)
    estimated_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 6), nullable=True)

    execution: Mapped["Execution"] = relationship("Execution", back_populates="spans")  # noqa: F821
    parent: Mapped[Optional["TraceSpan"]] = relationship(
        "TraceSpan", remote_side="TraceSpan.id", back_populates="children"
    )
    children: Mapped[list["TraceSpan"]] = relationship("TraceSpan", back_populates="parent")
