import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    slug: Mapped[str] = mapped_column(String(length=64), unique=True, nullable=False, default="")
    name: Mapped[str] = mapped_column(String(length=128), nullable=False, default="")
    title: Mapped[str] = mapped_column(String(length=128), nullable=False, default="")
    description: Mapped[str] = mapped_column(String(length=512), nullable=False, default="")
    icon_url: Mapped[str] = mapped_column(String(length=512), nullable=False, default="")
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    category: Mapped[str] = mapped_column(String(length=64), nullable=False, default="general")
    condition_type: Mapped[str] = mapped_column(String(length=64), nullable=False, default="none")
    condition_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    condition_config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    asset_url: Mapped[str] = mapped_column(String(length=512), nullable=False, default="")


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    achievement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("achievements.id"), nullable=False)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),
    )
