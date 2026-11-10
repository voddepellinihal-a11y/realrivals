import logging
from datetime import datetime, timedelta, timezone
import uuid

import jwt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.modules.auth import schemas, security
from app.models.auth import AuthSession, EmailVerificationToken, PasswordResetToken
from app.models.user import User, UserPreference

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])
# Alias router so biometric/profile settings are also reachable at PATCH /user/preferences.
user_router = APIRouter(prefix="/user", tags=["user"])

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
# Signing key comes from the environment (Render generates one); the fallback
# in Settings is development-only.
JWT_SECRET_KEY = settings.JWT_SECRET_KEY
JWT_ALGORITHM = settings.JWT_ALGORITHM


def _create_access_token(user_id: uuid.UUID) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def _decode_access_token(token: str) -> uuid.UUID:
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    return uuid.UUID(payload["sub"])


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str, refresh_token_expires_at: datetime) -> None:
    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=int((refresh_token_expires_at - datetime.now(timezone.utc)).total_seconds()),
        path="/",
    )


def _create_session(db: Session, user_id: uuid.UUID) -> AuthSession:
    refresh_token = security.generate_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    session = AuthSession(
        user_id=user_id,
        refresh_token_hash=security.hash_token(refresh_token),
        expires_at=expires_at,
        created_at=datetime.now(timezone.utc),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_current_user(
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        user_id = _decode_access_token(access_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


@router.post("/register")
def register(payload: schemas.RegisterRequest, response: Response, db: Session = Depends(get_db)) -> dict:
    # Registration is disabled for this private instance
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Registration is currently closed; this is a private instance.",
    )


@router.post("/login")
def login(payload: schemas.LoginRequest, response: Response, db: Session = Depends(get_db)) -> dict:
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if user is None or not security.verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.email_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified")

    access_token = _create_access_token(user.id)
    session = _create_session(db, user.id)
    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        "refresh_token",
        security.generate_token(),
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=int((session.expires_at - datetime.now(timezone.utc)).total_seconds()),
        path="/",
    )

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "email_verified": user.email_verified,
            "profile_setup_complete": user.profile_setup_complete,
        }
    }


@router.post("/logout")
def logout(response: Response, refresh_token: str | None = Cookie(default=None), db: Session = Depends(get_db)) -> dict:
    if refresh_token:
        token_hash = security.hash_token(refresh_token)
        session = (
            db.execute(select(AuthSession).where(AuthSession.refresh_token_hash == token_hash))
            .scalars()
            .first()
        )
        if session is not None and session.revoked_at is None:
            session.revoked_at = datetime.now(timezone.utc)
        db.commit()

    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Logged out"}


@router.post("/refresh")
def refresh(response: Response, refresh_token: str | None = Cookie(default=None), db: Session = Depends(get_db)) -> dict:
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")

    token_hash = security.hash_token(refresh_token)
    session = (
        db.execute(select(AuthSession).where(AuthSession.refresh_token_hash == token_hash))
        .scalars()
        .first()
    )
    if session is None or session.revoked_at is not None or session.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    session.revoked_at = datetime.now(timezone.utc)
    db.commit()

    new_session = _create_session(db, session.user_id)
    access_token = _create_access_token(session.user_id)
    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        "refresh_token",
        security.generate_token(),
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=int((new_session.expires_at - datetime.now(timezone.utc)).total_seconds()),
        path="/",
    )

    user = db.get(User, session.user_id)
    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "email_verified": user.email_verified,
            "profile_setup_complete": user.profile_setup_complete,
        }
    }


@router.post("/verify-email")
def verify_email(payload: schemas.VerifyEmailRequest, db: Session = Depends(get_db)) -> dict:
    token_hash = security.hash_token(payload.token)
    token = (
        db.execute(select(EmailVerificationToken).where(EmailVerificationToken.token_hash == token_hash))
        .scalars()
        .first()
    )
    if token is None or token.used_at is not None or token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token")

    user = db.get(User, token.user_id)
    user.email_verified = True
    token.used_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Email verified"}


@router.post("/resend-verification")
def resend_verification(payload: schemas.ResendVerificationRequest, db: Session = Depends(get_db)) -> dict:
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if user is None:
        # Generic response to prevent account enumeration
        return {"message": "If an account exists, a verification email has been sent."}
    if user.email_verified:
        return {"message": "Email already verified"}

    # Generate new verification token
    raw_token = security.generate_token()
    token_hash = security.hash_token(raw_token)
    db.add(
        EmailVerificationToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
    )
    db.commit()

    # Send verification email
    try:
        from app.services.email import send_verification_email
        email_sent = send_verification_email(payload.email, raw_token)
    except Exception as e:
        logger.error("Email service error during resend: %s", type(e).__name__)
        email_sent = False

    if email_sent:
        return {"message": "Verification email sent."}
    else:
        logger.warning("Email not sent for %s — SMTP not configured or delivery failed", payload.email)
        return {
            "message": "Email service not configured — use the token below to verify.",
            "verification_token": raw_token,
        }


