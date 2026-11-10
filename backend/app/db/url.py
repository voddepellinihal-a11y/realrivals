"""Database URL helpers shared by the application and Alembic.

SQLAlchemy 2 removed the ``postgres://`` alias and resolves ``postgresql://``
to psycopg3, but this project uses psycopg2.  A URL pasted straight from a
hosting dashboard therefore has to be normalised before it is used, otherwise
the connection fails with an opaque driver error.

Supported shapes::

    postgres://user:pw@host/db            -> postgresql+psycopg2://user:pw@host/db
    postgresql://user:pw@host/db          -> postgresql+psycopg2://user:pw@host/db
    postgresql+psycopg://user:pw@host/db  -> postgresql+psycopg2://user:pw@host/db
    postgresql+psycopg2://user:pw@host/db -> unchanged
"""

import os

#: The driver this project installs and uses.
DRIVER = "postgresql+psycopg2"


def normalize_database_url(url: str) -> str:
    """Force the synchronous psycopg2 driver on any supported URL shape."""
    if not url:
        return ""
    url = url.strip()
    if url.startswith("postgres://"):
        return f"{DRIVER}://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return f"{DRIVER}://" + url[len("postgresql://") :]
    if url.startswith("postgresql+psycopg://"):
        return f"{DRIVER}://" + url[len("postgresql+psycopg://") :]
    return url


def resolve_database_url(env_url: str = None, settings_url: str = "") -> str:
    """Resolve the database URL: environment first, then the settings."""
    raw = env_url if env_url is not None else os.getenv("DATABASE_URL", "")
    raw = raw or settings_url or ""
    return normalize_database_url(raw)


def describe_database_url(url: str) -> str:
    """A printable description of the URL with the password masked."""
    if not url:
        return "<not set>"
    try:
        from sqlalchemy.engine import make_url

        parsed = make_url(url)
        return (
            f"{parsed.drivername}://{parsed.username}:***@{parsed.host}"
            f":{parsed.port or 5432}/{parsed.database}"
        )
    except Exception:
        return "<unparsable>"


def missing_database_url_message() -> str:
    """Actionable message for a missing DATABASE_URL."""
    return (
        "DATABASE_URL is not set, so the database cannot be reached.\n"
        "  - On Render: set DATABASE_URL in the service's Environment tab "
        "(use the Supabase *connection pooler* URL, port 6543).\n"
        "  - Locally: copy .env.example to backend/.env and fill it in."
    )
