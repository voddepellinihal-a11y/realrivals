"""Seed private users for Real-Life Rivals.

Creates 2 pre-seeded accounts (1 male, 1 female) if they do not already exist.
Runs automatically on application startup.
"""
import os
import uuid

from sqlalchemy import select

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models.user import User
from app.models.user import User, UserPreference  # noqa: F401
from app.modules.auth.security import hash_password


def seed_private_users():
    """Create the 2 pre-seeded private user accounts if they don't exist."""
    db = SessionLocal()
    try:
        # User 1: Male Account
        user1_email = "rival1@realliferivals.com"
        existing1 = db.execute(select(User).where(User.email == user1_email)).scalar_one_or_none()
        if existing1 is None:
            user1 = User(
                id=uuid.uuid4(),
                username="rival1",
                email=user1_email,
                password_hash=hash_password("Rival1#2027!"),
                email_verified=True,
                gender="Male",
                profile_setup_complete=False,
                is_active=True,
            )
            db.add(user1)
            db.commit()
            db.refresh(user1)
            print(f"Seeded User 1: {user1_email}")
        else:
            print(f"User 1 already exists: {user1_email}")

        # User 2: Female Account
        user2_email = "rival2@realliferivals.com"
        existing2 = db.execute(select(User).where(User.email == user2_email)).scalar_one_or_none()
        if existing2 is None:
            user2 = User(
                id=uuid.uuid4(),
                username="rival2",
                email=user2_email,
                password_hash=hash_password("Rival2#2027!"),
                email_verified=True,
                gender="Female",
                profile_setup_complete=False,
                is_active=True,
            )
            db.add(user2)
            db.commit()
            db.refresh(user2)
            print(f"Seeded User 2: {user2_email}")
        else:
            print(f"User 2 already exists: {user2_email}")

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error seeding users: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_private_users()
    print("Seeding complete.")
