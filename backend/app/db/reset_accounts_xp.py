"""Reset the XP and level of the two pre-seeded private accounts.

This script is deliberately narrow.  It touches exactly two columns on the
``users`` row of the two seeded accounts:

    lifetime_xp -> 0
    level       -> 1

It does NOT touch anything else.  In particular it leaves alone:

* the accounts themselves (no insert, no delete, no recreate)
* usernames, emails, password hashes, gender, avatars and preferences
* ``season_xp`` and the current/longest streak
* routines, challenges, submissions, reviews and the XP ledger
  (``xp_transactions``) — that is the completion history

Usage::

    python -m app.db.reset_accounts_xp            # apply
    python -m app.db.reset_accounts_xp --dry-run  # show what would change
"""

import sys

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.user import User

#: The two pre-loaded private accounts.
SEEDED_EMAILS = (
    "rival1@realliferivals.com",
    "rival2@realliferivals.com",
)


def reset(dry_run: bool = False) -> int:
    db = SessionLocal()
    changed = 0
    try:
        users = (
            db.execute(select(User).where(User.email.in_(SEEDED_EMAILS)))
            .scalars()
            .all()
        )

        found = {u.email for u in users}
        for email in SEEDED_EMAILS:
            if email not in found:
                print(f"  {email}: NOT FOUND — skipped")
                continue

        for user in users:
            before = (user.lifetime_xp, user.level, user.season_xp)
            if user.lifetime_xp == 0 and user.level == 1:
                print(
                    f"  {user.email}: already at lifetime_xp=0, level=1 "
                    f"(season_xp={user.season_xp}) — nothing to do"
                )
                continue

            user.lifetime_xp = 0
            user.level = 1
            changed += 1
            print(
                f"  {user.email}: lifetime_xp {before[0]} -> 0, "
                f"level {before[1]} -> 1 (season_xp left at {before[2]})"
            )

        if dry_run:
            db.rollback()
            print(f"\nDry run — {changed} account(s) would be reset.")
        else:
            db.commit()
            print(f"\n{changed} account(s) reset.")
    except Exception as exc:
        db.rollback()
        print(f"Reset failed: {exc}")
        return 1
    finally:
        db.close()

    return 0


def verify() -> int:
    """Print the XP / level of both accounts."""
    db = SessionLocal()
    ok = True
    try:
        users = (
            db.execute(select(User).where(User.email.in_(SEEDED_EMAILS)))
            .scalars()
            .all()
        )
        print(f"{'email':34} {'lifetime_xp':>11} {'level':>6} {'season_xp':>10}")
        for user in sorted(users, key=lambda u: u.email):
            print(f"{user.email:34} {user.lifetime_xp:>11} {user.level:>6} {user.season_xp:>10}")
            if user.lifetime_xp != 0 or user.level != 1:
                ok = False
        if len(users) != len(SEEDED_EMAILS):
            print(f"Expected {len(SEEDED_EMAILS)} accounts, found {len(users)}.")
            ok = False
    finally:
        db.close()

    print("\nVERIFIED" if ok else "\nNOT VERIFIED")
    return 0 if ok else 1


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    if "--verify" in sys.argv:
        sys.exit(verify())
    sys.exit(reset(dry_run=dry_run))
