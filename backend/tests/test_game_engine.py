"""Tests for the game engine.

These tests use mocks for the database session so they can run without
a live database connection.
"""
import unittest
from datetime import date, datetime, timezone
from unittest.mock import MagicMock

from app.modules.game.services import level_service, streak_service
from app.modules.game.services import xp_service
from app.modules.auth import router as auth_router


class LevelServiceTestCase(unittest.TestCase):
    def test_zero_xp_is_level_one(self):
        self.assertEqual(level_service.calculate_level(0), 1)

    def test_negative_xp_is_level_one(self):
        self.assertEqual(level_service.calculate_level(-50), 1)

    def test_xp_for_next_level(self):
        self.assertEqual(level_service.xp_for_next_level(1), int(100 * 2 ** 1.5))

    def test_calculate_progress_zero(self):
        progress = level_service.calculate_progress(0)
        self.assertEqual(progress["level"], 1)
        self.assertEqual(progress["current_level_xp"], 0)
        # A fresh account shows an empty 0% bar across the full first-level span.
        self.assertEqual(progress["level_xp_span"], 283)
        self.assertEqual(progress["next_level_xp"], 283)
        self.assertEqual(progress["progress_percentage"], 0.0)
        self.assertEqual(progress["progress_percent"], 0.0)

    def test_calculate_progress_some_xp(self):
        progress = level_service.calculate_progress(282)
        self.assertEqual(progress["level"], 2)
        self.assertGreater(progress["progress_percentage"], 0.0)

    def test_level_formula_matches_spec(self):
        # level = floor((xp / 100) ** (1 / 1.5)) + 1
        for xp in (0, 1, 50, 100, 150, 282, 500, 1000):
            expected = max(1, int((xp / 100) ** (1 / 1.5)) + 1)
            self.assertEqual(level_service.calculate_level(xp), expected, f"xp={xp}")

    def test_zero_xp_renders_an_empty_bar(self):
        progress = level_service.calculate_progress(0)
        self.assertEqual(progress["progress_percentage"], 0.0)
        self.assertEqual(progress["current_level_xp"], 0)

    def test_progress_matches_frontend_math(self):
        # 150 XP -> level 2, 50 XP into a 182 XP span -> 27.5%
        progress = level_service.calculate_progress(150)
        self.assertEqual(progress["level"], 2)
        self.assertEqual(progress["current_level_xp"], 50)
        self.assertEqual(progress["next_level_xp"], 182)
        self.assertAlmostEqual(progress["progress_percentage"], 27.5, places=1)

    def test_progress_is_clamped_to_100(self):
        progress = level_service.calculate_progress(999_999)
        self.assertLessEqual(progress["progress_percentage"], 100.0)
        self.assertGreaterEqual(progress["progress_percentage"], 0.0)


class BmiTestCase(unittest.TestCase):
    def test_bmi_calculation(self):
        bmi = auth_router._compute_bmi(180, 80)
        self.assertIsNotNone(bmi)
        self.assertAlmostEqual(bmi, 24.7, places=1)

    def test_bmi_missing_inputs(self):
        self.assertIsNone(auth_router._compute_bmi(None, 80))
        self.assertIsNone(auth_router._compute_bmi(180, None))
        self.assertIsNone(auth_router._compute_bmi(0, 80))


class XpServiceTestCase(unittest.TestCase):
    def test_idempotency_returns_existing_without_awarding(self):
        db = MagicMock()

        class FakeTxn:
            id = "existing-txn"
            amount = 50

        fake_existing = FakeTxn()
        db.execute.return_value.scalar_one_or_none.return_value = fake_existing

        result = xp_service.award_xp(db, user_id="user-id", amount=50, source_type="SUBMISSION_APPROVE", source_id="sub-id")

        self.assertFalse(result["awarded"])
        self.assertEqual(result["reason"], "already_awarded")
        self.assertEqual(result["amount"], 50)
        # User record should not be modified/accessed for XP award path
        db.get.assert_not_called()

    def test_award_xp_new_transaction(self):
        db = MagicMock()
        # No existing transaction
        db.execute.return_value.scalar_one_or_none.return_value = None

        user = MagicMock()
        user.id = "user-id"
        user.lifetime_xp = 0
        user.season_xp = 0
        user.level = 1
        db.get.return_value = user

        class FakeTxn:
            id = "new-txn"

        result = xp_service.award_xp(db, user_id="user-id", amount=100, source_type="SUBMISSION_APPROVE", source_id="sub-id-2")

        self.assertTrue(result["awarded"])
        self.assertEqual(result["amount"], 100)
        self.assertEqual(user.lifetime_xp, 100)
        self.assertEqual(user.season_xp, 100)
        db.commit.assert_called_once()


class StreakServiceTestCase(unittest.TestCase):
    def test_first_ever_activity_sets_streak_to_one(self):
        db = MagicMock()
        user = MagicMock()
        user.id = "user-id"
        user.current_streak = 0
        user.longest_streak = 0
        user.last_active_date = None
        db.get.return_value = user

        result = streak_service.update_streak(db, "user-id", "UTC")

        self.assertEqual(result["current_streak"], 1)
        self.assertEqual(result["longest_streak"], 1)
        self.assertIsNotNone(result["last_active_date"])

    def test_consecutive_day_increments(self):
        db = MagicMock()
        user = MagicMock()
        user.id = "user-id"
        user.current_streak = 4
        user.longest_streak = 4
        user.last_active_date = date.today() - __import__("datetime").timedelta(days=1)
        db.get.return_value = user

        result = streak_service.update_streak(db, "user-id", "UTC")

        self.assertEqual(result["current_streak"], 5)
        self.assertEqual(result["longest_streak"], 5)

    def test_broken_streak_resets_to_one(self):
        db = MagicMock()
        user = MagicMock()
        user.id = "user-id"
        user.current_streak = 10
        user.longest_streak = 10
        user.last_active_date = date.today() - __import__("datetime").timedelta(days=5)
        db.get.return_value = user

        result = streak_service.update_streak(db, "user-id", "UTC")

        self.assertEqual(result["current_streak"], 1)
        self.assertEqual(result["longest_streak"], 10)

    def test_same_day_does_not_double_count(self):
        db = MagicMock()
        user = MagicMock()
        user.id = "user-id"
        user.current_streak = 7
        user.longest_streak = 7
        user.last_active_date = date.today()
        db.get.return_value = user

        result = streak_service.update_streak(db, "user-id", "UTC")

        self.assertEqual(result["current_streak"], 7)
        self.assertEqual(result["longest_streak"], 7)


if __name__ == "__main__":
    unittest.main()
