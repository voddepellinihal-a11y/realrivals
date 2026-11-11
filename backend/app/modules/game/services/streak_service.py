from datetime import date, datetime, timedelta, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.streak import Streak


def apply_streak_record(
    db: Session,
    user_id,
    group_id=None,
    today: date | None = None,
):
    """Update the group-scoped ``streaks`` row for a user.

    Mirrors :func:`update_streak` (which maintains the aggregate streak on the
    ``users`` row) but for the ``streaks`` table, which is scoped per group.

    * No row yet -> create one with a count of 1.
    * Last qualified yesterday -> the streak continues.
    * Last qualified today -> nothing changes.
    * Anything older -> the streak restarts at 1.
    """
    from app.models.streak import Streak

    today = today or datetime.now(timezone.utc).date()

    streak = db.execute(
        select(Streak).where(Streak.user_id == user_id, Streak.group_id == group_id)
    ).scalar_one_or_none()

    if streak is None:
        streak = Streak(
            id=uuid4(),
            user_id=user_id,
            group_id=group_id,
            current_count=1,
            longest_count=1,
            last_qualified_date=today,
            updated_at=datetime.now(timezone.utc),
        )
        db.add(streak)
        return streak

    if streak.last_qualified_date == today:
        pass  # already counted today
    elif streak.last_qualified_date == today - timedelta(days=1):
        streak.current_count += 1
        if streak.current_count > streak.longest_count:
            streak.longest_count = streak.current_count
    else:
        streak.current_count = 1
    streak.last_qualified_date = today
    streak.updated_at = datetime.now(timezone.utc)
    db.add(streak)
    return streak


def update_streak(db: Session, user_id, user_timezone: str = "UTC") -> dict:
    """Update user streak based on timezone-aware daily activity."""
    user = db.get(User, user_id)
    if user is None:
        return {"error": "user_not_found"}

    try:
        tz = ZoneInfo(user_timezone)
    except Exception:
        tz = ZoneInfo("UTC")

    today = datetime.now(tz).date()

    # Update user aggregate streak fields
    if user.last_active_date is None:
        user.current_streak = 1
        user.longest_streak = max(user.longest_streak, 1)
        user.last_active_date = today
    elif user.last_active_date == today:
        # Already counted today
        pass
    elif user.last_active_date == today - timedelta(days=1):
        user.current_streak += 1
        if user.current_streak > user.longest_streak:
            user.longest_streak = user.current_streak
        user.last_active_date = today
    else:
        # Streak broken
        user.current_streak = 1
        user.last_active_date = today

    db.commit()
    db.refresh(user)

    return {
        "current_streak": user.current_streak,
        "longest_streak": user.longest_streak,
        "last_active_date": str(user.last_active_date),
    }
