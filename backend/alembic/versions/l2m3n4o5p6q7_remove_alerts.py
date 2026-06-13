"""Remove alert_rules table."""

from alembic import op

revision = "l2m3n4o5p6q7"
down_revision = "k1l2m3n4o5p6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("alert_rules")


def downgrade() -> None:
    import sqlalchemy as sa
    from sqlalchemy.dialects import postgresql

    op.create_table(
        "alert_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("metric", sa.String(50), nullable=False),
        sa.Column("operator", sa.String(10), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("window_minutes", sa.Integer(), server_default="60", nullable=False),
        sa.Column("channels", postgresql.JSONB(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("trigger_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_alert_rules_workspace_id", "alert_rules", ["workspace_id"])
