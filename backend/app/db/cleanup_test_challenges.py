"""One-off cleanup: remove the seeded/test challenges (burpees, push-ups, etc.).

Usage:  python -m app.db.cleanup_test_challenges
"""
import sys

from app.db.session import SessionLocal
from app.modules.challenge.service import delete_challenge
from app.models.challenge import Challenge
from app.models.user import User
from sqlalchemy import select

# Title fragments of the placeholder / test challenges to remove.
TITLES_TO_REMOVE = (
    "burpee",
    "push-up",
    "pushup",
    "push up",
    "10 min physical activity",
    # artifacts created by the verification script / UI tests
    "evening focus sprint",
    "disposable challenge",
    "editable challenge",
    "temp ui routine",
    "morning sunlight walk",
    "sunrise walk",
    "evening 5k run",
)


def matches(title: str) -> bool:
    low = (title or "").lower()
    return any(fragment in low for fragment in TITLES_TO_REMOVE)


def cleanup() -> int:
    db = SessionLocal()
    removed = 0
    try:
        rows = db.execute(select(Challenge)).scalars().all()
        for c in rows:
            if not matches(c.title):
                continue

            creator = db.get(User, c.creator_id)
            title = c.title
            delete_challenge(db, c)
            removed += 1
            print(
                f"Removed challenge {c.id} '{title}' "
                f"(created by {creator.username if creator else '?'})"
            )

        print(f"\n{removed} challenge(s) removed.")
        return removed
    except Exception as e:
        db.rollback()
        print(f"Cleanup failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    cleanup()
    sys.exit(0)
