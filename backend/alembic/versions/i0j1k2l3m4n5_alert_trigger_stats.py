"""Add alert rule trigger stats."""

from alembic import op
import sqlalchemy as sa

revision = "i0j1k2l3m4n5"
down_revision = "g8h9i0j1k2l3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("alert_rules", sa.Column("trigger_count", sa.Integer(), server_default="0", nullable=False))
    op.add_column("alert_rules", sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("alert_rules", "last_triggered_at")
    op.drop_column("alert_rules", "trigger_count")
