import os
import sys
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import app


class TestBrowserAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health_check(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['service'], 'browser-api')

    @patch('app.boto3.client')
    def test_list_empty_bucket(self, mock_boto3):
        mock_s3 = MagicMock()
        mock_boto3.return_value = mock_s3
        mock_s3.list_objects_v2.return_value = {}

        response = self.client.get('/list')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['count'], 0)
        self.assertEqual(data['files'], [])

    @patch('app.boto3.client')
    def test_list_with_files(self, mock_boto3):
        mock_s3 = MagicMock()
        mock_boto3.return_value = mock_s3
        mock_s3.list_objects_v2.return_value = {
            'Contents': [
                {
                    'Key': 'abc123.txt',
                    'Size': 1024,
                    'LastModified': datetime(2024, 1, 15, 12, 0, 0),
                    'ETag': '"deadbeef"',
                }
            ]
        }

        response = self.client.get('/list')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['files'][0]['key'], 'abc123.txt')
        self.assertEqual(data['files'][0]['size_bytes'], 1024)
        self.assertEqual(data['files'][0]['etag'], 'deadbeef')

    @patch('app.boto3.client')
    def test_list_s3_error(self, mock_boto3):
        mock_s3 = MagicMock()
        mock_boto3.return_value = mock_s3
        mock_s3.list_objects_v2.side_effect = Exception("S3 connection error")

        response = self.client.get('/list')
        self.assertEqual(response.status_code, 500)
        self.assertIn('error', response.get_json())

    @patch('app.boto3.client')
    def test_list_max_keys_capped_at_200(self, mock_boto3):
        mock_s3 = MagicMock()
        mock_boto3.return_value = mock_s3
        mock_s3.list_objects_v2.return_value = {}

        self.client.get('/list?max_keys=9999')
        call_kwargs = mock_s3.list_objects_v2.call_args[1]
        self.assertLessEqual(call_kwargs['MaxKeys'], 200)


if __name__ == '__main__':
    unittest.main()
