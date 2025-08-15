#!/bin/bash

echo "=========================================="
echo "SmartEmailSender 最终版本构建脚本"
echo "=========================================="
echo ""

# 1. 安全检查 - 备份敏感文件
echo "🔒 安全检查和文件备份..."
mkdir -p .sensitive_backup

# 备份敏感文件
if [ -f "src/token_cache.json" ]; then
    mv src/token_cache.json .sensitive_backup/
    echo "✅ token_cache.json 已备份"
fi

if [ -f ".env" ]; then
    mv .env .sensitive_backup/
    echo "✅ .env 已备份"
fi

# 备份用户设置（避免覆盖）
if [ -f "settings.json" ]; then
    cp settings.json .sensitive_backup/settings.json.backup
    echo "✅ 用户settings.json已备份"
fi

echo ""

# 2. 环境检查
echo "🔍 检查构建环境..."
echo "Python版本: $(python --version)"
echo "PyInstaller版本: $(pyinstaller --version)"
echo ""

# 检查关键依赖
python -c "
try:
    import PySide6; print('✅ PySide6:', PySide6.__version__)
    import pandas; print('✅ pandas:', pandas.__version__)
    import msal; print('✅ msal:', msal.__version__)
    import jinja2; print('✅ jinja2:', jinja2.__version__)
    import openpyxl; print('✅ openpyxl:', openpyxl.__version__)
    import requests; print('✅ requests:', requests.__version__)
    print('✅ 所有依赖检查通过')
except ImportError as e:
    print('❌ 依赖检查失败:', e)
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ 依赖检查失败，请安装缺失的依赖"
    exit 1
fi

echo ""

# 3. 清理旧构建
echo "🧹 清理旧构建文件..."
rm -rf build dist
rm -rf releases
mkdir -p releases
echo "✅ 清理完成"
echo ""

# 4. 开始构建
echo "🚀 开始构建最终版本..."
echo "=========================================="

start_time=$(date +%s)

pyinstaller SmartEmailSender_final.spec --clean --noconfirm

build_exit_code=$?
end_time=$(date +%s)
build_time=$((end_time - start_time))

if [ $build_exit_code -eq 0 ]; then
    echo ""
    echo "✅ 构建成功！用时: ${build_time}秒"
else
    echo ""
    echo "❌ 构建失败！退出码: $build_exit_code"
    
    # 显示错误日志
    if [ -f "build/SmartEmailSender/warn-SmartEmailSender.txt" ]; then
        echo ""
        echo "构建警告:"
        tail -20 "build/SmartEmailSender/warn-SmartEmailSender.txt"
    fi
    
    exit 1
fi

# 5. 检查构建结果
echo ""
echo "📊 构建结果分析..."
echo "=========================================="

if [ -d "dist/SmartEmailSender.app" ]; then
    APP_SIZE=$(du -sh dist/SmartEmailSender.app | cut -f1)
    echo "✅ macOS应用包: SmartEmailSender.app ($APP_SIZE)"
    
    # 检查应用结构
    if [ -f "dist/SmartEmailSender.app/Contents/MacOS/SmartEmailSender" ]; then
        echo "✅ 可执行文件存在"
    else
        echo "❌ 可执行文件缺失"
    fi
    
    if [ -d "dist/SmartEmailSender.app/Contents/Resources" ]; then
        RESOURCES_COUNT=$(find dist/SmartEmailSender.app/Contents/Resources -type f | wc -l)
        echo "✅ 资源文件: $RESOURCES_COUNT 个"
    fi
    
elif [ -d "dist/SmartEmailSender" ]; then
    APP_SIZE=$(du -sh dist/SmartEmailSender | cut -f1)
    echo "✅ 应用程序文件夹: SmartEmailSender ($APP_SIZE)"
else
    echo "❌ 未找到构建输出"
    exit 1
fi

# 6. 安全检查
echo ""
echo "🔒 执行安全检查..."
./security_check.sh

if [ $? -ne 0 ]; then
    echo "❌ 安全检查失败！"
    exit 1
fi

# 7. 创建发布包
echo ""
echo "📦 创建发布包..."

cd dist

