# Digital Business Card Service

A serverless AWS solution that serves Apple Wallet passes (.pkpass) to iOS/macOS devices and vCard files to other devices, accessible at `pass.lemaire.tel`.

**Apple Developer Account Required**: You need an active Apple Developer Program membership to generate the certificates required for signing Apple Wallet passes.

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

# Documentation diagrams
npm install && npx mmdc -i aws-architecture.md -o aws-architecture.png --iconPacks @iconify-json/logos -b transparent -s 2
```

## Documentation Diagrams

The project uses [Mermaid](https://mermaid.js.org/) for architecture diagrams with custom configuration for AWS icons.

### Generate Architecture Diagrams

```bash
# Install dependencies (only needed once)
npm install

# Generate PNG from Mermaid markdown
npx mmdc -i aws-architecture.md -o aws-architecture.png --iconPacks @iconify-json/logos -b transparent -s 2

# Generate SVG format
npx mmdc -i aws-architecture.md -o aws-architecture.svg --iconPacks @iconify-json/logos -b transparent -s 2
```

**Command flags**:

- `--iconPacks @iconify-json/logos` - Enables AWS and tech logos
- `-b transparent` - Transparent background
- `-s 2` - Scale factor for higher resolution

## Security

**Critical**: Never commit certificates (.pem, .key, .p8), auth tokens, or the `.env` file to Git. All sensitive configuration uses environment variables.

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

## Todo

- **Domain Configuration Warning**: This code is currently configured for the domain `pass.lemaire.tel`. You'll need to update the domain configuration throughout the codebase (Terraform files, Lambda functions, and pass templates) to use your own domain before deployment.
- Make support multiple user
- Add support for Google Wallet (should be simpler because the pass lives in Google's cloud and updates propagate automatically without requiring a push to each device)
