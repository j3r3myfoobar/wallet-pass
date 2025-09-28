import os

def validate_authorization(event):
    """
    Validates the Authorization header for an Apple Wallet pass request.
    Returns an error dictionary if validation fails, otherwise returns None.
    """
    auth_header = event.get('headers', {}).get('authorization')
    if not auth_header:
        print("Authorization header is missing")
        return {'statusCode': 401, 'body': 'Unauthorized'}

    auth_token = os.environ.get('AUTH_TOKEN')
    if not auth_token:
        print("Error: AUTH_TOKEN environment variable is not set.")
        return {'statusCode': 500, 'body': 'Internal Server Error'}

    expected_token = f"ApplePass {auth_token}"

    if auth_header != expected_token:
        print(f"Authorization failed. Expected: {expected_token}, Got: {auth_header}")
        return {'statusCode': 401, 'body': 'Unauthorized'}

    return None # Indicates success
