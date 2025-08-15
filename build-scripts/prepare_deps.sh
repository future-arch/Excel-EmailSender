#!/bin/bash

# 准备QtWebEngine依赖包供轻量版下载
# 这个脚本从完整版中提取QtWebEngine组件并打包

echo "准备QtWebEngine依赖包..."

# 创建临时目录
TEMP_DIR="temp_deps"
OUTPUT_DIR="dependency_packages"
mkdir -p $TEMP_DIR
mkdir -p $OUTPUT_DIR

# 平台检测
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macos"
    ARCHIVE_EXT="tar.gz"
    COMPRESS_CMD="tar czf"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
    PLATFORM="windows"
    ARCHIVE_EXT="zip"
    COMPRESS_CMD="zip -r"
else
    PLATFORM="linux"
    ARCHIVE_EXT="tar.gz"
    COMPRESS_CMD="tar czf"
fi

echo "平台: $PLATFORM"

# 从现有的完整版安装中提取QtWebEngine
if [ -d "dist/SmartEmailSender.app" ]; then
    echo "从完整版app中提取QtWebEngine组件..."
    
    # macOS
    if [[ "$PLATFORM" == "macos" ]]; then
        # 复制QtWebEngine框架
        cp -R dist/SmartEmailSender.app/Contents/Resources/lib/python*/PySide6/Qt/lib/QtWebEngineCore.framework $TEMP_DIR/
        cp -R dist/SmartEmailSender.app/Contents/Resources/lib/python*/PySide6/Qt/lib/QtWebEngineWidgets.framework $TEMP_DIR/
        cp -R dist/SmartEmailSender.app/Contents/Resources/lib/python*/PySide6/Qt/lib/QtWebEngineQuick.framework $TEMP_DIR/ 2>/dev/null
        cp -R dist/SmartEmailSender.app/Contents/Resources/lib/python*/PySide6/Qt/lib/QtWebChannel.framework $TEMP_DIR/ 2>/dev/null
        
        # 复制相关的.so文件
        cp dist/SmartEmailSender.app/Contents/Resources/lib/python*/PySide6/QtWebEngine*.so $TEMP_DIR/ 2>/dev/null
        cp dist/SmartEmailSender.app/Contents/Resources/lib/python*/PySide6/QtWebChannel*.so $TEMP_DIR/ 2>/dev/null
    fi
    
    # 创建归档
    cd $TEMP_DIR
    ARCHIVE_NAME="qtwebengine-6.5-${PLATFORM}.${ARCHIVE_EXT}"
    echo "创建归档: $ARCHIVE_NAME"
    $COMPRESS_CMD ../$OUTPUT_DIR/$ARCHIVE_NAME *
    cd ..
    
    # 计算SHA256
    if [[ "$OSTYPE" == "darwin"* ]]; then
        SHA256=$(shasum -a 256 $OUTPUT_DIR/$ARCHIVE_NAME | cut -d' ' -f1)
    else
        SHA256=$(sha256sum $OUTPUT_DIR/$ARCHIVE_NAME | cut -d' ' -f1)
    fi
    
    # 获取文件大小
    SIZE=$(ls -l $OUTPUT_DIR/$ARCHIVE_NAME | awk '{print $5}')
    
    echo "文件: $ARCHIVE_NAME"
    echo "大小: $((SIZE / 1024 / 1024)) MB"
    echo "SHA256: $SHA256"
    
    # 生成配置信息
    cat > $OUTPUT_DIR/dep_info.json << EOF
{
  "qtwebengine": {
    "$PLATFORM": {
      "url": "$ARCHIVE_NAME",
      "size": $SIZE,
      "sha256": "$SHA256"
    }
  }
}
EOF
    
    echo "依赖包信息已保存到: $OUTPUT_DIR/dep_info.json"
    
else
    echo "错误：未找到完整版app。请先构建完整版。"
    exit 1
fi

# 清理临时目录
rm -rf $TEMP_DIR

echo ""
echo "准备完成！"
echo ""
echo "下一步："
echo "1. 将 $OUTPUT_DIR/$ARCHIVE_NAME 上传到您的CDN或GitHub Release"
echo "2. 更新 src/dependency_manager.py 中的URL和SHA256值"
echo "3. 构建轻量版: pyinstaller SmartEmailSender_lite.spec"

# 显示如何上传到GitHub Release
echo ""
echo "上传到GitHub Release示例："
echo "  gh release create v1.0-deps --title 'SmartEmailSender Dependencies v1.0' \\"
echo "    --notes 'QtWebEngine dependencies for lite version' \\"
echo "    $OUTPUT_DIR/$ARCHIVE_NAME"