from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def get_leaderboard(db: Session, scope: str = "season", limit: int = 50) -> list:
    """Get ranked leaderboard.

    scope: "season" (season_xp) or "lifetime" (lifetime_xp)
    """
    if scope == "lifetime":
        order_col = User.lifetime_xp
    else:
        order_col = User.season_xp

    users = (
        db.execute(
            select(User)
            .where(User.is_active == True)
            .order_by(order_col.desc(), User.created_at.asc())
            .limit(limit)
        )
        .scalars()
        .all()
    )

    result = []
    for rank, user in enumerate(users, start=1):
        xp = user.lifetime_xp if scope == "lifetime" else user.season_xp
        result.append({
            "rank": rank,
            "user_id": str(user.id),
            "username": user.username,
            "level": user.level,
            "xp": xp,
            "streak": user.current_streak,
            "avatar_id": str(user.avatar_id) if user.avatar_id else None,
        })

    return result
