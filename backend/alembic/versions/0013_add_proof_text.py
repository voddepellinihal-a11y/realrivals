"""add proof_text to submissions

Revision ID: 0013
Revises: 0012
Create Date: 2026-11-10

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("submissions", sa.Column("proof_text", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("submissions", "proof_text")
