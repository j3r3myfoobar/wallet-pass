#!/bin/bash

# Terraform wrapper script to load environment variables from .env file
# Usage: ./use-env.sh plan|apply|destroy

# Check if .env file exists
if [ ! -f "../.env" ]; then
    echo "❌ Error: .env file not found!"
    echo "📋 Copy .env.example to .env and fill in your values:"
    echo "   cp .env.example .env"
    exit 1
fi

# Load environment variables from .env file
echo "🔧 Loading environment variables from .env file..."
set -a  # automatically export all variables
source ../.env
set +a  # turn off automatic export

# Verify required Terraform variables are set
required_vars=(
    "TF_VAR_passkit_auth_token"
    "TF_VAR_apns_key_id"
    "TF_VAR_apns_team_id"
    "TF_VAR_apns_bundle_id"
    "TF_VAR_apns_private_key"
)

missing_vars=()
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "❌ Error: Missing required environment variables:"
    printf '   %s\n' "${missing_vars[@]}"
    echo "📝 Please update your .env file with the missing values"
    exit 1
fi

echo "✅ Environment variables loaded successfully"

# Run terraform command
if [ $# -eq 0 ]; then
    echo "Usage: $0 [terraform-command]"
    echo "Examples:"
    echo "  $0 plan"
    echo "  $0 apply"
    echo "  $0 destroy"
    exit 1
fi

terraform "$@"