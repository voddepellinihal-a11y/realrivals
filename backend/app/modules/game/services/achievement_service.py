from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.achievement import Achievement, UserAchievement
from app.models.user import User
from .xp_service import award_xp


# Default achievements to seed
DEFAULT_ACHIEVEMENTS = [
    {"slug": "first_submission", "title": "First Step", "description": "Complete your first challenge", "category": "milestone", "condition_type": "FIRST_SUBMISSION", "condition_value": 1, "xp_reward": 50},
    {"slug": "streak_3", "title": "Getting Started", "description": "Reach a 3-day streak", "category": "streak", "condition_type": "STREAK_X", "condition_value": 3, "xp_reward": 30},
    {"slug": "streak_7", "title": "Week Warrior", "description": "Reach a 7-day streak", "category": "streak", "condition_type": "STREAK_X", "condition_value": 7, "xp_reward": 100},
    {"slug": "streak_30", "title": "Monthly Master", "description": "Reach a 30-day streak", "category": "streak", "condition_type": "STREAK_X", "condition_value": 30, "xp_reward": 500},
    {"slug": "xp_1000", "title": "Rising Star", "description": "Earn 1,000 lifetime XP", "category": "xp", "condition_type": "XP_MILESTONE", "condition_value": 1000, "xp_reward": 100},
    {"slug": "xp_5000", "title": "Champion", "description": "Earn 5,000 lifetime XP", "category": "xp", "condition_type": "XP_MILESTONE", "condition_value": 5000, "xp_reward": 250},
    {"slug": "xp_10000", "title": "Legend", "description": "Earn 10,000 lifetime XP", "category": "xp", "condition_type": "XP_MILESTONE", "condition_value": 10000, "xp_reward": 500},
    {"slug": "routine_master", "title": "Routine Master", "description": "Complete 50 routines", "category": "routine", "condition_type": "ROUTINE_MASTER", "condition_value": 50, "xp_reward": 200},
]


def seed_achievements(db: Session):
    """Seed default achievements if they don't exist."""
    for ach in DEFAULT_ACHIEVEMENTS:
        existing = db.execute(select(Achievement).where(Achievement.slug == ach["slug"])).scalar_one_or_none()
        if existing is None:
            achievement = Achievement(
                slug=ach["slug"],
                title=ach["title"],
                description=ach["description"],
                category=ach["category"],
                condition_type=ach["condition_type"],
                condition_value=ach["condition_value"],
                xp_reward=ach["xp_reward"],
            )
            db.add(achievement)
    db.commit()


def check_and_unlock_achievements(db: Session, user_id, trigger_event: str):
    """Check and unlock achievements for a user based on trigger event."""
    user = db.get(User, user_id)
    if user is None:
        return []

    unlocked = []

    # Get all achievements
    achievements = db.execute(select(Achievement)).scalars().all()

    # Get already unlocked achievement IDs
    unlocked_ids = set(
        db.execute(
            select(UserAchievement.achievement_id).where(UserAchievement.user_id == user_id)
        ).scalars().all()
    )

    for ach in achievements:
        if ach.id in unlocked_ids:
            continue

        should_unlock = False

        if ach.condition_type == "FIRST_SUBMISSION" and trigger_event == "submission_approved":
            # Check if this is the first approved submission
            should_unlock = True  # Simplified — in production, check count

        elif ach.condition_type == "STREAK_X" and trigger_event == "streak_updated":
            if user.current_streak >= ach.condition_value:
                should_unlock = True

        elif ach.condition_type == "XP_MILESTONE" and trigger_event in ("xp_awarded", "submission_approved"):
            if user.lifetime_xp >= ach.condition_value:
                should_unlock = True

        elif ach.condition_type == "ROUTINE_MASTER" and trigger_event == "routine_completed":
            # In production, check routine count
            pass

        if should_unlock:
            ua = UserAchievement(
                user_id=user_id,
                achievement_id=ach.id,
                unlocked_at=datetime.now(timezone.utc),
            )
            db.add(ua)
            db.commit()
            # Award XP for achievement
            if ach.xp_reward > 0:
                award_xp(db, user_id, ach.xp_reward, "ACHIEVEMENT_UNLOCK", str(ach.id))
            unlocked.append({"slug": ach.slug, "title": ach.title, "xp_reward": ach.xp_reward})

    return unlocked