@router.post("/forgot-password")
def forgot_password(payload: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)) -> dict:
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if user is None:
        # Generic response to prevent account enumeration
        return {"message": "If an account exists, a password reset email has been sent."}

    # Generate reset token
    raw_token = security.generate_token()
    token_hash = security.hash_token(raw_token)
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
    )
    db.commit()

    # Send password reset email
    try:
        from app.services.email import send_password_reset_email
        email_sent = send_password_reset_email(payload.email, raw_token)
    except Exception as e:
        logger.error("Email service error during password reset: %s", type(e).__name__)
        email_sent = False

    if email_sent:
        return {"message": "Password reset email sent."}
    else:
        logger.warning("Email not sent for %s — SMTP not configured or delivery failed", payload.email)
        return {
            "message": "Password reset email service not configured — use the token below.",
            "reset_token": raw_token,
        }


@router.post("/reset-password")
def reset_password(payload: schemas.ResetPasswordRequest, db: Session = Depends(get_db)) -> dict:
    token_hash = security.hash_token(payload.token)
    token = (
        db.execute(select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash))
        .scalars()
        .first()
    )
    if token is None or token.used_at is not None or token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    user = db.get(User, token.user_id)
    user.password_hash = security.hash_password(payload.password)
    token.used_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Password reset successfully"}


@router.post("/onboarding")
def complete_onboarding(payload: schemas.OnboardingRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    # Check if username is taken by another user
    existing = db.execute(
        select(User).where(User.username == payload.username, User.id != user.id)
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

    # Update user profile
    user.username = payload.username
    user.password_hash = security.hash_password(payload.new_password)
    if payload.avatar_id:
        try:
            user.avatar_id = uuid.UUID(payload.avatar_id)
        except ValueError:
            pass
    user.profile_setup_complete = True
    user.updated_at = datetime.now(timezone.utc)

    # Update user preferences (timezone)
    prefs = db.execute(
        select(UserPreference).where(UserPreference.user_id == user.id)
    ).scalar_one_or_none()
    if prefs is None:
        prefs = UserPreference(
            id=uuid.uuid4(),
            user_id=user.id,
            interests={},
            timezone=payload.timezone,
            notification_preferences={},
        )
        db.add(prefs)
    else:
        prefs.timezone = payload.timezone
        prefs.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(user)

    return {
        "message": "Onboarding complete.",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "email_verified": user.email_verified,
            "profile_setup_complete": user.profile_setup_complete,
        },
    }


@router.post("/logout-all")
def logout_all(response: Response, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    sessions = (
        db.execute(select(AuthSession).where(AuthSession.user_id == user.id, AuthSession.revoked_at == None))
        .scalars()
        .all()
    )
    for session in sessions:
        session.revoked_at = datetime.now(timezone.utc)
    db.commit()
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Logged out all sessions"}


def _get_prefs(db: Session, user_id) -> "UserPreference | None":
    return db.execute(select(UserPreference).where(UserPreference.user_id == user_id)).scalar_one_or_none()


def _compute_bmi(height_cm, weight_kg):
    if height_cm and weight_kg and height_cm > 0:
        return round(weight_kg / ((height_cm / 100) ** 2), 1)
    return None


@router.get("/me")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    prefs = _get_prefs(db, user.id)
    height_cm = prefs.height_cm if prefs else None
    weight_kg = prefs.weight_kg if prefs else None
    target_weight_kg = prefs.target_weight_kg if prefs else None
    timezone = prefs.timezone if prefs else "UTC"

    from app.modules.game.services.level_service import calculate_progress

    progress = calculate_progress(user.lifetime_xp)

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "email_verified": user.email_verified,
            "profile_setup_complete": user.profile_setup_complete,
            "gender": user.gender,
            "avatar_id": str(user.avatar_id) if user.avatar_id else None,
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "target_weight_kg": target_weight_kg,
            "timezone": timezone,
            "bmi": _compute_bmi(height_cm, weight_kg),
            # Game engine state — lets the dashboard render the XP bar without a second call.
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
        }
    }


def _apply_preferences(payload: dict, user: User, db: Session) -> dict:
    prefs = _get_prefs(db, user.id)
    if prefs is None:
        prefs = UserPreference(
            id=uuid.uuid4(),
            user_id=user.id,
            interests={},
            timezone="UTC",
            notification_preferences={},
        )
        db.add(prefs)

    if "timezone" in payload:
        prefs.timezone = payload["timezone"]
    if "height_cm" in payload:
        prefs.height_cm = payload["height_cm"]
    if "weight_kg" in payload:
        prefs.weight_kg = payload["weight_kg"]
    if "target_weight_kg" in payload:
        prefs.target_weight_kg = payload["target_weight_kg"]
    if "interests" in payload:
        prefs.interests = payload["interests"]
    prefs.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "message": "Preferences updated.",
        "preferences": {
            "timezone": prefs.timezone,
            "height_cm": prefs.height_cm,
            "weight_kg": prefs.weight_kg,
            "target_weight_kg": prefs.target_weight_kg,
            "bmi": _compute_bmi(prefs.height_cm, prefs.weight_kg),
        },
    }


@router.patch("/preferences")
def update_preferences(payload: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return _apply_preferences(payload, user, db)


@user_router.patch("/preferences")
def update_user_preferences(payload: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Alias of PATCH /auth/preferences — saves height/weight/target and returns live BMI."""
    return _apply_preferences(payload, user, db)
