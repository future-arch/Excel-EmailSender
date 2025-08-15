@echo off
setlocal enabledelayedexpansion

REM SmartEmailSender Windows自解压构建器
REM 这个脚本会自动设置环境、安装依赖并构建Windows版本

echo.
echo ====================================================
echo   SmartEmailSender Windows 自动构建器 v1.0
echo ====================================================
echo.
echo 这个工具将自动为您：
echo ✅ 检查和安装Python环境
echo ✅ 安装所有必要的依赖
echo ✅ 构建Windows版本的SmartEmailSender  
echo ✅ 创建安装程序（如果有NSIS/Inno Setup）
echo ✅ 运行安全检查
echo.
pause

REM 1. 环境检查
echo.
echo 🔍 第1步：检查系统环境
echo ====================================================

REM 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未检测到Python，正在尝试安装...
    echo.
    echo 📥 正在下载Python 3.11...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe' -OutFile 'python-installer.exe'}"
    
    if exist python-installer.exe (
        echo 🔧 正在安装Python...
        python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
        echo ✅ Python安装完成，请重新运行此脚本
        del python-installer.exe
        pause
        exit /b 0
    ) else (
        echo ❌ Python下载失败，请手动安装Python 3.11+
        echo 下载地址：https://www.python.org/downloads/
        pause
        exit /b 1
    )
) else (
    for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
    echo ✅ 检测到Python版本：!PYTHON_VERSION!
)

REM 检查pip
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip未正确安装，正在修复...
    python -m ensurepip --default-pip
    python -m pip install --upgrade pip
) else (
    echo ✅ pip可用
)

REM 2. 依赖安装
echo.
echo 📦 第2步：安装依赖包
echo ====================================================

echo 正在安装基础依赖...
pip install --upgrade pip setuptools wheel

echo 正在安装PyInstaller...
pip install pyinstaller

echo 正在安装应用依赖...
if exist requirements.txt (
    pip install -r requirements.txt
) else (
    echo 正在安装核心依赖...
    pip install PySide6 pandas msal jinja2 requests python-dotenv openpyxl pillow pywin32
)

REM 验证关键依赖
echo.
echo 🧪 验证依赖安装...
python -c "try: import PySide6; print('✅ PySide6 OK'); import pandas; print('✅ pandas OK'); import msal; print('✅ msal OK'); import jinja2; print('✅ jinja2 OK'); import openpyxl; print('✅ openpyxl OK'); import requests; print('✅ requests OK'); print('✅ 所有依赖验证通过'); except ImportError as e: print('❌ 依赖验证失败:', e); exit(1)" || (
    echo ❌ 依赖安装失败，请检查网络连接
    pause
    exit /b 1
)

REM 3. 准备构建
echo.
echo 🔧 第3步：准备构建环境
echo ====================================================

REM 安全备份
echo 正在备份敏感文件...
if not exist .sensitive_backup mkdir .sensitive_backup

if exist src\token_cache.json (
    move src\token_cache.json .sensitive_backup\
    echo ✅ token_cache.json 已备份
)

if exist .env (
    move .env .sensitive_backup\
    echo ✅ .env 已备份
)

if exist settings.json (
    copy settings.json .sensitive_backup\settings.json.backup
    echo ✅ settings.json 已备份
)

REM 清理旧构建
echo 正在清理旧构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist releases rmdir /s /q releases
mkdir releases
echo ✅ 构建环境已准备

REM 4. 开始构建
echo.
echo 🚀 第4步：构建Windows应用程序
echo ====================================================

echo 开始PyInstaller构建...
set start_time=%time%

pyinstaller SmartEmailSender_windows.spec --clean --noconfirm

set build_exit_code=%errorlevel%

