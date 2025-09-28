import json
import boto3
import os
from datetime import datetime, timedelta
import urllib.parse
from jose import jwt
import time
import httpx

# Environment variables
TABLE_NAME = os.environ.get('TABLE_NAME', 'WalletRegistrations')
PASS_TYPE_IDENTIFIER = os.environ.get('PASS_TYPE_IDENTIFIER', 'pass.tel.lemaire.business')
SERIAL_NUMBER = os.environ.get('SERIAL_NUMBER', 'jeremy-business-card')
APNS_SECRETS_ARN = os.environ.get('APNS_SECRETS_ARN')

# APNs Configuration
APNS_HOST = "https://api.push.apple.com"  # Production

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)
secrets_client = boto3.client('secretsmanager')

def handler(event, context):
    """
    Handles S3 events when pass files are updated.
    Sends push notifications to all registered devices.
    """
    print(f"Received S3 event: {json.dumps(event)}")

    # Extract S3 event details
    for record in event.get('Records', []):
        if record.get('eventSource') == 'aws:s3':
            bucket_name = record['s3']['bucket']['name']
            object_key = urllib.parse.unquote_plus(record['s3']['object']['key'])
            event_name = record['eventName']

            print(f"S3 Event: {event_name}, Bucket: {bucket_name}, Object: {object_key}")

            # Only process .pkpass file updates
            if object_key.endswith('.pkpass') and event_name.startswith('ObjectCreated'):
                print(f"Processing pass update for: {object_key}")

                # Update all registered devices and send push notifications
                success = update_registered_devices()

                if success:
                    print("Successfully processed pass update")
                else:
                    print("Failed to process some pass updates")

    return {'statusCode': 200, 'body': 'Processing complete'}

def update_registered_devices():
    """
    Updates all registered devices with new pass version and sends push notifications.
    """
    try:
        # Get current timestamp for version tracking
        current_timestamp = str(int(datetime.utcnow().timestamp()))
        pass_id = f"{PASS_TYPE_IDENTIFIER}/{SERIAL_NUMBER}"

        # Scan for all registrations of this pass
        response = table.scan(
            FilterExpression='pass_id = :pass_id',
            ExpressionAttributeValues={
                ':pass_id': pass_id
            }
        )

        registered_devices = response.get('Items', [])
        print(f"Found {len(registered_devices)} registered devices")

        success_count = 0

        for device in registered_devices:
            device_id = device['deviceLibraryIdentifier']
            push_token = device['pushToken']

            # Update the last_updated_tag for this device
            try:
                table.update_item(
                    Key={
                        'pass_id': pass_id,
                        'deviceLibraryIdentifier': device_id
                    },
                    UpdateExpression='SET last_updated_tag = :timestamp, last_updated_at = :iso_timestamp',
                    ExpressionAttributeValues={
                        ':timestamp': current_timestamp,
                        ':iso_timestamp': datetime.utcnow().isoformat()
                    }
                )
                print(f"Updated version tag for device {device_id}")

                # Send push notification
                push_success = send_push_notification(push_token)
                if push_success:
                    success_count += 1
                    print(f"Push notification sent to device {device_id}")
                else:
                    print(f"Failed to send push notification to device {device_id}")

            except Exception as e:
                print(f"Error updating device {device_id}: {e}")

        print(f"Successfully updated {success_count} out of {len(registered_devices)} devices")
        return success_count == len(registered_devices)

    except Exception as e:
        print(f"Error in update_registered_devices: {e}")
        return False

def get_apns_credentials():
    """
    Retrieves APNs credentials from AWS Secrets Manager.
    """
    try:
        response = secrets_client.get_secret_value(SecretId=APNS_SECRETS_ARN)
        return json.loads(response['SecretString'])
    except Exception as e:
        print(f"Error retrieving APNs credentials: {e}")
        return None

def generate_jwt(credentials):
    """Generate the APNs auth token (JWT) using python-jose."""
    try:
        payload = {
            "iss": credentials['team_id'],
            "iat": int(time.time())
        }

        headers = {
            "alg": "ES256",
            "kid": credentials['key_id'],
        }

        token = jwt.encode(payload, credentials['private_key'], algorithm="ES256", headers=headers)
        return token
    except Exception as e:
        print(f"Error generating JWT: {e}")
        return None

def send_push_notification(push_token):
    """
    Send PassKit update notification to APNs using direct HTTP/2 calls.
    """
    try:
        # Get APNs credentials
        credentials = get_apns_credentials()
        if not credentials:
            print("Failed to retrieve APNs credentials")
            return False

        # Generate JWT token
        auth_token = generate_jwt(credentials)
        if not auth_token:
            print("Failed to generate JWT token")
            return False

        # Set up APNs request
        headers = {
            "authorization": f"bearer {auth_token}",
            "apns-topic": PASS_TYPE_IDENTIFIER,
            "apns-push-type": "background",  # PassKit uses background pushes
            "apns-priority": "5"  # Lower priority for background updates
        }

        # For PassKit, we send an empty payload - this tells the device to check for updates
        payload = {}

        url = f"{APNS_HOST}/3/device/{push_token}"

        print(f"Sending push notification to {push_token[:20]}...")

        with httpx.Client(http2=True, timeout=30.0) as client:
            response = client.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            print(f"✅ Push notification sent successfully to {push_token[:20]}...")
            return True
        else:
            print(f"❌ APNs error {response.status_code}: {response.text}")
            return False

    except Exception as e:
        print(f"Error sending push notification: {e}")
        return False