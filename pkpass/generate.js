const fs = require("fs");
const path = require("path");
const { PKPass } = require("passkit-generator");
require('dotenv').config({ path: path.join(__dirname, '..', '.env') });

// All configuration now comes from environment variables

function validateEnvironment() {
  const required = [
    'PASS_CERT_PATH', 'PASS_KEY_PATH', 'WWDR_CERT_PATH',
    'PASSKIT_AUTH_TOKEN', 'TEAM_IDENTIFIER', 'SERIAL_NUMBER',
    'PASS_TYPE_IDENTIFIER', 'WEB_SERVICE_URL', 'ORGANIZATION_NAME',
    'PASS_DESCRIPTION', 'LOGO_TEXT', 'CONTACT_NAME', 'CONTACT_EMAIL',
    'CONTACT_PHONE', 'CONTACT_LINKEDIN', 'CONTACT_WEBSITE'
  ];

  for (const env of required) {
    if (!process.env[env]) {
      throw new Error(`Missing required environment variable: ${env}`);
    }
  }
}

// No longer needed - all values come from environment variables

async function generatePass() {
  validateEnvironment();

  const certificates = {
    signerCert: fs.readFileSync(process.env.PASS_CERT_PATH),
    signerKey: fs.readFileSync(process.env.PASS_KEY_PATH),
    wwdr: fs.readFileSync(process.env.WWDR_CERT_PATH),
  };

  // Generate pass.json from template with environment variables
  await generatePassJson();

  // This points to the template folder containing pass.json + images
  const templateDir = path.join(__dirname, "template.pass");

  // Create pass from template
  const pass = await PKPass.from(
    {
      model: templateDir,
      certificates,
    }
  );

  const out = path.join(__dirname, "pass.pkpass");
  fs.writeFileSync(out, pass.getAsBuffer());
  console.log("Pass generated:", out);
}

async function generatePassJson() {
  const templatePath = path.join(__dirname, "template.pass", "pass.template.json");
  const outputPath = path.join(__dirname, "template.pass", "pass.json");

  // Read template
  let template = fs.readFileSync(templatePath, 'utf-8');

  // All values come from environment variables
  const replacements = {
    PASS_TYPE_IDENTIFIER: process.env.PASS_TYPE_IDENTIFIER,
    WEB_SERVICE_URL: process.env.WEB_SERVICE_URL,
    SERIAL_NUMBER: process.env.SERIAL_NUMBER,
    PASSKIT_AUTH_TOKEN: process.env.PASSKIT_AUTH_TOKEN,
    TEAM_IDENTIFIER: process.env.TEAM_IDENTIFIER,
    ORGANIZATION_NAME: process.env.ORGANIZATION_NAME,
    PASS_DESCRIPTION: process.env.PASS_DESCRIPTION,
    LOGO_TEXT: process.env.LOGO_TEXT,
    CONTACT_EMAIL: process.env.CONTACT_EMAIL,
    CONTACT_PHONE: process.env.CONTACT_PHONE,
    LINKEDIN_URL: process.env.CONTACT_LINKEDIN,
    WEBSITE_URL: process.env.CONTACT_WEBSITE
  };

  for (const [key, value] of Object.entries(replacements)) {
    template = template.replace(new RegExp(`\\$\\{${key}\\}`, 'g'), value);
  }

  // Write generated pass.json
  fs.writeFileSync(outputPath, template);
  console.log("Generated pass.json using environment variables");
}

function createVCard() {
  // All values from environment variables
  const name = process.env.CONTACT_NAME;
  const title = process.env.LOGO_TEXT;
  const email = process.env.CONTACT_EMAIL;
  const phone = process.env.CONTACT_PHONE;
  const linkedIn = process.env.CONTACT_LINKEDIN;

  // Read photo and convert to base64
  const photoPath = path.join(__dirname, 'template.pass', 'photo.jpg');
  const photoBase64 = fs.readFileSync(photoPath).toString('base64');

  // Build vCard content using v3.0 format for better compatibility
  const vCardContent = [
    'BEGIN:VCARD',
    'VERSION:3.0',
    `FN:${name}`,
    `TITLE:${title}`,
    `TEL;TYPE=CELL:${phone}`,
    `EMAIL:${email}`,
    `X-SOCIALPROFILE;TYPE=linkedin:${linkedIn}`,
    `PHOTO;ENCODING=BASE64;TYPE=JPEG:${photoBase64}`,
    'END:VCARD'
  ].join('\r\n');

  // Write to file
  const outputPath = path.join(__dirname, 'contact.vcard');
  fs.writeFileSync(outputPath, vCardContent);
  console.log(`vCard created at ${outputPath} using environment variables`);
}


async function main() {
    await generatePass();
    createVCard();
}

main().catch(console.error);