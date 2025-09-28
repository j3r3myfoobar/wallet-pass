import os
import boto3
import base64
from datetime import datetime, timezone
from botocore.exceptions import ClientError

s3 = boto3.client('s3')

def is_apple_device(user_agent):
    """Check if the User-Agent indicates an Apple device that supports .pkpass files."""
    apple_indicators = ['iPhone', 'iPad', 'iPod', 'Macintosh', 'Darwin', 'passd']
    return any(indicator in user_agent for indicator in apple_indicators)

def validate_environment():
    """Validate that required environment variables are set."""
    bucket_name = os.environ.get('S3_BUCKET_NAME')
    if not bucket_name:
        print("Error: S3_BUCKET_NAME environment variable not set")
        return None, {
            'statusCode': 500,
            'body': '{"message": "Server configuration error"}'
        }
    return bucket_name, None

def extract_and_validate_headers(event):
    """Extract and validate headers from the event."""
    try:
        headers = event.get('headers', {})
        user_agent = headers.get('User-Agent', '')
        if_modified_since = headers.get('If-Modified-Since') or headers.get('if-modified-since')
        print(f"User-Agent: {user_agent}")
        if if_modified_since:
            print(f"If-Modified-Since: {if_modified_since}")
        return user_agent, if_modified_since
    except Exception as e:
        print(f"Error extracting headers: {e}")
        return '', None

def determine_file_type(user_agent):
    """Determine file type and content type based on User-Agent."""
    if is_apple_device(user_agent):
        return 'pass.pkpass', 'application/vnd.apple.pkpass'
    else:
        return 'contact.vcard', 'text/vcard'

def retrieve_and_encode_file(bucket_name, key):
    """Retrieve file from S3 and encode it for HTTP response."""
    try:
        s3_object = s3.get_object(Bucket=bucket_name, Key=key)
        file_content = s3_object['Body'].read()
        last_modified = s3_object['LastModified']

        # Validate file content
        if not file_content:
            print(f"Warning: Empty file retrieved from S3: {key}")
            return None, None, {
                'statusCode': 404,
                'body': '{"message": "File not found or empty"}'
            }

        # Encode file content
        try:
            encoded_content = base64.b64encode(file_content).decode('utf-8')
            return encoded_content, last_modified, None
        except Exception as e:
            print(f"Error encoding file content: {e}")
            return None, None, {
                'statusCode': 500,
                'body': '{"message": "Error processing file content"}'
            }

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchKey':
            print(f"Error: File not found in S3: {key}")
            return None, None, {
                'statusCode': 404,
                'body': '{"message": "Requested file not found"}'
            }
        elif error_code == 'NoSuchBucket':
            print(f"Error: S3 bucket not found: {bucket_name}")
            return None, None, {
                'statusCode': 500,
                'body': '{"message": "Storage configuration error"}'
            }
        else:
            print(f"AWS ClientError: {e}")
            return None, None, {
                'statusCode': 500,
                'body': '{"message": "Error retrieving file from storage"}'
            }
    except Exception as e:
        print(f"General S3 Error: {e}")
        return None, None, {
            'statusCode': 500,
            'body': '{"message": "Error retrieving file from storage"}'
        }

def format_http_date(dt):
    """Format datetime to HTTP date format (RFC 7231)."""
    return dt.strftime('%a, %d %b %Y %H:%M:%S GMT')

def check_if_modified_since(if_modified_since, last_modified, last_modified_str):
    """Check If-Modified-Since header and return 304 response if file not modified."""
    if not if_modified_since:
        return None  # No conditional request

    try:
        # Parse the If-Modified-Since date and make it timezone-aware (GMT)
        if_modified_date = datetime.strptime(if_modified_since, '%a, %d %b %Y %H:%M:%S GMT').replace(tzinfo=timezone.utc)

        # Convert S3 LastModified to same format for comparison (remove microseconds)
        s3_modified_date = last_modified.replace(microsecond=0)

        # If file hasn't been modified since the requested date, return 304
        if s3_modified_date <= if_modified_date:
            print(f"File not modified since {if_modified_since}, returning 304")
            return {
                'statusCode': 304,
                'headers': {
                    'Last-Modified': last_modified_str
                },
                'body': ''
            }
        else:
            print(f"File modified since {if_modified_since}, returning full content")
            return None  # File was modified, continue with normal response
    except ValueError as e:
        print(f"Error parsing If-Modified-Since header: {e}")
        return None  # Continue with normal response if header parsing fails

def handler(event, context):
    # Validate environment configuration
    bucket_name, env_error = validate_environment()
    if env_error:
        return env_error

    # Extract and validate headers
    user_agent, if_modified_since = extract_and_validate_headers(event)

    # Determine file type based on User-Agent
    key, content_type = determine_file_type(user_agent)

    # Retrieve file from S3 and encode it
    encoded_content, last_modified, retrieval_error = retrieve_and_encode_file(bucket_name, key)
    if retrieval_error:
        return retrieval_error

    # Format Last-Modified header in HTTP date format (RFC 7231)
    last_modified_str = format_http_date(last_modified)

    # Check If-Modified-Since header for conditional requests
    not_modified_response = check_if_modified_since(if_modified_since, last_modified, last_modified_str)
    if not_modified_response:
        # Return 304 Not Modified
        return not_modified_response
    else:
        # Return 200 OK with full content
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': content_type,
                'Content-Disposition': f'attachment; filename="{key}"',
                'Last-Modified': last_modified_str
            },
            'body': encoded_content,
            'isBase64Encoded': True
        }
