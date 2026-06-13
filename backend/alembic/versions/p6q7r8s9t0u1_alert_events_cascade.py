"""Cascade delete alert_events when alert_rules are removed."""

from typing import Sequence, Union

from alembic import op

revision: str = "p6q7r8s9t0u1"
down_revision: Union[str, None] = "o5p6q7r8s9t0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("alert_events_rule_id_fkey", "alert_events", type_="foreignkey")
    op.create_foreign_key(
        "alert_events_rule_id_fkey",
        "alert_events",
        "alert_rules",
        ["rule_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("alert_events_rule_id_fkey", "alert_events", type_="foreignkey")
    op.create_foreign_key(
        "alert_events_rule_id_fkey",
        "alert_events",
        "alert_rules",
        ["rule_id"],
        ["id"],
    )
