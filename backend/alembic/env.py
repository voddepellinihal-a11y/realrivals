"""Alembic environment for Real-Life Rivals.

The database URL is read from the environment (``DATABASE_URL``) and falls back
to the application settings.  It is normalised by :mod:`app.db.url` so that a
URL copied straight out of a hosting dashboard still works — SQLAlchemy 2
dropped the ``postgres://`` alias and resolves ``postgresql://`` to psycopg3,
which is not installed here.  Both cases used to abort the build with a bare
``exit 1``.
"""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.db.base import Base
from app.db.url import describe_database_url, missing_database_url_message, resolve_database_url
import app.models  # noqa: F401  (register all models on Base.metadata)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

db_url = resolve_database_url(settings_url=getattr(settings, "DATABASE_URL", ""))

if not db_url:
    raise RuntimeError(missing_database_url_message())

# ConfigParser treats '%' as an interpolation character, so a URL-encoded
# password has to be escaped before it is stored (and is un-escaped again
# when the section is read back).
config.set_main_option("sqlalchemy.url", db_url.replace("%", "%%"))

print(f"Alembic: using database {describe_database_url(db_url)}")


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    try:
        run_migrations_online()
    except Exception as exc:
        print(
            "\nAlembic could not reach the database.\n"
            f"  URL: {describe_database_url(db_url)}\n"
            f"  Error: {type(exc).__name__}: {exc}\n"
            "  Check that DATABASE_URL points at a reachable database "
            "(Supabase users: use the connection pooler on port 6543 - the "
            "direct host on port 5432 is not reachable from every network) "
            "and that the schema is not locked by another migration.",
            file=__import__("sys").stderr,
        )
        raise
