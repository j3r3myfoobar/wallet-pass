import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Add lambda_functions to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda_functions'))

from passkit_unregistration_function import handler


class TestPasskitUnregistrationFunction(unittest.TestCase):

    @patch('passkit_unregistration_function.table')
    @patch('passkit_unregistration_function.common.validate_authorization')
    @patch.dict(os.environ, {'TABLE_NAME': 'test-table', 'AUTH_TOKEN': 'test-token'})
    def test_successful_unregistration(self, mock_validate_auth, mock_table):
        # Setup
        mock_validate_auth.return_value = None  # No auth error
        mock_table.delete_item.return_value = None

        event = {
            'pathParameters': {
                'deviceLibraryIdentifier': 'test-device-123',
                'passTypeIdentifier': 'pass.tel.lemaire.business',
                'serialNumber': 'pass-v5'
            },
            'headers': {
                'Authorization': 'ApplePass test-token'
            }
        }

        # Execute
        result = handler(event, {})

        # Assert
        self.assertEqual(result['statusCode'], 200)
        self.assertEqual(result['body'], '')

        # Verify DynamoDB delete operation
        mock_table.delete_item.assert_called_once_with(
            Key={
                'pass_id': 'pass.tel.lemaire.business/pass-v5',
                'deviceLibraryIdentifier': 'test-device-123'
            }
        )

    @patch('passkit_unregistration_function.common.validate_authorization')
    def test_authorization_failure(self, mock_validate_auth):
        # Setup
        mock_validate_auth.return_value = {'statusCode': 401, 'body': json.dumps({'error': 'Unauthorized'})}

        event = {
            'pathParameters': {
                'deviceLibraryIdentifier': 'test-device-123',
                'passTypeIdentifier': 'pass.tel.lemaire.business',
                'serialNumber': 'pass-v5'
            }
        }

        # Execute
        result = handler(event, {})

        # Assert
        self.assertEqual(result['statusCode'], 401)
        body = json.loads(result['body'])
        self.assertEqual(body['error'], 'Unauthorized')

    def test_invalid_path_parameters(self):
        invalid_cases = [
            ({'pathParameters': None}, 'Invalid request format'),
            ({'pathParameters': {}}, 'Missing path parameters'),
            ({'pathParameters': {'passTypeIdentifier': 'pass.tel.lemaire.business', 'serialNumber': 'pass-v5'}}, 'Missing path parameters'),
            ({'pathParameters': {'deviceLibraryIdentifier': 'test-device-123', 'passTypeIdentifier': 'pass.tel.lemaire.business'}}, 'Missing path parameters'),
        ]

        for event, expected_error in invalid_cases:
            with self.subTest(event=event):
                result = handler(event, {})
                self.assertEqual(result['statusCode'], 400)
                body = json.loads(result['body'])
                self.assertEqual(body['error'], expected_error)

    @patch('passkit_unregistration_function.table')
    @patch('passkit_unregistration_function.common.validate_authorization')
    def test_dynamodb_delete_error(self, mock_validate_auth, mock_table):
        # Setup
        mock_validate_auth.return_value = None
        mock_table.delete_item.side_effect = Exception('DynamoDB deletion error')

        event = {
            'pathParameters': {
                'deviceLibraryIdentifier': 'test-device-123',
                'passTypeIdentifier': 'pass.tel.lemaire.business',
                'serialNumber': 'pass-v5'
            },
            'headers': {
                'Authorization': 'ApplePass test-token'
            }
        }

        # Execute
        result = handler(event, {})

        # Assert
        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(result['body'], 'Internal Server Error')

    @patch('passkit_unregistration_function.table')
    @patch('passkit_unregistration_function.common.validate_authorization')
    def test_unregister_nonexistent_device(self, mock_validate_auth, mock_table):
        # Setup - DynamoDB delete_item doesn't fail even if item doesn't exist
        mock_validate_auth.return_value = None
        mock_table.delete_item.return_value = None

        event = {
            'pathParameters': {
                'deviceLibraryIdentifier': 'nonexistent-device',
                'passTypeIdentifier': 'pass.tel.lemaire.business',
                'serialNumber': 'pass-v5'
            },
            'headers': {
                'Authorization': 'ApplePass test-token'
            }
        }

        # Execute
        result = handler(event, {})

        # Assert - Should still return 200 (idempotent operation)
        self.assertEqual(result['statusCode'], 200)
        self.assertEqual(result['body'], '')

        # Verify delete was attempted
        mock_table.delete_item.assert_called_once_with(
            Key={
                'pass_id': 'pass.tel.lemaire.business/pass-v5',
                'deviceLibraryIdentifier': 'nonexistent-device'
            }
        )

    def test_malformed_event(self):
        # Test completely malformed event
        event = {}

        result = handler(event, {})

        self.assertEqual(result['statusCode'], 400)
        body = json.loads(result['body'])
        self.assertEqual(body['error'], 'Missing path parameters')

    @patch('passkit_unregistration_function.table')
    @patch('passkit_unregistration_function.common.validate_authorization')
    def test_special_characters_in_parameters(self, mock_validate_auth, mock_table):
        # Setup
        mock_validate_auth.return_value = None
        mock_table.delete_item.return_value = None

        event = {
            'pathParameters': {
                'deviceLibraryIdentifier': 'device-with-special-chars-123!@#',
                'passTypeIdentifier': 'pass.tel.lemaire.business',
                'serialNumber': 'pass-v5-special'
            },
            'headers': {
                'Authorization': 'ApplePass test-token'
            }
        }

        # Execute
        result = handler(event, {})

        # Assert
        self.assertEqual(result['statusCode'], 200)

        # Verify the pass_id was constructed correctly
        mock_table.delete_item.assert_called_once_with(
            Key={
                'pass_id': 'pass.tel.lemaire.business/pass-v5-special',
                'deviceLibraryIdentifier': 'device-with-special-chars-123!@#'
            }
        )


if __name__ == '__main__':
    unittest.main()