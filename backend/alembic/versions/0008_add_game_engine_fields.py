"""add game engine fields and achievement columns

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-10

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Achievement new columns
    op.add_column("achievements", sa.Column("slug", sa.String(length=64), nullable=True))
    op.add_column("achievements", sa.Column("title", sa.String(length=128), nullable=True))
    op.add_column("achievements", sa.Column("icon_url", sa.String(length=512), nullable=True))
    op.add_column("achievements", sa.Column("category", sa.String(length=64), server_default=sa.text("'general'"), nullable=True))
    op.add_column("achievements", sa.Column("condition_type", sa.String(length=64), server_default=sa.text("'none'"), nullable=True))
    op.add_column("achievements", sa.Column("condition_value", sa.Integer(), server_default=sa.text("0"), nullable=True))


def downgrade() -> None:
    op.drop_column("achievements", "condition_value")
    op.drop_column("achievements", "condition_type")
    op.drop_column("achievements", "category")
    op.drop_column("achievements", "icon_url")
    op.drop_column("achievements", "title")
    op.drop_column("achievements", "slug")
