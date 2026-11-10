"""The seeded private accounts must not use source-code passwords in production.

The repository is public, so a password baked into the source is a password
everybody knows.  In production the two accounts must come from the
environment.
"""
import os
import unittest
from unittest.mock import MagicMock, patch

from app.db import seed_private_users
from app.modules.auth.security import verify_password


class SeededAccountPasswordTestCase(unittest.TestCase):
    def setUp(self):
        self.seed = seed_private_users
        os.environ.pop("RIVAL1_PASSWORD", None)
        os.environ.pop("RIVAL2_PASSWORD", None)

    def tearDown(self):
        os.environ.pop("RIVAL1_PASSWORD", None)
        os.environ.pop("RIVAL2_PASSWORD", None)

    def test_development_falls_back_to_the_known_local_passwords(self):
        with patch.object(self.seed.settings, "ENVIRONMENT", "development"):
            p1, p2 = self.seed.account_passwords()
        self.assertTrue(p1)
        self.assertTrue(p2)

    def test_production_uses_the_environment_passwords(self):
        os.environ["RIVAL1_PASSWORD"] = "env-password-one"
        os.environ["RIVAL2_PASSWORD"] = "env-password-two"
        with patch.object(self.seed.settings, "ENVIRONMENT", "production"):
            p1, p2 = self.seed.account_passwords()
        self.assertEqual(p1, "env-password-one")
        self.assertEqual(p2, "env-password-two")

    def test_production_has_no_fallback_password(self):
        """With nothing in the environment, production must not invent one."""
        with patch.object(self.seed.settings, "ENVIRONMENT", "production"):
            p1, p2 = self.seed.account_passwords()
        self.assertEqual(p1, "")
        self.assertEqual(p2, "")

    def test_seeding_is_skipped_in_production_without_passwords(self):
        with patch.object(self.seed.settings, "ENVIRONMENT", "production"), \
             patch.object(self.seed, "SessionLocal") as session_factory:
            self.seed.seed_private_users()
        session_factory.assert_not_called()

    def test_the_created_account_uses_the_environment_password(self):
        os.environ["RIVAL1_PASSWORD"] = "env-password-one"
        os.environ["RIVAL2_PASSWORD"] = "env-password-two"
        db = MagicMock()
        # No existing users -> the seeder creates both.
        db.execute.return_value.scalar_one_or_none.return_value = None

        with patch.object(self.seed.settings, "ENVIRONMENT", "production"), \
             patch.object(self.seed, "SessionLocal", return_value=db):
            self.seed.seed_private_users()

        created = [call.args[0] for call in db.add.call_args_list]
        self.assertEqual(len(created), 2)
        self.assertTrue(verify_password("env-password-one", created[0].password_hash))
        self.assertTrue(verify_password("env-password-two", created[1].password_hash))

    def test_development_still_seeds_the_known_local_accounts(self):
        db = MagicMock()
        db.execute.return_value.scalar_one_or_none.return_value = None

        with patch.object(self.seed.settings, "ENVIRONMENT", "development"), \
             patch.object(self.seed, "SessionLocal", return_value=db):
            self.seed.seed_private_users()

        created = [call.args[0] for call in db.add.call_args_list]
        self.assertEqual(len(created), 2)
        self.assertTrue(
            verify_password(self.seed.DEV_RIVAL1_PASSWORD, created[0].password_hash)
        )
        self.assertTrue(
            verify_password(self.seed.DEV_RIVAL2_PASSWORD, created[1].password_hash)
        )


if __name__ == "__main__":
    unittest.main()
