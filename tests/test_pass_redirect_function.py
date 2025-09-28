import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add lambda_functions to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda_functions'))

from pass_redirect_function import handler


class TestPassRedirectFunction(unittest.TestCase):

    @patch('pass_redirect_function.s3')
    @patch.dict(os.environ, {'S3_BUCKET_NAME': 'test-bucket'})
    def test_apple_user_agents_return_pkpass(self, mock_s3):
        mock_s3.get_object.return_value = {
            'Body': MagicMock(read=MagicMock(return_value=b'fake-pkpass-content'))
        }

        apple_agents = ['iPhone iOS 17.0', 'iPad iOS 17.0', 'Macintosh; Intel Mac OS X 10_15_7', 'passd/1.0 CFNetwork/1410.0.3 Darwin/22.6.0']

        for user_agent in apple_agents:
            with self.subTest(user_agent=user_agent):
                event = {'headers': {'User-Agent': user_agent}}
                result = handler(event, {})

                self.assertEqual(result['statusCode'], 200)
                self.assertEqual(result['headers']['Content-Type'], 'application/vnd.apple.pkpass')
                self.assertEqual(result['headers']['Content-Disposition'], 'attachment; filename="pass.pkpass"')
                self.assertTrue(result['isBase64Encoded'])

        self.assertEqual(mock_s3.get_object.call_count, len(apple_agents))

    @patch('pass_redirect_function.s3')
    @patch.dict(os.environ, {'S3_BUCKET_NAME': 'test-bucket'})
    def test_non_apple_user_agents_return_vcard(self, mock_s3):
        mock_s3.get_object.return_value = {
            'Body': MagicMock(read=MagicMock(return_value=b'fake-vcard-content'))
        }

        non_apple_agents = ['Mozilla/5.0 (Linux; Android 10)', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', None]

        for user_agent in non_apple_agents:
            with self.subTest(user_agent=user_agent):
                headers = {'User-Agent': user_agent} if user_agent else {}
                event = {'headers': headers}
                result = handler(event, {})

                self.assertEqual(result['statusCode'], 200)
                self.assertEqual(result['headers']['Content-Type'], 'text/vcard')
                self.assertEqual(result['headers']['Content-Disposition'], 'attachment; filename="contact.vcard"')
                self.assertTrue(result['isBase64Encoded'])

        self.assertEqual(mock_s3.get_object.call_count, len(non_apple_agents))

    @patch('pass_redirect_function.s3')
    @patch.dict(os.environ, {'S3_BUCKET_NAME': 'test-bucket'})
    def test_s3_error_returns_500(self, mock_s3):
        mock_s3.get_object.side_effect = Exception('S3 error')
        event = {'headers': {'User-Agent': 'iPhone'}}
        result = handler(event, {})

        self.assertEqual(result['statusCode'], 500)
        self.assertIn('Error retrieving file from storage', result['body'])

    @patch.dict(os.environ, {})
    def test_missing_s3_bucket_env_var(self):
        event = {'headers': {'User-Agent': 'iPhone'}}
        result = handler(event, {})
        self.assertEqual(result['statusCode'], 500)


if __name__ == '__main__':
    unittest.main()