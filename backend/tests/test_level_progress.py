"""Tests for the canonical level/XP progression service.

`calculate_level_and_progress` is the single source of truth for the level
number and the progress-bar percentage, so the API and the dashboard can never
disagree.
"""
import unittest

from app.modules.game.service import calculate_level_and_progress


class ZeroXpStartTestCase(unittest.TestCase):
    def test_zero_xp_starts_at_level_one_with_an_empty_bar(self):
        result = calculate_level_and_progress(0)
        self.assertEqual(result["level"], 1)
        self.assertEqual(result["current_level_min_xp"], 0)
        self.assertEqual(result["xp_in_level"], 0)
        self.assertEqual(result["progress_percent"], 0.0)

    def test_zero_xp_reports_the_full_first_level_span(self):
        result = calculate_level_and_progress(0)
        self.assertEqual(result["next_level_xp"], 283)
        self.assertEqual(result["level_xp_span"], 283)

    def test_negative_xp_behaves_like_zero(self):
        result = calculate_level_and_progress(-500)
        self.assertEqual(result["level"], 1)
        self.assertEqual(result["xp_in_level"], 0)
        self.assertEqual(result["progress_percent"], 0.0)


class LevelFormulaTestCase(unittest.TestCase):
    def test_level_formula(self):
        # level = floor((xp / 100) ** (1 / 1.5)) + 1
        for xp in (1, 50, 100, 150, 282, 283, 500, 1000, 519):
            expected = int((xp / 100.0) ** (1.0 / 1.5)) + 1
            self.assertEqual(
                calculate_level_and_progress(xp)["level"], expected, f"xp={xp}"
            )

    def test_level_one_holds_until_100_xp(self):
        self.assertEqual(calculate_level_and_progress(1)["level"], 1)
        self.assertEqual(calculate_level_and_progress(99)["level"], 1)

    def test_level_two_starts_at_100_xp(self):
        self.assertEqual(calculate_level_and_progress(100)["level"], 2)
        self.assertEqual(calculate_level_and_progress(282)["level"], 2)

    def test_level_three_starts_at_283_xp(self):
        self.assertEqual(calculate_level_and_progress(283)["level"], 3)


class ProgressBoundsTestCase(unittest.TestCase):
    def test_level_bounds_for_150_xp(self):
        result = calculate_level_and_progress(150)
        self.assertEqual(result["level"], 2)
        self.assertEqual(result["current_level_min_xp"], 100)
        self.assertEqual(result["next_level_xp"], 282)
        self.assertEqual(result["xp_in_level"], 50)
        self.assertEqual(result["level_xp_span"], 182)
        self.assertAlmostEqual(result["progress_percent"], 27.47, places=2)

    def test_progress_is_never_negative(self):
        for xp in (0, 1, 50, 100, 150, 282, 1000):
            self.assertGreaterEqual(
                calculate_level_and_progress(xp)["progress_percent"], 0.0
            )

    def test_progress_never_exceeds_100(self):
        for xp in (0, 1, 50, 100, 150, 282, 283, 519, 1000, 100_000):
            self.assertLessEqual(
                calculate_level_and_progress(xp)["progress_percent"], 100.0
            )

    def test_xp_in_level_never_negative(self):
        for xp in (0, 1, 50, 100, 150, 282, 283, 1000):
            self.assertGreaterEqual(
                calculate_level_and_progress(xp)["xp_in_level"], 0
            )

    def test_more_xp_never_reduces_progress_within_a_level(self):
        """The bar shows progress *inside* the current level.

        Progress therefore resets to ~0% when a new level starts, but it must
        never go backwards while the level stays the same.
        """
        for level in (1, 2, 3):
            xps = [xp for xp in range(0, 2000) if calculate_level_and_progress(xp)["level"] == level]
            previous = -1.0
            for xp in xps:
                current = calculate_level_and_progress(xp)["progress_percent"]
                self.assertGreaterEqual(current, previous, f"xp={xp} level={level}")
                previous = current

    def test_progress_resets_at_a_level_boundary(self):
        """99 XP fills level 1; 100 XP opens level 2 at 0%."""
        self.assertAlmostEqual(
            calculate_level_and_progress(99)["progress_percent"], 99.0, places=2
        )
        self.assertEqual(calculate_level_and_progress(100)["progress_percent"], 0.0)
        self.assertEqual(calculate_level_and_progress(100)["level"], 2)


class BarRenderingTestCase(unittest.TestCase):
    """The bar must be empty (0%) exactly when the account has no XP."""

    def test_fresh_account_renders_an_empty_bar(self):
        result = calculate_level_and_progress(0)
        self.assertEqual(result["progress_percent"], 0.0)
        self.assertEqual(result["xp_in_level"], 0)

    def test_first_xp_moves_the_bar_off_zero(self):
        result = calculate_level_and_progress(1)
        self.assertGreater(result["progress_percent"], 0.0)

    def test_result_exposes_every_key_the_dashboard_needs(self):
        result = calculate_level_and_progress(150)
        for key in (
            "level",
            "current_level_min_xp",
            "next_level_xp",
            "xp_in_level",
            "level_xp_span",
            "progress_percent",
        ):
            self.assertIn(key, result)


if __name__ == "__main__":
    unittest.main()
