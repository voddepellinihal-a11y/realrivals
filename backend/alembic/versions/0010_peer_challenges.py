"""add peer challenge fields

Revision ID: 0010
Revises: 0009
Create Date: 2026-11-10

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("challenges", sa.Column("target_user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("challenges", sa.Column("is_daily", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.add_column("challenges", sa.Column("proof_type", sa.String(length=32), server_default=sa.text("'photo'"), nullable=False))
    op.add_column("challenge_assignments", sa.Column("proof_status", sa.String(length=32), server_default=sa.text("'pending'"), nullable=False))


def downgrade() -> None:
    op.drop_column("challenge_assignments", "proof_status")
    op.drop_column("challenges", "proof_type")
    op.drop_column("challenges", "is_daily")
    op.drop_column("challenges", "target_user_id")
