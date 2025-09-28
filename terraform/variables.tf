variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "eu-west-3"
}

variable "passkit_auth_token" {
  description = "Authentication token for PassKit API - Generate with: openssl rand -base64 32"
  type        = string
  sensitive   = true
  # No default value - must be provided via terraform.tfvars or environment variable
}

variable "log_retention_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 14

  validation {
    condition = contains([
      1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653
    ], var.log_retention_days)
    error_message = "Log retention days must be one of the valid CloudWatch retention periods."
  }
}

variable "force_destroy_bucket" {
  description = "Allow Terraform to destroy the S3 bucket even if it contains objects"
  type        = bool
  default     = false
}

# APNs (Apple Push Notification service) credentials
variable "apns_key_id" {
  description = "APNs Key ID from Apple Developer account"
  type        = string
  sensitive   = true
  # No default - must be provided via terraform.tfvars
}

variable "apns_team_id" {
  description = "APNs Team ID from Apple Developer account"
  type        = string
  sensitive   = true
  # No default - must be provided via terraform.tfvars
}

variable "apns_bundle_id" {
  description = "Bundle ID for the wallet pass"
  type        = string
  sensitive   = true
  # No default - must be provided via terraform.tfvars
}

variable "apns_private_key" {
  description = "APNs private key content (PEM format)"
  type        = string
  sensitive   = true
  # No default - must be provided via terraform.tfvars
}