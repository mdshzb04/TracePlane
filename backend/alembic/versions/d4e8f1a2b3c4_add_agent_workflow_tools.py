"""add_agent_workflow_tools

Revision ID: d4e8f1a2b3c4
Revises: c3d8e12f5a67
Create Date: 2026-06-10 18:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d4e8f1a2b3c4"
down_revision: Union[str, None] = "c3d8e12f5a67"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "agents",
        sa.Column("workflow", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "agents",
        sa.Column("tools", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("agents", "tools")
    op.drop_column("agents", "workflow")
