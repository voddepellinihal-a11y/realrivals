from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.url import missing_database_url_message, normalize_database_url

database_url = normalize_database_url(settings.DATABASE_URL)

if not database_url:
    raise RuntimeError(missing_database_url_message())

engine = create_engine(database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
