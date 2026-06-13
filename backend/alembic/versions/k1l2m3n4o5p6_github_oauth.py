"""Add GitHub OAuth fields to users."""

from alembic import op
import sqlalchemy as sa

revision = "k1l2m3n4o5p6"
down_revision = "j0k1l2m3n4o5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("provider", sa.String(20), nullable=False, server_default="email"),
    )
    op.add_column("users", sa.Column("github_id", sa.String(64), nullable=True))
    op.add_column("users", sa.Column("avatar_url", sa.String(512), nullable=True))
    op.alter_column("users", "password_hash", existing_type=sa.String(255), nullable=True)
    op.create_index("ix_users_github_id", "users", ["github_id"], unique=True)
    op.execute("UPDATE users SET provider = 'email' WHERE provider IS NULL")


def downgrade() -> None:
    op.execute("UPDATE users SET password_hash = '' WHERE password_hash IS NULL")
    op.alter_column("users", "password_hash", existing_type=sa.String(255), nullable=False)
    op.drop_index("ix_users_github_id", table_name="users")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "github_id")
    op.drop_column("users", "provider")
