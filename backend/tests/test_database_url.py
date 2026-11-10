"""Database URL handling for the app and for Alembic.

A URL pasted from a hosting dashboard must work no matter which scheme it
uses, and a URL-encoded password must survive ConfigParser's interpolation.
"""
import os
import unittest
from configparser import ConfigParser

from app.db.url import (
    describe_database_url,
    missing_database_url_message,
    normalize_database_url,
    resolve_database_url,
)

POOLER = (
    "postgresql+psycopg2://postgres.abc:secret%40word@aws-0-ap-south-1.pooler"
    ".supabase.com:6543/postgres?sslmode=require"
)


class NormalizeDatabaseUrlTestCase(unittest.TestCase):
    def test_psycopg2_url_is_unchanged(self):
        self.assertEqual(normalize_database_url(POOLER), POOLER)

    def test_postgres_scheme_is_upgraded(self):
        url = POOLER.replace("postgresql+psycopg2://", "postgres://")
        self.assertEqual(normalize_database_url(url), POOLER)

    def test_postgresql_scheme_gets_the_psycopg2_driver(self):
        url = POOLER.replace("postgresql+psycopg2://", "postgresql://")
        self.assertEqual(normalize_database_url(url), POOLER)

    def test_psycopg3_scheme_gets_the_psycopg2_driver(self):
        url = POOLER.replace("postgresql+psycopg2://", "postgresql+psycopg://")
        self.assertEqual(normalize_database_url(url), POOLER)

    def test_empty_url_stays_empty(self):
        self.assertEqual(normalize_database_url(""), "")

    def test_whitespace_is_trimmed(self):
        self.assertEqual(normalize_database_url(f"  {POOLER}  "), POOLER)

    def test_every_scheme_ends_up_on_the_same_driver(self):
        for scheme in ("postgres://", "postgresql://", "postgresql+psycopg://", "postgresql+psycopg2://"):
            with self.subTest(scheme=scheme):
                url = POOLER.replace("postgresql+psycopg2://", scheme)
                self.assertTrue(normalize_database_url(url).startswith("postgresql+psycopg2://"))


class ResolveDatabaseUrlTestCase(unittest.TestCase):
    def test_environment_wins_over_settings(self):
        url = resolve_database_url(env_url="postgres://from-env/db", settings_url="postgresql://from-settings/db")
        self.assertEqual(url, "postgresql+psycopg2://from-env/db")

    def test_settings_are_used_when_the_environment_is_empty(self):
        url = resolve_database_url(env_url="", settings_url="postgresql://from-settings/db")
        self.assertEqual(url, "postgresql+psycopg2://from-settings/db")

    def test_environment_variable_is_read_by_default(self):
        os.environ["DATABASE_URL"] = "postgres://from-os-env/db"
        try:
            self.assertEqual(
                resolve_database_url(settings_url="postgresql://from-settings/db"),
                "postgresql+psycopg2://from-os-env/db",
            )
        finally:
            os.environ.pop("DATABASE_URL", None)


class DescribeDatabaseUrlTestCase(unittest.TestCase):
    def test_the_password_is_masked(self):
        described = describe_database_url(POOLER)
        self.assertNotIn("secret", described)
        self.assertNotIn("secret%40word", described)
        self.assertIn("***", described)
        self.assertIn("6543", described)
        self.assertIn("aws-0-ap-south-1.pooler.supabase.com", described)

    def test_a_missing_url_is_reported(self):
        self.assertEqual(describe_database_url(""), "<not set>")

    def test_the_message_is_actionable(self):
        message = missing_database_url_message()
        self.assertIn("DATABASE_URL", message)
        self.assertIn("6543", message)


class ConfigParserEscapingTestCase(unittest.TestCase):
    """Alembic stores the URL in a ConfigParser, where '%' is special."""

    def test_a_percent_encoded_password_survives_the_configparser(self):
        parser = ConfigParser()
        parser.add_section("alembic")
        escaped = POOLER.replace("%", "%%")
        parser.set("alembic", "sqlalchemy.url", escaped)

        # Reading it back must give the original URL, not a mangled one.
        self.assertEqual(parser.get("alembic", "sqlalchemy.url"), POOLER)
        self.assertEqual(dict(parser.items("alembic"))["sqlalchemy.url"], POOLER)

    def test_an_unescaped_percent_would_break_the_configparser(self):
        """Guards the reason the escaping exists in the first place.

        ``ConfigParser.set`` rejects a bare '%' outright, so without the
        escaping Alembic would abort with "invalid interpolation syntax".
        """
        parser = ConfigParser()
        parser.add_section("alembic")

        with self.assertRaises(ValueError):
            parser.set("alembic", "sqlalchemy.url", POOLER)

    def test_the_escaped_value_can_actually_be_set_and_read(self):
        parser = ConfigParser()
        parser.add_section("alembic")
        parser.set("alembic", "sqlalchemy.url", POOLER.replace("%", "%%"))
        self.assertEqual(parser.get("alembic", "sqlalchemy.url"), POOLER)


if __name__ == "__main__":
    unittest.main()
