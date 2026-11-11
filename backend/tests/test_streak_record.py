"""The group-scoped streak record must use the model's real field names.

Regression: the review path read ``streak.longest_streak`` while the model
defines ``longest_count``, so approving a proof on a consecutive day raised
``AttributeError`` and returned a 500.
"""
import unittest
from datetime import date, timedelta
from unittest.mock import MagicMock

from app.modules.game.services import streak_service


def make_streak(current_count=1, longest_count=1, last_qualified=None):
    streak = MagicMock()
    streak.current_count = current_count
    streak.longest_count = longest_count
    streak.last_qualified_date = last_qualified
    return streak


class ApplyStreakRecordTestCase(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 11, 11)

    def _db_with(self, existing):
        db = MagicMock()
        db.execute.return_value.scalar_one_or_none.return_value = existing
        return db

    def test_a_first_activity_creates_a_streak_of_one(self):
        db = self._db_with(None)
        streak = streak_service.apply_streak_record(db, "user-id", None, today=self.today)

        self.assertEqual(streak.current_count, 1)
        self.assertEqual(streak.longest_count, 1)
        self.assertEqual(streak.last_qualified_date, self.today)
        db.add.assert_called_once()

    def test_a_consecutive_day_extends_the_streak(self):
        existing = make_streak(
            current_count=4, longest_count=4, last_qualified=self.today - timedelta(days=1)
        )
        db = self._db_with(existing)

        streak = streak_service.apply_streak_record(db, "user-id", None, today=self.today)

        self.assertEqual(streak.current_count, 5)
        self.assertEqual(streak.longest_count, 5)
        self.assertEqual(streak.last_qualified_date, self.today)

    def test_the_longest_count_is_not_lowered(self):
        existing = make_streak(
            current_count=1, longest_count=9, last_qualified=self.today - timedelta(days=1)
        )
        db = self._db_with(existing)

        streak = streak_service.apply_streak_record(db, "user-id", None, today=self.today)

        self.assertEqual(streak.current_count, 2)
        self.assertEqual(streak.longest_count, 9)

    def test_the_same_day_does_not_double_count(self):
        existing = make_streak(
            current_count=3, longest_count=3, last_qualified=self.today
        )
        db = self._db_with(existing)

        streak = streak_service.apply_streak_record(db, "user-id", None, today=self.today)

        self.assertEqual(streak.current_count, 3)
        self.assertEqual(streak.longest_count, 3)

    def test_a_broken_streak_restarts_at_one(self):
        existing = make_streak(
            current_count=7, longest_count=7, last_qualified=self.today - timedelta(days=5)
        )
        db = self._db_with(existing)

        streak = streak_service.apply_streak_record(db, "user-id", None, today=self.today)

        self.assertEqual(streak.current_count, 1)
        self.assertEqual(streak.longest_count, 7)

    def test_it_uses_the_model_field_names(self):
        """Guard against reading a field the model does not define."""
        from app.models.streak import Streak

        self.assertTrue(hasattr(Streak, "current_count"))
        self.assertTrue(hasattr(Streak, "longest_count"))
        self.assertFalse(hasattr(Streak, "longest_streak"))


if __name__ == "__main__":
    unittest.main()
