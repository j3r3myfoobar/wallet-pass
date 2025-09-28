# Certificates Directory

This directory contains Apple Developer certificates required for PassKit signing.

## ⚠️ SECURITY WARNING

**NEVER commit actual certificate files to Git!**

## Required Files (NOT included in repository)

You need to place these files here for the project to work:

### 1. Apple Pass Type Certificate
- `pass.pem` - Your Pass Type ID certificate from Apple Developer
- `pass.key` - Private key for the Pass Type ID certificate

### 2. Apple Worldwide Developer Relations Certificate
- `wwdr.pem` - Apple's intermediate certificate (can be downloaded from Apple)

### 3. APNs Authentication Key (for push notifications)
- `AuthKey_XXXXXXXXXX.p8` - Your APNs authentication key from Apple Developer
- Replace `XXXXXXXXXX` with your actual Key ID

### 4. Notification Certificate (alternative to APNs key)
- `notif_key.pem` - Alternative notification certificate (if not using APNs key)

## How to Obtain These Certificates

1. **Pass Type ID Certificate:**
   - Go to Apple Developer Console
   - Certificates, Identifiers & Profiles > Certificates
   - Create a new "Pass Type ID Certificate"
   - Download and install in Keychain
   - Export as .p12, then convert to .pem and .key

2. **WWDR Certificate:**
   - Download from: https://developer.apple.com/certificationauthority/AppleWWDRCA.cer
   - Convert to PEM format

3. **APNs Authentication Key:**
   - Apple Developer Console > Keys
   - Create new key with APNs service enabled
   - Download the .p8 file

## Security Best Practices

- Keep certificates in secure location locally
- Use environment variables for certificate paths in production
- Rotate certificates before expiration
- Use AWS Secrets Manager for production secrets
- Never share private keys or commit them to version control

## File Permissions

Set restrictive permissions on certificate files:
```bash
chmod 600 *.pem *.key *.p8
```