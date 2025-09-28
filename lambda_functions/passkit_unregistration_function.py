import json
import boto3
import os
import common

# Get the DynamoDB table name from environment variables
TABLE_NAME = os.environ.get('TABLE_NAME', 'WalletRegistrations')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)

def handler(event, context):
    """
    Handles the device unregistration request for an Apple Wallet pass.
    Endpoint: DELETE /v1/devices/{deviceLibraryIdentifier}/registrations/{passTypeIdentifier}/{serialNumber}
    """
    print(f"Received event: {json.dumps(event)}")

    # --- 1. Extract path parameters from the API Gateway event ---
    try:
        params = event.get('pathParameters', {})
        device_id = params.get('deviceLibraryIdentifier')
        pass_type_id = params.get('passTypeIdentifier')
        serial_number = params.get('serialNumber')

        if not all([device_id, pass_type_id, serial_number]):
            print("Error: Missing one or more path parameters.")
            return {'statusCode': 400, 'body': json.dumps({'error': 'Missing path parameters'})}

    except Exception as e:
        print(f"Error parsing path parameters: {e}")
        return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid request format'})}

    # --- 2. Validate Authorization Header ---
    auth_error = common.validate_authorization(event)
    if auth_error:
        return auth_error

    # --- 3. Delete the registration from DynamoDB ---
    pass_id = f"{pass_type_id}/{serial_number}"
    
    try:
        table.delete_item(
            Key={
                'pass_id': pass_id,
                'deviceLibraryIdentifier': device_id
            }
        )
        print(f"Successfully unregistered device {device_id} for pass {pass_id}")
    except Exception as e:
        print(f"Error deleting item from DynamoDB: {e}")
        return {'statusCode': 500, 'body': 'Internal Server Error'}

    # --- 4. Return success ---
    return {'statusCode': 200, 'body': ''}
