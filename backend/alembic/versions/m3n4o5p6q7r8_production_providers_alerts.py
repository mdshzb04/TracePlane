"""Production provider connections and alert rules."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "m3n4o5p6q7r8"
down_revision = "l2m3n4o5p6q7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "provider_connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("provider_id", sa.String(50), nullable=False),
        sa.Column("api_key_encrypted", sa.Text(), nullable=False),
        sa.Column("key_hint", sa.String(12), nullable=False, server_default=""),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("workspace_id", "provider_id", name="uq_provider_workspace"),
    )
    op.create_index("ix_provider_connections_workspace_id", "provider_connections", ["workspace_id"])

    op.create_table(
        "alert_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("metric", sa.String(64), nullable=False),
        sa.Column("operator", sa.String(16), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("window_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("channels", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("trigger_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_alert_rules_workspace_id", "alert_rules", ["workspace_id"])


def downgrade() -> None:
    op.drop_table("alert_rules")
    op.drop_table("provider_connections")
