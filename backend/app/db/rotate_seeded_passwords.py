"""Rotate the passwords of the two seeded private accounts.

The seeded accounts are created once, on the first boot.  When you deploy an
existing database (the usual case) they already exist, so the passwords
configured in Render would never be applied — the old ones would keep working.

Run this **once**, locally, with the same values you set on Render:

    set RIVAL1_PASSWORD=... && set RIVAL2_PASSWORD=...
    python -m app.db.rotate_seeded_passwords

After that the accounts use the new passwords everywhere.
"""

import os
import sys

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.user import User
from app.modules.auth.security import hash_password

ACCOUNTS = (
    ("RIVAL1_PASSWORD", "rival1@realliferivals.com"),
    ("RIVAL2_PASSWORD", "rival2@realliferivals.com"),
)


def rotate() -> int:
    passwords = [(env_key, email, os.environ.get(env_key, "")) for env_key, email in ACCOUNTS]
    missing = [env_key for env_key, _, value in passwords if not value]
    if missing:
        print(f"Missing environment variable(s): {', '.join(missing)}")
        return 1

    db = SessionLocal()
    changed = 0
    try:
        for _, email, password in passwords:
            user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
            if user is None:
                print(f"  {email}: not found — skipped (it will be seeded on first boot)")
                continue
            user.password_hash = hash_password(password)
            db.add(user)
            db.commit()
            changed += 1
            print(f"  {email}: password updated")
        print(f"\n{changed} account password(s) rotated.")
        return 0
    except Exception as exc:
        db.rollback()
        print(f"Rotation failed: {exc}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(rotate())
