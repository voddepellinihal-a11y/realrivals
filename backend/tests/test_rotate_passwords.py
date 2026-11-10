"""Rotating the seeded account passwords must apply the environment values."""
import os
import unittest
from unittest.mock import MagicMock, patch

from app.db import rotate_seeded_passwords as rotate_module
from app.modules.auth.security import verify_password


class RotateSeededPasswordsTestCase(unittest.TestCase):
    def setUp(self):
        os.environ.pop("RIVAL1_PASSWORD", None)
        os.environ.pop("RIVAL2_PASSWORD", None)

    def tearDown(self):
        os.environ.pop("RIVAL1_PASSWORD", None)
        os.environ.pop("RIVAL2_PASSWORD", None)

    def test_it_refuses_to_run_without_passwords(self):
        self.assertEqual(rotate_module.rotate(), 1)

    def test_it_updates_the_existing_accounts(self):
        os.environ["RIVAL1_PASSWORD"] = "brand-new-one"
        os.environ["RIVAL2_PASSWORD"] = "brand-new-two"

        db = MagicMock()
        users = []
        for email in ("rival1@realliferivals.com", "rival2@realliferivals.com"):
            user = MagicMock()
            user.email = email
            users.append(user)
        db.execute.return_value.scalar_one_or_none.side_effect = users

        with patch.object(rotate_module, "SessionLocal", return_value=db):
            self.assertEqual(rotate_module.rotate(), 0)

        updated = [call.args[0] for call in db.add.call_args_list]
        self.assertEqual(len(updated), 2)
        self.assertTrue(verify_password("brand-new-one", updated[0].password_hash))
        self.assertTrue(verify_password("brand-new-two", updated[1].password_hash))

    def test_a_missing_account_is_skipped(self):
        os.environ["RIVAL1_PASSWORD"] = "brand-new-one"
        os.environ["RIVAL2_PASSWORD"] = "brand-new-two"

        db = MagicMock()
        user = MagicMock()
        user.email = "rival1@realliferivals.com"
        db.execute.return_value.scalar_one_or_none.side_effect = [user, None]

        with patch.object(rotate_module, "SessionLocal", return_value=db):
            self.assertEqual(rotate_module.rotate(), 0)

        updated = [call.args[0] for call in db.add.call_args_list]
        self.assertEqual(len(updated), 1)


if __name__ == "__main__":
    unittest.main()
