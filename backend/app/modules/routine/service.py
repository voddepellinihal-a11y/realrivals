"""Routine completion logic — the XP engine for daily habits.

Completing a routine awards the routine's XP through the immutable
``xp_transactions`` ledger.  The ledger entry is keyed by
``(user_id, source_type, source_id)`` where ``source_id`` encodes the
routine **and the calendar day**, so the same routine can be re-completed on
a later day but never pays out twice for the same day.
"""

from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.models.routine import Routine
from app.models.user import User
from app.modules.game.services.streak_service import update_streak
from app.modules.game.services.xp_service import award_xp

ROUTINE_XP_SOURCE_TYPE = "ROUTINE_COMPLETE"


def routine_xp_source_id(routine_id, completed_on: date) -> str:
    """Stable ledger key for a routine completion on a given day."""
    return f"{ROUTINE_XP_SOURCE_TYPE}:{routine_id}:{completed_on.isoformat()}"


def apply_completion(
    db: Session,
    user: User,
    routine: Routine,
    completed: bool,
    today: date | None = None,
    user_timezone: str = "UTC",
) -> dict:
    """Mark a routine complete/incomplete and pay out XP for the completion.

    * Completing a routine that was not completed awards ``routine.xp`` once.
    * Completing it again on the same day does not pay out twice.
    * Un-completing a routine never pays XP (and never claws it back).
    * Completing a routine also advances the user's daily streak.
    """
    today = today or datetime.now(timezone.utc).date()
    was_completed = bool(routine.completed)

    routine.completed = completed
    if completed:
        routine.completed_at = datetime.now(timezone.utc)
        routine.last_completed_on = today
    else:
        routine.completed_at = None
        routine.last_completed_on = None
    db.add(routine)

    xp_awarded = 0
    leveled_up = False
    new_level = user.level

    if completed and not was_completed:
        award = award_xp(
            db,
            user.id,
            int(routine.xp or 0),
            ROUTINE_XP_SOURCE_TYPE,
            routine_xp_source_id(routine.id, today),
        )
        if award.get("awarded"):
            xp_awarded = int(award.get("amount") or 0)
            leveled_up = bool(award.get("leveled_up"))
            new_level = award.get("new_level", user.level)

    streak = {"current_streak": user.current_streak, "longest_streak": user.longest_streak}
    if completed and not was_completed:
        streak = update_streak(db, user.id, user_timezone) or streak

    db.commit()

    return {
        "id": str(routine.id),
        "completed": completed,
        "xp_awarded": xp_awarded,
        "leveled_up": leveled_up,
        "level": new_level,
        "current_streak": streak.get("current_streak", 0),
        "longest_streak": streak.get("longest_streak", 0),
    }
