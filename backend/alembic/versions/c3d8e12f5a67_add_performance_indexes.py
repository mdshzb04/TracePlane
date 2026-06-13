"""add_performance_indexes

Revision ID: c3d8e12f5a67
Revises: b7f2c91d4e03
Create Date: 2026-06-09 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "c3d8e12f5a67"
down_revision: Union[str, None] = "b7f2c91d4e03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_executions_agent_started",
        "executions",
        ["agent_id", "started_at"],
        unique=False,
    )
    op.create_index(
        "ix_executions_agent_status",
        "executions",
        ["agent_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_evaluations_agent_date",
        "evaluations",
        ["agent_id", "evaluation_date"],
        unique=False,
    )
    op.create_index("ix_evaluations_score", "evaluations", ["score"], unique=False)
    op.create_index("ix_audit_logs_created", "audit_logs", ["created_at"], unique=False)
    op.create_index(
        "ix_execution_events_exec_ts",
        "execution_events",
        ["execution_id", "timestamp"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_execution_events_exec_ts", table_name="execution_events")
    op.drop_index("ix_audit_logs_created", table_name="audit_logs")
    op.drop_index("ix_evaluations_score", table_name="evaluations")
    op.drop_index("ix_evaluations_agent_date", table_name="evaluations")
    op.drop_index("ix_executions_agent_status", table_name="executions")
    op.drop_index("ix_executions_agent_started", table_name="executions")
