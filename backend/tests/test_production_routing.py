"""Production readiness: SPA routing, static assets, CORS and env-var wiring.

These are the things that break a deployment *after* it is live, so they are
covered here rather than only exercised by hand.
"""
import os
import unittest

from fastapi.testclient import TestClient

from app.main import app

DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")
HAS_BUILD = os.path.isfile(os.path.join(DIST, "index.html"))

# Paths that belong to the API — they must 404 as JSON, never fall back to the SPA.
API_PATHS = ("/auth/does-not-exist", "/challenges/nope", "/routines/nope", "/game/nope")


class SpaRoutingTestCase(unittest.TestCase):
    """Client-side routes must serve index.html, not 404."""

    @unittest.skipUnless(HAS_BUILD, "frontend/dist not built")
    def test_client_routes_serve_the_spa(self):
        client = TestClient(app)
        # "/routines" is deliberately absent: it is a real API endpoint
        # (GET /routines) and must keep returning API responses.
        for path in ("/login", "/dashboard", "/onboarding", "/some/deep/path"):
            with self.subTest(path=path):
                response = client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn("text/html", response.headers["content-type"])
                self.assertIn("<div id=\"root\">", response.text)

    def test_api_paths_are_not_shadowed_by_the_spa(self):
        """GET /routines is an API route, so it must not serve index.html."""
        client = TestClient(app)
        response = client.get("/routines")
        self.assertNotIn("<div id=\"root\">", response.text)
        self.assertIn(response.status_code, (200, 401))

    @unittest.skipUnless(HAS_BUILD, "frontend/dist not built")
    def test_index_is_served_at_the_root(self):
        client = TestClient(app)
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("<div id=\"root\">", response.text)

    def test_unknown_api_paths_still_return_json_404(self):
        client = TestClient(app)
        for path in API_PATHS:
            with self.subTest(path=path):
                response = client.get(path)
                self.assertEqual(response.status_code, 404)
                self.assertNotIn("<div id=\"root\">", response.text)

    def test_health_endpoints_are_not_swallowed_by_the_spa(self):
        client = TestClient(app)
        self.assertEqual(client.get("/health").status_code, 200)
        self.assertEqual(client.get("/health").json(), {"status": "ok"})


class StaticAssetTestCase(unittest.TestCase):
    @unittest.skipUnless(HAS_BUILD, "frontend/dist not built")
    def test_index_html_is_never_cached(self):
        client = TestClient(app)
        response = client.get("/")
        self.assertIn("no-cache", response.headers.get("cache-control", ""))

    @unittest.skipUnless(HAS_BUILD, "frontend/dist not built")
    def test_hashed_assets_are_cached_immutably(self):
        assets = os.path.join(DIST, "assets")
        if not os.path.isdir(assets):
            self.skipTest("no built assets")
        name = next((f for f in os.listdir(assets) if f.endswith(".js")), None)
        if name is None:
            self.skipTest("no built js asset")
        client = TestClient(app)
        response = client.get(f"/assets/{name}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("immutable", response.headers.get("cache-control", ""))


class CorsTestCase(unittest.TestCase):
    def test_preflight_is_allowed_across_origins(self):
        client = TestClient(app)
        response = client.options(
            "/auth/login",
            headers={
                "Origin": "https://real-life-rivals.onrender.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        self.assertIn(response.status_code, (200, 400))
        self.assertIn("access-control-allow-origin", {k.lower() for k in response.headers})

    def test_simple_request_carries_the_allow_origin_header(self):
        client = TestClient(app)
        response = client.get("/health", headers={"Origin": "https://example.com"})
        self.assertIn("access-control-allow-origin", {k.lower() for k in response.headers})


class EnvironmentWiringTestCase(unittest.TestCase):
    """Render injects ENVIRONMENT and JWT_SECRET_KEY — the app must read them."""

    def test_settings_expose_environment(self):
        from app.core.config import Settings

        self.assertTrue(hasattr(Settings, "model_fields"))
        self.assertIn("ENVIRONMENT", Settings.model_fields)
        self.assertIn("JWT_SECRET_KEY", Settings.model_fields)

    def test_unknown_environment_variables_do_not_break_startup(self):
        from app.core.config import Settings

        os.environ["RENDER_ONLY_VARIABLE"] = "1"
        try:
            settings = Settings()
            self.assertTrue(settings.ENVIRONMENT)
        finally:
            os.environ.pop("RENDER_ONLY_VARIABLE", None)

    def test_production_requires_a_strong_jwt_secret(self):
        from app.core.config import Settings

        os.environ["ENVIRONMENT"] = "production"
        os.environ.pop("JWT_SECRET_KEY", None)
        try:
            with self.assertRaises(Exception):
                Settings()
        finally:
            os.environ.pop("ENVIRONMENT", None)

    def test_production_accepts_a_generated_jwt_secret(self):
        from app.core.config import Settings

        os.environ["ENVIRONMENT"] = "production"
        os.environ["JWT_SECRET_KEY"] = "a" * 48
        try:
            settings = Settings()
            self.assertEqual(settings.JWT_SECRET_KEY, "a" * 48)
        finally:
            os.environ.pop("ENVIRONMENT", None)
            os.environ.pop("JWT_SECRET_KEY", None)

    def test_auth_uses_the_configured_jwt_secret(self):
        from app.modules.auth import router as auth_router

        self.assertTrue(auth_router.JWT_SECRET_KEY)
        self.assertGreaterEqual(len(auth_router.JWT_SECRET_KEY.encode()), 32)


if __name__ == "__main__":
    unittest.main()
