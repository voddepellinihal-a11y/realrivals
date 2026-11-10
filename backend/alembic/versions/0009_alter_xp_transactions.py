"""alter xp_transactions for game engine

Revision ID: 0009
Revises: 0008
Create Date: 2026-11-10

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename columns
    op.alter_column("xp_transactions", "points", new_column_name="amount")
    op.alter_column("xp_transactions", "transaction_type", new_column_name="source_type")
    op.alter_column("xp_transactions", "submission_id", new_column_name="source_id")

    # Drop old unique constraint and column
    op.drop_constraint("xp_transactions_idempotency_key_key", "xp_transactions", type_="unique")
    op.drop_column("xp_transactions", "idempotency_key")

    # Add new unique constraint
    op.create_unique_constraint("uq_xp_transaction_source", "xp_transactions", ["user_id", "source_type", "source_id"])


def downgrade() -> None:
    op.drop_constraint("uq_xp_transaction_source", "xp_transactions", type_="unique")
    op.add_column("xp_transactions", sa.Column("idempotency_key", sa.String(length=128), nullable=True))
    op.create_unique_constraint("xp_transactions_idempotency_key_key", "xp_transactions", ["idempotency_key"])
    op.alter_column("xp_transactions", "source_id", new_column_name="submission_id")
    op.alter_column("xp_transactions", "source_type", new_column_name="transaction_type")
    op.alter_column("xp_transactions", "amount", new_column_name="points")
