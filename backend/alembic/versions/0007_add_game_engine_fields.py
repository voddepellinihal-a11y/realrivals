"""add game engine fields to users

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-10

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("lifetime_xp", sa.BigInteger(), server_default=sa.text("0"), nullable=False))
    op.add_column("users", sa.Column("season_xp", sa.BigInteger(), server_default=sa.text("0"), nullable=False))
    op.add_column("users", sa.Column("level", sa.Integer(), server_default=sa.text("1"), nullable=False))
    op.add_column("users", sa.Column("current_streak", sa.Integer(), server_default=sa.text("0"), nullable=False))
    op.add_column("users", sa.Column("longest_streak", sa.Integer(), server_default=sa.text("0"), nullable=False))
    op.add_column("users", sa.Column("last_active_date", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "last_active_date")
    op.drop_column("users", "longest_streak")
    op.drop_column("users", "current_streak")
    op.drop_column("users", "level")
    op.drop_column("users", "season_xp")
    op.drop_column("users", "lifetime_xp")
