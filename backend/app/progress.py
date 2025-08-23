"""Progress and leveling utilities for the AI Tutoring application.

This module encapsulates logic for updating a user's experience points (XP), level and
daily streak. The level is derived from XP thresholds defined in XP_THRESHOLDS. A user
gains a configurable amount of XP per action (e.g., per chat message). The daily
streak increases when the user interacts with the system on consecutive days and
resets when a day is missed.
"""

from __future__ import annotations

import sqlite3
import datetime
from typing import Tuple, Optional

# Define XP thresholds for leveling. Index 0 corresponds to level 0, index 1 to
# level 1, etc. A user must accumulate at least the XP value at the next index
# to reach that level. For example, if XP_THRESHOLDS = [0, 100, 250, 500], a user
# with 120 XP has reached level 1 (>=100) but not level 2 (>=250).
XP_THRESHOLDS: list[int] = [0, 100, 250, 500, 1000, 2000]


def update_progress(
    user_id: int,
    db: sqlite3.Connection,
    xp_gain: int = 10,
    current_date: Optional[str] = None,
) -> Tuple[int, int, int]:
    """Update a user's XP, level and streak based on a new action.

    Args:
        user_id: The ID of the user whose progress is being updated.
        db: An open SQLite connection.
        xp_gain: The amount of experience points to add for this action.
        current_date: Optional ISO date string (YYYY-MM-DD) used for testing. If
            None, the current system date is used.

    Returns:
        A tuple (new_xp, new_level, new_streak) reflecting the updated progress.

    The function performs the following steps:
        1. Retrieves the user's existing XP, level, streak_count and last_streak_date.
        2. Adds xp_gain to the XP.
        3. Determines the new level based on XP_THRESHOLDS.
        4. Calculates the new streak_count: if the previous streak date is yesterday,
           increment the streak; if it's the same day, preserve; otherwise reset to 1.
        5. Persists the updated values back to the users table.
    """
    cursor = db.cursor()
    cursor.execute(
        "SELECT xp, level, streak_count, last_streak_date FROM users WHERE id = ?",
        (user_id,),
    )
    row = cursor.fetchone()
    # Initialize defaults if user not found or columns missing
    if not row:
        raise ValueError(f"User with id {user_id} does not exist")
    current_xp = row["xp"] if row["xp"] is not None else 0
    current_level = row["level"] if row["level"] is not None else 0
    current_streak = row["streak_count"] if row["streak_count"] is not None else 0
    last_date_str = row["last_streak_date"]
    # Update XP
    new_xp = current_xp + xp_gain
    # Determine new level by finding the highest threshold not exceeding new_xp
    new_level = current_level
    for idx in range(current_level + 1, len(XP_THRESHOLDS)):
        if new_xp >= XP_THRESHOLDS[idx]:
            new_level = idx
        else:
            break
    # Determine date for streak computation
    today_date = (
        datetime.date.fromisoformat(current_date)
        if current_date is not None
        else datetime.date.today()
    )
    last_date = None
    if last_date_str:
        try:
            last_date = datetime.date.fromisoformat(last_date_str)
        except ValueError:
            last_date = None
    # Compute new streak: start at 1 if no previous date
    if last_date is None:
        new_streak = 1
    else:
        delta_days = (today_date - last_date).days
        if delta_days == 0:
            # same day, preserve streak
            new_streak = current_streak
        elif delta_days == 1:
            # consecutive day, increment streak
            new_streak = current_streak + 1
        else:
            # missed a day or more, reset
            new_streak = 1
    # Persist updates
    cursor.execute(
        "UPDATE users SET xp = ?, level = ?, streak_count = ?, last_streak_date = ? WHERE id = ?",
        (
            new_xp,
            new_level,
            new_streak,
            today_date.isoformat(),
            user_id,
        ),
    )
    db.commit()
    return new_xp, new_level, new_streak