if %build_exit_code% equ 0 (
    echo ✅ PyInstaller构建成功！
) else (
    echo ❌ 构建失败，退出码：%build_exit_code%
    
    if exist build\SmartEmailSender\warn-SmartEmailSender.txt (
        echo.
        echo 📋 构建警告信息：
        type build\SmartEmailSender\warn-SmartEmailSender.txt
    )
    
    echo.
    echo 🔧 可能的解决方案：
    echo - 检查是否有杀毒软件干扰
    echo - 确保有足够的磁盘空间（至少2GB）
    echo - 重新运行此脚本
    pause
    exit /b 1
)

REM 5. 验证构建结果
echo.
echo 📊 第5步：验证构建结果
echo ====================================================

if exist dist\SmartEmailSender (
    for /f %%i in ('powershell "(Get-ChildItem -Recurse 'dist\SmartEmailSender' | Measure-Object -Sum Length).Sum / 1MB"') do set app_size_mb=%%i
    echo ✅ 应用程序构建完成：!app_size_mb! MB
    
    if exist dist\SmartEmailSender\SmartEmailSender.exe (
        echo ✅ 主执行文件存在
    ) else (
        echo ❌ 警告：主执行文件缺失
    )
    
    for /f %%i in ('dir /s /b dist\SmartEmailSender\* ^| find /c /v ""') do set file_count=%%i
    echo ✅ 应用程序包含 !file_count! 个文件
    
) else (
    echo ❌ 构建输出目录不存在
    pause
    exit /b 1
)

REM 6. 创建分发包
echo.
echo 📦 第6步：创建分发包
echo ====================================================

echo 正在创建ZIP压缩包...
cd dist
powershell "Compress-Archive -Path 'SmartEmailSender' -DestinationPath '../releases/SmartEmailSender-Windows.zip' -Force"

if %errorlevel% equ 0 (
    cd ..
    for /f %%i in ('powershell "(Get-Item 'releases/SmartEmailSender-Windows.zip').Length / 1MB"') do set zip_size_mb=%%i
    echo ✅ ZIP包创建成功：!zip_size_mb! MB
) else (
    cd ..
    echo ❌ ZIP包创建失败
)

REM 7. 创建安装程序（如果可用）
echo.
echo 🔧 第7步：创建安装程序（可选）
echo ====================================================

REM 检查NSIS
where makensis >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 检测到NSIS，正在创建安装程序...
    makensis SmartEmailSender_advanced.nsi
    if exist releases\SmartEmailSender-Setup.exe (
        for /f %%i in ('powershell "(Get-Item 'releases/SmartEmailSender-Setup.exe').Length / 1MB"') do set nsis_size_mb=%%i
        echo ✅ NSIS安装程序创建成功：!nsis_size_mb! MB
    )
) else (
    echo ⚠️  未检测到NSIS（可选）
)

REM 检查Inno Setup
where iscc >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 检测到Inno Setup，正在创建安装程序...
    iscc SmartEmailSender.iss
    if exist releases\SmartEmailSender-Setup-InnoSetup.exe (
        for /f %%i in ('powershell "(Get-Item 'releases/SmartEmailSender-Setup-InnoSetup.exe').Length / 1MB"') do set inno_size_mb=%%i
        echo ✅ Inno Setup安装程序创建成功：!inno_size_mb! MB
    )
) else (
    echo ⚠️  未检测到Inno Setup（可选）
)

REM 8. 运行安全检查
echo.
echo 🔒 第8步：安全检查
echo ====================================================

echo 正在验证构建包安全性...

REM 简化的安全检查（内嵌版本）
set "FOUND_SENSITIVE=false"
set "SENSITIVE_PATTERNS=token_cache.json .env credentials secrets private_key api_key auth_token password"

for %%p in (!SENSITIVE_PATTERNS!) do (
    if exist "dist\SmartEmailSender\%%p" (
        echo ⚠️  发现敏感文件：%%p
        set "FOUND_SENSITIVE=true"
    )
)

