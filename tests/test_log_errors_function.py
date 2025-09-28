import unittest
from unittest.mock import patch
import json
import sys
import os

# Add lambda_functions to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda_functions'))

from log_errors_function import handler


class TestLogErrorsFunction(unittest.TestCase):

    @patch('builtins.print')
    def test_logs_error_messages(self, mock_print):
        event = {
            'body': json.dumps({
                'logs': [
                    '[2025-09-27 13:14:00 +0200] Get serial #s task (for device 123) failed',
                    'Network connection timeout'
                ]
            })
        }

        result = handler(event, {})

        self.assertEqual(result['statusCode'], 200)
        self.assertEqual(result['body'], '')
        mock_print.assert_any_call('Apple Wallet Error: [2025-09-27 13:14:00 +0200] Get serial #s task (for device 123) failed')
        mock_print.assert_any_call('Apple Wallet Error: Network connection timeout')

    @patch('builtins.print')
    def test_handles_invalid_json_gracefully(self, mock_print):
        event = {'body': 'invalid-json'}
        result = handler(event, {})

        self.assertEqual(result['statusCode'], 200)
        mock_print.assert_any_call('Error: Invalid JSON in request body.')


if __name__ == '__main__':
    unittest.main()