"""add_executions_prompt_versions_evaluations

Revision ID: b7f2c91d4e03
Revises: af335969ab64
Create Date: 2026-06-09 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "b7f2c91d4e03"
down_revision: Union[str, None] = "af335969ab64"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "prompt_versions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("agent_id", "version", name="uq_prompt_versions_agent_version"),
    )
    op.create_index("ix_prompt_versions_agent", "prompt_versions", ["agent_id"])
    op.create_index("ix_prompt_versions_current", "prompt_versions", ["agent_id", "is_current"])

    op.create_table(
        "executions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("input", sa.Text, nullable=True),
        sa.Column("output", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column("token_usage", JSONB, nullable=True, server_default="{}"),
        sa.Column("estimated_cost", sa.Numeric(10, 6), nullable=True, server_default="0"),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("prompt_version_id", UUID(as_uuid=True), sa.ForeignKey("prompt_versions.id"), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_executions_agent", "executions", ["agent_id"])
    op.create_index("ix_executions_status", "executions", ["status"])
    op.create_index("ix_executions_started", "executions", ["started_at"])

    op.create_table(
        "execution_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("execution_id", UUID(as_uuid=True), sa.ForeignKey("executions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("event_data", JSONB, nullable=True, server_default="{}"),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_execution_events_exec", "execution_events", ["execution_id"])

    op.create_table(
        "evaluations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("test_case", sa.Text, nullable=False),
        sa.Column("expected_output", sa.Text, nullable=True),
        sa.Column("actual_output", sa.Text, nullable=True),
        sa.Column("score", sa.Numeric(5, 2), nullable=True),
        sa.Column("evaluation_date", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_evaluations_agent", "evaluations", ["agent_id"])


def downgrade() -> None:
    op.drop_table("evaluations")
    op.drop_table("execution_events")
    op.drop_table("executions")
    op.drop_table("prompt_versions")