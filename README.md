# Excel EmailSender

A professional email sending application that integrates with Microsoft Graph API to send personalized bulk emails using Excel data.

## Features

- 📧 **Bulk Email Sending** - Send personalized emails to multiple recipients
- 📊 **Excel Integration** - Import recipient data from Excel files
- 🎨 **HTML Templates** - Support for rich HTML email templates with Jinja2
- 📎 **Attachments** - Support for both common and personalized attachments
- 🔐 **Secure Authentication** - Microsoft Graph API integration with MSAL
- 🎯 **Test Mode** - Preview and test emails before sending
- 📱 **Modern GUI** - Built with PySide6 for a professional interface

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your Azure AD credentials:
```bash
cp .env.example .env
```

Edit `.env` file with your actual values:
```
AZURE_CLIENT_ID=your-client-id-here
AZURE_TENANT_ID=your-tenant-id-here
TEST_SELF_EMAIL=your-test-email@example.com
```

### 3. Azure AD App Registration
1. Go to Azure Portal → Azure Active Directory → App registrations
2. Create new application or use existing one
3. Note down Application (client) ID and Directory (tenant) ID
4. Grant the following Microsoft Graph API permissions:
   - `Mail.Send`
   - `Mail.ReadWrite`
   - `User.Read`

### 4. Run the Application
```bash
python src/EmailSender.py
```

## Usage

1. **Connect to Microsoft Graph** - Authenticate with your Microsoft account
2. **Import Excel Data** - Select your Excel file with recipient information
3. **Configure Templates** - Set up your email subject and body templates
4. **Add Attachments** - Include any common or personalized attachments
5. **Test & Send** - Use test mode to preview, then send to all recipients

## Security Best Practices

- Never commit `.env` file to version control
- Use least privilege principle for API permissions
- Regularly rotate client secrets
- Keep dependencies up to date

## Building Executable

Use PyInstaller to create a standalone executable:
```bash
pyinstaller "Excel EmailSender.spec"
```

## License

This project is for educational and business use only.