if [ -d "SmartEmailSender.app" ]; then
    # macOS DMG创建（如果有create-dmg工具）
    if command -v create-dmg >/dev/null 2>&1; then
        echo "创建DMG镜像..."
        create-dmg \
            --volname "SmartEmailSender" \
            --window-pos 200 120 \
            --window-size 600 400 \
            --icon-size 100 \
            --icon "SmartEmailSender.app" 175 190 \
            --hide-extension "SmartEmailSender.app" \
            --app-drop-link 425 190 \
            "../releases/SmartEmailSender-macOS.dmg" \
            "SmartEmailSender.app" 2>/dev/null
            
        if [ $? -eq 0 ]; then
            DMG_SIZE=$(du -sh ../releases/SmartEmailSender-macOS.dmg | cut -f1)
            echo "✅ DMG镜像已创建: SmartEmailSender-macOS.dmg ($DMG_SIZE)"
        fi
    fi
    
    # 创建ZIP包
    echo "创建ZIP压缩包..."
    zip -r -q ../releases/SmartEmailSender-macOS.zip SmartEmailSender.app
    ZIP_SIZE=$(du -sh ../releases/SmartEmailSender-macOS.zip | cut -f1)
    echo "✅ ZIP包已创建: SmartEmailSender-macOS.zip ($ZIP_SIZE)"
    
else
    # Windows/Linux
    zip -r -q ../releases/SmartEmailSender.zip SmartEmailSender
    ZIP_SIZE=$(du -sh ../releases/SmartEmailSender.zip | cut -f1)
    echo "✅ ZIP包已创建: SmartEmailSender.zip ($ZIP_SIZE)"
fi

cd ..

# 8. 生成检查和信息文件
echo ""
echo "📋 生成发布信息..."

# 创建README
cat > releases/README.txt << EOF
SmartEmailSender v1.0.0 - 智能邮件批量发送工具
===============================================

构建日期: $(date '+%Y-%m-%d %H:%M:%S')
构建版本: 1.0.0

系统要求:
- macOS 10.15 (Catalina) 或更高版本
- 需要网络连接进行Microsoft 365认证

安装说明:
1. 解压ZIP文件或打开DMG镜像
2. 将SmartEmailSender.app拖拽到Applications文件夹
3. 首次运行时，系统可能提示安全警告：
   - 打开"系统偏好设置" > "安全性与隐私"
   - 点击"仍要打开"允许应用运行

首次使用:
1. 启动应用后会提示Microsoft 365登录
2. 使用您的工作或学校账户登录
3. 授权必要的邮件发送权限

功能特点:
✅ Excel数据批量导入
✅ Microsoft 365群组支持  
✅ HTML邮件模板编辑
✅ 个性化附件支持
✅ 多种发送模式
✅ 自动更新检查

技术支持:
如有问题，请提供以下信息：
- 操作系统版本
- 应用版本 (1.0.0)
- 错误描述或截图

构建信息:
- 构建时间: ${build_time}秒
- 应用大小: $APP_SIZE
- Python版本: $(python --version)
- 包含组件: Qt WebEngine, pandas, MSAL
EOF

# 9. 恢复敏感文件
echo ""
echo "🔄 恢复备份文件..."

if [ -f ".sensitive_backup/token_cache.json" ]; then
    mv .sensitive_backup/token_cache.json src/
    echo "✅ token_cache.json 已恢复"
fi

if [ -f ".sensitive_backup/.env" ]; then
    mv .sensitive_backup/.env ./
    echo "✅ .env 已恢复" 
fi

if [ -f ".sensitive_backup/settings.json.backup" ]; then
    # 如果用户没有自定义设置，恢复备份
    if [ ! -f "settings.json" ] || [ ! -s "settings.json" ]; then
        mv .sensitive_backup/settings.json.backup settings.json
        echo "✅ settings.json 已恢复"
    else
        rm .sensitive_backup/settings.json.backup
    fi
fi

rmdir .sensitive_backup 2>/dev/null || true

# 10. 最终报告
echo ""
echo "🎉 构建完成！"
echo "=========================================="
echo "发布文件位于: releases/"
echo ""
ls -lh releases/
echo ""
echo "下一步:"
echo "1. 测试应用功能"
echo "2. 上传到发布渠道"
echo "3. 更新官网下载链接"
echo ""
echo "构建统计:"
echo "- 总用时: ${build_time}秒"
echo "- 应用大小: $APP_SIZE"
echo "- 发布包数量: $(ls releases/ | wc -l)"
echo ""
echo "✨ 准备发布！"