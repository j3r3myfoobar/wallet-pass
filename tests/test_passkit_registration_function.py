import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Add lambda_functions to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda_functions'))

from passkit_registration_function import handler


class TestPasskitRegistrationFunction(unittest.TestCase):

    @patch('passkit_registration_function.table')
    @patch('passkit_registration_function.common.validate_authorization')
    @patch.dict(os.environ, {'TABLE_NAME': 'test-table', 'AUTH_TOKEN': 'test-token'})
    def test_successful_new_registration(self, mock_validate_auth, mock_table):
        # Setup
        mock_validate_auth.return_value = None  # No auth error
        mock_table.get_item.return_value = {}  # No existing item
        mock_table.put_item.return_value = None

        event = {
            'pathParameters': {
                'deviceLibraryIdentifier': 'test-device-123',
                'passTypeIdentifier': 'pass.tel.lemaire.business',
                'serialNumber': 'pass-v5'
            },
            'body': json.dumps({
                'pushToken': 'abcd1234pushtoken'
            }),
            'headers': {
                'Authorization': 'ApplePass test-token'
            }
        }

        # Execute
        result = handler(event, {})

        # Assert
        self.assertEqual(result['statusCode'], 201)  # Created
        self.assertEqual(result['body'], '')

        # Verify DynamoDB operations
        mock_table.get_item.assert_called_once_with(
            Key={
                'pass_id': 'pass.tel.lemaire.business/pass-v5',
                'deviceLibraryIdentifier': 'test-device-123'
            }
        )
        mock_table.put_item.assert_called_once()

        # Check the item that was put
        put_item_call = mock_table.put_item.call_args
        item = put_item_call.kwargs['Item']
        self.assertEqual(item['pass_id'], 'pass.tel.lemaire.business/pass-v5')
        self.assertEqual(item['deviceLibraryIdentifier'], 'test-device-123')
        self.assertEqual(item['pushToken'], 'abcd1234pushtoken')
        self.assertEqual(item['last_updated_tag'], '0')

    @patch('passkit_registration_function.table')
    @patch('passkit_registration_function.common.validate_authorization')
    @patch.dict(os.environ, {'TABLE_NAME': 'test-table', 'AUTH_TOKEN': 'test-token'})
    def test_successful_existing_registration_update(self, mock_validate_auth, mock_table):
        # Setup
        mock_validate_auth.return_value = None
        mock_table.get_item.return_value = {
            'Item': {
                'pass_id': 'pass.tel.lemaire.business/pass-v5',
                'deviceLibraryIdentifier': 'test-device-123',
                'pushToken': 'old-push-token'
            }
        }
        mock_table.put_item.return_value = None

        event = {
            'pathParameters': {
                'deviceLibraryIdentifier': 'test-device-123',
                'passTypeIdentifier': 'pass.tel.lemaire.business',
                'serialNumber': 'pass-v5'
            },
            'body': json.dumps({
                'pushToken': 'new-push-token'
            }),
            'headers': {
                'Authorization': 'ApplePass test-token'
            }
        }

        # Execute
        result = handler(event, {})

        # Assert
        self.assertEqual(result['statusCode'], 200)  # Updated existing
        self.assertEqual(result['body'], '')

    @patch('passkit_registration_function.common.validate_authorization')
    def test_authorization_failure(self, mock_validate_auth):
        # Setup
        mock_validate_auth.return_value = {'statusCode': 401, 'body': json.dumps({'error': 'Unauthorized'})}

        event = {
            'pathParameters': {
                'deviceLibraryIdentifier': 'test-device-123',
                'passTypeIdentifier': 'pass.tel.lemaire.business',
                'serialNumber': 'pass-v5'
            },
            'body': json.dumps({
                'pushToken': 'abcd1234pushtoken'
            })
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
            ({'pathParameters': {'passTypeIdentifier': 'pass.tel.lemaire.business', 'serialNumber': 'pass-v5'}}, 'Missing path parameters'),
            ({'pathParameters': {}}, 'Missing path parameters'),
        ]

        for event_data, expected_error in invalid_cases:
            with self.subTest(event=event_data):
                event = {**event_data, 'body': json.dumps({'pushToken': 'test'})}
                result = handler(event, {})
                self.assertEqual(result['statusCode'], 400)
                body = json.loads(result['body'])
                self.assertEqual(body['error'], expected_error)

    @patch('passkit_registration_function.common.validate_authorization')
    def test_missing_push_token(self, mock_validate_auth):
        # Setup
        mock_validate_auth.return_value = None

        event = {
            'pathParameters': {
                'deviceLibraryIdentifier': 'test-device-123',
                'passTypeIdentifier': 'pass.tel.lemaire.business',
                'serialNumber': 'pass-v5'
            },
            'body': json.dumps({}),  # No pushToken
            'headers': {
                'Authorization': 'ApplePass test-token'
            }
        }

        # Execute
        result = handler(event, {})

        # Assert
        self.assertEqual(result['statusCode'], 400)
        body = json.loads(result['body'])
        self.assertEqual(body['error'], 'pushToken is required')

    @patch('passkit_registration_function.common.validate_authorization')
    def test_invalid_json_body(self, mock_validate_auth):
        # Setup
        mock_validate_auth.return_value = None

        event = {
            'pathParameters': {
                'deviceLibraryIdentifier': 'test-device-123',
                'passTypeIdentifier': 'pass.tel.lemaire.business',
                'serialNumber': 'pass-v5'
            },
            'body': 'invalid-json',  # Invalid JSON
            'headers': {
                'Authorization': 'ApplePass test-token'
            }
        }

        # Execute
        result = handler(event, {})

        # Assert
        self.assertEqual(result['statusCode'], 400)
        body = json.loads(result['body'])
        self.assertEqual(body['error'], 'Invalid JSON format')

    @patch('passkit_registration_function.table')
    @patch('passkit_registration_function.common.validate_authorization')
    def test_dynamodb_get_item_error(self, mock_validate_auth, mock_table):
        # Setup
        mock_validate_auth.return_value = None
        mock_table.get_item.side_effect = Exception('DynamoDB connection error')

        event = {
            'pathParameters': {
                'deviceLibraryIdentifier': 'test-device-123',
                'passTypeIdentifier': 'pass.tel.lemaire.business',
                'serialNumber': 'pass-v5'
            },
            'body': json.dumps({
                'pushToken': 'abcd1234pushtoken'
            }),
            'headers': {
                'Authorization': 'ApplePass test-token'
            }
        }

        # Execute
        result = handler(event, {})

        # Assert
        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(result['body'], 'Internal Server Error')

    @patch('passkit_registration_function.table')
    @patch('passkit_registration_function.common.validate_authorization')
    def test_dynamodb_put_item_error(self, mock_validate_auth, mock_table):
        # Setup
        mock_validate_auth.return_value = None
        mock_table.get_item.return_value = {}  # No existing item
        mock_table.put_item.side_effect = Exception('DynamoDB write error')

        event = {
            'pathParameters': {
                'deviceLibraryIdentifier': 'test-device-123',
                'passTypeIdentifier': 'pass.tel.lemaire.business',
                'serialNumber': 'pass-v5'
            },
            'body': json.dumps({
                'pushToken': 'abcd1234pushtoken'
            }),
            'headers': {
                'Authorization': 'ApplePass test-token'
            }
        }

        # Execute
        result = handler(event, {})

        # Assert
        self.assertEqual(result['statusCode'], 500)
        body = json.loads(result['body'])
        self.assertEqual(body['error'], 'Could not save registration')

    @patch('passkit_registration_function.table')
    @patch('passkit_registration_function.common.validate_authorization')
    def test_empty_body(self, mock_validate_auth, mock_table):
        # Setup
        mock_validate_auth.return_value = None

        event = {
            'pathParameters': {
                'deviceLibraryIdentifier': 'test-device-123',
                'passTypeIdentifier': 'pass.tel.lemaire.business',
                'serialNumber': 'pass-v5'
            },
            'body': None,  # No body
            'headers': {
                'Authorization': 'ApplePass test-token'
            }
        }

        # Execute
        result = handler(event, {})

        # Assert
        self.assertEqual(result['statusCode'], 400)
        body = json.loads(result['body'])
        self.assertEqual(body['error'], 'pushToken is required')


if __name__ == '__main__':
    unittest.main()