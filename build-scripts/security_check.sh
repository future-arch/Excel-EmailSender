#!/bin/bash

echo "🔒 安全检查 - 验证打包文件中是否包含敏感信息"
echo "================================================="

# 定义敏感文件模式
SENSITIVE_FILES=(
    "token_cache.json"
    "settings.json" 
    ".env"
    ".secrets"
    "credentials"
    "private_key"
    "api_key"
    "auth_token"
    "password"
    "secret"
)

# 检查dist目录中的应用
APP_PATHS=(
    "dist/SmartEmailSender.app"
    "dist/SmartEmailSender_Lite.app"
    "dist/SmartEmailSender"
    "dist/SmartEmailSender_Lite"
)

FOUND_SENSITIVE=false

for app_path in "${APP_PATHS[@]}"; do
    if [ -d "$app_path" ] || [ -f "$app_path" ]; then
        echo ""
        echo "检查: $app_path"
        echo "-------------------"
        
        for pattern in "${SENSITIVE_FILES[@]}"; do
            # 搜索敏感文件
            found_files=$(find "$app_path" -name "*$pattern*" 2>/dev/null)
            
            if [ -n "$found_files" ]; then
                echo "⚠️  发现敏感文件: $pattern"
                echo "$found_files"
                FOUND_SENSITIVE=true
            fi
        done
        
        # 检查ZIP文件中的敏感内容
        if [ -f "$app_path.zip" ]; then
            echo "检查ZIP文件: $app_path.zip"
            for pattern in "${SENSITIVE_FILES[@]}"; do
                # Use exact matching for sensitive files to avoid false positives
                if unzip -l "$app_path.zip" 2>/dev/null | grep -E "(^|/)${pattern}(\$|/)" > /dev/null; then
                    echo "⚠️  ZIP中发现敏感文件模式: $pattern"
                    FOUND_SENSITIVE=true
                fi
            done
        fi
        
        if [ "$FOUND_SENSITIVE" = false ]; then
            echo "✅ 未发现敏感文件"
        fi
    fi
done

# 检查releases目录
if [ -d "releases" ]; then
    echo ""
    echo "检查发布文件..."
    echo "-------------------"
    
    for zip_file in releases/*.zip; do
        if [ -f "$zip_file" ]; then
            echo "检查: $zip_file"
            for pattern in "${SENSITIVE_FILES[@]}"; do
                # Use exact matching for sensitive files to avoid false positives
                if unzip -l "$zip_file" 2>/dev/null | grep -E "(^|/)${pattern}(\$|/)" > /dev/null; then
                    echo "⚠️  发布ZIP中发现敏感文件: $pattern"
                    FOUND_SENSITIVE=true
                fi
            done
        fi
    done
fi

echo ""
echo "================================================="
if [ "$FOUND_SENSITIVE" = true ]; then
    echo "❌ 安全检查失败！发现敏感文件，请清理后重新打包"
    exit 1
else
    echo "✅ 安全检查通过！未发现敏感文件"
    exit 0
fi