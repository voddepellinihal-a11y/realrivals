from fastapi import APIRouter, Depends, Query

from app.db.session import get_db
from app.modules.auth.router import get_current_user
from app.models.user import User
from .services.level_service import calculate_progress
from .services.leaderboard_service import get_leaderboard
from .services.achievement_service import seed_achievements, check_and_unlock_achievements
from .services.streak_service import update_streak
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter(prefix="/game", tags=["game"])


@router.get("/profile")
def get_profile(user=Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    progress = calculate_progress(user.lifetime_xp)
    return {
        "user_id": str(user.id),
        "username": user.username,
        "gender": user.gender,
        "level": progress["level"],
        "lifetime_xp": user.lifetime_xp,
        "season_xp": user.season_xp,
        "current_level_xp": progress["current_level_xp"],
        "next_level_xp": progress["next_level_xp"],
        "progress_percentage": progress["progress_percentage"],
        # Canonical progression keys — identical maths to the dashboard bar.
        "current_level_min_xp": progress["current_level_min_xp"],
        "xp_in_level": progress["xp_in_level"],
        "level_xp_span": progress["level_xp_span"],
        "progress_percent": progress["progress_percent"],
        "current_streak": user.current_streak,
        "longest_streak": user.longest_streak,
        "last_active_date": str(user.last_active_date) if user.last_active_date else None,
    }


@router.get("/leaderboard")
def get_leaderboard_endpoint(
    scope: str = Query(default="season", pattern="^(season|lifetime)$"),
    limit: int = Query(default=50, ge=1, le=100),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    return get_leaderboard(db, scope=scope, limit=limit)


@router.get("/achievements")
def get_achievements(user=Depends(get_current_user), db: Session = Depends(get_db)) -> list:
    from app.models.achievement import Achievement, UserAchievement

    # Seed achievements if none exist
    seed_achievements(db)

    achievements = db.execute(select(Achievement)).scalars().all()
    unlocked_ids = set(
        db.execute(
            select(UserAchievement.achievement_id).where(UserAchievement.user_id == user.id)
        ).scalars().all()
    )

    result = []
    for ach in achievements:
        result.append({
            "id": str(ach.id),
            "slug": ach.slug,
            "title": ach.title,
            "description": ach.description,
            "icon_url": ach.icon_url,
            "xp_reward": ach.xp_reward,
            "category": ach.category,
            "condition_type": ach.condition_type,
            "condition_value": ach.condition_value,
            "unlocked": ach.id in unlocked_ids,
        })
    return result


@router.get("/history")
def get_xp_history(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    from app.models.xp_transaction import XpTransaction

    txns = (
        db.execute(
            select(XpTransaction)
            .where(XpTransaction.user_id == user.id)
            .order_by(XpTransaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        .scalars()
        .all()
    )

    return [
        {
            "id": str(t.id),
            "amount": t.amount,
            "source_type": t.source_type,
            "source_id": t.source_id,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in txns
    ]
