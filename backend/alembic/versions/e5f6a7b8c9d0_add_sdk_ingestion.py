"""add_sdk_ingestion

Revision ID: e5f6a7b8c9d0
Revises: d4e8f1a2b3c4
Create Date: 2026-06-10 20:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e8f1a2b3c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workspaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.add_column("users", sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_users_workspace_id", "users", "workspaces", ["workspace_id"], ["id"])

    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("key_hash", sa.String(64), nullable=False),
        sa.Column("key_prefix", sa.String(12), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"], unique=True)
    op.create_index("ix_api_keys_workspace_id", "api_keys", ["workspace_id"])

    op.add_column("agents", sa.Column("framework", sa.String(50), nullable=True))
    op.add_column("agents", sa.Column("environment", sa.String(50), nullable=True))
    op.add_column("agents", sa.Column("provider", sa.String(50), nullable=True))
    op.add_column("agents", sa.Column("external_name", sa.String(255), nullable=True))
    op.add_column("agents", sa.Column("source", sa.String(30), nullable=False, server_default="sdk"))
    op.add_column("agents", sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("agents", sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_agents_workspace_id", "agents", "workspaces", ["workspace_id"], ["id"])
    op.create_index(
        "ix_agents_workspace_external_name",
        "agents",
        ["workspace_id", "external_name"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_agents_workspace_external_name", table_name="agents")
    op.drop_constraint("fk_agents_workspace_id", "agents", type_="foreignkey")
    op.drop_column("agents", "workspace_id")
    op.drop_column("agents", "last_seen_at")
    op.drop_column("agents", "source")
    op.drop_column("agents", "external_name")
    op.drop_column("agents", "provider")
    op.drop_column("agents", "environment")
    op.drop_column("agents", "framework")
    op.drop_index("ix_api_keys_workspace_id", table_name="api_keys")
    op.drop_index("ix_api_keys_key_hash", table_name="api_keys")
    op.drop_table("api_keys")
    op.drop_constraint("fk_users_workspace_id", "users", type_="foreignkey")
    op.drop_column("users", "workspace_id")
    op.drop_table("workspaces")
