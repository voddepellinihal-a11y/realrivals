from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime, timezone

from app.db.session import get_db
from app.modules.auth.router import get_current_user
from app.models.challenge import Challenge, ChallengeAssignment
from app.models.user import User
from app.models.xp_transaction import XpTransaction

router = APIRouter(prefix="/challenges", tags=["challenges"])


def _serialize_challenge(c: Challenge, db: Session, user) -> dict:
    """Full representation of a challenge as the dashboard expects it."""
    opponent = db.get(User, c.target_user_id) if c.target_user_id else None
    return {
        "id": str(c.id),
        "title": c.title,
        "description": c.description,
        "category": c.category,
        "difficulty": c.difficulty,
        "base_xp": c.base_xp,
        "proof_type": c.proof_type,
        "proof_required": c.proof_type,
        "challenge_type": c.challenge_type,
        "status": c.status,
        "is_daily": c.is_daily,
        "target_user_id": str(c.target_user_id) if c.target_user_id else None,
        "target_username": opponent.username if opponent else None,
        "created_by_me": c.creator_id == user.id,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


@router.get("")
def list_challenges(user=Depends(get_current_user), db: Session = Depends(get_db)) -> list:
    try:
        from app.models.group import GroupMember

        memberships = db.execute(
            select(GroupMember.group_id).where(GroupMember.user_id == user.id)
        ).scalars().all()
        group_ids = list(memberships or [])

        query = select(Challenge).where(
            or_(
                Challenge.creator_id == user.id,
                Challenge.target_user_id == user.id,
                Challenge.group_id.in_(group_ids) if group_ids else False,
            )
        ).order_by(Challenge.created_at.desc())

        items = db.execute(query).scalars().all()
        return [_serialize_challenge(c, db, user) for c in items]
    except Exception:
        return []


@router.post("")
def create_challenge(payload: dict, user=Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    challenge = Challenge(
        id=uuid4(),
        creator_id=user.id,
        group_id=payload.get("group_id"),
        title=payload.get("title") or "New Challenge",
        description=payload.get("description") or "",
        category=payload.get("category") or "productivity",
        difficulty=payload.get("difficulty") or "medium",
        base_xp=payload.get("base_xp") or 50,
        challenge_type=payload.get("challenge_type") or "GROUP_OPEN",
        source_type=payload.get("source_type") or "ADMIN",
        is_daily=payload.get("is_daily", False),
        proof_type=payload.get("proof_type") or "photo",
        status="ACTIVE",
        created_at=datetime.now(timezone.utc),
    )
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    return _serialize_challenge(challenge, db, user)


@router.post("/direct")
def create_direct_challenge(payload: dict, user=Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    target_identifier = payload.get("target_username_or_id")
    if not target_identifier:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="target_username_or_id is required")

    # Resolve target user by username or user_id
    target_user = None
    try:
        # Try UUID parse first
        import uuid as _uuid
        target_id = _uuid.UUID(target_identifier)
        target_user = db.get(User, target_id)
    except (ValueError, Exception):
        target_user = db.execute(select(User).where(User.username == target_identifier)).scalar_one_or_none()
    if target_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found")

    if target_user.id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot challenge yourself")

    challenge = Challenge(
        id=uuid4(),
        creator_id=user.id,
        group_id=None,
        title=payload.get("title") or "Rival vs Rival Challenge",
        description=payload.get("description") or "",
        category=payload.get("category") or "productivity",
        difficulty=payload.get("difficulty") or "medium",
        base_xp=payload.get("xp_reward") or 50,
        challenge_type="DIRECT_VS",
        target_user_id=target_user.id,
        proof_type=payload.get("proof_type") or "photo",
        source_type="FRIEND",
        status="PENDING_ACCEPTANCE",
        created_at=datetime.now(timezone.utc),
    )
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    return {
        **_serialize_challenge(challenge, db, user),
        "challenge_type": challenge.challenge_type,
        "target_username": target_user.username,
        "xp_reward": challenge.base_xp,
    }


@router.post("/{id}/accept")
def accept_direct_challenge(id: str, user=Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    challenge = db.get(Challenge, id)
    if challenge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")
    if challenge.challenge_type != "DIRECT_VS":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a direct challenge")
    if challenge.target_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the target of this challenge")
    if challenge.status != "PENDING_ACCEPTANCE":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Challenge is not pending acceptance")

    challenge.status = "ACTIVE"
    db.add(
        ChallengeAssignment(
            id=uuid4(),
            challenge_id=challenge.id,
            user_id=user.id,
            group_id=None,
            status="accepted",
            assigned_at=datetime.now(timezone.utc),
        )
    )
    db.add(
        ChallengeAssignment(
            id=uuid4(),
            challenge_id=challenge.id,
            user_id=challenge.creator_id,
            group_id=None,
            status="in_progress",
            assigned_at=datetime.now(timezone.utc),
        )
    )
    db.commit()
    return {"id": str(challenge.id), "status": challenge.status}


@router.post("/{id}/decline")
def decline_direct_challenge(id: str, user=Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    challenge = db.get(Challenge, id)
    if challenge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")
    if challenge.challenge_type != "DIRECT_VS":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a direct challenge")
    if challenge.target_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the target of this challenge")
    if challenge.status != "PENDING_ACCEPTANCE":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Challenge is not pending acceptance")

    challenge.status = "DECLINED"
    db.commit()
    return {"id": str(challenge.id), "status": challenge.status}


@router.get("/versus")
def versus_challenges(user=Depends(get_current_user), db: Session = Depends(get_db)) -> list:
    challenges = (
        db.execute(
            select(Challenge)
            .where(
                Challenge.challenge_type == "DIRECT_VS",
                or_(Challenge.creator_id == user.id, Challenge.target_user_id == user.id),
            )
            .order_by(Challenge.created_at.desc())
        )
        .scalars()
        .all()
    )

    result = []
    for c in challenges:
        opponent = db.get(User, c.target_user_id if c.creator_id == user.id else c.creator_id)
        result.append({
            "id": str(c.id),
            "title": c.title,
            "description": c.description,
            "category": c.category,
            "xp_reward": c.base_xp,
            "proof_type": c.proof_type,
            "status": c.status,
            "is_challenger": c.creator_id == user.id,
            "opponent_id": str(opponent.id) if opponent else None,
            "opponent_username": opponent.username if opponent else "Unknown",
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
    return result


@router.patch("/{id}")
def update_challenge(id: str, payload: dict, user=Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Edit a challenge the current user created."""
    from app.modules.challenge.service import apply_edits, assert_can_edit

    challenge = db.get(Challenge, id)
    assert_can_edit(user, challenge)

    apply_edits(challenge, payload or {})
    db.commit()
    db.refresh(challenge)

    return {
        "id": str(challenge.id),
        "title": challenge.title,
        "description": challenge.description,
        "category": challenge.category,
        "difficulty": challenge.difficulty,
        "base_xp": challenge.base_xp,
        "proof_type": challenge.proof_type,
        "status": challenge.status,
        "challenge_type": challenge.challenge_type,
    }


@router.delete("/{id}")
def delete_challenge(id: str, user=Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Remove a challenge the current user created."""
    from app.modules.challenge.service import assert_can_delete, delete_challenge as _delete

    challenge = db.get(Challenge, id)
    assert_can_delete(user, challenge)
    _delete(db, challenge)
    return {"id": str(id), "deleted": True}


@router.post("/{id}/publish")
def publish_challenge(id: str, user=Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    challenge = db.get(Challenge, id)
    if challenge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")
    challenge.status = "ACTIVE"
    challenge.published_at = datetime.now(timezone.utc)
    db.commit()
    return {"id": str(challenge.id), "status": challenge.status}


@router.post("/{id}/assignments")
def assign_challenge(id: str, payload: dict, user=Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    challenge = db.get(Challenge, id)
    if challenge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")
    user_ids = payload.get("user_ids") or []
    now = datetime.now(timezone.utc)
    for uid in user_ids:
        db.add(
            ChallengeAssignment(
                id=uuid4(),
                challenge_id=challenge.id,
                user_id=uid,
                group_id=challenge.group_id,
                due_at=now,
                status="pending",
                assigned_at=now,
            )
        )
    db.commit()
    return {"assigned": len(user_ids or [])}
