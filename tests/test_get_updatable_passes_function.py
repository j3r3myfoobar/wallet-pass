import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Add lambda_functions to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lambda_functions'))

from get_updatable_passes_function import handler


class TestGetUpdatablePassesFunction(unittest.TestCase):

    @patch('get_updatable_passes_function.table')
    @patch.dict(os.environ, {'TABLE_NAME': 'test-table'})
    def test_successful_request_with_updated_pass(self, mock_table):
        # Setup
        mock_table.get_item.return_value = {
            'Item': {
                'pass_id': 'pass.tel.lemaire.business/jeremy-business-card',
                'deviceLibraryIdentifier': 'test-device-123',
                'serialNumber': 'pass-v5',
                'last_updated_tag': '1695000000'
            }
        }

        event = {
            'pathParameters': {
                'deviceLibraryIdentifier': 'test-device-123',
                'passTypeIdentifier': 'pass.tel.lemaire.business'
            },
            'queryStringParameters': {
                'passesUpdatedSince': '1690000000'
            }
        }

        # Execute
        result = handler(event, {})

        # Assert
        self.assertEqual(result['statusCode'], 200)
        self.assertEqual(result['headers']['Content-Type'], 'application/json')

        body = json.loads(result['body'])
        self.assertIn('lastUpdated', body)
        self.assertEqual(body['serialNumbers'], ['pass-v5'])

        mock_table.get_item.assert_called_once_with(
            Key={
                'pass_id': 'pass.tel.lemaire.business/jeremy-business-card',
                'deviceLibraryIdentifier': 'test-device-123'
            }
        )

    @patch('get_updatable_passes_function.table')
    @patch.dict(os.environ, {'TABLE_NAME': 'test-table'})
    def test_successful_request_no_updates_since_timestamp(self, mock_table):
        # Setup
        mock_table.get_item.return_value = {
            'Item': {
                'pass_id': 'pass.tel.lemaire.business/jeremy-business-card',
                'deviceLibraryIdentifier': 'test-device-123',
                'serialNumber': 'pass-v5',
                'last_updated_tag': '1690000000'  # Same as query timestamp
            }
        }

        event = {
            'pathParameters': {
                'deviceLibraryIdentifier': 'test-device-123',
                'passTypeIdentifier': 'pass.tel.lemaire.business'
            },
            'queryStringParameters': {
                'passesUpdatedSince': '1695000000'  # Later timestamp
            }
        }

        # Execute
        result = handler(event, {})

        # Assert
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertEqual(body['serialNumbers'], [])  # No updates

    @patch('get_updatable_passes_function.table')
    @patch.dict(os.environ, {'TABLE_NAME': 'test-table'})
    def test_successful_request_no_timestamp_returns_all(self, mock_table):
        # Setup
        mock_table.get_item.return_value = {
            'Item': {
                'pass_id': 'pass.tel.lemaire.business/jeremy-business-card',
                'deviceLibraryIdentifier': 'test-device-123',
                'serialNumber': 'pass-v5',
                'last_updated_tag': '1695000000'
            }
        }

        event = {
            'pathParameters': {
                'deviceLibraryIdentifier': 'test-device-123',
                'passTypeIdentifier': 'pass.tel.lemaire.business'
            },
            'queryStringParameters': None  # No timestamp filter
        }

        # Execute
        result = handler(event, {})

        # Assert
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertEqual(body['serialNumbers'], ['pass-v5'])  # Returns all passes

    @patch('get_updatable_passes_function.table')
    @patch.dict(os.environ, {'TABLE_NAME': 'test-table'})
    def test_device_not_registered(self, mock_table):
        # Setup
        mock_table.get_item.return_value = {}  # No item found

        event = {
            'pathParameters': {
                'deviceLibraryIdentifier': 'unknown-device',
                'passTypeIdentifier': 'pass.tel.lemaire.business'
            }
        }

        # Execute
        result = handler(event, {})

        # Assert
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertEqual(body['serialNumbers'], [])  # Empty list

    def test_invalid_path_parameters(self):
        invalid_cases = [
            ({}, 'Missing path parameters'),
            ({'pathParameters': None}, 'Invalid request format'),
            ({'pathParameters': {'passTypeIdentifier': 'pass.tel.lemaire.business'}}, 'Missing path parameters'),
        ]

        for event, expected_error in invalid_cases:
            with self.subTest(event=event):
                result = handler(event, {})
                self.assertEqual(result['statusCode'], 400)
                body = json.loads(result['body'])
                self.assertEqual(body['error'], expected_error)

    @patch('get_updatable_passes_function.table')
    @patch.dict(os.environ, {'TABLE_NAME': 'test-table'})
    def test_dynamodb_error(self, mock_table):
        # Setup
        mock_table.get_item.side_effect = Exception('DynamoDB connection error')

        event = {
            'pathParameters': {
                'deviceLibraryIdentifier': 'test-device-123',
                'passTypeIdentifier': 'pass.tel.lemaire.business'
            }
        }

        # Execute
        result = handler(event, {})

        # Assert
        self.assertEqual(result['statusCode'], 500)
        body = json.loads(result['body'])
        self.assertEqual(body['error'], 'Database query failed')

    @patch('get_updatable_passes_function.table')
    @patch.dict(os.environ, {'TABLE_NAME': 'test-table'})
    def test_pass_without_last_updated_tag(self, mock_table):
        # Setup - pass without last_updated_tag defaults to '0'
        mock_table.get_item.return_value = {
            'Item': {
                'pass_id': 'pass.tel.lemaire.business/jeremy-business-card',
                'deviceLibraryIdentifier': 'test-device-123',
                'serialNumber': 'pass-v5'
                # Missing last_updated_tag
            }
        }

        event = {
            'pathParameters': {
                'deviceLibraryIdentifier': 'test-device-123',
                'passTypeIdentifier': 'pass.tel.lemaire.business'
            },
            'queryStringParameters': {
                'passesUpdatedSince': '1695000000'
            }
        }

        # Execute
        result = handler(event, {})

        # Assert
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertEqual(body['serialNumbers'], [])  # Not updated since timestamp


if __name__ == '__main__':
    unittest.main()