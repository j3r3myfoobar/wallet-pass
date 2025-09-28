output "api_gateway_url" {
  description = "URL of the API Gateway"
  value       = aws_apigatewayv2_api.pass_api.api_endpoint
}

output "custom_domain_url" {
  description = "Custom domain URL for the pass service"
  value       = "https://${aws_apigatewayv2_domain_name.pass_domain_name.domain_name}"
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket storing pass files"
  value       = aws_s3_bucket.pass_files_bucket.id
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table for wallet registrations"
  value       = aws_dynamodb_table.wallet_registrations.name
}

output "lambda_function_names" {
  description = "Names of all Lambda functions"
  value = {
    pass_redirect     = aws_lambda_function.pass_redirect_function.function_name
    registration      = aws_lambda_function.passkit_registration_function.function_name
    unregistration    = aws_lambda_function.passkit_unregistration_function.function_name
    error_logging     = aws_lambda_function.log_errors_function.function_name
  }
}