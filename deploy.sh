#!/bin/bash
set -e  # Exit on any error

echo "Starting deployment..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}INFO: $1${NC}"
}

print_success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
}

print_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

# Clean up previous build artifacts
print_status "Cleaning up previous build artifacts..."
rm -rf lambda_functions/__pycache__/
rm -rf lambda_functions/*.pyc
rm -f terraform/lambda_functions.zip

# Install Lambda dependencies
print_status "Installing Lambda dependencies..."
cd lambda_functions

# Create temporary directory for dependencies
mkdir -p .build
cp *.py .build/
cp requirements.txt .build/

cd .build

# Install only production dependencies (exclude dev dependencies)
pip3 install -r requirements.txt -t . --no-deps --only-binary=all 2>/dev/null || {
    # Fallback: install with dependencies if no-deps fails
    pip3 install boto3==1.34.131 botocore==1.34.131 -t . --only-binary=all
}

# Remove unnecessary files to reduce package size
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
find . -name "*.dist-info" -type d -exec rm -rf {} + 2>/dev/null || true

# Create deployment package
print_status "Creating deployment package..."
zip -r ../../terraform/lambda_functions.zip . -x "requirements.txt" "*.dist-info/*" > /dev/null

cd ../..
rm -rf lambda_functions/.build

print_success "Lambda package created successfully"

# Deploy with Terraform
print_status "Deploying infrastructure with Terraform..."
cd terraform

# Check if .env file exists
if [ ! -f "../.env" ]; then
    print_error ".env file not found!"
    print_status "Please copy .env.example to .env and fill in your values:"
    print_status "  cp .env.example .env"
    exit 1
fi

# Initialize Terraform if needed
if [ ! -d ".terraform" ]; then
    print_status "Initializing Terraform..."
    terraform init
fi

# Validate configuration
print_status "Validating Terraform configuration..."
../use-env.sh validate

# Plan deployment
print_status "Planning deployment..."
./use-env.sh plan -out=tfplan

# Apply deployment
print_status "Applying deployment..."
./use-env.sh apply tfplan

# Clean up plan file
rm -f tfplan

cd ..

print_success "Deployment completed successfully!"
print_status "Your serverless application is now updated at: https://pass.lemaire.tel"