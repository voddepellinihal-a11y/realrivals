"""Canonical level / XP progression service.

This is the single source of truth for the level number and the progress-bar
percentage, so the API (``/game/profile``, ``/auth/me``) and the dashboard can
never disagree.

XP required to *reach* level L is ``100 * L ** 1.5`` and the level for a given
amount of lifetime XP is::

    level = floor((lifetime_xp / 100) ** (1 / 1.5)) + 1

so a brand-new account with 0 XP sits at level 1 with an **empty 0%** bar.
"""

import math

XP_BASE = 100
XP_EXPONENT = 1.5

#: XP needed to go from level 1 to level 2 (100 * 2 ** 1.5 rounded up).
FIRST_LEVEL_SPAN = 283

PROOF_TYPES = ("photo", "text", "link")


def calculate_level_and_progress(lifetime_xp: int) -> dict:
    """Compute current level, level bounds, and exact percentage progress.

    Ensures 0 XP starts cleanly at 0.0%.
    """
    if lifetime_xp is None or lifetime_xp <= 0:
        return {
            "level": 1,
            "current_level_min_xp": 0,
            "next_level_xp": FIRST_LEVEL_SPAN,
            "xp_in_level": 0,
            "level_xp_span": FIRST_LEVEL_SPAN,
            "progress_percent": 0.0,
        }

    # Level formula: XP = 100 * (L ^ 1.5)
    level = int(math.floor(math.pow(lifetime_xp / 100.0, 1.0 / 1.5))) + 1

    current_level_min_xp = int(100 * math.pow(level - 1, 1.5))
    next_level_xp = int(100 * math.pow(level, 1.5))

    xp_in_level = lifetime_xp - current_level_min_xp
    level_xp_span = next_level_xp - current_level_min_xp

    if level_xp_span <= 0:
        progress_percent = 100.0
    else:
        progress_percent = min(100.0, max(0.0, (xp_in_level / level_xp_span) * 100.0))

    return {
        "level": level,
        "current_level_min_xp": current_level_min_xp,
        "next_level_xp": next_level_xp,
        "xp_in_level": xp_in_level,
        "level_xp_span": level_xp_span,
        "progress_percent": round(progress_percent, 2),
    }


def calculate_level(lifetime_xp: int) -> int:
    """The level for a given amount of lifetime XP (0 XP -> level 1)."""
    return calculate_level_and_progress(lifetime_xp)["level"]
