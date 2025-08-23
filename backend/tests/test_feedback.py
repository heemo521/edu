"""Tests for feedback endpoints."""

import os
import unittest

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app import database


class FeedbackTestCase(unittest.TestCase):
    """Ensure feedback can be created and retrieved."""

    def setUp(self):
        db_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'ai_tutoring.db')
        db_path = os.path.abspath(db_path)
        if os.path.exists(db_path):
            os.remove(db_path)
        database.init_db()
        self.client = TestClient(app)

    def test_feedback_flow(self):
        # Register a user
        res = self.client.post('/register', json={'username': 'fbuser', 'password': 'pw', 'role': 'student'})
        self.assertEqual(res.status_code, 201)
        user_id = res.json()['id']

        # Use first topic for feedback
        topics = self.client.get('/topics').json()
        topic_id = topics[0]['id']

        # Submit feedback
        fb_res = self.client.post(
            '/feedback',
            json={'user_id': user_id, 'topic_id': topic_id, 'rating': 4, 'comments': 'Great'}
        )
        self.assertEqual(fb_res.status_code, 201)
        fb_id = fb_res.json()['id']

        # Retrieve feedback for topic
        list_res = self.client.get(f'/feedback/{topic_id}')
        self.assertEqual(list_res.status_code, 200)
        data = list_res.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], fb_id)
        self.assertEqual(data[0]['rating'], 4)
        self.assertEqual(data[0]['comments'], 'Great')


if __name__ == '__main__':
    unittest.main()

