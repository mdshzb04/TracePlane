import uuid
from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel


class Workspace(BaseModel):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    organization: Mapped[Optional["Organization"]] = relationship(  # noqa: F821
        "Organization", back_populates="workspaces"
    )
    api_keys: Mapped[list["ApiKey"]] = relationship("ApiKey", back_populates="workspace")  # noqa: F821
    agents: Mapped[list["Agent"]] = relationship("Agent", back_populates="workspace")  # noqa: F821
