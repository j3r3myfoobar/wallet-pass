import os
import boto3
import base64
from datetime import datetime, timezone
from botocore.exceptions import ClientError

s3 = boto3.client('s3')

def handler(event, context):
    # Validate environment configuration
    bucket_name = os.environ.get('S3_BUCKET_NAME')
    if not bucket_name:
        print("Error: S3_BUCKET_NAME environment variable not set")
        return {
            'statusCode': 500,
            'body': '{"message": "Server configuration error"}'
        }

    # Extract and validate headers
    try:
        headers = event.get('headers', {})
        user_agent = headers.get('User-Agent', '')
        if_modified_since = headers.get('If-Modified-Since') or headers.get('if-modified-since')
        print(f"User-Agent: {user_agent}")
        if if_modified_since:
            print(f"If-Modified-Since: {if_modified_since}")
    except Exception as e:
        print(f"Error extracting headers: {e}")
        user_agent = ''
        if_modified_since = None

    # Determine file type based on User-Agent
    if 'iPhone' in user_agent or 'iPad' in user_agent or 'iPod' in user_agent or 'Macintosh' in user_agent or 'Darwin' in user_agent or 'passd' in user_agent:
        key = 'pass.pkpass'
        content_type = 'application/vnd.apple.pkpass'
    else:
        key = 'contact.vcard'
        content_type = 'text/vcard'

    # Retrieve file from S3 with specific error handling
    try:
        s3_object = s3.get_object(Bucket=bucket_name, Key=key)
        file_content = s3_object['Body'].read()
        last_modified = s3_object['LastModified']

        # Validate file content
        if not file_content:
            print(f"Warning: Empty file retrieved from S3: {key}")
            return {
                'statusCode': 404,
                'body': '{"message": "File not found or empty"}'
            }

        # Encode and return file
        try:
            encoded_content = base64.b64encode(file_content).decode('utf-8')
        except Exception as e:
            print(f"Error encoding file content: {e}")
            return {
                'statusCode': 500,
                'body': '{"message": "Error processing file content"}'
            }

        # Format Last-Modified header in HTTP date format (RFC 7231)
        last_modified_str = last_modified.strftime('%a, %d %b %Y %H:%M:%S GMT')

        # Check If-Modified-Since header for conditional requests
        if if_modified_since:
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
            except ValueError as e:
                print(f"Error parsing If-Modified-Since header: {e}")
                # Continue with normal response if header parsing fails

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

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchKey':
            print(f"Error: File not found in S3: {key}")
            return {
                'statusCode': 404,
                'body': '{"message": "Requested file not found"}'
            }
        elif error_code == 'NoSuchBucket':
            print(f"Error: S3 bucket not found: {bucket_name}")
            return {
                'statusCode': 500,
                'body': '{"message": "Storage configuration error"}'
            }
        else:
            print(f"AWS ClientError: {e}")
            return {
                'statusCode': 500,
                'body': '{"message": "Error retrieving file from storage"}'
            }
    except Exception as e:
        print(f"General S3 Error: {e}")
        return {
            'statusCode': 500,
            'body': '{"message": "Error retrieving file from storage"}'
        }
