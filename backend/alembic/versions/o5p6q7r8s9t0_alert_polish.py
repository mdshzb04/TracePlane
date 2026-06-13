"""Alert polish: cooldown, event context, severity."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "o5p6q7r8s9t0"
down_revision: Union[str, None] = "n4o5p6q7r8s9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "alert_rules",
        sa.Column("cooldown_minutes", sa.Integer(), nullable=False, server_default="15"),
    )
    op.add_column("alert_events", sa.Column("severity", sa.String(length=16), nullable=True))
    op.add_column("alert_events", sa.Column("agent_name", sa.String(length=255), nullable=True))
    op.add_column("alert_events", sa.Column("provider", sa.String(length=64), nullable=True))
    op.add_column("alert_events", sa.Column("model", sa.String(length=120), nullable=True))
    op.add_column("alert_events", sa.Column("environment", sa.String(length=64), nullable=True))
    op.add_column(
        "alert_events",
        sa.Column("is_test", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    op.drop_column("alert_events", "is_test")
    op.drop_column("alert_events", "environment")
    op.drop_column("alert_events", "model")
    op.drop_column("alert_events", "provider")
    op.drop_column("alert_events", "agent_name")
    op.drop_column("alert_events", "severity")
    op.drop_column("alert_rules", "cooldown_minutes")
