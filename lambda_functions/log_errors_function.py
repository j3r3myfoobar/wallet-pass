import json

def handler(event, context):
    """
    Handles error logging requests from the Apple Wallet app.
    Endpoint: POST /v1/log
    """
    print(f"Received event: {json.dumps(event)}")

    try:
        body = json.loads(event.get('body', '{}'))
        logs = body.get('logs')
        if logs:
            for log_message in logs:
                print(f"Apple Wallet Error: {log_message}")
        else:
            print("No logs found in request body.")

    except json.JSONDecodeError:
        print("Error: Invalid JSON in request body.")
        # Still return 200 OK as per Apple's recommendation
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # Still return 200 OK

    # Apple's documentation states to always return a 200 OK for this endpoint.
    return {'statusCode': 200, 'body': ''}
