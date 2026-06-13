import uuid
from typing import Optional

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    provider: Mapped[str] = mapped_column(String(20), nullable=False, default="email")
    github_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True, index=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="viewer"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    workspace_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    agents: Mapped[list["Agent"]] = relationship(  # noqa: F821
        "Agent", back_populates="creator", foreign_keys="[Agent.created_by]"
    )
    organization_memberships: Mapped[list["OrganizationMember"]] = relationship(  # noqa: F821
        "OrganizationMember", back_populates="user"
    )

    @property
    def has_password(self) -> bool:
        return self.password_hash is not None

    @property
    def has_github(self) -> bool:
        return self.github_id is not None

    __table_args__ = (
        {"comment": "Application users"},
    )