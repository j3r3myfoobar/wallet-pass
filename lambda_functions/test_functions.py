"""
Basic local testing for Lambda functions.
Run with: python3 test_functions.py
"""

import json
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

def test_pass_redirect_function():
    """Test the pass redirect function with different user agents."""
    print("Testing pass_redirect_function...")

    # Import the function
    from pass_redirect_function import handler

    # Mock S3 response
    mock_s3_response = {
        'Body': Mock()
    }
    mock_s3_response['Body'].read.return_value = b'fake-pass-content'

    # Test iOS user agent
    with patch('pass_redirect_function.s3') as mock_s3:
        mock_s3.get_object.return_value = mock_s3_response

        event = {
            'headers': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)'
            }
        }

        # Set environment variable
        os.environ['S3_BUCKET_NAME'] = 'test-bucket'

        result = handler(event, {})

        # Assertions
        assert result['statusCode'] == 200
        assert 'application/vnd.apple.pkpass' in result['headers']['Content-Type']
        mock_s3.get_object.assert_called_with(Bucket='test-bucket', Key='pass.pkpass')
        print("  SUCCESS: iOS user agent test passed")

    # Test non-iOS user agent
    with patch('pass_redirect_function.s3') as mock_s3:
        mock_s3.get_object.return_value = mock_s3_response

        event = {
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        }

        result = handler(event, {})

        # Assertions
        assert result['statusCode'] == 200
        assert 'text/vcard' in result['headers']['Content-Type']
        mock_s3.get_object.assert_called_with(Bucket='test-bucket', Key='contact.vcard')
        print("  SUCCESS: Non-iOS user agent test passed")

def test_passkit_registration_function():
    """Test the passkit registration function."""
    print("Testing passkit_registration_function...")

    from passkit_registration_function import handler

    # Mock DynamoDB
    with patch('passkit_registration_function.table') as mock_table:
        mock_table.put_item.return_value = {}

        event = {
            'pathParameters': {
                'deviceLibraryIdentifier': 'test-device-123',
                'passTypeIdentifier': 'pass.lemaire.tel',
                'serialNumber': 'businesscard-123'
            },
            'headers': {
                'authorization': 'ApplePass test-auth-token'
            },
            'body': '{"pushToken": "test-push-token"}'
        }

        os.environ['TABLE_NAME'] = 'test-table'
        os.environ['AUTH_TOKEN'] = 'test-auth-token'

        result = handler(event, {})

        # Should return 201 for successful registration
        assert result['statusCode'] == 201
        mock_table.put_item.assert_called_once()
        print("  SUCCESS: Registration test passed")

def run_all_tests():
    """Run all tests."""
    print("Starting Lambda function tests...\n")

    try:
        test_pass_redirect_function()
        test_passkit_registration_function()

        print(f"\nAll tests passed!")
        return True

    except Exception as e:
        print(f"\nTEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)