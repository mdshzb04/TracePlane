import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel


class Evaluation(BaseModel):
    __tablename__ = "evaluations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    test_case: Mapped[str] = mapped_column(Text, nullable=False)
    expected_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actual_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    evaluation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now
    )

    agent: Mapped["Agent"] = relationship(  # noqa: F821
        "Agent", back_populates="evaluations"
    )

    __table_args__ = (
        {"comment": "Benchmark evaluations for agent performance"},
    )