#!/bin/bash

echo "=========================================="
echo "SmartEmailSender 跨平台构建脚本"
echo "=========================================="
echo ""

# 检测操作系统
OS="Unknown"
case "$(uname -s)" in
    Linux*)     OS=Linux;;
    Darwin*)    OS=Mac;;
    CYGWIN*)    OS=Cygwin;;
    MINGW*)     OS=Windows;;
    *)          OS="Unknown:$(uname -s)";;
esac

echo "🖥️  检测到操作系统: $OS"

# 根据系统选择相应的构建
case $OS in
    Mac)
        echo "🍎 开始macOS构建..."
        if [ -f "build_final.sh" ]; then
            chmod +x build_final.sh
            ./build_final.sh
        else
            echo "❌ 未找到macOS构建脚本"
        fi
        ;;
    
    Linux)
        echo "🐧 开始Linux构建..."
        # Linux构建逻辑
        echo "🚧 Linux构建功能正在开发中..."
        
        # 安全检查 - 备份敏感文件
        echo "🔒 安全检查和文件备份..."
        mkdir -p .sensitive_backup
        mv src/token_cache.json .sensitive_backup/ 2>/dev/null || true
        mv .env .sensitive_backup/ 2>/dev/null || true
        
        # 清理旧构建
        rm -rf build dist releases
        mkdir -p releases
        
        # 构建Linux版本
        pyinstaller SmartEmailSender_final.spec --clean --noconfirm
        
        if [ -d "dist/SmartEmailSender" ]; then
            cd dist
            tar -czf ../releases/SmartEmailSender-Linux.tar.gz SmartEmailSender
            cd ..
            echo "✅ Linux版本构建完成"
        fi
        
        # 恢复敏感文件
        mv .sensitive_backup/token_cache.json src/ 2>/dev/null || true
        mv .sensitive_backup/.env . 2>/dev/null || true
        rmdir .sensitive_backup 2>/dev/null || true
        ;;
        
    Windows|Cygwin)
        echo "🪟 检测到Windows环境..."
        if [ -f "build_windows.bat" ]; then
            echo "请在Windows命令提示符中运行: build_windows.bat"
            echo "或者在Git Bash中运行Windows构建"
        else
            echo "❌ 未找到Windows构建脚本"
        fi
        ;;
        
    *)
        echo "❌ 不支持的操作系统: $OS"
        exit 1
        ;;
esac

echo ""
echo "✨ 跨平台构建脚本执行完成！"