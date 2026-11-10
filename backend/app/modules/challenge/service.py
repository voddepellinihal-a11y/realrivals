"""Challenge ownership, editing and removal helpers."""

from fastapi import HTTPException, status
from sqlalchemy import select

PROOF_TYPES = ("photo", "text", "link")
MAX_BASE_XP = 100000
MAX_TITLE = 128
MAX_DESCRIPTION = 1024


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")


def _forbidden() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can only change challenges you created",
    )


def assert_can_edit(user, challenge) -> None:
    """Only the creator of a challenge may edit it."""
    if challenge is None:
        raise _not_found()
    if challenge.creator_id != user.id:
        raise _forbidden()


def assert_can_delete(user, challenge) -> None:
    """Only the creator of a challenge may remove it."""
    if challenge is None:
        raise _not_found()
    if challenge.creator_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only remove challenges you created",
        )


def apply_edits(challenge, payload: dict):
    """Apply an edit payload to a challenge and return it.

    Only the fields present in the payload are touched; blank values are
    ignored so an empty form never wipes a challenge.
    """
    if "title" in payload:
        title = str(payload["title"] or "").strip()
        if title:
            challenge.title = title[:MAX_TITLE]

    if "description" in payload:
        description = str(payload["description"] or "").strip()
        challenge.description = description[:MAX_DESCRIPTION]

    if "category" in payload:
        category = str(payload["category"] or "").strip()
        if category:
            challenge.category = category[:64]

    if "difficulty" in payload:
        difficulty = str(payload["difficulty"] or "").strip()
        if difficulty:
            challenge.difficulty = difficulty[:32]

    if "base_xp" in payload and payload["base_xp"] is not None:
        try:
            base_xp = int(payload["base_xp"])
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="base_xp must be an integer"
            )
        if base_xp < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="base_xp cannot be negative"
            )
        challenge.base_xp = min(base_xp, MAX_BASE_XP)

    if "xp_reward" in payload and payload["xp_reward"] is not None:
        try:
            xp_reward = int(payload["xp_reward"])
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="xp_reward must be an integer"
            )
        if xp_reward < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="xp_reward cannot be negative"
            )
        challenge.base_xp = min(xp_reward, MAX_BASE_XP)

    if "proof_type" in payload and payload["proof_type"] is not None:
        proof_type = str(payload["proof_type"] or "").strip().lower()
        if proof_type not in PROOF_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"proof_type must be one of: {', '.join(PROOF_TYPES)}",
            )
        challenge.proof_type = proof_type

    return challenge


def delete_challenge(db, challenge) -> None:
    """Delete a challenge together with its assignments, submissions and reviews.

    ``submissions`` link to a challenge through ``challenge_assignments``, so the
    children have to be removed from the leaves up to satisfy the FK constraints.
    """
    from app.models.challenge import ChallengeAssignment
    from app.models.submission import Submission
    from app.models.verification_review import VerificationReview

    assignment_ids = [
        a.id
        for a in db.execute(
            select(ChallengeAssignment).where(
                ChallengeAssignment.challenge_id == challenge.id
            )
        ).scalars().all()
    ]

    submission_ids: list = []
    if assignment_ids:
        submission_ids = [
            s.id
            for s in db.execute(
                select(Submission).where(Submission.assignment_id.in_(assignment_ids))
            ).scalars().all()
        ]

    if submission_ids:
        db.query(VerificationReview).filter(
            VerificationReview.submission_id.in_(submission_ids)
        ).delete(synchronize_session=False)
        db.query(Submission).filter(Submission.id.in_(submission_ids)).delete(
            synchronize_session=False
        )

    if assignment_ids:
        db.query(ChallengeAssignment).filter(
            ChallengeAssignment.id.in_(assignment_ids)
        ).delete(synchronize_session=False)

    db.delete(challenge)
    db.commit()
