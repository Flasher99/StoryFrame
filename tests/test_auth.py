import unittest, uuid
from fastapi.testclient import TestClient
from backend.app import app

class AuthTests(unittest.TestCase):
    def test_registration_login_logout_and_project_isolation(self):
        a=TestClient(app)
        b=TestClient(app)
        self.assertEqual(a.get('/api/projects').status_code,401)
        self.assertEqual(a.post('/api/demo').status_code,401)
        email=f'auth-{uuid.uuid4().hex}@example.com'
        reg=a.post('/api/auth/register',json={'name':'Alice','email':email,'password':'securepass987'})
        self.assertEqual(reg.status_code,200,reg.text)
        self.assertEqual(reg.json()['name'],'Alice')
        self.assertEqual(a.get('/api/auth/me').status_code,200)
        self.assertEqual(a.post('/api/auth/register',json={'name':'Again','email':email,'password':'securepass987'}).status_code,409)
        self.assertEqual(b.post('/api/auth/login',json={'email':email,'password':'wrongpass123'}).status_code,401)
        p=a.post('/api/demo').json()
        self.assertIn(p['id'],[x['id'] for x in a.get('/api/projects').json()])
        self.assertEqual(b.get(f"/api/projects/{p['id']}").status_code,401)
        self.assertEqual(b.post('/api/auth/login',json={'email':email,'password':'securepass987'}).status_code,200)
        self.assertEqual(b.get(f"/api/projects/{p['id']}").status_code,200)
        c=TestClient(app)
        other=c.post('/api/auth/register',json={'name':'Bob','email':f'bob-{uuid.uuid4().hex}@example.com','password':'secretpass123'})
        self.assertEqual(other.status_code,200)
        self.assertEqual(c.get(f"/api/projects/{p['id']}").status_code,404)
        self.assertEqual(c.get(f"/api/projects/{p['id']}/video").status_code,404)
        self.assertEqual(a.post('/api/auth/logout').status_code,200)
        self.assertEqual(a.get('/api/auth/me').status_code,401)
        self.assertEqual(b.get('/api/auth/me').status_code,200)
    def test_removed_google_signin_endpoint(self):
        client=TestClient(app)
        self.assertEqual(client.post('/api/auth/google',json={'credential':'x'*30}).status_code,404)
        self.assertEqual(client.get('/api/auth/config').status_code,404)
