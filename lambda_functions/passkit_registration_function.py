import json
import boto3
import os
from datetime import datetime, timezone
from botocore.exceptions import ClientError
import common

# Get the DynamoDB table name from environment variables
TABLE_NAME = os.environ.get('TABLE_NAME', 'WalletRegistrations')
MAX_REG_PER_SERIAL = 400

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)

def extract_path_parameters(event):
    """Extract and validate path parameters from the API Gateway event."""
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

def extract_push_token(event):
    """Extract and validate pushToken from the request body."""
    try:
        body_content = event.get('body') or '{}'
        body = json.loads(body_content)
        push_token = body.get('pushToken')
        if not push_token:
            print("Error: pushToken is missing from the request body.")
            return None, {'statusCode': 400, 'body': json.dumps({'error': 'pushToken is required'})}
        return push_token, None
    except json.JSONDecodeError:
        print("Error: Invalid JSON in request body.")
        return None, {'statusCode': 400, 'body': json.dumps({'error': 'Invalid JSON format'})}

def is_device_registered(pass_id, device_id):
    """Check if this device is already registered for this pass."""
    try:
        response = table.get_item(
            Key={
                'pass_id': pass_id,
                'deviceLibraryIdentifier': device_id
            }
        )
        return 'Item' in response
    except Exception as e:
        print(f"Error checking for existing item in DynamoDB: {e}")
        raise

def prepare_registration_item(pass_id, device_id, pass_type_id, serial_number, push_token):
    """Prepare the registration item for DynamoDB storage."""
    timestamp = datetime.now(timezone.utc).isoformat()
    return {
        'pass_id': pass_id,
        'deviceLibraryIdentifier': device_id,
        'passTypeIdentifier': pass_type_id,
        'serialNumber': serial_number,
        'pushToken': push_token,
        'registered_at': timestamp,
        'last_updated_at': timestamp,
        'last_updated_tag': '0'  # Initialize to 0, will be updated when pass changes
    }

def store_registration(item):
    """Store the registration item in DynamoDB."""
    try:
        table.put_item(Item=item)
        print(f"Successfully registered device {item['deviceLibraryIdentifier']} for pass {item['pass_id']}")
        return True
    except Exception as e:
        print(f"Error writing to DynamoDB: {e}")
        raise

def validate_registration_count(pass_id):
    """Validate that registration count hasn't exceeded the limit."""
    try:
        scan_response = table.scan(
            FilterExpression="pass_id = :pass_id",
            ExpressionAttributeValues={':pass_id': pass_id},
            Select='COUNT'
        )
        current_count = scan_response['Count']

        if current_count >= MAX_REG_PER_SERIAL:
            print(f"Registration limit of {MAX_REG_PER_SERIAL} reached for pass {pass_id}")
            return {'statusCode': 429, 'body': json.dumps({'error': 'Registration limit exceeded'})}

        return None  # No error, count is within limit
    except Exception as e:
        print(f"Error counting registrations: {e}")
        return {'statusCode': 500, 'body': json.dumps({'error': 'Could not check registration count'})}

def handler(event, context):
    """
    Handles the device registration request for an Apple Wallet pass.
    Endpoint: POST /v1/devices/{deviceLibraryIdentifier}/registrations/{passTypeIdentifier}/{serialNumber}
    """
    print(f"Received event: {json.dumps(event)}")

    # --- 1. Extract path parameters from the API Gateway event ---
    path_params, error_response = extract_path_parameters(event)
    if error_response:
        return error_response
    device_id, pass_type_id, serial_number = path_params

    # --- 2. Validate Authorization Header ---
    auth_error = common.validate_authorization(event)
    if auth_error:
        return auth_error

    # --- 3. Extract pushToken from the request body ---
    push_token, error_response = extract_push_token(event)
    if error_response:
        return error_response


    # --- 4. Store the registration in DynamoDB ---
    # Create a composite key for the partition key
    pass_id = f"{pass_type_id}/{serial_number}"

    # Check if this device is already registered for this pass
    try:
        is_existing = is_device_registered(pass_id, device_id)
    except Exception as e:
        return {'statusCode': 500, 'body': 'Internal Server Error'}

    # If new registration, check count limit
    if not is_existing:
        count_error = validate_registration_count(pass_id)
        if count_error:
            return count_error

    # Prepare the item for DynamoDB
    item = prepare_registration_item(pass_id, device_id, pass_type_id, serial_number, push_token)

    # Store the registration
    try:
        store_registration(item)
    except Exception as e:
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
