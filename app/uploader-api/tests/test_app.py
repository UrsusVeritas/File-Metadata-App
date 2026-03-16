import io
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import app


class TestUploaderAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health_check(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['service'], 'uploader-api')

    def test_upload_no_file_part(self):
        response = self.client.post('/upload')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    def test_upload_empty_filename(self):
        data = {'file': (io.BytesIO(b''), '')}
        response = self.client.post('/upload', content_type='multipart/form-data', data=data)
        self.assertEqual(response.status_code, 400)

    def test_upload_disallowed_extension(self):
        data = {'file': (io.BytesIO(b'exec'), 'malware.exe')}
        response = self.client.post('/upload', content_type='multipart/form-data', data=data)
        self.assertEqual(response.status_code, 415)

    def test_upload_no_extension(self):
        data = {'file': (io.BytesIO(b'data'), 'noextension')}
        response = self.client.post('/upload', content_type='multipart/form-data', data=data)
        self.assertEqual(response.status_code, 400)

    @patch('app.s3_client')
    def test_upload_success(self, mock_s3):
        mock_s3.upload_fileobj.return_value = None
        data = {'file': (io.BytesIO(b'test content'), 'test.txt')}
        response = self.client.post('/upload', content_type='multipart/form-data', data=data)
        self.assertEqual(response.status_code, 201)
        resp_data = response.get_json()
        self.assertIn('filename', resp_data)
        self.assertIn('bucket', resp_data)
        self.assertTrue(resp_data['filename'].endswith('.txt'))

    @patch('app.s3_client')
    def test_upload_s3_failure(self, mock_s3):
        mock_s3.upload_fileobj.side_effect = Exception("S3 connection error")
        data = {'file': (io.BytesIO(b'test content'), 'test.txt')}
        response = self.client.post('/upload', content_type='multipart/form-data', data=data)
        self.assertEqual(response.status_code, 500)


if __name__ == '__main__':
    unittest.main()
