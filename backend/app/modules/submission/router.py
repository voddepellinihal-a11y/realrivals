import base64
import datetime
import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.router import get_current_user
from app.models.challenge import Challenge, ChallengeAssignment
from app.models.group import GroupMember
from app.models.submission import Submission
from app.models.user import User
from app.models.verification_review import VerificationReview
from app.models.xp_transaction import XpTransaction
from app.models.streak import Streak

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.post("")
def create_submission(payload: dict, user=Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    assignment_id = payload.get("assignment_id")
    proof_type = payload.get("proof_type") or "photo"
    proof_text = payload.get("proof_text")
    proof_url = payload.get("proof_url") or payload.get("proof_data_url")
    description = payload.get("description") or ""

    if not assignment_id:
        # If no assignment, try to find the user's assignment for the given challenge
        challenge_id = payload.get("challenge_id")
        if challenge_id:
            assignment = db.execute(
                select(ChallengeAssignment).where(
                    ChallengeAssignment.challenge_id == challenge_id,
                    ChallengeAssignment.user_id == user.id,
                )
            ).scalars().first()
            if assignment:
                assignment_id = str(assignment.id)
        if not assignment_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="assignment_id is required")

    # Validate proof content based on type
    if proof_type == "text":
        if not proof_text:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="proof_text is required for text proof")
        stored_proof_url = None
    elif proof_type in ("photo", "link"):
        if not proof_url:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="proof_url is required for photo/link proof")
        stored_proof_url = proof_url
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid proof_type. Use photo, text, or link")

    # If it's a data URL (base64), store it directly in proof_text/url? We'll keep it in proof_url as a data URL string.
    submission = Submission(
        id=uuid.uuid4(),
        assignment_id=assignment_id,
        user_id=user.id,
        attempt_number=1,
        proof_url=stored_proof_url or "",
        proof_type=proof_type,
        proof_text=proof_text,
        description=description,
        status="PENDING_REVIEW",
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return {
        "id": str(submission.id),
        "assignment_id": str(submission.assignment_id),
        "status": submission.status,
        "proof_type": submission.proof_type,
        "engagement": "proof_submitted",
    }


@router.post("/upload-url")
def create_upload_url(payload: dict, user=Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    assignment_id = payload.get("assignment_id")
    if not assignment_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="assignment_id is required")

    submission = Submission(
        id=uuid.uuid4(),
        assignment_id=assignment_id,
        user_id=user.id,
        attempt_number=1,
        proof_url="",
        proof_type="photo",
        description=payload.get("description") or "",
        status="PENDING_REVIEW",
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return {
        "submission_id": str(submission.id),
        "upload_url": f"/api/objects/{submission.id}",
        "proof_url": submission.proof_url,
    }


@router.post("/{submission_id}")
def submit_proof(submission_id: str, payload: dict, user=Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    submission = db.get(Submission, submission_id)
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    if submission.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your submission")
    submission.proof_text = payload.get("proof_text") or submission.proof_text
    submission.proof_url = payload.get("proof_url") or submission.proof_url
    submission.status = "PENDING_REVIEW"
    submission.submitted_at = datetime.now(timezone.utc)
    db.commit()
    return {"id": str(submission.id), "status": submission.status}


@router.get("/{submission_id}")
def get_submission(submission_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    submission = db.get(Submission, submission_id)
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    assignment = db.get(ChallengeAssignment, submission.assignment_id)
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Assignment not found")

    is_participant = (assignment.user_id == user.id) or (challenge_participant(db, user.id, assignment.challenge_id) and submission.user_id == user.id)
    is_rival_view = challenge_participant(db, user.id, assignment.challenge_id) and submission.user_id != user.id
    if not (is_participant or is_rival_view):
        # also allow if user is in the same group
        if not in_group(db, user.id, assignment.group_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this submission")

    return {
        "id": str(submission.id),
        "challenge_id": str(assignment.challenge_id),
        "assignment_id": str(submission.assignment_id),
        "user_id": str(submission.user_id),
        "username": submission_username(db, submission.user_id),
        "attempt_number": submission.attempt_number,
        "proof_url": submission.proof_url,
        "proof_text": submission.proof_text,
        "proof_type": submission.proof_type,
        "description": submission.description,
        "status": submission.status,
        "submitted_at": submission.submitted_at.isoformat() if submission.submitted_at else None,
    }


def challenge_participant(db: Session, user_id, challenge_id) -> bool:
    challenge = db.get(Challenge, challenge_id)
    if challenge is None:
        return False
    if challenge.challenge_type == "DIRECT_VS":
        return challenge.creator_id == user_id or challenge.target_user_id == user_id
    assignment = db.execute(
        select(ChallengeAssignment).where(ChallengeAssignment.challenge_id == challenge_id, ChallengeAssignment.user_id == user_id)
    ).scalar_one_or_none()
    return assignment is not None


def in_group(db: Session, user_id, group_id) -> bool:
    if not group_id:
        return False
    membership = db.execute(
        select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
    ).scalar_one_or_none()
    return membership is not None


def submission_username(db: Session, user_id) -> str | None:
    u = db.get(User, user_id)
    return u.username if u else None


@router.get("/challenge/{challenge_id}/submissions")
def list_challenge_submissions(challenge_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)) -> list:
    challenge = db.get(Challenge, challenge_id)
    if challenge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")

    # Only participants (direct rivals or group members) can view
    is_participant = (
        challenge.challenge_type == "DIRECT_VS" and (challenge.creator_id == user.id or challenge.target_user_id == user.id)
    ) or in_group(db, user.id, challenge.group_id) or challenge_participant(db, user.id, challenge_id)
    if not is_participant:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view submissions for this challenge")

    submissions = (
        db.execute(
            select(Submission)
            .join(ChallengeAssignment, Submission.assignment_id == ChallengeAssignment.id)
            .where(ChallengeAssignment.challenge_id == challenge_id)
            .order_by(Submission.submitted_at.desc())
        )
        .scalars()
        .all()
    )

    result = []
    for sub in submissions:
        uname = submission_username(db, sub.user_id)
        result.append({
            "id": str(sub.id),
            "challenge_id": challenge_id,
            "user_id": str(sub.user_id),
            "username": uname,
            "proof_url": sub.proof_url,
            "proof_text": sub.proof_text,
            "proof_type": sub.proof_type,
            "description": sub.description,
            "status": sub.status,
            "submitted_at": sub.submitted_at.isoformat() if sub.submitted_at else None,
            "is_me": sub.user_id == user.id,
        })
    return result


@router.post("/{submission_id}/reviews")
def review_submission(submission_id: str, payload: dict, user=Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    submission = db.get(Submission, submission_id)
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    assignment = db.get(ChallengeAssignment, submission.assignment_id)
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    challenge = db.get(Challenge, assignment.challenge_id)

    # Users cannot review their own submissions
    if submission.user_id == user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot review your own submission")

    # Check reviewer is an authorized participant (group member or direct rival)
    is_authorized = challenge_participant(db, user.id, assignment.challenge_id) or in_group(db, user.id, assignment.group_id)
    if not is_authorized:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to review this submission")

    # Check if already reviewed
    existing_review = db.execute(
        select(VerificationReview).where(VerificationReview.submission_id == submission.id)
    ).scalar_one_or_none()
    if existing_review is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Submission already reviewed")

    decision = payload.get("decision")
    if decision not in ("approved", "rejected"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Decision must be 'approved' or 'rejected'")

    comments = payload.get("comments") or ""

    review = VerificationReview(
        id=uuid.uuid4(),
        submission_id=submission.id,
        reviewer_id=user.id,
        decision=decision,
        comments=comments,
        reviewed_at=datetime.now(timezone.utc),
    )
    db.add(review)
    submission.status = decision

    xp_awarded = 0
    if decision == "approved":
        existing_xp = db.execute(
            select(XpTransaction).where(
                XpTransaction.user_id == submission.user_id,
                XpTransaction.source_type == "SUBMISSION_APPROVE",
                XpTransaction.source_id == str(submission.id),
            )
        ).scalar_one_or_none()

        if existing_xp is None:
            base_xp = challenge.base_xp if challenge else 50
            xp_txn = XpTransaction(
                id=uuid.uuid4(),
                user_id=submission.user_id,
                amount=base_xp,
                source_type="SUBMISSION_APPROVE",
                source_id=str(submission.id),
                created_at=datetime.now(timezone.utc),
            )
            db.add(xp_txn)
            xp_awarded = base_xp

            # Update user's lifetime/season XP and level
            submitter = db.get(User, submission.user_id)
            if submitter is not None:
                submitter.lifetime_xp = (submitter.lifetime_xp or 0) + base_xp
                submitter.season_xp = (submitter.season_xp or 0) + base_xp
                # Recalculate level
                from app.modules.game.services.level_service import calculate_level
                submitter.level = calculate_level(submitter.lifetime_xp)

            assignment.status = "completed"
            assignment.completed_at = datetime.now(timezone.utc)

            streak = db.execute(
                select(Streak).where(Streak.user_id == submission.user_id, Streak.group_id == assignment.group_id)
            ).scalar_one_or_none()
            today = datetime.now(timezone.utc).date()
            if streak is None:
                streak = Streak(
                    id=uuid.uuid4(),
                    user_id=submission.user_id,
                    group_id=assignment.group_id,
                    current_count=1,
                    longest_count=1,
                    last_qualified_date=today,
                    updated_at=datetime.now(timezone.utc),
                )
                db.add(streak)
            else:
                from datetime import timedelta
                if streak.last_qualified_date == today - timedelta(days=1):
                    streak.current_count += 1
                    if streak.current_count > streak.longest_streak:
                        streak.longest_streak = streak.current_count
                elif streak.last_qualified_date != today:
                    streak.current_count = 1
                streak.last_qualified_date = today
                streak.updated_at = datetime.now(timezone.utc)

    db.commit()
    return {
        "review_id": str(review.id),
        "submission_id": str(submission.id),
        "decision": decision,
        "comments": comments,
        "xp_awarded": xp_awarded,
    }
