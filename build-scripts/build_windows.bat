@echo off
echo ==========================================
echo SmartEmailSender Windows构建脚本
echo ==========================================
echo.

REM 1. 安全检查 - 备份敏感文件
echo 🔒 安全检查和文件备份...
if not exist .sensitive_backup mkdir .sensitive_backup

REM 备份敏感文件
if exist src\token_cache.json (
    move src\token_cache.json .sensitive_backup\
    echo ✅ token_cache.json 已备份
)

if exist .env (
    move .env .sensitive_backup\
    echo ✅ .env 已备份
)

REM 备份用户设置（避免覆盖）
if exist settings.json (
    copy settings.json .sensitive_backup\settings.json.backup
    echo ✅ 用户settings.json已备份
)

echo.

REM 2. 环境检查
echo 🔍 检查构建环境...
python --version
pyinstaller --version
echo.

REM 检查关键依赖
python -c "try: import PySide6; print('✅ PySide6:', PySide6.__version__); import pandas; print('✅ pandas:', pandas.__version__); import msal; print('✅ msal:', msal.__version__); import jinja2; print('✅ jinja2:', jinja2.__version__); import openpyxl; print('✅ openpyxl:', openpyxl.__version__); import requests; print('✅ requests:', requests.__version__); print('✅ 所有依赖检查通过'); except ImportError as e: print('❌ 依赖检查失败:', e); exit(1)"

if %errorlevel% neq 0 (
    echo ❌ 依赖检查失败，请安装缺失的依赖
    pause
    exit /b 1
)

echo.

REM 3. 清理旧构建
echo 🧹 清理旧构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist releases rmdir /s /q releases
mkdir releases
echo ✅ 清理完成
echo.

REM 4. 开始构建
echo 🚀 开始构建Windows版本...
echo ==========================================

set start_time=%time%

pyinstaller SmartEmailSender_windows.spec --clean --noconfirm

set build_exit_code=%errorlevel%

if %build_exit_code% equ 0 (
    echo.
    echo ✅ 构建成功！
) else (
    echo.
    echo ❌ 构建失败！退出码: %build_exit_code%
    
    REM 显示错误日志
    if exist build\SmartEmailSender\warn-SmartEmailSender.txt (
        echo.
        echo 构建警告:
        type build\SmartEmailSender\warn-SmartEmailSender.txt
    )
    
    pause
    exit /b 1
)

REM 5. 检查构建结果
echo.
echo 📊 构建结果分析...
echo ==========================================

if exist dist\SmartEmailSender (
    for /f %%i in ('powershell "(Get-ChildItem -Recurse 'dist\SmartEmailSender' | Measure-Object -Sum Length).Sum / 1MB"') do set app_size_mb=%%i
    echo ✅ Windows应用程序: SmartEmailSender (!app_size_mb! MB)
    
    REM 检查应用结构
    if exist dist\SmartEmailSender\SmartEmailSender.exe (
        echo ✅ 可执行文件存在
    ) else (
        echo ❌ 可执行文件缺失
    )
    
    REM 统计文件数量
    for /f %%i in ('dir /s /b dist\SmartEmailSender\* ^| find /c /v ""') do set file_count=%%i
    echo ✅ 应用文件总数: !file_count! 个
    
) else (
    echo ❌ 未找到构建输出
    pause
    exit /b 1
)

REM 6. 创建发布包
echo.
echo 📦 创建发布包...

cd dist
powershell "Compress-Archive -Path 'SmartEmailSender' -DestinationPath '../releases/SmartEmailSender-Windows.zip' -Force"

if %errorlevel% equ 0 (
    for /f %%i in ('powershell "(Get-Item '../releases/SmartEmailSender-Windows.zip').Length / 1MB"') do set zip_size_mb=%%i
    echo ✅ Windows ZIP包已创建: SmartEmailSender-Windows.zip (!zip_size_mb! MB)
) else (
    echo ❌ ZIP包创建失败
)

cd ..

REM 7. 创建安装程序脚本 (NSIS)
echo.
echo 📦 创建NSIS安装程序脚本...

