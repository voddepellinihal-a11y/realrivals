"""add gender and profile_setup_complete to users

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-10

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("gender", sa.String(length=32), nullable=True))
    op.add_column("users", sa.Column("profile_setup_complete", sa.Boolean(), server_default=sa.text("false"), nullable=False))


def downgrade() -> None:
    op.drop_column("users", "profile_setup_complete")
    op.drop_column("users", "gender")
