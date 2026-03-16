import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import app


class TestMetadataService(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health_check(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['service'], 'metadata-service')

    def test_process_no_file_part(self):
        response = self.client.post('/process')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    def test_process_empty_filename(self):
        data = {'file': (io.BytesIO(b''), '')}
        response = self.client.post('/process', content_type='multipart/form-data', data=data)
        self.assertEqual(response.status_code, 400)

    def test_process_returns_metadata(self):
        content = b'hello world'
        data = {'file': (io.BytesIO(content), 'test.txt')}
        response = self.client.post('/process', content_type='multipart/form-data', data=data)
        self.assertEqual(response.status_code, 200)
        resp_data = response.get_json()
        self.assertEqual(resp_data['filename'], 'test.txt')
        self.assertEqual(resp_data['extension'], 'txt')
        self.assertEqual(resp_data['size_bytes'], len(content))
        self.assertIn('processed_at', resp_data)
        self.assertEqual(resp_data['service'], 'metadata-service')

    def test_process_file_without_extension(self):
        data = {'file': (io.BytesIO(b'data'), 'noextension')}
        response = self.client.post('/process', content_type='multipart/form-data', data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['extension'], 'unknown')


if __name__ == '__main__':
    unittest.main()