echo ; SmartEmailSender NSIS安装脚本 > SmartEmailSender_installer.nsi
echo !define PRODUCT_NAME "SmartEmailSender" >> SmartEmailSender_installer.nsi
echo !define PRODUCT_VERSION "1.0.0" >> SmartEmailSender_installer.nsi
echo !define PRODUCT_PUBLISHER "SmartEmailSender" >> SmartEmailSender_installer.nsi
echo !define PRODUCT_WEB_SITE "https://smartemailsender.com" >> SmartEmailSender_installer.nsi
echo !define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\SmartEmailSender.exe" >> SmartEmailSender_installer.nsi
echo !define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" >> SmartEmailSender_installer.nsi
echo. >> SmartEmailSender_installer.nsi
echo SetCompressor lzma >> SmartEmailSender_installer.nsi
echo. >> SmartEmailSender_installer.nsi
echo Name "${PRODUCT_NAME} ${PRODUCT_VERSION}" >> SmartEmailSender_installer.nsi
echo OutFile "releases\SmartEmailSender-Setup.exe" >> SmartEmailSender_installer.nsi
echo InstallDir "$PROGRAMFILES\SmartEmailSender" >> SmartEmailSender_installer.nsi
echo ShowInstDetails show >> SmartEmailSender_installer.nsi
echo ShowUnInstDetails show >> SmartEmailSender_installer.nsi
echo. >> SmartEmailSender_installer.nsi
echo Section "MainSection" SEC01 >> SmartEmailSender_installer.nsi
echo   SetOverwrite ifnewer >> SmartEmailSender_installer.nsi
echo   SetOutPath "$INSTDIR" >> SmartEmailSender_installer.nsi
echo   File /r "dist\SmartEmailSender\*.*" >> SmartEmailSender_installer.nsi
echo   CreateDirectory "$SMPROGRAMS\SmartEmailSender" >> SmartEmailSender_installer.nsi
echo   CreateShortCut "$SMPROGRAMS\SmartEmailSender\SmartEmailSender.lnk" "$INSTDIR\SmartEmailSender.exe" >> SmartEmailSender_installer.nsi
echo   CreateShortCut "$DESKTOP\SmartEmailSender.lnk" "$INSTDIR\SmartEmailSender.exe" >> SmartEmailSender_installer.nsi
echo SectionEnd >> SmartEmailSender_installer.nsi
echo. >> SmartEmailSender_installer.nsi
echo ✅ NSIS脚本已创建

REM 8. 生成README
echo.
echo 📋 生成发布信息...

echo SmartEmailSender v1.0.0 - Windows版智能邮件批量发送工具 > releases\README.txt
echo =============================================== >> releases\README.txt
echo. >> releases\README.txt
echo 构建日期: %date% %time% >> releases\README.txt
echo 构建版本: 1.0.0 >> releases\README.txt
echo. >> releases\README.txt
echo 系统要求: >> releases\README.txt
echo - Windows 10 或更高版本 >> releases\README.txt
echo - 需要网络连接进行Microsoft 365认证 >> releases\README.txt
echo. >> releases\README.txt
echo 安装说明: >> releases\README.txt
echo 1. 下载SmartEmailSender-Windows.zip >> releases\README.txt
echo 2. 解压到任意目录 >> releases\README.txt
echo 3. 运行SmartEmailSender.exe >> releases\README.txt
echo 4. 或者使用SmartEmailSender-Setup.exe安装程序 >> releases\README.txt
echo. >> releases\README.txt
echo 首次使用: >> releases\README.txt
echo 1. 启动应用后会提示Microsoft 365登录 >> releases\README.txt
echo 2. 使用您的工作或学校账户登录 >> releases\README.txt
echo 3. 授权必要的邮件发送权限 >> releases\README.txt
echo. >> releases\README.txt

REM 9. 恢复敏感文件
echo.
echo 🔄 恢复备份文件...

if exist .sensitive_backup\token_cache.json (
    move .sensitive_backup\token_cache.json src\
    echo ✅ token_cache.json 已恢复
)

if exist .sensitive_backup\.env (
    move .sensitive_backup\.env .\
    echo ✅ .env 已恢复
)

if exist .sensitive_backup\settings.json.backup (
    if not exist settings.json (
        move .sensitive_backup\settings.json.backup settings.json
        echo ✅ settings.json 已恢复
    ) else (
        del .sensitive_backup\settings.json.backup
    )
)

rmdir .sensitive_backup 2>nul

REM 10. 最终报告
echo.
echo 🎉 Windows构建完成！
echo ==========================================
echo 发布文件位于: releases\
echo.
dir releases\
echo.
echo 下一步:
echo 1. 测试Windows应用功能
echo 2. 使用NSIS编译安装程序 (如果已安装NSIS)
echo 3. 上传到发布渠道
echo.
echo ✨ 准备发布Windows版本！

pause