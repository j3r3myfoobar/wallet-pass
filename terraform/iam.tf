# --- IAM Role for Lambda Execution ---
resource "aws_iam_role" "lambda_exec_role" {
  name = "lemaire-tel-lambda-exec-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# --- IAM Policy for Lambda (S3 and DynamoDB) ---
resource "aws_iam_policy" "lambda_passkit_policy" {
  name        = "lemaire-tel-lambda-passkit-policy"
  description = "Allows Lambda functions to get objects from S3 and manage DynamoDB registrations."

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = "s3:GetObject",
        Resource = "${aws_s3_bucket.pass_files_bucket.arn}/*"
      },
      {
        Effect = "Allow",
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:GetItem",
          "dynamodb:DeleteItem",
          "dynamodb:Scan"
        ],
        Resource = aws_dynamodb_table.wallet_registrations.arn
      }
    ]
  })
}

# --- Attach the PassKit policy to the Lambda role ---
resource "aws_iam_role_policy_attachment" "lambda_passkit_attach" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.lambda_passkit_policy.arn
}

# --- Add basic Lambda logging policy ---
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  lifecycle {
    create_before_destroy = true
    prevent_destroy = false
  }
}

# --- API Gateway CloudWatch Role ---
resource "aws_iam_role" "api_gateway_cloudwatch_role" {
  name = "lemaire-tel-apigw-cloudwatch-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "api_gateway_cloudwatch_attach" {
  role       = aws_iam_role.api_gateway_cloudwatch_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
}