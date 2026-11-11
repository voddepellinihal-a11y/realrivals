"""Delete one user account together with everything that belongs to it.

This is a destructive, targeted tool.  It refuses to run without an explicit
``--confirm`` flag and it refuses to touch the two pre-loaded private accounts.

Usage::

    python -m app.db.delete_account --email unitygamers143@gmail.com --confirm

Children are removed from the leaves up so every foreign key is satisfied.
Challenges the account only *received* (``target_user_id``) are not deleted —
the reference is cleared instead, because another user may still be playing
them.
"""

import sys

from sqlalchemy import delete, func, select

from app.db.session import SessionLocal
from app.models.achievement import UserAchievement
from app.models.auth import AuthSession, EmailVerificationToken, PasswordResetToken
from app.models.challenge import Challenge, ChallengeAssignment
from app.models.group import Group, GroupMember
from app.models.routine import Routine
from app.models.streak import Streak
from app.models.submission import Submission
from app.models.user import User, UserPreference
from app.models.verification_review import VerificationReview
from app.models.xp_transaction import XpTransaction

#: The two pre-loaded accounts - never removable with this tool.
PROTECTED_EMAILS = (
    "rival1@realliferivals.com",
    "rival2@realliferivals.com",
)


def _count(db, stmt) -> int:
    return db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()


def delete_account(email: str, confirm: bool) -> int:
    if not confirm:
        print("Refusing to run without --confirm.")
        return 1
    if email in PROTECTED_EMAILS:
        print(f"{email} is a pre-loaded private account and cannot be deleted with this tool.")
        return 1

    db = SessionLocal()
    try:
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if user is None:
            print(f"No account found for {email}.")
            return 1

        print(f"Deleting {user.username} <{user.email}> ({user.id})")

        # Challenges this account created - remove them with their children.
        created_challenges = (
            db.execute(select(Challenge.id).where(Challenge.creator_id == user.id))
            .scalars()
            .all()
        )
        if created_challenges:
            assignment_ids = (
                db.execute(
                    select(ChallengeAssignment.id).where(
                        ChallengeAssignment.challenge_id.in_(created_challenges)
                    )
                )
                .scalars()
                .all()
            )
            if assignment_ids:
                submission_ids = (
                    db.execute(
                        select(Submission.id).where(
                            Submission.assignment_id.in_(assignment_ids)
                        )
                    )
                    .scalars()
                    .all()
                )
                if submission_ids:
                    db.execute(
                        delete(VerificationReview).where(
                            VerificationReview.submission_id.in_(submission_ids)
                        )
                    )
                    db.execute(Submission.__table__.delete().where(Submission.id.in_(submission_ids)))
                db.execute(
                    ChallengeAssignment.__table__.delete().where(
                        ChallengeAssignment.id.in_(assignment_ids)
                    )
                )
            db.execute(Challenge.__table__.delete().where(Challenge.id.in_(created_challenges)))
            print(f"  removed {len(created_challenges)} challenge(s) they created")

        # Challenges they only received: clear the reference instead of deleting.
        cleared = db.execute(
            Challenge.__table__.update()
            .where(Challenge.target_user_id == user.id)
            .values(target_user_id=None)
        )
        if cleared.rowcount:
            print(f"  cleared them as the target of {cleared.rowcount} challenge(s)")

        # Submissions they made.
        submission_ids = (
            db.execute(select(Submission.id).where(Submission.user_id == user.id))
            .scalars()
            .all()
        )
        if submission_ids:
            db.execute(
                delete(VerificationReview).where(
                    VerificationReview.submission_id.in_(submission_ids)
                )
            )
        db.execute(delete(Submission).where(Submission.user_id == user.id))
        db.execute(delete(VerificationReview).where(VerificationReview.reviewer_id == user.id))
        db.execute(delete(ChallengeAssignment).where(ChallengeAssignment.user_id == user.id))

        # Simple per-user rows.
        db.execute(delete(XpTransaction).where(XpTransaction.user_id == user.id))
        db.execute(delete(Streak).where(Streak.user_id == user.id))
        db.execute(delete(UserAchievement).where(UserAchievement.user_id == user.id))
        db.execute(delete(Routine).where(Routine.user_id == user.id))
        db.execute(delete(GroupMember).where(GroupMember.user_id == user.id))

        # Groups they created: keep a group that still has members, otherwise
        # remove it together with its challenges.
        for group in db.execute(select(Group).where(Group.created_by == user.id)).scalars().all():
            members = db.execute(
                select(GroupMember).where(GroupMember.group_id == group.id)
            ).scalars().all()
            if members:
                print(f"  kept group {group.name!r}: {len(members)} other member(s) remain")
                continue
            db.execute(
                delete(Challenge).where(Challenge.group_id == group.id)
            )
            db.execute(delete(Group).where(Group.id == group.id))

        db.execute(delete(AuthSession).where(AuthSession.user_id == user.id))
        db.execute(delete(EmailVerificationToken).where(EmailVerificationToken.user_id == user.id))
        db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id))
        db.execute(delete(UserPreference).where(UserPreference.user_id == user.id))

        db.execute(delete(User).where(User.id == user.id))
        db.commit()
        print("Account deleted.")
        return 0
    except Exception as exc:
        db.rollback()
        print(f"Deletion failed: {type(exc).__name__}: {exc}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    args = sys.argv[1:]
    email = None
    confirm = "--confirm" in args
    if "--email" in args:
        index = args.index("--email")
        if index + 1 < len(args):
            email = args[index + 1]
    if not email:
        print("usage: python -m app.db.delete_account --email <address> --confirm")
        sys.exit(1)
    sys.exit(delete_account(email, confirm))
