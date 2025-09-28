import json
import boto3
import os
import common

# Get the DynamoDB table name from environment variables
TABLE_NAME = os.environ.get('TABLE_NAME', 'WalletRegistrations')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)

def extract_unregistration_path_parameters(event):
    """Extract and validate path parameters for unregistration request."""
    try:
        params = event.get('pathParameters', {})
        device_id = params.get('deviceLibraryIdentifier')
        pass_type_id = params.get('passTypeIdentifier')
        serial_number = params.get('serialNumber')

        if not all([device_id, pass_type_id, serial_number]):
            print("Error: Missing one or more path parameters.")
            return None, {'statusCode': 400, 'body': json.dumps({'error': 'Missing path parameters'})}

        return (device_id, pass_type_id, serial_number), None
    except Exception as e:
        print(f"Error parsing path parameters: {e}")
        return None, {'statusCode': 400, 'body': json.dumps({'error': 'Invalid request format'})}

def validate_unregistration_authorization(event):
    """Validate authorization header for unregistration request."""
    auth_error = common.validate_authorization(event)
    return auth_error  # Returns None if valid, error response if invalid

def delete_device_registration(device_id, pass_type_id, serial_number):
    """Delete the device registration from DynamoDB."""
    pass_id = f"{pass_type_id}/{serial_number}"

    try:
        table.delete_item(
            Key={
                'pass_id': pass_id,
                'deviceLibraryIdentifier': device_id
            }
        )
        print(f"Successfully unregistered device {device_id} for pass {pass_id}")
        return None  # Success
    except Exception as e:
        print(f"Error deleting item from DynamoDB: {e}")
        return {'statusCode': 500, 'body': 'Internal Server Error'}

def handler(event, context):
    """
    Handles the device unregistration request for an Apple Wallet pass.
    Endpoint: DELETE /v1/devices/{deviceLibraryIdentifier}/registrations/{passTypeIdentifier}/{serialNumber}
    """
    print(f"Received event: {json.dumps(event)}")

    # --- 1. Extract path parameters from the API Gateway event ---
    path_params, error = extract_unregistration_path_parameters(event)
    if error:
        return error
    device_id, pass_type_id, serial_number = path_params

    # --- 2. Validate Authorization Header ---
    auth_error = validate_unregistration_authorization(event)
    if auth_error:
        return auth_error

    # --- 3. Delete the registration from DynamoDB ---
    deletion_error = delete_device_registration(device_id, pass_type_id, serial_number)
    if deletion_error:
        return deletion_error

    # --- 4. Return success ---
    return {'statusCode': 200, 'body': ''}
