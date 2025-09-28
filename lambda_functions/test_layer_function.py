import json
import sys
import os

def handler(event, context):
    """
    Test function to debug layer loading issues.
    """
    try:
        print(f"Python path: {sys.path}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Contents of /opt: {os.listdir('/opt') if os.path.exists('/opt') else 'Not found'}")

        if os.path.exists('/opt/python'):
            print(f"Contents of /opt/python: {os.listdir('/opt/python')}")

        # Try importing jwt
        import jwt
        print("JWT import successful!")
        print(f"JWT version: {jwt.__version__ if hasattr(jwt, '__version__') else 'Unknown'}")

        # Try importing httpx
        import httpx
        print("HTTPX import successful!")

        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'success', 'jwt_available': True, 'httpx_available': True})
        }

    except ImportError as e:
        print(f"Import error: {e}")
        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'error', 'error': str(e), 'path': sys.path})
        }
    except Exception as e:
        print(f"General error: {e}")
        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'error', 'error': str(e)})
        }