import os
import unittest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app import database

class PlanTestCase(unittest.TestCase):
    def setUp(self):
        db_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'ai_tutoring.db')
        db_path = os.path.abspath(db_path)
        if os.path.exists(db_path):
            os.remove(db_path)
        database.init_db()
        self.client = TestClient(app)

    def test_plan_lifecycle(self):
        # register user
        reg = self.client.post('/register', json={'username':'planner','password':'pw','role':'student'})
        self.assertEqual(reg.status_code, 201)
        user_id = reg.json()['id']
        # fetch topics
        topics = self.client.get('/topics').json()
        t1 = topics[0]['id']
        t2 = topics[1]['id']
        # create goals
        g1 = self.client.post('/goals', json={'user_id':user_id,'topic_id':t1,'description':'g1','target_sessions':2})
        self.assertEqual(g1.status_code,201)
        g2 = self.client.post('/goals', json={'user_id':user_id,'topic_id':t2,'description':'g2','target_sessions':3})
        self.assertEqual(g2.status_code,201)
        g1_id = g1.json()['id']
        g2_id = g2.json()['id']
        # create plan
        plan_res = self.client.post(
            '/plans',
            json={
                'user_id': user_id,
                'goal_ids': [g1_id, g2_id],
                'due_date': '2025-01-01',
                'recurrence': 'weekly'
            }
        )
        self.assertEqual(plan_res.status_code, 201)
        plan = plan_res.json()
        self.assertEqual(len(plan['goals']), 2)
        plan_id = plan['id']
        # get plans
        plans_list = self.client.get(f'/plans/{user_id}')
        self.assertEqual(plans_list.status_code,200)
        self.assertEqual(len(plans_list.json()),1)
        # delete plan
        del_res = self.client.delete(f'/plans/{plan_id}')
        self.assertEqual(del_res.status_code,200)
        # ensure deleted
        plans_list2 = self.client.get(f'/plans/{user_id}')
        self.assertEqual(plans_list2.status_code,200)
        self.assertEqual(plans_list2.json(),[])

if __name__ == '__main__':
    unittest.main()
