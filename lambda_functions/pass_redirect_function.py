import os
import boto3
import base64
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
        print(f"User-Agent: {user_agent}")
    except Exception as e:
        print(f"Error extracting headers: {e}")
        user_agent = ''

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

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': content_type,
                'Content-Disposition': f'attachment; filename="{key}"',
                'Cache-Control': 'public, max-age=3600'  # Cache for 1 hour
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
