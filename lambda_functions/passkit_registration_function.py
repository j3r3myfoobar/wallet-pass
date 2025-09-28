import json
import boto3
import os
from datetime import datetime, timezone
import common

# Get the DynamoDB table name from environment variables
TABLE_NAME = os.environ.get('TABLE_NAME', 'WalletRegistrations')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)

def handler(event, context):
    """
    Handles the device registration request for an Apple Wallet pass.
    Endpoint: POST /v1/devices/{deviceLibraryIdentifier}/registrations/{passTypeIdentifier}/{serialNumber}
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


    # --- 3. Extract pushToken from the request body ---
    try:
        body_content = event.get('body') or '{}'
        body = json.loads(body_content)
        push_token = body.get('pushToken')
        if not push_token:
            print("Error: pushToken is missing from the request body.")
            return {'statusCode': 400, 'body': json.dumps({'error': 'pushToken is required'})}
    except json.JSONDecodeError:
        print("Error: Invalid JSON in request body.")
        return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid JSON format'})}


    # --- 4. Store the registration in DynamoDB ---
    # Create a composite key for the partition key
    pass_id = f"{pass_type_id}/{serial_number}"
    
    # Check if this device is already registered for this pass
    try:
        response = table.get_item(
            Key={
                'pass_id': pass_id,
                'deviceLibraryIdentifier': device_id
            }
        )
        is_existing = 'Item' in response
    except Exception as e:
        print(f"Error checking for existing item in DynamoDB: {e}")
        return {'statusCode': 500, 'body': 'Internal Server Error'}

    # Prepare the item for DynamoDB
    timestamp = datetime.now(timezone.utc).isoformat()
    current_timestamp_tag = str(int(datetime.now(timezone.utc).timestamp()))

    item = {
        'pass_id': pass_id,
        'deviceLibraryIdentifier': device_id,
        'passTypeIdentifier': pass_type_id,
        'serialNumber': serial_number,
        'pushToken': push_token,
        'registered_at': timestamp,
        'last_updated_at': timestamp,
        'last_updated_tag': '0'  # Initialize to 0, will be updated when pass changes
    }

    # Put the item into the table (this will create or overwrite)
    try:
        table.put_item(Item=item)
        print(f"Successfully registered device {device_id} for pass {pass_id}")
    except Exception as e:
        print(f"Error writing to DynamoDB: {e}")
        return {'statusCode': 500, 'body': json.dumps({'error': 'Could not save registration'})}

    # --- 5. Return the correct HTTP status code ---
    # If the registration already existed, return 200 OK.
    # If it's a new registration, return 201 Created.
    if is_existing:
        print(f"Device {device_id} was already registered. Updated registration.")
        return {'statusCode': 200, 'body': ''}
    else:
        print(f"New registration for device {device_id} successful.")
        return {'statusCode': 201, 'body': ''}
