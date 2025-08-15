; SmartEmailSender Advanced NSIS Installer Script
; 功能完整的Windows安装程序

!define PRODUCT_NAME "SmartEmailSender"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "SmartEmailSender"
!define PRODUCT_WEB_SITE "https://smartemailsender.com"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\SmartEmailSender.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

; 现代UI
!include "MUI2.nsh"

; 压缩器
SetCompressor /SOLID lzma

; 安装程序属性
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "releases\SmartEmailSender-Setup.exe"
InstallDir "$PROGRAMFILES\SmartEmailSender"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show

; 请求管理员权限
RequestExecutionLevel admin

; UI配置
!define MUI_ABORTWARNING
!define MUI_ICON "assets\SmartEmailSender.ico"
!define MUI_UNICON "assets\SmartEmailSender.ico"

; 欢迎页面
!insertmacro MUI_PAGE_WELCOME

; 许可协议页面
!define MUI_LICENSEPAGE_TEXT_TOP "请仔细阅读以下许可协议。您必须接受协议条款才能安装 ${PRODUCT_NAME}。"
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"

; 组件选择页面
!insertmacro MUI_PAGE_COMPONENTS

; 安装目录选择页面
!insertmacro MUI_PAGE_DIRECTORY

; 安装页面
!insertmacro MUI_PAGE_INSTFILES

; 完成页面
!define MUI_FINISHPAGE_RUN "$INSTDIR\SmartEmailSender.exe"
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\README.txt"
!insertmacro MUI_PAGE_FINISH

; 卸载页面
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; 语言
!insertmacro MUI_LANGUAGE "SimpChinese"

; 版本信息
VIProductVersion "1.0.0.0"
VIAddVersionKey /LANG=${LANG_SIMPCHINESE} "ProductName" "${PRODUCT_NAME}"
VIAddVersionKey /LANG=${LANG_SIMPCHINESE} "Comments" "智能邮件批量发送工具"
VIAddVersionKey /LANG=${LANG_SIMPCHINESE} "CompanyName" "${PRODUCT_PUBLISHER}"
VIAddVersionKey /LANG=${LANG_SIMPCHINESE} "LegalTrademarks" ""
VIAddVersionKey /LANG=${LANG_SIMPCHINESE} "LegalCopyright" "© 2024 ${PRODUCT_PUBLISHER}"
VIAddVersionKey /LANG=${LANG_SIMPCHINESE} "FileDescription" "${PRODUCT_NAME} 安装程序"
VIAddVersionKey /LANG=${LANG_SIMPCHINESE} "FileVersion" "${PRODUCT_VERSION}"
VIAddVersionKey /LANG=${LANG_SIMPCHINESE} "ProductVersion" "${PRODUCT_VERSION}"

Section "核心程序 (必需)" SEC01
  SectionIn RO
  SetOverwrite ifnewer
  SetOutPath "$INSTDIR"
  File /r "dist\SmartEmailSender\*.*"
  
  ; 注册表项
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\SmartEmailSender.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\SmartEmailSender.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
SectionEnd

Section "桌面快捷方式" SEC02
  CreateShortCut "$DESKTOP\SmartEmailSender.lnk" "$INSTDIR\SmartEmailSender.exe"
SectionEnd

Section "开始菜单快捷方式" SEC03
  CreateDirectory "$SMPROGRAMS\SmartEmailSender"
  CreateShortCut "$SMPROGRAMS\SmartEmailSender\SmartEmailSender.lnk" "$INSTDIR\SmartEmailSender.exe"
  CreateShortCut "$SMPROGRAMS\SmartEmailSender\卸载SmartEmailSender.lnk" "$INSTDIR\uninst.exe"
SectionEnd

Section "文件关联" SEC04
  WriteRegStr HKCR ".xlsx\OpenWithProgids" "SmartEmailSender.xlsx" ""
  WriteRegStr HKCR "SmartEmailSender.xlsx" "" "Excel文件"
  WriteRegStr HKCR "SmartEmailSender.xlsx\shell\open\command" "" '"$INSTDIR\SmartEmailSender.exe" "%1"'
SectionEnd

Section -AdditionalIcons
  WriteIniStr "$INSTDIR\${PRODUCT_NAME}.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
  CreateShortCut "$SMPROGRAMS\SmartEmailSender\访问官网.lnk" "$INSTDIR\${PRODUCT_NAME}.url"
  CreateShortCut "$SMPROGRAMS\SmartEmailSender\卸载SmartEmailSender.lnk" "$INSTDIR\uninst.exe"
SectionEnd

Section -Post
  WriteUninstaller "$INSTDIR\uninst.exe"
SectionEnd

; 组件描述
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC01} "安装SmartEmailSender核心程序文件"
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC02} "在桌面创建SmartEmailSender快捷方式"
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC03} "在开始菜单创建SmartEmailSender程序组"
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC04} "将Excel文件与SmartEmailSender关联"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; 卸载程序
Section Uninstall
  Delete "$INSTDIR\${PRODUCT_NAME}.url"
  Delete "$INSTDIR\uninst.exe"
  Delete "$INSTDIR\SmartEmailSender.exe"
  
  ; 删除所有文件
  RMDir /r "$INSTDIR"
  
  ; 删除快捷方式
  Delete "$SMPROGRAMS\SmartEmailSender\*.*"
  RMDir "$SMPROGRAMS\SmartEmailSender"
  Delete "$DESKTOP\SmartEmailSender.lnk"
  
  ; 删除注册表项
  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  
  ; 删除文件关联
  DeleteRegKey HKCR ".xlsx\OpenWithProgids" "SmartEmailSender.xlsx"
  DeleteRegKey HKCR "SmartEmailSender.xlsx"
  
  SetAutoClose true
SectionEnd