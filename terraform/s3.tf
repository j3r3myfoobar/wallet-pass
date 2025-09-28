# --- S3 Bucket for Pass Files ---
resource "aws_s3_bucket" "pass_files_bucket" {
  bucket        = "lemaire-tel-pass-files"
  force_destroy = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "pass_files_bucket_encryption" {
  bucket = aws_s3_bucket.pass_files_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "pass_files_bucket_access" {
  bucket = aws_s3_bucket.pass_files_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket Notification for Pass Updates
resource "aws_s3_bucket_notification" "pass_update_notification" {
  bucket = aws_s3_bucket.pass_files_bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.s3_pass_update_function.arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".pkpass"
  }

  depends_on = [aws_lambda_permission.s3_invoke_pass_update_permission]
}