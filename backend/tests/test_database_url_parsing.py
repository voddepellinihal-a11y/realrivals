"""Parsing of DATABASE_URL host forms: DNS, IPv4, IPv6 and malformed input.

A host that is wrapped in square brackets (``@[aws-0-...pooler.supabase.com]``)
makes :func:`urllib.parse.urlsplit` raise ``ValueError`` — that is what broke
the Render preflight.  These tests pin the behaviour for every host form and
make sure the password never reaches a log line.
"""
import unittest
from io import StringIO
from unittest.mock import patch

from app.db import url as db_url
from app.db import check_database

SUPABASE_HOST = "aws-0-ap-south-1.pooler.supabase.com"
SUPABASE_DNS = f"postgresql+psycopg2://postgres.abc:p%40ss@{SUPABASE_HOST}:6543/postgres?sslmode=require"
SUPABASE_BRACKETED = f"postgresql+psycopg2://postgres.abc:p%40ss@[{SUPABASE_HOST}]:6543/postgres?sslmode=require"
IPV4_URL = "postgresql+psycopg2://postgres.abc:p%40ss@203.0.113.10:5432/postgres"
IPV6_URL = "postgresql+psycopg2://postgres.abc:p%40ss@[2001:db8::1]:5432/postgres"
LOCALHOST_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres"


class SupabaseHostnameTestCase(unittest.TestCase):
    def test_dns_hostname_is_parsed(self):
        host, port = db_url.host_port(SUPABASE_DNS)
        self.assertEqual(host, SUPABASE_HOST)
        self.assertEqual(port, 6543)

    def test_bracketed_dns_hostname_is_repaired(self):
        host, port = db_url.host_port(SUPABASE_BRACKETED)
        self.assertEqual(host, SUPABASE_HOST)
        self.assertEqual(port, 6543)

    def test_the_repair_produces_a_url_without_brackets(self):
        self.assertEqual(db_url.normalize_database_url(SUPABASE_BRACKETED), SUPABASE_DNS)


class Ipv4TestCase(unittest.TestCase):
    def test_ipv4_host_and_port(self):
        host, port = db_url.host_port(IPV4_URL)
        self.assertEqual(host, "203.0.113.10")
        self.assertEqual(port, 5432)

    def test_ipv4_is_untouched_by_normalisation(self):
        self.assertEqual(db_url.normalize_database_url(IPV4_URL), IPV4_URL)

    def test_a_bracketed_ipv4_is_repaired(self):
        bracketed = IPV4_URL.replace("@203.0.113.10", "@[203.0.113.10]")
        host, port = db_url.host_port(bracketed)
        self.assertEqual(host, "203.0.113.10")
        self.assertEqual(port, 5432)


class Ipv6TestCase(unittest.TestCase):
    def test_bracketed_ipv6_is_parsed_and_preserved(self):
        host, port = db_url.host_port(IPV6_URL)
        self.assertEqual(host, "2001:db8::1")
        self.assertEqual(port, 5432)
        self.assertEqual(db_url.normalize_database_url(IPV6_URL), IPV6_URL)

    def test_ipv6_without_a_port_defaults_to_5432(self):
        url = "postgresql+psycopg2://postgres:pw@[2001:db8::1]/postgres"
        host, port = db_url.host_port(url)
        self.assertEqual(host, "2001:db8::1")
        self.assertEqual(port, 5432)

    def test_localhost_is_supported(self):
        host, port = db_url.host_port(LOCALHOST_URL)
        self.assertEqual(host, "localhost")
        self.assertEqual(port, 5432)


class InvalidUrlTestCase(unittest.TestCase):
    def test_an_empty_url_reports_a_missing_configuration(self):
        problems = db_url.database_url_problems("")
        self.assertEqual(len(problems), 1)
        self.assertIn("DATABASE_URL is not set", problems[0])

    def test_an_unparseable_url_is_reported(self):
        problems = db_url.database_url_problems("not-a-database-url")
        self.assertTrue(problems)
        self.assertTrue(any("could not be parsed" in p for p in problems))

    def test_host_port_raises_a_clear_error_for_an_unparseable_url(self):
        with self.assertRaises(ValueError) as ctx:
            db_url.host_port("not-a-database-url")
        self.assertIn("could not be parsed", str(ctx.exception))

    def test_a_url_without_a_host_is_reported(self):
        problems = db_url.database_url_problems("postgresql+psycopg2:///postgres")
        self.assertTrue(any("host name" in p for p in problems))

    def test_host_port_raises_when_there_is_no_host(self):
        with self.assertRaises(ValueError):
            db_url.host_port("postgresql+psycopg2:///postgres")


class BracketedHostnameNoticeTestCase(unittest.TestCase):
    def test_a_bracketed_dns_host_is_detected(self):
        notice = db_url.bracketed_host_notice(SUPABASE_BRACKETED)
        self.assertIsNotNone(notice)
        self.assertIn("square brackets", notice)
        self.assertIn(SUPABASE_HOST, notice)

    def test_a_bracketed_ipv6_is_not_reported(self):
        self.assertIsNone(db_url.bracketed_host_notice(IPV6_URL))

    def test_an_unbracketed_url_is_not_reported(self):
        self.assertIsNone(db_url.bracketed_host_notice(SUPABASE_DNS))

    def test_the_notice_does_not_leak_the_password(self):
        notice = db_url.bracketed_host_notice(SUPABASE_BRACKETED)
        self.assertNotIn("p%40ss", notice)


class DescribeMaskedTestCase(unittest.TestCase):
    def test_the_password_never_appears_in_the_description(self):
        described = db_url.describe_database_url(SUPABASE_DNS)
        self.assertNotIn("p%40ss", described)
        self.assertIn("***", described)
        self.assertIn(SUPABASE_HOST, described)
        self.assertIn("6543", described)

    def test_the_bracketed_form_is_described_with_the_host_name(self):
        described = db_url.describe_database_url(SUPABASE_BRACKETED)
        self.assertIn(SUPABASE_HOST, described)
        self.assertNotIn("p%40ss", described)


class PreflightReportingTestCase(unittest.TestCase):
    """The preflight must report the problem and still validate the connection."""

    def test_the_configuration_error_is_printed_to_stderr(self):
        stderr = StringIO()
        with patch.object(check_database.settings, "DATABASE_URL", SUPABASE_BRACKETED), \
             patch.object(check_database, "host_port", side_effect=ValueError("unreachable")), \
             patch("sys.stderr", stderr):
            check_database.check()

        output = stderr.getvalue()
        self.assertIn("configuration problem", output)
        self.assertIn("square brackets", output)

    def test_an_unusable_url_fails_the_preflight(self):
        stderr = StringIO()
        with patch.object(check_database.settings, "DATABASE_URL", ""), \
             patch("sys.stderr", stderr):
            exit_code = check_database.check()

        self.assertEqual(exit_code, 1)
        self.assertIn("DATABASE_URL is not set", stderr.getvalue())

    def test_the_preflight_reports_when_the_host_cannot_be_reached(self):
        stderr = StringIO()
        with patch.object(check_database.settings, "DATABASE_URL", SUPABASE_DNS), \
             patch.object(check_database, "host_port", side_effect=ValueError("no host")), \
             patch("sys.stderr", stderr):
            exit_code = check_database.check()

        self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
