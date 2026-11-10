"""routine xp + completion tracking

Adds the columns the dashboard needs so a routine can actually earn XP:
xp, category, completed, completed_at and last_completed_on.

Revision ID: 0015
Revises: 0014
Create Date: 2026-11-10

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "routines",
        sa.Column("xp", sa.Integer(), nullable=False, server_default="25"),
    )
    op.add_column(
        "routines",
        sa.Column("category", sa.String(length=64), nullable=False, server_default="health"),
    )
    op.add_column(
        "routines",
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "routines",
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "routines",
        sa.Column("last_completed_on", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("routines", "last_completed_on")
    op.drop_column("routines", "completed_at")
    op.drop_column("routines", "completed")
    op.drop_column("routines", "category")
    op.drop_column("routines", "xp")
