"""Pre-flight check for the database connection.

Run this before the migrations during a build so a misconfigured
``DATABASE_URL`` fails with an explanation instead of a bare ``exit 1``::

    python -m app.db.check_database

It reports the resolved driver/host/port (password masked), whether the host
is reachable, and whether the database answers a trivial query.
"""

import socket
import sys
from urllib.parse import urlsplit

from app.core.config import settings
from app.db.url import describe_database_url, missing_database_url_message, normalize_database_url


def _host_port(url: str):
    parts = urlsplit(url)
    host = parts.hostname or ""
    port = parts.port or 5432
    return host, port


def check() -> int:
    url = normalize_database_url(settings.DATABASE_URL or "")
    if not url:
        print(missing_database_url_message(), file=sys.stderr)
        return 1

    host, port = _host_port(url)
    print(f"Database: {describe_database_url(url)}")

    if not host:
        print("Could not parse a host out of DATABASE_URL.", file=sys.stderr)
        return 1

    # 1. TCP reachability
    try:
        with socket.create_connection((host, port), timeout=15):
            print(f"TCP:      reachable at {host}:{port}")
    except OSError as exc:
        print(f"TCP:      FAILED to reach {host}:{port} -> {exc}", file=sys.stderr)
        print(
            "  Supabase users: use the *connection pooler* URL (port 6543). "
            "The direct host on port 5432 is not reachable from every network "
            "(Render's outbound addresses are dynamic and not IPv6).",
            file=sys.stderr,
        )
        return 1

    # 2. The database itself
    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 15})
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        engine.dispose()
        print("Query:    SELECT 1 succeeded")
    except Exception as exc:
        print(f"Query:    FAILED -> {type(exc).__name__}: {exc}", file=sys.stderr)
        print(
            "  Check the database name, the password (URL-encode special "
            "characters such as @ and $ as %40 and %24) and that the role is "
            "allowed to connect.",
            file=sys.stderr,
        )
        return 1

    print("Database connection OK.")
    return 0


if __name__ == "__main__":
    sys.exit(check())
