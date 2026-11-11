"""Database URL helpers shared by the application, Alembic and the preflight.

Two things have to be handled before a URL can be used:

* **The driver.**  SQLAlchemy 2 removed the ``postgres://`` alias and resolves
  a bare ``postgresql://`` to psycopg3, but this project uses psycopg2.  A URL
  pasted straight from a hosting dashboard therefore has to be normalised::

      postgres://user:pw@host/db            -> postgresql+psycopg2://user:pw@host/db
      postgresql://user:pw@host/db          -> postgresql+psycopg2://user:pw@host/db
      postgresql+psycopg://user:pw@host/db  -> postgresql+psycopg2://user:pw@host/db
      postgresql+psycopg2://user:pw@host/db -> unchanged

* **Square brackets around the host.**  In a URL ``[...]`` is only valid
  around an IPv6 literal.  Hosts are sometimes copied wrapped in brackets
  (``@[aws-0-...pooler.supabase.com]:6543``), which makes
  :func:`urllib.parse.urlsplit` raise ``ValueError`` because the content is
  not an IP literal.  Such brackets are stripped, because the intended host is
  unambiguous — but the malformed configuration is reported so the operator can
  fix the source variable rather than relying on the repair.

Nothing here prints the password.
"""

import ipaddress
import os
import re

#: The driver this project installs and uses.
DRIVER = "postgresql+psycopg2"

#: Default PostgreSQL port.
DEFAULT_PORT = 5432

#: The first ``[...]`` group inside a URL authority (host part).
_BRACKETS = re.compile(r"\[([^\]]+)\]")

#: The URL scheme prefix, if any.
_SCHEME = "://"


def _is_ip_literal(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def _split_authority(url: str):
    """Split ``scheme://authority/rest`` into ``(authority, rest)``.

    Returns ``(None, url)`` when there is no scheme, in which case the whole
    string is treated as the authority.
    """
    idx = url.find(_SCHEME)
    if idx == -1:
        return None, url
    start = idx + len(_SCHEME)
    end = url.find("/", start)
    if end == -1:
        return url[start:], ""
    return url[start:end], url[end:]


def bracketed_host_notice(url: str) -> str | None:
    """Explain a host that was wrapped in square brackets unnecessarily.

    Brackets are valid only around an IPv6 literal.  A DNS name or an IPv4
    address inside them is a malformed URL, and :func:`urllib.parse.urlsplit`
    refuses to parse it at all::

        ValueError: 'aws-0-ap-south-1.pooler.supabase.com' does not appear to
        be an IPv4 or IPv6 address
    """
    authority, _ = _split_authority(url or "")
    match = _BRACKETS.search(authority or "")
    if not match:
        return None

    inner = match.group(1)
    if _is_ip_literal(inner):
        return None  # a genuine IPv6 literal - brackets are correct

    return (
        f"DATABASE_URL wraps the host in square brackets: [{inner}].\n"
        "  Square brackets are only valid around an IPv6 literal, so the host "
        "must be written without them.\n"
        f"  Change the environment variable from '@[{inner}]' to '@{inner}'."
    )


def _strip_brackets_around_non_ip(url: str) -> str:
    """Remove ``[`` ``]`` when they wrap something that is not an IP literal."""
    authority, rest = _split_authority(url or "")
    if not authority:
        return url

    match = _BRACKETS.search(authority)
    if not match:
        return url

    inner = match.group(1)
    if _is_ip_literal(inner):
        return url  # keep a real IPv6 literal

    fixed_authority = authority[: match.start(1) - 1] + inner + authority[match.end(1) + 1 :]
    return url[: len(url) - len(authority) - len(rest)] + fixed_authority + rest


def normalize_database_url(url: str) -> str:
    """Return a URL that this project can actually connect with.

    Never raises: the result is a best-effort normalisation, and
    :func:`database_url_problems` is the place that reports a bad
    configuration.  Stripping the driver and brackets here means the engine,
    Alembic and the preflight all see the same clean URL.
    """
    if not url:
        return ""
    url = url.strip()
    if not url:
        return ""

    for prefix in ("postgres://", "postgresql://", "postgresql+psycopg://"):
        if url.startswith(prefix):
            url = DRIVER + "://" + url[len(prefix) :]
            break

    return _strip_brackets_around_non_ip(url)


def database_url_problems(url: str) -> list:
    """Return human-readable problems with a raw ``DATABASE_URL``.

    An empty list means the URL is usable.
    """
    problems = []
    if not url or not url.strip():
        return [missing_database_url_message()]

    notice = bracketed_host_notice(url)
    if notice:
        problems.append(notice)

    normalized = normalize_database_url(url)
    if not normalized:
        return [missing_database_url_message()]

    try:
        from sqlalchemy.engine import make_url

        parsed = make_url(normalized)
    except Exception as exc:
        problems.append(
            f"DATABASE_URL could not be parsed as a PostgreSQL connection string: {exc}"
        )
        return problems

    if not parsed.host:
        problems.append("DATABASE_URL does not contain a host name.")

    if parsed.host and not _is_ip_literal(parsed.host):
        host = parsed.host
        if "/" in host or " " in host or "@" in host:
            problems.append(f"DATABASE_URL contains an invalid host name: {host!r}")

    return problems


def host_port(url: str) -> tuple:
    """Return ``(host, port)`` for a database URL.

    Handles DNS names, IPv4 addresses and bracketed IPv6 literals.  Raises
    ``ValueError`` with a clear message when the URL cannot be parsed.
    """
    if not url:
        raise ValueError(missing_database_url_message())

    normalized = normalize_database_url(url)
    try:
        from sqlalchemy.engine import make_url

        parsed = make_url(normalized)
    except Exception as exc:
        raise ValueError(
            f"DATABASE_URL could not be parsed as a PostgreSQL connection string: {exc}"
        ) from exc

    host = parsed.host or ""
    if not host:
        raise ValueError("DATABASE_URL does not contain a host name.")
    return host, parsed.port or DEFAULT_PORT


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

        parsed = make_url(normalize_database_url(url))
        return (
            f"{parsed.drivername}://{parsed.username}:***@{parsed.host}"
            f":{parsed.port or DEFAULT_PORT}/{parsed.database}"
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
