# --- Lambda Functions ---

# CloudWatch log groups with explicit retention policy
resource "aws_cloudwatch_log_group" "pass_redirect_function_logs" {
  name              = "/aws/lambda/lemaire-tel-pass-redirect"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "passkit_registration_function_logs" {
  name              = "/aws/lambda/lemaire-tel-passkit-registration"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "passkit_unregistration_function_logs" {
  name              = "/aws/lambda/lemaire-tel-passkit-unregistration"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "log_errors_function_logs" {
  name              = "/aws/lambda/lemaire-tel-log-errors"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "get_updatable_passes_function_logs" {
  name              = "/aws/lambda/lemaire-tel-get-updatable-passes"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "s3_pass_update_function_logs" {
  name              = "/aws/lambda/lemaire-tel-s3-pass-update"
  retention_in_days = var.log_retention_days
}

data "archive_file" "lambda_functions_zip" {
  type        = "zip"
  source_dir  = "../lambda_functions"
  output_path = "${path.module}/lambda_functions.zip"
  excludes    = ["requirements.txt", "__pycache__", "*.pyc"]
}

# Pure Python layer for APNs push notifications (works on both ARM64 and x86_64)
data "aws_lambda_layer_version" "python_jose_apns" {
  layer_name = "lemaire-tel-python-jose-apns"
  version    = 2  # Pure Python layer with python-jose + ECDSA + HTTPX + HTTP/2 support
}

resource "aws_lambda_function" "pass_redirect_function" {
  function_name    = "lemaire-tel-pass-redirect"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "pass_redirect_function.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.lambda_functions_zip.output_path
  source_code_hash = data.archive_file.lambda_functions_zip.output_base64sha256
  depends_on       = [aws_cloudwatch_log_group.pass_redirect_function_logs]

  environment {
    variables = {
      S3_BUCKET_NAME = aws_s3_bucket.pass_files_bucket.bucket
    }
  }
}

resource "aws_lambda_function" "passkit_registration_function" {
  function_name    = "lemaire-tel-passkit-registration"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "passkit_registration_function.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.lambda_functions_zip.output_path
  source_code_hash = data.archive_file.lambda_functions_zip.output_base64sha256
  depends_on       = [aws_cloudwatch_log_group.passkit_registration_function_logs]

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.wallet_registrations.name
      AUTH_TOKEN = var.passkit_auth_token
    }
  }
}

resource "aws_lambda_function" "passkit_unregistration_function" {
  function_name    = "lemaire-tel-passkit-unregistration"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "passkit_unregistration_function.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.lambda_functions_zip.output_path
  source_code_hash = data.archive_file.lambda_functions_zip.output_base64sha256
  depends_on       = [aws_cloudwatch_log_group.passkit_unregistration_function_logs]

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.wallet_registrations.name
      AUTH_TOKEN = var.passkit_auth_token
    }
  }
}

resource "aws_lambda_function" "log_errors_function" {
  function_name    = "lemaire-tel-log-errors"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "log_errors_function.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.lambda_functions_zip.output_path
  source_code_hash = data.archive_file.lambda_functions_zip.output_base64sha256
  depends_on       = [aws_cloudwatch_log_group.log_errors_function_logs]
}

resource "aws_lambda_function" "get_updatable_passes_function" {
  function_name    = "lemaire-tel-get-updatable-passes"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "get_updatable_passes_function.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.lambda_functions_zip.output_path
  source_code_hash = data.archive_file.lambda_functions_zip.output_base64sha256
  depends_on       = [aws_cloudwatch_log_group.get_updatable_passes_function_logs]

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.wallet_registrations.name
      AUTH_TOKEN = var.passkit_auth_token
    }
  }
}

resource "aws_lambda_function" "s3_pass_update_function" {
  function_name    = "lemaire-tel-s3-pass-update"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "s3_pass_update_function.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.lambda_functions_zip.output_path
  source_code_hash = data.archive_file.lambda_functions_zip.output_base64sha256
  timeout          = 60  # Increased timeout for push notifications
  layers           = [data.aws_lambda_layer_version.python_jose_apns.arn]
  depends_on       = [aws_cloudwatch_log_group.s3_pass_update_function_logs]

  environment {
    variables = {
      TABLE_NAME            = aws_dynamodb_table.wallet_registrations.name
      PASS_TYPE_IDENTIFIER  = "pass.tel.lemaire.business"
      SERIAL_NUMBER         = "jeremy-business-card"
      APNS_SECRETS_ARN      = aws_secretsmanager_secret.apns_credentials.arn
    }
  }
}

# --- Lambda Permissions ---
resource "aws_lambda_permission" "api_gw_redirect_permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.pass_redirect_function.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.pass_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gw_registration_permission" {
  statement_id  = "AllowAPIGatewayInvokeRegistration"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.passkit_registration_function.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.pass_api.execution_arn}/*/POST/v1/devices/{deviceLibraryIdentifier}/registrations/{passTypeIdentifier}/{serialNumber}"
}

resource "aws_lambda_permission" "api_gw_unregistration_permission" {
  statement_id  = "AllowAPIGatewayInvokeUnregistration"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.passkit_unregistration_function.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.pass_api.execution_arn}/*/DELETE/v1/devices/{deviceLibraryIdentifier}/registrations/{passTypeIdentifier}/{serialNumber}"
}

resource "aws_lambda_permission" "api_gw_log_errors_permission" {
  statement_id  = "AllowAPIGatewayInvokeLogErrors"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.log_errors_function.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.pass_api.execution_arn}/*/POST/v1/log"
}

resource "aws_lambda_permission" "api_gw_get_updatable_passes_permission" {
  statement_id  = "AllowAPIGatewayInvokeGetUpdatablePasses"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_updatable_passes_function.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.pass_api.execution_arn}/*/GET/v1/devices/{deviceLibraryIdentifier}/registrations/{passTypeIdentifier}"
}

resource "aws_lambda_permission" "s3_invoke_pass_update_permission" {
  statement_id  = "AllowS3InvokePassUpdate"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.s3_pass_update_function.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.pass_files_bucket.arn
}