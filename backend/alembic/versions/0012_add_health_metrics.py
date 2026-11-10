"""add health metrics to user_preferences

Revision ID: 0012
Revises: 0011
Create Date: 2026-11-10

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_preferences", sa.Column("height_cm", sa.Float(), nullable=True))
    op.add_column("user_preferences", sa.Column("weight_kg", sa.Float(), nullable=True))
    op.add_column("user_preferences", sa.Column("target_weight_kg", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("user_preferences", "target_weight_kg")
    op.drop_column("user_preferences", "weight_kg")
    op.drop_column("user_preferences", "height_cm")
