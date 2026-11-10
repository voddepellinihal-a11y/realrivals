import uuid
from datetime import datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Float, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    username: Mapped[str] = mapped_column(String(length=30), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(length=255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    gender: Mapped[str | None] = mapped_column(String(length=32), nullable=True)
    profile_setup_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    avatar_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Game engine fields
    lifetime_xp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    season_xp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    current_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_active_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    interests: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    timezone: Mapped[str] = mapped_column(String(length=64), nullable=False, default="UTC")
    notification_preferences: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # Health metrics
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Avatar(Base):
    __tablename__ = "avatars"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name: Mapped[str] = mapped_column(String(length=64), nullable=False)
    asset_url: Mapped[str] = mapped_column(String(length=512), nullable=False)
    unlock_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


from app.models.achievement import Achievement, UserAchievement  # noqa: F401, F403
from app.models.auth import AuthSession, EmailVerificationToken, PasswordResetToken  # noqa: F401, F403
from app.models.challenge import Challenge, ChallengeAssignment  # noqa: F401, F403
from app.models.group import Group, GroupMember  # noqa: F401, F403
from app.models.routine import Routine  # noqa: F401, F403
from app.models.streak import Streak  # noqa: F401, F403
from app.models.submission import Submission  # noqa: F401, F403
from app.models.verification_review import VerificationReview  # noqa: F401, F403
from app.models.xp_transaction import XpTransaction  # noqa: F401, F403
