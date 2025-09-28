# Digital Business Card Service

A serverless AWS solution that serves Apple Wallet passes (.pkpass) to iOS/macOS devices and vCard files to other devices, accessible at `pass.lemaire.tel`.

## Architecture

- **Lambda Functions**: User-Agent detection, pass serving, Apple Wallet webhook handling
- **API Gateway**: RESTful endpoints for pass distribution and Apple Wallet integration
- **S3**: Pass file storage with CloudFront distribution
- **DynamoDB**: Device registration tracking
- **Route 53**: DNS management for custom domain

## Quick Start

### 1. Environment Setup

```bash
# Clone and install dependencies
git clone <repository>
cd wallet-pass
npm install

# Copy and configure environment
cp .env.example .env
# Edit .env with your Apple Developer credentials and AWS settings
```

### 2. Generate Pass Files

```bash
cd pkpass
npm install
npm run generate  # Creates pass.pkpass and contact.vcard
```

### 3. Deploy Infrastructure

```bash
cd terraform
terraform init
./use-env.sh apply  # Deploys using .env configuration
```

### 4. Upload Files

```bash
./upload-files.sh  # Uploads pass files to S3
```

## Configuration

**Single `.env` file** contains all configuration:
- **Apple Developer**: Certificates, team ID, bundle ID, auth tokens
- **AWS Settings**: Region, retention policies
- **Pass Content**: Serial numbers, service URLs

Public configuration (names, descriptions, URLs) is in `config.json`.

## Key Features

- **Smart Device Detection**: Automatically serves .pkpass to Apple devices, .vcard to others
- **Apple Wallet Integration**: Full webhook support for pass updates and device management
- **Secure Credentials**: All sensitive data in environment variables, never committed
- **Unified Configuration**: Single .env file for both Node.js and Terraform

## Development Commands

```bash
# Testing
python3 -m pytest tests/ -v

# Infrastructure
cd terraform && ./use-env.sh plan|apply|destroy

# Pass generation
cd pkpass && npm run generate

# File upload
./upload-files.sh
```

## Security

⚠️ **Critical**: Never commit certificates (.pem, .key, .p8), auth tokens, or the `.env` file to Git. All sensitive configuration uses environment variables.

## File Structure

```
/
├── terraform/          # Infrastructure as Code + deployment script
├── lambda_functions/    # Python serverless functions
├── pkpass/             # Pass generation tools + templates
├── config.json         # Public configuration
├── .env.example        # Environment template
└── tests/              # Unit tests
```