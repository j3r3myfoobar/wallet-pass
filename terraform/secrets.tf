# --- AWS Secrets Manager for APNs Credentials ---

resource "aws_secretsmanager_secret" "apns_credentials" {
  name                    = "lemaire-tel-apns-credentials"
  description             = "Apple Push Notification Service JWT credentials"
  recovery_window_in_days = 7

  tags = {
    Name    = "APNs Credentials"
    Project = "lemaire.tel Pass Service"
  }
}

# Secret version - you'll need to populate this manually after deployment
resource "aws_secretsmanager_secret_version" "apns_credentials_version" {
  secret_id = aws_secretsmanager_secret.apns_credentials.id

  # APNs credentials from variables (populated via terraform.tfvars)
  secret_string = jsonencode({
    key_id      = var.apns_key_id
    team_id     = var.apns_team_id
    bundle_id   = var.apns_bundle_id
    private_key = var.apns_private_key
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# Grant Lambda access to the secret
data "aws_iam_policy_document" "secrets_manager_policy" {
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue"
    ]
    resources = [
      aws_secretsmanager_secret.apns_credentials.arn
    ]
  }
}

resource "aws_iam_policy" "lambda_secrets_policy" {
  name        = "lemaire-tel-lambda-secrets-policy"
  description = "Allow Lambda to access APNs secrets"
  policy      = data.aws_iam_policy_document.secrets_manager_policy.json
}

resource "aws_iam_role_policy_attachment" "lambda_secrets_attachment" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.lambda_secrets_policy.arn
}