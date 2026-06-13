"""P9 replay, API key stats, prompt hash

Revision ID: b1c2d3e4f5a6
Revises: c3d8e12f5a67
Create Date: 2026-06-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("api_keys", sa.Column("request_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("api_keys", sa.Column("total_cost", sa.Numeric(12, 6), nullable=False, server_default="0"))
    op.add_column("prompt_versions", sa.Column("prompt_hash", sa.String(64), nullable=True))
    op.add_column("executions", sa.Column("replay_of_id", sa.UUID(), nullable=True))
    op.add_column("executions", sa.Column("is_replay", sa.Boolean(), nullable=False, server_default="false"))
    op.create_foreign_key(
        "fk_executions_replay_of_id",
        "executions",
        "executions",
        ["replay_of_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_executions_replay_of_id", "executions", ["replay_of_id"])


def downgrade() -> None:
    op.drop_index("ix_executions_replay_of_id", table_name="executions")
    op.drop_constraint("fk_executions_replay_of_id", "executions", type_="foreignkey")
    op.drop_column("executions", "is_replay")
    op.drop_column("executions", "replay_of_id")
    op.drop_column("prompt_versions", "prompt_hash")
    op.drop_column("api_keys", "total_cost")
    op.drop_column("api_keys", "request_count")
