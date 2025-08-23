"""Unit tests for AI Tutoring MVP backend endpoints.

Uses Python's built-in unittest framework and FastAPI's TestClient to test
registration, login, chat, history, dashboard and subscription functionality.
"""

import os
import unittest

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app import database


class APITestCase(unittest.TestCase):
    """Test suite for the AI tutoring backend."""

    def setUp(self):
        # Remove existing database to ensure a clean state
        db_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'ai_tutoring.db')
        # Resolve absolute path
        db_path = os.path.abspath(db_path)
        if os.path.exists(db_path):
            os.remove(db_path)
        # Reinitialize DB
        database.init_db()
        self.client = TestClient(app)

    def test_registration_and_login(self):
        # Register new user
        res = self.client.post('/register', json={'username': 'test', 'password': 'pass1', 'role': 'student'})
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertIn('id', data)
        # Duplicate registration should fail
        dup = self.client.post('/register', json={'username': 'test', 'password': 'pass2', 'role': 'student'})
        self.assertEqual(dup.status_code, 400)
        # Login with correct password
        login = self.client.post('/login', json={'username': 'test', 'password': 'pass1'})
        self.assertEqual(login.status_code, 200)
        self.assertIn('user_id', login.json())
        # Login with incorrect password
        bad_login = self.client.post('/login', json={'username': 'test', 'password': 'wrong'})
        self.assertEqual(bad_login.status_code, 401)

    def test_chat_history_and_dashboard(self):
        # Setup user
        reg = self.client.post('/register', json={'username': 'alice', 'password': 'wonder', 'role': 'student'})
        user_id = reg.json()['id']
        threads = self.client.get(f'/threads/{user_id}').json()
        thread_id = threads[0]['id']
        # Chat interactions
        self.client.post(
            '/chat', json={'user_id': user_id, 'thread_id': 1, 'message': 'What is 1+1?'}
        )
        self.client.post(
            '/chat', json={'user_id': user_id, 'thread_id': 1, 'message': 'OK'}
        )
        # History
        hist = self.client.get(f'/history/{user_id}/1')
        self.client.post('/chat', json={'user_id': user_id, 'thread_id': thread_id, 'message': 'What is 1+1?'})
        self.client.post('/chat', json={'user_id': user_id, 'thread_id': thread_id, 'message': 'OK'})
        # History
        hist = self.client.get(f'/history/{user_id}/{thread_id}')
        self.assertEqual(hist.status_code, 200)
        history = hist.json()
        self.assertEqual(len(history), 2)
        # Dashboard
        dash = self.client.get(f'/dashboard/{user_id}')
        self.assertEqual(dash.status_code, 200)
        summary = dash.json()
        self.assertEqual(summary['total_messages'], 2)

    def test_subscription(self):
        reg = self.client.post('/register', json={'username': 'bob', 'password': 'builder', 'role': 'parent'})
        user_id = reg.json()['id']
        # Check default subscription
        sub = self.client.get(f'/subscription/{user_id}')
        self.assertEqual(sub.status_code, 200)
        self.assertEqual(sub.json()['status'], 'inactive')
        # Activate subscription
        act = self.client.post('/subscribe', json={'user_id': user_id, 'action': 'activate'})
        self.assertEqual(act.status_code, 200)
        self.assertEqual(act.json()['status'], 'active')
        # Cancel subscription
        cancel = self.client.post('/subscribe', json={'user_id': user_id, 'action': 'cancel'})
        self.assertEqual(cancel.status_code, 200)
        self.assertEqual(cancel.json()['status'], 'inactive')

    def test_goal_templates(self):
        # Register user
        reg = self.client.post('/register', json={'username': 'sara', 'password': 'pass', 'role': 'student'})
        user_id = reg.json()['id']

        # Generate goals from math template
        res = self.client.post(f'/goals/templates/math', json={'user_id': user_id})
        self.assertEqual(res.status_code, 201)
        goals = res.json()
        self.assertEqual(len(goals), 2)

        # Verify goals persisted
        list_res = self.client.get(f'/goals/{user_id}')
        self.assertEqual(list_res.status_code, 200)
        self.assertEqual(len(list_res.json()), 2)
    def test_summary_crud(self):
        reg = self.client.post('/register', json={'username': 'sum', 'password': 'pass', 'role': 'student'})
        user_id = reg.json()['id']
        thread_id = self.client.get(f'/threads/{user_id}').json()[0]['id']
        # Create summary
        res = self.client.post('/summaries', json={'user_id': user_id, 'thread_id': thread_id, 'summary': 'hello'})
        self.assertEqual(res.status_code, 201)
        # Read summary
        get_res = self.client.get(f'/summaries/{user_id}/{thread_id}')
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()['summary'], 'hello')
        # Update summary
        upd = self.client.put('/summaries', json={'user_id': user_id, 'thread_id': thread_id, 'summary': 'updated'})
        self.assertEqual(upd.status_code, 200)
        get_res2 = self.client.get(f'/summaries/{user_id}/{thread_id}')
        self.assertEqual(get_res2.json()['summary'], 'updated')


if __name__ == '__main__':
    unittest.main()
