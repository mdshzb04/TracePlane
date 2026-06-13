"""Remove sandbox workspace columns

Revision ID: g8h9i0j1k2l3
Revises: f7a8b9c0d1e2
Create Date: 2026-06-11

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "g8h9i0j1k2l3"
down_revision: Union[str, None] = "f7a8b9c0d1e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_workspaces_sandbox_expires", table_name="workspaces")
    op.drop_column("users", "is_sandbox")
    op.drop_column("workspaces", "expires_at")
    op.drop_column("workspaces", "is_sandbox")


def downgrade() -> None:
    op.add_column("workspaces", sa.Column("is_sandbox", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("workspaces", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("is_sandbox", sa.Boolean(), nullable=False, server_default="false"))
    op.create_index("ix_workspaces_sandbox_expires", "workspaces", ["is_sandbox", "expires_at"])
