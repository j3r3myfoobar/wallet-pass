import unittest
from unittest.mock import patch
import sys
import os

# Add lambda_functions to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda_functions'))

import common


class TestCommon(unittest.TestCase):

    @patch.dict(os.environ, {'AUTH_TOKEN': 'test-token'})
    @patch('builtins.print')
    def test_valid_authorization(self, mock_print):
        event = {'headers': {'authorization': 'ApplePass test-token'}}
        result = common.validate_authorization(event)
        self.assertIsNone(result)

    @patch.dict(os.environ, {'AUTH_TOKEN': 'test-token'})
    @patch('builtins.print')
    def test_authorization_failures(self, mock_print):
        failure_cases = [
            ({}, 'Authorization header is missing'),
            ({'headers': {}}, 'Authorization header is missing'),
            ({'headers': {'authorization': ''}}, 'Authorization header is missing'),
            ({'headers': {'authorization': 'wrong-token'}}, 'Authorization failed'),
            ({'headers': {'authorization': 'Bearer test-token'}}, 'Authorization failed'),
        ]

        for event, expected_error_start in failure_cases:
            with self.subTest(event=event):
                result = common.validate_authorization(event)
                self.assertEqual(result['statusCode'], 401)
                self.assertEqual(result['body'], 'Unauthorized')

    @patch.dict(os.environ, {})
    @patch('builtins.print')
    def test_missing_env_var_returns_500(self, mock_print):
        event = {'headers': {'authorization': 'ApplePass some-token'}}
        result = common.validate_authorization(event)
        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(result['body'], 'Internal Server Error')


if __name__ == '__main__':
    unittest.main()