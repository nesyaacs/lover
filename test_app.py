import unittest
import json
import app
import database

class ScrapbookTestCase(unittest.TestCase):

    def setUp(self):
        app.app.config['TESTING'] = True
        self.client = app.app.test_client()
        database.init_db()

    def test_index_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Mensiversary', response.data)

    def test_api_visit_logging(self):
        payload = {'name': 'nama'}
        response = self.client.post('/api/visit', 
                                    data=json.dumps(payload),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')

    def test_admin_authentication(self):
        # 1. Unauthenticated access to /admin should redirect to /admin/login
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login', response.headers['Location'])

        # 2. Wrong password attempt
        login_res = self.client.post('/admin/login', data={
            'username': 'admin',
            'password': 'wrongpassword'
        })
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b'Username atau password yang kamu masukkan salah!', login_res.data)

        # 3. Successful login attempt
        login_success = self.client.post('/admin/login', data={
            'username': 'nesya',
            'password': 'neysadmin'
        }, follow_redirects=True)
        self.assertEqual(login_success.status_code, 200)
        self.assertIn(b'Monitoring Dashboard Admin', login_success.data)

        # 4. Logout attempt
        logout_res = self.client.get('/admin/logout')
        self.assertEqual(logout_res.status_code, 302)

if __name__ == '__main__':
    unittest.main()
