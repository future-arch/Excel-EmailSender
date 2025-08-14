# SmartEmailSender Project

## Project Overview
A professional bulk email sending application that integrates with Microsoft Graph API to send personalized emails using Excel data.

## Key Features
- **Bulk Email Sending**: Send personalized emails to multiple recipients
- **Excel Integration**: Import recipient data from Excel files (.xlsx/.xls)
- **Microsoft 365 Groups Integration**: Select and send emails to M365 groups
  - Send to group email addresses (all members receive as group email)
  - Send to individual member email addresses (each member receives personal email)
  - Group member preview and selection interface
- **HTML Templates**: Rich email templates with Jinja2 syntax (e.g., `{{姓名}}`)
- **Attachment Support**: 
  - Common attachments (sent to everyone)
  - Personalized attachments (matched by name in filename)
- **Secure Authentication**: Microsoft Graph API with MSAL OAuth
- **Test Modes**: Draft saving, self-testing, formal sending
- **Recipient Filtering**: Filter recipients by Excel column values
- **Rich Text Editor**: Bold, italic, underline, fonts, colors, bullet lists

## Technical Stack
- **Language**: Python 3
- **GUI Framework**: PySide6 (Qt6)
- **Email API**: Microsoft Graph API
- **Authentication**: MSAL (Microsoft Authentication Library)
- **Template Engine**: Jinja2
- **Data Processing**: pandas
- **Excel Reading**: openpyxl

## Project Structure
```
/
├── src/SmartEmailSender.py    # Main application file
├── requirements.txt            # Python dependencies  
├── README.md                  # Documentation
├── assets/                    # Application icons
│   └── SmartEmailSender.icns
└── data/                      # Data folder (empty)
```

## Dependencies
- pandas>=1.5.0
- requests>=2.28.0  
- msal>=1.20.0
- jinja2>=3.1.0
- python-dotenv>=1.0.0
- PySide6>=6.5.0
- openpyxl>=3.1.0

## Configuration
Requires environment variables:
- `AZURE_CLIENT_ID`: Azure AD application client ID
- `AZURE_TENANT_ID`: Azure AD tenant ID  
- `TEST_SELF_EMAIL`: Email for testing mode

Required Microsoft Graph API permissions:
- `Mail.Send`: Send emails
- `Mail.ReadWrite`: Read/write emails
- `User.Read`: Read user profile
- `GroupMember.Read.All`: Read group memberships
- `Group.Read.All`: Read group information

## Security Features
- OAuth2 authentication with Microsoft
- Token caching with automatic refresh
- Environment variable configuration
- Test mode to prevent accidental sends
- Minimum required permissions (Mail.Send, Mail.ReadWrite, User.Read)

## Key Classes
- `MailerApp`: Main GUI application
- `MailWorker`: Background email sending worker
- `AuthDialog`: OAuth authentication dialog
- `VerificationDialog`: Personalized attachment preview
- `GroupSelectionDialog`: Microsoft 365 group selection interface

## New Features Added (Latest Update)
- **Microsoft 365 Groups Integration**: Users can now select M365 groups as email recipients
- **Dual Sending Modes**: Choose between sending to group email addresses or individual member emails
- **Group Member Preview**: Preview group members before sending
- **Flexible Recipient Selection**: Support both Excel data and M365 groups, with option to choose when both are available

## Run Command
```bash
python src/SmartEmailSender.py
```

## Git Status
- Repository: Clean working directory
- Main branch: main
- Recent commits include cleanup and project renaming