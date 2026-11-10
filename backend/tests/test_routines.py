"""Tests for routine completion (XP award) and challenge/routine removal.

These use mocks for the database session so they can run without a live
database connection, matching the style of test_game_engine.py.
"""
import unittest
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

from app.modules.routine import service as routine_service


def make_user(user_id="user-id", lifetime_xp=0):
    user = MagicMock()
    user.id = user_id
    user.lifetime_xp = lifetime_xp
    user.season_xp = lifetime_xp
    user.level = 1
    user.current_streak = 0
    user.longest_streak = 0
    user.last_active_date = None
    return user


def make_routine(routine_id="routine-id", xp=25, completed=False):
    routine = MagicMock()
    routine.id = routine_id
    routine.xp = xp
    routine.completed = completed
    routine.completed_at = None
    routine.last_completed_on = None
    return routine


class RoutineXpSourceIdTestCase(unittest.TestCase):
    def test_source_id_is_stable_for_the_same_routine_and_day(self):
        a = routine_service.routine_xp_source_id("abc", date(2026, 11, 10))
        b = routine_service.routine_xp_source_id("abc", date(2026, 11, 10))
        self.assertEqual(a, b)

    def test_source_id_changes_across_days(self):
        a = routine_service.routine_xp_source_id("abc", date(2026, 11, 10))
        b = routine_service.routine_xp_source_id("abc", date(2026, 11, 11))
        self.assertNotEqual(a, b)

    def test_source_id_changes_across_routines(self):
        a = routine_service.routine_xp_source_id("abc", date(2026, 11, 10))
        b = routine_service.routine_xp_source_id("xyz", date(2026, 11, 10))
        self.assertNotEqual(a, b)

    def test_source_id_is_namespaced_by_source_type(self):
        source_id = routine_service.routine_xp_source_id("abc", date(2026, 11, 10))
        self.assertIn("ROUTINE_COMPLETE", source_id)


class RoutineCompletionTestCase(unittest.TestCase):
    def test_completing_a_routine_awards_its_xp(self):
        db = MagicMock()
        user = make_user()
        routine = make_routine(xp=25)

        with patch.object(routine_service, "award_xp", return_value={"awarded": True, "amount": 25}) as award:
            result = routine_service.apply_completion(db, user, routine, True, today=date(2026, 11, 10))

        self.assertTrue(result["completed"])
        self.assertTrue(routine.completed)
        self.assertEqual(result["xp_awarded"], 25)
        self.assertEqual(award.call_count, 1)
        self.assertEqual(award.call_args[0][2], 25)
        self.assertEqual(award.call_args[0][3], "ROUTINE_COMPLETE")

    def test_completing_an_already_completed_routine_does_not_award_again(self):
        db = MagicMock()
        user = make_user()
        routine = make_routine(xp=25, completed=True)

        with patch.object(routine_service, "award_xp", return_value={"awarded": True, "amount": 25}) as award:
            result = routine_service.apply_completion(db, user, routine, True, today=date(2026, 11, 10))

        self.assertEqual(result["xp_awarded"], 0)
        self.assertEqual(award.call_count, 0)

    def test_uncompleting_a_routine_awards_no_xp(self):
        db = MagicMock()
        user = make_user()
        routine = make_routine(xp=25, completed=True)

        with patch.object(routine_service, "award_xp") as award:
            result = routine_service.apply_completion(db, user, routine, False, today=date(2026, 11, 10))

        self.assertFalse(result["completed"])
        self.assertFalse(routine.completed)
        self.assertEqual(result["xp_awarded"], 0)
        self.assertEqual(award.call_count, 0)

    def test_completion_records_when_it_happened(self):
        db = MagicMock()
        user = make_user()
        routine = make_routine()

        with patch.object(routine_service, "award_xp", return_value={"awarded": True, "amount": 25}):
            routine_service.apply_completion(db, user, routine, True, today=date(2026, 11, 10))

        self.assertIsNotNone(routine.completed_at)
        self.assertEqual(routine.last_completed_on, date(2026, 11, 10))

    def test_completion_updates_the_daily_streak(self):
        db = MagicMock()
        user = make_user()
        routine = make_routine()

        with patch.object(routine_service, "award_xp", return_value={"awarded": True, "amount": 25}), \
             patch.object(routine_service, "update_streak", return_value={"current_streak": 1}) as streak:
            result = routine_service.apply_completion(db, user, routine, True, today=date(2026, 11, 10))

        self.assertEqual(streak.call_count, 1)
        self.assertEqual(result["current_streak"], 1)

    def test_uncompleting_does_not_touch_the_streak(self):
        db = MagicMock()
        user = make_user()
        routine = make_routine(completed=True)

        with patch.object(routine_service, "award_xp"), \
             patch.object(routine_service, "update_streak") as streak:
            routine_service.apply_completion(db, user, routine, False, today=date(2026, 11, 10))

        self.assertEqual(streak.call_count, 0)

    def test_already_awarded_transaction_is_not_paid_twice(self):
        """The XP ledger is the source of truth for idempotency."""
        db = MagicMock()
        user = make_user()
        routine = make_routine(completed=False)

        with patch.object(
            routine_service,
            "award_xp",
            return_value={"awarded": False, "reason": "already_awarded", "amount": 25},
        ):
            result = routine_service.apply_completion(db, user, routine, True, today=date(2026, 11, 10))

        self.assertEqual(result["xp_awarded"], 0)


class OwnershipTestCase(unittest.TestCase):
    def test_user_may_delete_a_challenge_they_created(self):
        from app.modules.challenge import service as challenge_service

        db = MagicMock()
        user = make_user()
        challenge = MagicMock()
        challenge.creator_id = user.id

        challenge_service.assert_can_delete(user, challenge)

    def test_user_may_not_delete_someone_elses_challenge(self):
        from app.modules.challenge import service as challenge_service
        from fastapi import HTTPException

        db = MagicMock()
        user = make_user()
        challenge = MagicMock()
        challenge.creator_id = "another-user-id"

        with self.assertRaises(HTTPException) as ctx:
            challenge_service.assert_can_delete(user, challenge)

        self.assertEqual(ctx.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
