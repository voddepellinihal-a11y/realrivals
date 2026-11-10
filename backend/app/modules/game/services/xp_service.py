from datetime import datetime, timezone
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.xp_transaction import XpTransaction
from .level_service import calculate_level, calculate_progress


def award_xp(db: Session, user_id, amount: int, source_type: str, source_id) -> dict:
    """Award XP to a user idempotently.

    Checks if an XP transaction with the same (user_id, source_type, source_id) already exists.
    If so, returns the existing transaction without re-awarding.
    Otherwise, creates a new transaction and updates user XP/level.
    """
    # ``source_id`` may be a UUID (submission) or a composite string (routine + day).
    source_id = str(source_id)

    # Check for existing transaction (idempotency)
    existing = db.execute(
        select(XpTransaction).where(
            XpTransaction.user_id == user_id,
            XpTransaction.source_type == source_type,
            XpTransaction.source_id == source_id,
        )
    ).scalar_one_or_none()

    if existing is not None:
        return {
            "awarded": False,
            "reason": "already_awarded",
            "transaction_id": str(existing.id),
            "amount": existing.amount,
        }

    # Lock user record for update
    user = db.get(User, user_id)
    if user is None:
        return {"awarded": False, "reason": "user_not_found"}

    old_level = user.level

    # Create XP transaction
    txn = XpTransaction(
        id=uuid.uuid4(),
        user_id=user_id,
        amount=amount,
        source_type=source_type,
        source_id=source_id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(txn)

    # Update user XP
    user.lifetime_xp += amount
    user.season_xp += amount

    # Recalculate level
    new_level = calculate_level(user.lifetime_xp)
    leveled_up = new_level > old_level
    user.level = new_level

    db.commit()
    db.refresh(user)

    return {
        "awarded": True,
        "amount": amount,
        "transaction_id": str(txn.id),
        "old_level": old_level,
        "new_level": new_level,
        "leveled_up": leveled_up,
        "lifetime_xp": user.lifetime_xp,
        "season_xp": user.season_xp,
    }