REM 检查ZIP包
if exist releases\SmartEmailSender-Windows.zip (
    for %%p in (!SENSITIVE_PATTERNS!) do (
        powershell -Command "if (Select-String -Path 'releases\SmartEmailSender-Windows.zip' -Pattern '%%p' -Quiet) { exit 1 }" >nul 2>&1
        if !errorlevel! equ 1 (
            echo ⚠️  ZIP包中发现敏感文件模式：%%p
            set "FOUND_SENSITIVE=true"
        )
    )
)

if "!FOUND_SENSITIVE!"=="false" (
    echo ✅ 安全检查通过
) else (
    echo ❌ 安全检查发现问题，但构建仍然可用
    echo 注意：请确保不要将敏感文件分发给其他用户
)

REM 9. 生成使用说明
echo.
echo 📋 第9步：生成使用说明
echo ====================================================

echo 正在创建README文件...

(
echo SmartEmailSender v1.0.0 - Windows版本
echo =====================================
echo.
echo 构建完成时间：%date% %time%
echo 构建环境：Windows %OS%
echo Python版本：!PYTHON_VERSION!
echo.
echo 📁 发布文件说明：
echo.
if exist releases\SmartEmailSender-Windows.zip echo ✅ SmartEmailSender-Windows.zip - 绿色版本（解压即用）
if exist releases\SmartEmailSender-Setup.exe echo ✅ SmartEmailSender-Setup.exe - NSIS安装程序
if exist releases\SmartEmailSender-Setup-InnoSetup.exe echo ✅ SmartEmailSender-Setup-InnoSetup.exe - Inno Setup安装程序
echo.
echo 🚀 使用方法：
echo.
echo 方法1：绿色版本
echo 1. 解压 SmartEmailSender-Windows.zip
echo 2. 运行 SmartEmailSender\SmartEmailSender.exe
echo.
echo 方法2：安装程序
echo 1. 运行任一安装程序
echo 2. 按照向导完成安装
echo 3. 从开始菜单启动应用
echo.
echo 💡 首次使用：
echo 1. 启动应用会提示Microsoft 365登录
echo 2. 使用工作或学校账户登录
echo 3. 授权必要的邮件权限
echo 4. 准备Excel数据文件开始使用
echo.
echo ⚠️  系统要求：
echo - Windows 10 或更高版本
echo - Microsoft Edge ^(WebView2支持^)
echo - 网络连接用于认证
echo.
echo 🆘 技术支持：
echo 如有问题，请联系开发者或查看日志文件
echo.
echo ✨ 感谢使用SmartEmailSender！
) > releases\README.txt

echo ✅ README文件已创建

REM 10. 恢复文件和完成
echo.
echo 🔄 第10步：清理和完成
echo ====================================================

echo 正在恢复备份文件...

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

REM 最终报告
echo.
echo 🎉 构建完成！
echo ====================================================
echo.
echo 📊 构建统计：
echo - 构建用时：从 %start_time% 到 %time%
if defined app_size_mb echo - 应用大小：!app_size_mb! MB
if defined zip_size_mb echo - ZIP包大小：!zip_size_mb! MB
if defined nsis_size_mb echo - NSIS安装程序：!nsis_size_mb! MB  
if defined inno_size_mb echo - Inno安装程序：!inno_size_mb! MB

echo.
echo 📂 发布文件位于 releases\ 文件夹：
dir releases\ /b

echo.
echo 🚀 下一步操作：
echo 1. 测试运行 dist\SmartEmailSender\SmartEmailSender.exe
echo 2. 验证所有功能正常工作
echo 3. 使用 releases\ 中的文件进行分发
echo.
echo ✨ SmartEmailSender Windows版本构建完成！
echo 感谢您的使用！

echo.
echo 按任意键测试运行应用程序...
pause >nul

if exist dist\SmartEmailSender\SmartEmailSender.exe (
    echo 🚀 正在启动SmartEmailSender进行测试...
    start "" "dist\SmartEmailSender\SmartEmailSender.exe"
    echo.
    echo ✅ 应用程序已启动，请检查功能是否正常
) else (
    echo ❌ 无法找到可执行文件进行测试
)

echo.
echo 构建器执行完成！按任意键退出...
pause >nul