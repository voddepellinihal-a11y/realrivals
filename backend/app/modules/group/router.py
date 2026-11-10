from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from uuid import uuid4
import hashlib
import secrets

from app.db.session import get_db
from app.modules.auth.router import get_current_user
from app.models.group import Group, GroupMember
from app.models.user import User
from app.models.submission import Submission
from app.models.challenge import Challenge, ChallengeAssignment

router = APIRouter(prefix="/groups", tags=["groups"])


def _generate_invite_code() -> str:
    return secrets.token_urlsafe(8)


@router.post("")
def create_group(payload: dict, user=Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    group = Group(
        id=uuid4(),
        name=payload.get("name") or "My Group",
        description=payload.get("description") or "",
        invite_code_hash=hashlib.sha256(_generate_invite_code().encode()).hexdigest(),
        created_by=user.id,
        is_active=True,
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    db.add(GroupMember(group_id=group.id, user_id=user.id, role="admin", status="active"))
    db.commit()
    return {"id": str(group.id), "name": group.name, "invite_code_hash": group.invite_code_hash}


@router.post("/join")
def join_group(payload: dict, user=Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    code = payload.get("invite_code")
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invite_code is required")

    groups = db.execute(select(Group).where(Group.invite_code_hash == hashlib.sha256(code.encode()).hexdigest())).scalars().all()
    group = groups[0] if groups else None
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    existing = db.execute(
        select(GroupMember).where(GroupMember.group_id == group.id, GroupMember.user_id == user.id)
    ).scalar_one_or_none()
    if existing is None:
        db.add(GroupMember(group_id=group.id, user_id=user.id, role="member", status="active"))
        db.commit()
    return {"group_id": str(group.id), "name": group.name, "joined": True}


@router.get("/{group_id}/reviews/pending")
def pending_reviews(group_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    # Check reviewer is an authorized group member
    membership = db.execute(
        select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == user.id)
    ).scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized in this group")

    # Get all pending submissions for challenges in this group
    pending_submissions = (
        db.execute(
            select(Submission, ChallengeAssignment, Challenge)
            .join(ChallengeAssignment, Submission.assignment_id == ChallengeAssignment.id)
            .join(Challenge, ChallengeAssignment.challenge_id == Challenge.id)
            .where(Challenge.group_id == group_id, Submission.status == "submitted")
        )
        .all()
    )

    result = []
    for sub, assignment, challenge in pending_submissions:
        # Skip own submissions
        if sub.user_id == user.id:
            continue
        submitter = db.get(User, sub.user_id)
        result.append({
            "submission_id": str(sub.id),
            "assignment_id": str(sub.assignment_id),
            "challenge_title": challenge.title,
            "submitter_username": submitter.username if submitter else "Unknown",
            "proof_url": sub.proof_url,
            "proof_type": sub.proof_type,
            "description": sub.description,
            "submitted_at": sub.submitted_at.isoformat() if sub.submitted_at else None,
        })
    return result
