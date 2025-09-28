#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}INFO: $1${NC}"
}

print_success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
}

print_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}WARNING: $1${NC}"
}

echo "Uploading pass files to S3..."

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install it first:"
    print_status "  brew install awscli"
    print_status "  pip3 install awscli"
    exit 1
fi

# Get bucket name from Terraform outputs
print_status "Getting S3 bucket name from Terraform..."
cd ../terraform

if [ ! -f "terraform.tfstate" ]; then
    print_error "terraform.tfstate not found. Please run 'terraform apply' first."
    exit 1
fi

BUCKET_NAME=$(terraform output -raw s3_bucket_name 2>/dev/null || echo "lemaire-tel-pass-files")

if [ -z "$BUCKET_NAME" ]; then
    print_warning "Could not get bucket name from Terraform output, using default: lemaire-tel-pass-files"
    BUCKET_NAME="lemaire-tel-pass-files"
fi

print_status "Using S3 bucket: $BUCKET_NAME"

cd ../pkpass

# Check if pass files exist
PASS_FILE="pass.pkpass"
VCARD_FILE="contact.vcard"

if [ ! -f "$PASS_FILE" ]; then
    print_error "Pass file not found: $PASS_FILE"
    print_status "Please generate passes first:"
    print_status "  npm run generate"
    exit 1
fi

if [ ! -f "$VCARD_FILE" ]; then
    print_error "vCard file not found: $VCARD_FILE"
    print_status "Please generate passes first:"
    print_status "  npm run generate"
    exit 1
fi

# Check AWS credentials
print_status "Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials not configured. Please run:"
    print_status "  aws configure"
    exit 1
fi

# Upload files to S3
print_status "Uploading pass.pkpass..."
aws s3 cp "$PASS_FILE" "s3://$BUCKET_NAME/pass.pkpass" \
    --content-type "application/vnd.apple.pkpass" \
    --metadata "description=Apple Wallet Pass"

if [ $? -eq 0 ]; then
    print_success "pass.pkpass uploaded successfully"
else
    print_error "Failed to upload pass.pkpass"
    exit 1
fi

print_status "Uploading contact.vcard..."
aws s3 cp "$VCARD_FILE" "s3://$BUCKET_NAME/contact.vcard" \
    --content-type "text/vcard" \
    --metadata "description=vCard Contact"

if [ $? -eq 0 ]; then
    print_success "contact.vcard uploaded successfully"
else
    print_error "Failed to upload contact.vcard"
    exit 1
fi

# Verify uploads
print_status "Verifying uploads..."
aws s3 ls "s3://$BUCKET_NAME/" --human-readable

print_success "All files uploaded successfully!"
print_status "Your pass service is ready at: https://pass.lemaire.tel"