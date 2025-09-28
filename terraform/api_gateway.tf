# --- API Gateway Resources ---
resource "aws_apigatewayv2_api" "pass_api" {
  name          = "lemaire-tel-pass-api"
  protocol_type = "HTTP"
}

# Integration for Pass/vCard Redirection Lambda
resource "aws_apigatewayv2_integration" "redirect_lambda_integration" {
  api_id           = aws_apigatewayv2_api.pass_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.pass_redirect_function.invoke_arn
}

# Integration for PassKit Registration Lambda
resource "aws_apigatewayv2_integration" "registration_lambda_integration" {
  api_id           = aws_apigatewayv2_api.pass_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.passkit_registration_function.invoke_arn
}

# Integration for PassKit Unregistration Lambda
resource "aws_apigatewayv2_integration" "unregistration_lambda_integration" {
  api_id           = aws_apigatewayv2_api.pass_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.passkit_unregistration_function.invoke_arn
}

# Integration for Error Logging Lambda
resource "aws_apigatewayv2_integration" "log_errors_lambda_integration" {
  api_id           = aws_apigatewayv2_api.pass_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.log_errors_function.invoke_arn
}

# Integration for Get Updatable Passes Lambda
resource "aws_apigatewayv2_integration" "get_updatable_passes_lambda_integration" {
  api_id           = aws_apigatewayv2_api.pass_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.get_updatable_passes_function.invoke_arn
}

# Route for Pass/vCard Redirection (default route)
resource "aws_apigatewayv2_route" "default_route" {
  api_id    = aws_apigatewayv2_api.pass_api.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.redirect_lambda_integration.id}"
}

# Route for PassKit Registration
resource "aws_apigatewayv2_route" "registration_route" {
  api_id    = aws_apigatewayv2_api.pass_api.id
  route_key = "POST /v1/devices/{deviceLibraryIdentifier}/registrations/{passTypeIdentifier}/{serialNumber}"
  target    = "integrations/${aws_apigatewayv2_integration.registration_lambda_integration.id}"
}

# Route for PassKit Unregistration
resource "aws_apigatewayv2_route" "unregistration_route" {
  api_id    = aws_apigatewayv2_api.pass_api.id
  route_key = "DELETE /v1/devices/{deviceLibraryIdentifier}/registrations/{passTypeIdentifier}/{serialNumber}"
  target    = "integrations/${aws_apigatewayv2_integration.unregistration_lambda_integration.id}"
}

# Route for Error Logging
resource "aws_apigatewayv2_route" "log_errors_route" {
  api_id    = aws_apigatewayv2_api.pass_api.id
  route_key = "POST /v1/log"
  target    = "integrations/${aws_apigatewayv2_integration.log_errors_lambda_integration.id}"
}

# Route for Get Updatable Passes
resource "aws_apigatewayv2_route" "get_updatable_passes_route" {
  api_id    = aws_apigatewayv2_api.pass_api.id
  route_key = "GET /v1/devices/{deviceLibraryIdentifier}/registrations/{passTypeIdentifier}"
  target    = "integrations/${aws_apigatewayv2_integration.get_updatable_passes_lambda_integration.id}"
}

# Route for Get Pass (for Apple Wallet to download updated passes)
resource "aws_apigatewayv2_route" "get_pass_route" {
  api_id    = aws_apigatewayv2_api.pass_api.id
  route_key = "GET /v1/passes/{passTypeIdentifier}/{serialNumber}"
  target    = "integrations/${aws_apigatewayv2_integration.redirect_lambda_integration.id}"
}

# --- API Gateway Logging ---
resource "aws_cloudwatch_log_group" "api_gateway_access_logs" {
  name              = "/aws/apigateway/lemaire-tel-pass-api-access"
  retention_in_days = var.log_retention_days
}

resource "aws_apigatewayv2_stage" "default_stage" {
  api_id      = aws_apigatewayv2_api.pass_api.id
  name        = "$default"
  auto_deploy = true
  depends_on = [
    aws_apigatewayv2_route.default_route,
    aws_apigatewayv2_route.registration_route,
  ]

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway_access_logs.arn
    format          = jsonencode({
      requestId               = "$context.requestId"
      ip                      = "$context.identity.sourceIp"
      caller                  = "$context.identity.caller"
      user                    = "$context.identity.user"
      requestTime             = "$context.requestTime"
      httpMethod              = "$context.httpMethod"
      resourcePath            = "$context.resourcePath"
      status                  = "$context.status"
      protocol                = "$context.protocol"
      responseLength          = "$context.responseLength"
      integrationErrorMessage = "$context.integrationErrorMessage"
    })
  }
}