"""Auth cookies must be HTTPS-only in production, plain-HTTP friendly in dev."""
import unittest
from unittest.mock import patch

from fastapi import Response

from app.modules.auth import router as auth_router


class CookieSecurityTestCase(unittest.TestCase):
    def test_the_flag_follows_the_environment(self):
        with patch.object(auth_router.settings, "ENVIRONMENT", "production"):
            self.assertTrue(auth_router.settings.is_production)
        with patch.object(auth_router.settings, "ENVIRONMENT", "development"):
            self.assertFalse(auth_router.settings.is_production)

    def test_cookies_are_https_only_in_production(self):
        response = Response()
        with patch.object(auth_router.settings, "ENVIRONMENT", "production"), \
             patch.object(auth_router, "COOKIE_SECURE", True):
            auth_router._set_auth_cookies(
                response, "access", "refresh", auth_router.datetime.now(auth_router.timezone.utc)
            )

        headers = response.headers.getlist("set-cookie")
        self.assertEqual(len(headers), 2)
        for header in headers:
            self.assertIn("Secure", header)
            self.assertIn("HttpOnly", header)
            self.assertIn("SameSite=lax", header)

    def test_cookies_are_not_secure_in_development(self):
        response = Response()
        with patch.object(auth_router.settings, "ENVIRONMENT", "development"), \
             patch.object(auth_router, "COOKIE_SECURE", False):
            auth_router._set_auth_cookies(
                response, "access", "refresh", auth_router.datetime.now(auth_router.timezone.utc)
            )

        for header in response.headers.getlist("set-cookie"):
            self.assertNotIn("Secure", header)
            self.assertIn("HttpOnly", header)


if __name__ == "__main__":
    unittest.main()
