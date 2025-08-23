"""Unit tests for progress and leveling features.

These tests verify that the XP/level system and streak counting behave as expected.
The tests use FastAPI's TestClient for endpoint-level checks and call the
progress.update_progress function directly for more granular control over dates.
"""

import os
import unittest
import sqlite3

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app import database, progress


class ProgressTestCase(unittest.TestCase):
    """Test suite for XP/level and streak progress functionality."""

    def setUp(self):
        # Remove existing database to ensure a clean state
        db_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'ai_tutoring.db')
        db_path = os.path.abspath(db_path)
        if os.path.exists(db_path):
            os.remove(db_path)
        # Initialize a fresh DB
        database.init_db()
        self.client = TestClient(app)

    def test_xp_and_level_increment(self):
        """Ensure that XP accumulates and the user levels up when passing thresholds."""
        # Register a new user
        res = self.client.post('/register', json={'username': 'lev', 'password': '1234', 'role': 'student'})
        user_id = res.json()['id']
        thread_id = self.client.get(f'/threads/{user_id}').json()[0]['id']
        # Each chat grants default 10 XP. After 15 chats, XP should be 150.
        # According to XP_THRESHOLDS [0,100,250,...], 150 XP corresponds to level 1.
        for _ in range(15):
            self.client.post('/chat', json={'user_id': user_id, 'thread_id': thread_id, 'message': 'dummy'})
        # Fetch dashboard to verify XP and level
        dash = self.client.get(f'/dashboard/{user_id}').json()
        self.assertGreaterEqual(dash['xp'], 150)
        self.assertEqual(dash['level'], 1)
        # A few more chats to cross the next threshold (250 XP -> level 2)
        for _ in range(15):
            self.client.post('/chat', json={'user_id': user_id, 'thread_id': thread_id, 'message': 'dummy2'})
        dash2 = self.client.get(f'/dashboard/{user_id}').json()
        # After 30 chats total, XP >= 300, level should be >= 2
        self.assertGreaterEqual(dash2['xp'], 300)
        self.assertGreaterEqual(dash2['level'], 2)

    def test_streak_counting(self):
        """Verify that streaks increment on consecutive days and reset after a gap."""
        # Manually open a new SQLite connection for direct progress updates
        # Use the same database file as the application. Setting row_factory ensures
        # we can access columns by name.
        db_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'ai_tutoring.db')
        db_path = os.path.abspath(db_path)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        # Register user via API to ensure row exists
        res = self.client.post('/register', json={'username': 'streaker', 'password': 'pass', 'role': 'student'})
        user_id = res.json()['id']
        # On day 1, perform a progress update
        progress.update_progress(user_id, conn, xp_gain=5, current_date='2025-08-01')
        # On day 2 (consecutive), streak should increment
        progress.update_progress(user_id, conn, xp_gain=5, current_date='2025-08-02')
        cur = conn.cursor()
        cur.execute('SELECT streak_count FROM users WHERE id = ?', (user_id,))
        row = cur.fetchone()
        self.assertEqual(row['streak_count'], 2)
        # Skip a day and update on day 4; streak should reset to 1
        progress.update_progress(user_id, conn, xp_gain=5, current_date='2025-08-04')
        cur.execute('SELECT streak_count FROM users WHERE id = ?', (user_id,))
        row2 = cur.fetchone()
        self.assertEqual(row2['streak_count'], 1)
        conn.close()


if __name__ == '__main__':
    unittest.main()
