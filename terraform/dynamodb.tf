# --- DynamoDB Table for Registrations ---
resource "aws_dynamodb_table" "wallet_registrations" {
  name           = "WalletRegistrations"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "pass_id"
  range_key      = "deviceLibraryIdentifier"

  server_side_encryption {
    enabled = true
  }

  attribute {
    name = "pass_id"
    type = "S"
  }

  attribute {
    name = "deviceLibraryIdentifier"
    type = "S"
  }

  tags = {
    Name    = "WalletRegistrations"
    Project = "lemaire.tel Pass Service"
  }
}