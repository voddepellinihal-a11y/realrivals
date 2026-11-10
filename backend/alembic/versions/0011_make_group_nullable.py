"""make group_id nullable for peer challenges

Revision ID: 0011
Revises: 0010
Create Date: 2026-11-10

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("challenges", "group_id", nullable=True)
    op.alter_column("challenge_assignments", "group_id", nullable=True)


def downgrade() -> None:
    op.alter_column("challenge_assignments", "group_id", nullable=False)
    op.alter_column("challenges", "group_id", nullable=False)
