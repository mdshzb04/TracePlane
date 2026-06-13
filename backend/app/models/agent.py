import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel


class Agent(BaseModel):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    framework: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    environment: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    external_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="sdk")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )
    tags: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True, default=list)
    workflow: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(JSONB, nullable=True, default=list)
    tools: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True, default=list)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    workspace_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    workspace: Mapped[Optional["Workspace"]] = relationship(  # noqa: F821
        "Workspace", back_populates="agents"
    )
    creator: Mapped[Optional["User"]] = relationship(  # noqa: F821
        "User", back_populates="agents", foreign_keys=[created_by]
    )
    executions: Mapped[list["Execution"]] = relationship(  # noqa: F821
        "Execution", back_populates="agent"
    )
    evaluations: Mapped[list["Evaluation"]] = relationship(  # noqa: F821
        "Evaluation", back_populates="agent"
    )

    __table_args__ = (
        {"comment": "Registered AI agents"},
    )

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["tags"] = data.get("tags") or []
        data["workflow"] = data.get("workflow") or []
        data["tools"] = data.get("tools") or []
        return data