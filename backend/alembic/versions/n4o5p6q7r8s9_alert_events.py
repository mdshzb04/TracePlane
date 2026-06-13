"""Add alert_events table for email delivery audit trail."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "n4o5p6q7r8s9"
down_revision: Union[str, None] = "m3n4o5p6q7r8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "alert_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("workspace_id", sa.UUID(), nullable=False),
        sa.Column("rule_id", sa.UUID(), nullable=False),
        sa.Column("rule_name", sa.String(length=255), nullable=False),
        sa.Column("metric", sa.String(length=64), nullable=False),
        sa.Column("current_value", sa.Float(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("channel_type", sa.String(length=32), nullable=False),
        sa.Column("recipient", sa.String(length=320), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("resend_id", sa.String(length=128), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("resend_response", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["rule_id"], ["alert_rules.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alert_events_workspace_id", "alert_events", ["workspace_id"])
    op.create_index("ix_alert_events_rule_id", "alert_events", ["rule_id"])


def downgrade() -> None:
    op.drop_index("ix_alert_events_rule_id", table_name="alert_events")
    op.drop_index("ix_alert_events_workspace_id", table_name="alert_events")
    op.drop_table("alert_events")
