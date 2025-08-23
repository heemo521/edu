"""Integration tests for summary endpoints."""

import os
import unittest

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app import database


class SummaryTestCase(unittest.TestCase):
    """Ensure summaries can be created, retrieved and updated."""

    def setUp(self):
        db_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'ai_tutoring.db')
        db_path = os.path.abspath(db_path)
        if os.path.exists(db_path):
            os.remove(db_path)
        database.init_db()
        self.client = TestClient(app)

    def test_summary_crud(self):
        # Register a user and obtain their default thread
        reg = self.client.post('/register', json={'username': 'sum', 'password': 'pw', 'role': 'student'})
        self.assertEqual(reg.status_code, 201)
        user_id = reg.json()['id']
        thread_id = self.client.get(f'/threads/{user_id}').json()[0]['id']

        # Create a summary for the thread
        res = self.client.post('/summaries', json={'user_id': user_id, 'thread_id': thread_id, 'summary': 'hello'})
        self.assertEqual(res.status_code, 201)

        # Retrieve the summary
        get_res = self.client.get(f'/summaries/{user_id}/{thread_id}')
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()['summary'], 'hello')

        # Update the summary
        upd = self.client.put('/summaries', json={'user_id': user_id, 'thread_id': thread_id, 'summary': 'updated'})
        self.assertEqual(upd.status_code, 200)

        # Confirm the update persisted
        get_res2 = self.client.get(f'/summaries/{user_id}/{thread_id}')
        self.assertEqual(get_res2.status_code, 200)
        self.assertEqual(get_res2.json()['summary'], 'updated')


if __name__ == '__main__':  # pragma: no cover
    unittest.main()

