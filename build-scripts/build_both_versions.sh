#!/bin/bash

echo "=========================================="
echo "SmartEmailSender 双版本构建脚本"
echo "=========================================="
echo ""

# 安全检查 - 备份敏感文件
echo "🔒 备份敏感文件..."
mkdir -p .sensitive_backup
mv src/token_cache.json .sensitive_backup/ 2>/dev/null || true
mv .env .sensitive_backup/ 2>/dev/null || true
echo "✅ 敏感文件已备份到 .sensitive_backup/"

# 清理旧的构建
echo "清理旧的构建文件..."
rm -rf build dist

# 1. 构建完整版
echo ""
echo "1. 构建完整版（包含所有组件）..."
echo "=========================================="
pyinstaller SmartEmailSender.spec --clean --noconfirm

if [ -d "dist/SmartEmailSender.app" ]; then
    FULL_SIZE=$(du -sh dist/SmartEmailSender.app | cut -f1)
    echo "✅ 完整版构建成功: $FULL_SIZE"
    
    # 创建完整版ZIP
    cd dist
    zip -r -q SmartEmailSender-Full-macOS.zip SmartEmailSender.app
    cd ..
    echo "✅ 完整版ZIP已创建"
else
    echo "❌ 完整版构建失败"
    exit 1
fi

# 2. 准备依赖包（从完整版提取）
echo ""
echo "2. 准备依赖包..."
echo "=========================================="
chmod +x prepare_deps.sh
./prepare_deps.sh

# 3. 构建轻量版
echo ""
echo "3. 构建轻量版（不含QtWebEngine）..."
echo "=========================================="

# 备份并清理
mv dist dist_full
rm -rf build

# 构建轻量版
pyinstaller SmartEmailSender_lite.spec --clean --noconfirm

if [ -d "dist/SmartEmailSender_Lite.app" ]; then
    LITE_SIZE=$(du -sh dist/SmartEmailSender_Lite.app | cut -f1)
    echo "✅ 轻量版构建成功: $LITE_SIZE"
    
    # 创建轻量版ZIP
    cd dist
    zip -r -q SmartEmailSender-Lite-macOS.zip SmartEmailSender_Lite.app
    cd ..
    echo "✅ 轻量版ZIP已创建"
else
    echo "❌ 轻量版构建失败"
fi

# 4. 整理输出文件
echo ""
echo "4. 整理输出文件..."
echo "=========================================="

# 创建发布目录
mkdir -p releases
mv dist_full/SmartEmailSender-Full-macOS.zip releases/ 2>/dev/null
mv dist/SmartEmailSender-Lite-macOS.zip releases/ 2>/dev/null
cp dependency_packages/*.tar.gz releases/ 2>/dev/null
cp dependency_packages/*.zip releases/ 2>/dev/null

# 5. 生成版本对比报告
echo ""
echo "=========================================="
echo "构建完成！版本对比："
echo "=========================================="
echo ""

if [ -f "releases/SmartEmailSender-Full-macOS.zip" ]; then
    FULL_ZIP_SIZE=$(ls -lh releases/SmartEmailSender-Full-macOS.zip | awk '{print $5}')
    echo "📦 完整版:"
    echo "   - 应用大小: $FULL_SIZE"
    echo "   - ZIP大小: $FULL_ZIP_SIZE"
    echo "   - 特点: 包含所有组件，开箱即用"
fi

if [ -f "releases/SmartEmailSender-Lite-macOS.zip" ]; then
    LITE_ZIP_SIZE=$(ls -lh releases/SmartEmailSender-Lite-macOS.zip | awk '{print $5}')
    echo ""
    echo "📦 轻量版:"
    echo "   - 应用大小: $LITE_SIZE"
    echo "   - ZIP大小: $LITE_ZIP_SIZE"
    echo "   - 特点: 首次运行需下载QtWebEngine（约580MB）"
fi

if [ -d "dependency_packages" ]; then
    echo ""
    echo "📦 依赖包:"
    ls -lh dependency_packages/*.* 2>/dev/null | awk '{print "   - " $9 ": " $5}'
fi

echo ""
echo "=========================================="
# 6. 最终安全检查
echo ""
echo "6. 执行安全检查..."
echo "=========================================="
./security_check.sh

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 构建完成并通过安全检查！"
else
    echo ""
    echo "❌ 安全检查失败，请检查并清理敏感文件"
    exit 1
fi

# 恢复敏感文件
echo ""
echo "🔄 恢复敏感文件..."
mv .sensitive_backup/token_cache.json src/ 2>/dev/null || true
mv .sensitive_backup/.env . 2>/dev/null || true
rmdir .sensitive_backup 2>/dev/null || true
echo "✅ 敏感文件已恢复"

echo ""
echo "发布文件位于 releases/ 目录"
echo ""
echo "发布说明模板："
echo "----------------------------------------"
echo "## SmartEmailSender v1.0.0"
echo ""
echo "提供两个版本供选择："
echo ""
echo "### 🎯 完整版 (推荐)"
echo "- 文件：SmartEmailSender-Full-macOS.zip"
echo "- 大小：约1.3GB（压缩后约500MB）"
echo "- 特点：包含所有必要组件，下载后即可使用"
echo "- 适合：网络不稳定或需要离线安装的用户"
echo ""
echo "### 🚀 轻量版"
echo "- 文件：SmartEmailSender-Lite-macOS.zip"  
echo "- 大小：约50MB"
echo "- 特点：首次运行时需要下载额外组件（约580MB）"
echo "- 适合：想要更小下载体积的用户"
echo ""
echo "### 安装说明"
echo "1. 下载对应版本的ZIP文件"
echo "2. 解压到Applications文件夹"
echo "3. 首次运行时可能需要在系统偏好设置中允许运行"
echo "----------------------------------------"