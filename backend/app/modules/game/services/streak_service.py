from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.streak import Streak


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
