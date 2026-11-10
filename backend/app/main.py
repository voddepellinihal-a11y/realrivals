from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import OperationalError
from sqlalchemy import text

from app.core.config import settings
from app.db.session import get_db, engine
from app.db.seed_private_users import seed_private_users
from app.modules.auth.router import router as auth_router
from app.modules.auth.router import user_router
from app.modules.challenge.router import router as challenge_router
from app.modules.game.router import router as game_router
from app.modules.group.router import router as group_router
from app.modules.routine.router import router as routine_router
from app.modules.submission.router import router as submission_router

app = FastAPI(title=settings.APP_NAME, version="0.1.0")

# --- CORS ------------------------------------------------------------------
# The API and the SPA are served from the same origin, but the API is also
# reachable from the deployed web domain (and from any local dev client).
# Starlette echoes the requesting origin when credentials are enabled, which is
# what cookie-based auth requires.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type"],
)


#: First path segments that belong to the API.  They must 404 as JSON instead
#: of falling through to the single-page app.
API_PREFIXES = frozenset(
    {
        "auth",
        "user",
        "challenges",
        "routines",
        "submissions",
        "game",
        "groups",
        "health",
        "docs",
        "openapi.json",
        "redoc",
    }
)


class SPAStaticFiles(StaticFiles):
    """Serve the built SPA with the right caching rules and a history fallback.

    * ``index.html`` must never be cached, otherwise a browser keeps pointing
      at the previous build's hashed assets and the user sees a stale UI.
    * Content-hashed assets under ``/assets`` are safe to cache forever.
    * Unknown paths (``/login``, ``/dashboard``, ``/onboarding`` …) fall back to
      ``index.html`` with a 200 so client-side routing works on a hard refresh.
    """

    async def get_response(self, path, scope):
        try:
            response = await super().get_response(path, scope)
        except Exception as exc:  # noqa: BLE001 - StarletteHTTPException and friends
            status_code = getattr(exc, "status_code", None)
            if status_code != 404:
                raise
            response = await self._spa_fallback(scope)

        if response.status_code == 404:
            response = await self._spa_fallback(scope)

        # Starlette normalises the path with OS separators ("assets\\x.js" on
        # Windows), so normalise before deciding how long to cache it.
        normalized = path.replace("\\", "/").lstrip("/")
        if normalized.startswith("assets/"):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        else:
            response.headers["Cache-Control"] = "no-cache, must-revalidate"
        return response

    async def _spa_fallback(self, scope):
        """Return index.html for client-side routes, JSON 404 for API paths."""
        route_path = scope.get("path", "") or ""
        first_segment = route_path.strip("/").split("/")[0]
        if first_segment in API_PREFIXES:
            return JSONResponse({"detail": "Not Found"}, status_code=404)

        index_file = Path(self.directory) / "index.html"
        if not index_file.is_file():
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        return FileResponse(
            index_file,
            headers={"Cache-Control": "no-cache, must-revalidate"},
        )


@app.on_event("startup")
def startup_event():
    # Seed private users on startup
    try:
        seed_private_users()
    except Exception as e:
        print(f"Warning: seed_private_users failed: {e}")
    # Seed achievements on startup
    try:
        from app.modules.game.services.achievement_service import seed_achievements
        from app.db.session import SessionLocal
        db = SessionLocal()
        seed_achievements(db)
        db.close()
    except Exception as e:
        print(f"Warning: seed_achievements failed: {e}")


@app.get("/health")
def health_check():
    """Liveness check — FastAPI process is running."""
    return {"status": "ok"}


@app.get("/health/ready")
def readiness_check():
    """Readiness check — verifies database connectivity."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": "unavailable"},
        )


# Graceful handling of database connectivity errors
@app.exception_handler(OperationalError)
async def db_error_handler(request, exc):
    return JSONResponse(
        status_code=503,
        content={"detail": "Database not connected. Check your Supabase credentials / network."},
    )


app.include_router(auth_router)
app.include_router(user_router)
app.include_router(challenge_router)
app.include_router(game_router)
app.include_router(group_router)
app.include_router(routine_router)
app.include_router(submission_router)


frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", SPAStaticFiles(directory=str(frontend_dist), html=True), name="frontend")
else:  # pragma: no cover - only when the frontend has not been built yet
    import logging

    logging.getLogger(__name__).warning(
        "frontend/dist not found - the API will serve but the SPA will not render. "
        "Build it with `cd frontend && npm install && npm run build`."
    )
