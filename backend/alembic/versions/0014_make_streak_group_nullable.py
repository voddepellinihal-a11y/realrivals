"""make streaks.group_id nullable

Revision ID: 0014
Revises: 0013
Create Date: 2026-11-10

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("streaks", "group_id", nullable=True)


def downgrade() -> None:
    op.alter_column("streaks", "group_id", nullable=False)
