"""Reproduce the Alembic build failures reported from Render.

Runs `alembic upgrade head` in a subprocess with different DATABASE_URL shapes
and reports which ones fail.  Mirrors what the Render build command does.

The base URL comes from the environment / backend/.env — never from source.
"""
import os
import pathlib
import subprocess
import sys

BACKEND = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))


def _base_url() -> str:
    from app.core.config import settings

    url = settings.DATABASE_URL
    if not url:
        print("DATABASE_URL is not set — nothing to reproduce against.")
        raise SystemExit(1)
    return url


POOLER = _base_url()

CASES = [
    ("pooler URL with %-encoded password", POOLER),
    ("postgres:// scheme", POOLER.replace("postgresql+psycopg2://", "postgres://")),
    ("postgresql:// scheme", POOLER.replace("postgresql+psycopg2://", "postgresql://")),
    ("unreachable host (simulates direct port blocked)",
     POOLER.replace("6543", "5432").replace("aws-0-ap-south-1.pooler.supabase.com", "10.255.255.1")),
    ("empty", ""),
]

for label, url in CASES:
    env = dict(os.environ)
    env["DATABASE_URL"] = url
    env.pop("PYTHONPATH", None)
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=str(BACKEND),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        print(f"[FAIL] {label}")
        print("        timed out")
        continue

    tail = (proc.stderr or proc.stdout).strip().splitlines()
    last = tail[-1] if tail else ""
    print(f"[{'PASS' if proc.returncode == 0 else 'FAIL'}] {label}")
    print(f"        exit={proc.returncode}  {last[:150]}")
