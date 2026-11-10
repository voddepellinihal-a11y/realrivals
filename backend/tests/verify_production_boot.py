"""Simulate the Render production boot.

Renders runs:
    ENVIRONMENT=production
    JWT_SECRET_KEY=<generated>
    DATABASE_URL=<supabase pooler>

and then `uvicorn app.main:app`.  This script reproduces that environment and
imports the app exactly like the server does, so we catch boot-time failures
before they happen in production.
"""
import os
import sys

# Exactly what Render injects.
os.environ["ENVIRONMENT"] = "production"
os.environ["JWT_SECRET_KEY"] = "R" * 64  # Render's generated secret
os.environ["RENDER_EXTERNAL_URL"] = "https://real-life-rivals.onrender.com"

# The app must not read a stray local .env in production.
os.environ.pop("APP_ENV", None)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

failures = []


def check(label, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {label}" + (f"  -> {detail}" if detail else ""))
    if not ok:
        failures.append(label)


try:
    from app.core.config import settings

    check("ENVIRONMENT is read from the environment", settings.ENVIRONMENT == "production", settings.ENVIRONMENT)
    check("is_production is True", settings.is_production is True)
    check("JWT_SECRET_KEY comes from the environment", settings.JWT_SECRET_KEY == "R" * 64)
    check("frontend_url falls back to RENDER_EXTERNAL_URL",
          settings.frontend_url == "https://real-life-rivals.onrender.com", settings.frontend_url)
    check("cors_origins defaults to '*'", settings.cors_origins == ["*"], str(settings.cors_origins))
except Exception as exc:
    check("settings import", False, f"{type(exc).__name__}: {exc}")
    raise SystemExit(1)

try:
    from app.main import app
    from app.modules.auth import router as auth_router

    check("app imports in production mode", True)
    check("auth uses the injected secret", auth_router.JWT_SECRET_KEY == "R" * 64)

    # FastAPI keeps included routers wrapped, so the OpenAPI schema is the
    # authoritative list of registered endpoints.
    schema_paths = set(app.openapi()["paths"])
    for needed in ("/health", "/health/ready", "/auth/login", "/challenges", "/routines"):
        check(f"route {needed} is registered", needed in schema_paths)
except Exception as exc:
    check("app import", False, f"{type(exc).__name__}: {exc}")
    raise SystemExit(1)

try:
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get("/health")
    check("GET /health returns 200", resp.status_code == 200, str(resp.status_code))
    resp = client.get("/login")
    check("GET /login serves the SPA", resp.status_code == 200 and "<div id=\"root\">" in resp.text)
    resp = client.get("/health", headers={"Origin": "https://example.com"})
    check("CORS header present", "access-control-allow-origin" in {k.lower() for k in resp.headers})
except Exception as exc:
    check("smoke test", False, f"{type(exc).__name__}: {exc}")

print()
if failures:
    print(f"PRODUCTION BOOT: {len(failures)} failure(s): {failures}")
    raise SystemExit(1)
print("PRODUCTION BOOT: all checks passed")
