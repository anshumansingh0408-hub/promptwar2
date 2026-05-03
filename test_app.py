import unittest
import json
from app import app, ip_requests

class ElectionGuideTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        app.testing = True
        # Clear rate limit dictionary before each test
        ip_requests.clear()

    def test_index_route(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    def test_chat_empty_message(self):
        response = self.app.post('/chat', json={"message": "   "})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data["code"], "EMPTY_MESSAGE")

    def test_chat_missing_message(self):
        response = self.app.post('/chat')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data["code"], "INVALID_JSON")

    def test_chat_message_too_long(self):
        long_message = "a" * 501
        response = self.app.post('/chat', json={"message": long_message})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data["code"], "MESSAGE_TOO_LONG")

    def test_rate_limit(self):
        # Send 20 requests rapidly with empty message to avoid hitting the real API
        for _ in range(20):
            response = self.app.post('/chat', json={"message": ""})
            self.assertEqual(response.status_code, 400)
        
        # The 21st request should be rate limited
        response = self.app.post('/chat', json={"message": ""})
        self.assertEqual(response.status_code, 429)
        data = json.loads(response.data)
        self.assertEqual(data["code"], "RATE_LIMIT_EXCEEDED")

    def test_security_headers(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('X-Frame-Options', response.headers)
        self.assertEqual(response.headers['X-Frame-Options'], 'DENY')

if __name__ == "__main__":
    unittest.main()
