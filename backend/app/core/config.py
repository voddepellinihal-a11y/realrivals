import os
from typing import List

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

#: Used only when no JWT_SECRET_KEY is supplied (local development).
#: It is deliberately obvious and long enough to avoid PyJWT's key-length warning.
DEV_JWT_SECRET = "dev-only-insecure-secret-change-me-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Render (and most PaaS providers) inject their own variables.
        # Unknown ones must not stop the app from booting.
        extra="ignore",
    )

    APP_ENV: str = "development"
    # Render's blueprint sets ENVIRONMENT=production.
    ENVIRONMENT: str = "development"
    APP_NAME: str = "RealLifeRivals"
    # Supabase Postgres.  Use the *connection pooler* URL (port 6543) from
    # Render — the direct host (port 5432) is not reachable from every network.
    # The value lives in the environment / .env, never in the repository.
    DATABASE_URL: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"

    # Signing key for access/refresh tokens.  Render generates one for us
    # (JWT_SECRET_KEY -> generateValue: true).
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"

    # Comma separated list of allowed origins.  "*" allows every domain.
    CORS_ORIGINS: str = "*"

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "Real-Life Rivals"
    FRONTEND_URL: str = ""

    @property
    def database_url(self) -> str:
        return self.DATABASE_URL

    @property
    def frontend_url(self) -> str:
        """Public URL of the app — used to build links in emails.

        Falls back to Render's ``RENDER_EXTERNAL_URL`` and finally to the local
        address, so production links point at the deployed site.
        """
        if self.FRONTEND_URL:
            return self.FRONTEND_URL
        render_url = os.environ.get("RENDER_EXTERNAL_URL", "").strip()
        if render_url:
            return render_url
        return "http://localhost:8000"

    @property
    def is_production(self) -> bool:
        return (self.ENVIRONMENT or self.APP_ENV or "development").lower() == "production"

    @property
    def cors_origins(self) -> List[str]:
        origins = [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        return origins or ["*"]

    @model_validator(mode="after")
    def _validate_secrets(self):
        """Fail fast in production rather than running with a known secret.

        ``DATABASE_URL`` is deliberately *not* validated here: tools that only
        need the configuration (Alembic's URL resolution, tests) must be able
        to load the settings without a database.  The application itself
        reports a missing database URL with a clear message in
        ``app.db.session``.
        """
        if self.is_production:
            if not self.JWT_SECRET_KEY:
                raise ValueError(
                    "JWT_SECRET_KEY must be set when ENVIRONMENT=production "
                    "(Render: JWT_SECRET_KEY -> generateValue: true)"
                )
            if len(self.JWT_SECRET_KEY.encode("utf-8")) < 32:
                raise ValueError(
                    "JWT_SECRET_KEY must be at least 32 bytes when ENVIRONMENT=production"
                )
        elif not self.JWT_SECRET_KEY:
            self.JWT_SECRET_KEY = DEV_JWT_SECRET
        return self


settings = Settings()
