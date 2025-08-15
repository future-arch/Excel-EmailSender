# Azure AD 应用快速设置指南

## 1. 创建Azure AD应用（2分钟）
1. 访问 https://portal.azure.com
2. 搜索"Azure Active Directory" → "App registrations" → "New registration"
3. 填写：
   - Name: `SmartEmailSender`
   - Supported account types: `Accounts in this organizational directory only`
   - Redirect URI: `Public client/native (mobile & desktop)` → `http://localhost`

## 2. 配置权限（1分钟）
1. 进入刚创建的应用 → "API permissions"
2. 点击"Add a permission" → "Microsoft Graph" → "Delegated permissions"
3. 搜索并添加：
   - `Mail.Send`
   - `Mail.ReadWrite` 
   - `User.Read`
   - `GroupMember.Read.All`
   - `Group.Read.All`
   - `Directory.Read.All` (如果需要读取群组成员详细信息)
4. 点击"Grant admin consent"

## 3. 获取配置信息（30秒）
1. 在应用的"Overview"页面复制：
   - `Application (client) ID` → 这是你的 `AZURE_CLIENT_ID`
   - `Directory (tenant) ID` → 这是你的 `AZURE_TENANT_ID`

## 4. 创建.env文件
```bash
AZURE_CLIENT_ID=你复制的Application ID
AZURE_TENANT_ID=你复制的Directory ID
TEST_SELF_EMAIL=你的邮箱@公司域名.com
```

就这样！总共3-4分钟搞定。