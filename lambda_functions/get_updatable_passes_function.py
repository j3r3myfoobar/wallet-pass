import json
import boto3
import os
from datetime import datetime, timezone
import common

# Get the DynamoDB table name from environment variables
TABLE_NAME = os.environ.get('TABLE_NAME', 'WalletRegistrations')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)

def extract_path_parameters(event):
    """Extract and validate path parameters from the event."""
    try:
        params = event.get('pathParameters', {})
        device_id = params.get('deviceLibraryIdentifier')
        pass_type_id = params.get('passTypeIdentifier')

        if not all([device_id, pass_type_id]):
            print("Error: Missing path parameters.")
            return None, {'statusCode': 400, 'body': json.dumps({'error': 'Missing path parameters'})}

        return (device_id, pass_type_id), None
    except Exception as e:
        print(f"Error parsing path parameters: {e}")
        return None, {'statusCode': 400, 'body': json.dumps({'error': 'Invalid request format'})}

def extract_query_parameters(event):
    """Extract and validate query parameters from the event."""
    try:
        query_params = event.get('queryStringParameters') or {}
        passes_updated_since = query_params.get('passesUpdatedSince')

        # Validate timestamp if provided
        if passes_updated_since:
            try:
                int(passes_updated_since)
            except (ValueError, TypeError):
                print(f"Error: Invalid timestamp format: {passes_updated_since}")
                return None, {'statusCode': 400, 'body': json.dumps({'error': 'Invalid timestamp format'})}

        return passes_updated_since, None
    except Exception as e:
        print(f"Error parsing query parameters: {e}")
        return None, {'statusCode': 400, 'body': json.dumps({'error': 'Invalid query parameters'})}

def query_registered_passes(device_id, pass_type_id):
    """Query DynamoDB for registered passes for the device."""
    try:
        # For your single business card use case, we know the exact pass_id
        pass_id = f"{pass_type_id}/jeremy-business-card"

        response = table.get_item(
            Key={
                'pass_id': pass_id,
                'deviceLibraryIdentifier': device_id
            }
        )

        if 'Item' in response:
            items = [response['Item']]
        else:
            items = []
            print(f"No registration found for device {device_id} and pass {pass_id}")

        return items, None
    except Exception as e:
        print(f"Error querying DynamoDB: {e}")
        return None, {'statusCode': 500, 'body': json.dumps({'error': 'Database query failed'})}

def filter_passes_by_update_time(items, passes_updated_since):
    """Filter passes by update time if provided."""
    try:
        updated_passes = []

        for item in items:
            serial_number = item.get('serialNumber')
            if not serial_number:
                print(f"Warning: Pass item missing serialNumber: {item}")
                continue

            last_updated = item.get('last_updated_tag', '0')

            # If passesUpdatedSince is provided, only include passes updated after that time
            if passes_updated_since:
                try:
                    if int(last_updated) > int(passes_updated_since):
                        updated_passes.append(serial_number)
                except (ValueError, TypeError) as e:
                    print(f"Error comparing timestamps: last_updated={last_updated}, passesUpdatedSince={passes_updated_since}, error={e}")
                    continue
            else:
                # If no timestamp provided, return all registered passes
                updated_passes.append(serial_number)

        return updated_passes, None
    except Exception as e:
        print(f"Error filtering passes: {e}")
        return None, {'statusCode': 500, 'body': json.dumps({'error': 'Error processing pass data'})}

def build_response(updated_passes):
    """Build the final response for Apple Wallet."""
    current_timestamp = str(int(datetime.now(timezone.utc).timestamp()))

    response_body = {
        "lastUpdated": current_timestamp,
        "serialNumbers": updated_passes
    }

    print(f"Returning {len(updated_passes)} updated passes: {updated_passes}")
    print(f"Response to Apple: {json.dumps(response_body)}")

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(response_body)
    }

def handler(event, context):
    """
    Handles the Get Updatable Passes request from Apple Wallet.
    Endpoint: GET /v1/devices/{deviceLibraryIdentifier}/registrations/{passTypeIdentifier}
    Optional query parameter: passesUpdatedSince
    """
    print(f"Received event: {json.dumps(event)}")

    # --- 1. Extract path parameters ---
    path_params, error = extract_path_parameters(event)
    if error:
        return error
    device_id, pass_type_id = path_params

    # --- 2. No authorization required for Get Updatable Passes ---
    # According to Apple's PassKit documentation, this endpoint does not require
    # authorization header - devices are authenticated via prior registration

    # --- 3. Extract query parameters ---
    passes_updated_since, error = extract_query_parameters(event)
    if error:
        return error

    print(f"Device: {device_id}, PassType: {pass_type_id}, UpdatedSince: {passes_updated_since}")

    # --- 4. Query DynamoDB for registered passes ---
    items, error = query_registered_passes(device_id, pass_type_id)
    if error:
        return error

    # --- 5. Filter by update time if provided ---
    updated_passes, error = filter_passes_by_update_time(items, passes_updated_since)
    if error:
        return error

    # --- 6. Return response ---
    return build_response(updated_passes)