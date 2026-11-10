"""widen xp_transactions.source_id to a string

The XP ledger is keyed by (user_id, source_type, source_id).  Submissions use a
submission UUID as the source, but other sources (routine completions keyed by
routine + calendar day, streaks, achievements) need a composite key that is not
a UUID.

Revision ID: 0016
Revises: 0015
Create Date: 2026-11-10

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql

# revision identifiers, used by Alembic.
revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "xp_transactions",
        "source_id",
        type_=sa.String(length=128),
        existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
        postgresql_using="source_id::text",
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM xp_transactions WHERE source_id !~* "
        "'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'"
    )
    op.alter_column(
        "xp_transactions",
        "source_id",
        type_=sa.dialects.postgresql.UUID(as_uuid=True),
        existing_type=sa.String(length=128),
        postgresql_using="source_id::uuid",
    )
