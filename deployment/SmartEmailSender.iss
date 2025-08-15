; SmartEmailSender Inno Setup Script
; 专业的Windows安装程序

[Setup]
; 应用信息
AppId={{E8A0B6C4-1234-5678-9ABC-DEF012345678}
AppName=SmartEmailSender
AppVersion=1.0.0
AppPublisher=SmartEmailSender
AppPublisherURL=https://smartemailsender.com
AppSupportURL=https://smartemailsender.com/support
AppUpdatesURL=https://smartemailsender.com/download
DefaultDirName={autopf}\SmartEmailSender
DisableProgramGroupPage=yes
LicenseFile=LICENSE.txt
InfoBeforeFile=INSTALL_INFO.txt
OutputDir=releases
OutputBaseFilename=SmartEmailSender-Setup-InnoSetup
SetupIconFile=assets\SmartEmailSender.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

; 系统要求
MinVersion=10.0
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

; 特权
PrivilegesRequired=admin

; 界面设置
WizardImageFile=installer_wizard.bmp
WizardSmallImageFile=installer_small.bmp

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
Source: "dist\SmartEmailSender\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "README.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "field_mapping_config.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "version.json"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\SmartEmailSender"; Filename: "{app}\SmartEmailSender.exe"
Name: "{autodesktop}\SmartEmailSender"; Filename: "{app}\SmartEmailSender.exe"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\SmartEmailSender"; Filename: "{app}\SmartEmailSender.exe"; Tasks: quicklaunchicon

[Registry]
; 文件关联
Root: HKCR; Subkey: ".xlsx\OpenWithProgids"; ValueType: string; ValueName: "SmartEmailSender.xlsx"; ValueData: ""; Flags: uninsdeletevalue
Root: HKCR; Subkey: "SmartEmailSender.xlsx"; ValueType: string; ValueName: ""; ValueData: "Excel文件"; Flags: uninsdeletekey
Root: HKCR; Subkey: "SmartEmailSender.xlsx\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\SmartEmailSender.exe,0"
Root: HKCR; Subkey: "SmartEmailSender.xlsx\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\SmartEmailSender.exe"" ""%1"""

; 应用路径注册
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\SmartEmailSender.exe"; ValueType: string; ValueName: ""; ValueData: "{app}\SmartEmailSender.exe"; Flags: uninsdeletekey

[Run]
Filename: "{app}\SmartEmailSender.exe"; Description: "{cm:LaunchProgram,SmartEmailSender}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\*.log"
Type: files; Name: "{app}\token_cache.json"
Type: files; Name: "{app}\settings.json"

[Code]
// 检查是否已安装Microsoft Edge WebView2
function IsWebView2Installed: Boolean;
var
  Version: String;
begin
  Result := RegQueryStringValue(HKLM, 'SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Version) or
            RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Version);
end;

// 初始化安装程序时检查依赖
function InitializeSetup(): Boolean;
begin
  Result := True;
  if not IsWebView2Installed then
  begin
    if MsgBox('SmartEmailSender需要Microsoft Edge WebView2运行时。是否现在下载并安装？', mbConfirmation, MB_YESNO) = IDYES then
    begin
      // 可以在这里添加下载WebView2的代码
      MsgBox('请访问 https://developer.microsoft.com/en-us/microsoft-edge/webview2/ 下载并安装WebView2运行时。', mbInformation, MB_OK);
    end;
  end;
end;

// 安装完成后的操作
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // 创建用户配置目录
    ForceDirectories(ExpandConstant('{userappdata}\SmartEmailSender'));
    
    // 设置防火墙例外（如果需要）
    // Exec('netsh', 'advfirewall firewall add rule name="SmartEmailSender" dir=in action=allow program="' + ExpandConstant('{app}') + '\SmartEmailSender.exe"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
end;