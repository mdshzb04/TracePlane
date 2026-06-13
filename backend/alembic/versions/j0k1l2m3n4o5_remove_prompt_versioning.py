"""Remove prompt versioning tables and execution FK."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "j0k1l2m3n4o5"
down_revision = "i0j1k2l3m4n5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("executions_prompt_version_id_fkey", "executions", type_="foreignkey")
    op.drop_column("executions", "prompt_version_id")
    op.drop_table("prompt_versions")


def downgrade() -> None:
    op.create_table(
        "prompt_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("prompt_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.add_column(
        "executions",
        sa.Column("prompt_version_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "executions_prompt_version_id_fkey",
        "executions",
        "prompt_versions",
        ["prompt_version_id"],
        ["id"],
    )
