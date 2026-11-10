"""Level / XP progression maths.

Thin compatibility layer over :mod:`app.modules.game.service`, which is the
single source of truth for the level number and the progress percentage.

XP required to *reach* level L:  ``100 * L ** 1.5``
Level from lifetime XP::

    level = floor((lifetime_xp / 100) ** (1 / 1.5)) + 1

so a brand-new account with 0 XP sits at level 1 with an **empty 0%** bar.
"""

import math

from app.modules.game.service import (
    FIRST_LEVEL_SPAN,
    XP_BASE,
    XP_EXPONENT,
    calculate_level,
    calculate_level_and_progress,
)

__all__ = [
    "FIRST_LEVEL_SPAN",
    "XP_BASE",
    "XP_EXPONENT",
    "calculate_level",
    "calculate_level_and_progress",
    "xp_threshold_for_level",
    "xp_for_next_level",
    "level_xp_span",
    "calculate_progress",
]


def xp_threshold_for_level(level: int) -> int:
    """Cumulative lifetime XP required to reach `level` (level 0 -> 0 XP)."""
    if level <= 0:
        return 0
    return int(math.floor(XP_BASE * (level ** XP_EXPONENT)))


def xp_for_next_level(level: int) -> int:
    """Cumulative lifetime XP required to reach the next level."""
    if level < 1:
        level = 1
    return xp_threshold_for_level(level + 1)


def level_xp_span(level: int) -> int:
    """XP needed to advance from `level` to `level + 1`."""
    if level < 1:
        level = 1
    return max(1, xp_threshold_for_level(level) - xp_threshold_for_level(level - 1))


def calculate_progress(lifetime_xp: int) -> dict:
    """Level progress details, in the shape the API has always returned."""
    if lifetime_xp is None or lifetime_xp < 0:
        lifetime_xp = 0

    canonical = calculate_level_and_progress(lifetime_xp)

    return {
        "level": canonical["level"],
        # XP earned inside the current level.
        "current_level_xp": canonical["xp_in_level"],
        # XP needed to finish the current level.
        "next_level_xp": canonical["level_xp_span"],
        "progress_percentage": canonical["progress_percent"],
        # The canonical keys, so callers can use either shape.
        "current_level_min_xp": canonical["current_level_min_xp"],
        "xp_in_level": canonical["xp_in_level"],
        "level_xp_span": canonical["level_xp_span"],
        "progress_percent": canonical["progress_percent"],
        "lifetime_xp": lifetime_xp,
    }
