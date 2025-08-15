#!/bin/bash
# Universal build script that detects platform and builds accordingly

echo "🚀 SmartEmailSender Universal Build Script"
echo "=========================================="

# Detect platform
PLATFORM=$(uname -s)
echo "🔍 Detected platform: $PLATFORM"

case "$PLATFORM" in
    Darwin*)
        echo "🍎 Building for macOS..."
        ./build_macos.sh
        ;;
    Linux*)
        echo "🐧 Building for Linux (using PyInstaller)..."
        # On Linux, we'll use PyInstaller similar to Windows
        if [ ! -f "SmartEmailSender.spec" ]; then
            echo "❌ Error: SmartEmailSender.spec not found"
            exit 1
        fi
        
        echo "📦 Installing PyInstaller and dependencies..."
        pip install pyinstaller
        pip install -r requirements.txt
        
        echo "🧹 Cleaning previous builds..."
        rm -rf build/ dist/ __pycache__/
        
        echo "🔨 Building Linux executable with PyInstaller..."
        pyinstaller SmartEmailSender.spec
        
        if [ -d "dist/SmartEmailSender" ]; then
            echo "✅ Build successful! Created: dist/SmartEmailSender/"
            cd dist
            tar -czf "SmartEmailSender-Linux.tar.gz" "SmartEmailSender/"
            echo "📦 Archive created: SmartEmailSender-Linux.tar.gz"
            cd ..
        else
            echo "❌ Build failed!"
            exit 1
        fi
        ;;
    CYGWIN*|MINGW*|MSYS*)
        echo "🪟 Building for Windows..."
        ./build_windows.sh
        ;;
    *)
        echo "❌ Unsupported platform: $PLATFORM"
        echo "This script supports macOS (Darwin), Linux, and Windows (CYGWIN/MINGW/MSYS)"
        exit 1
        ;;
esac

echo ""
echo "🎉 Build process completed!"
echo "📂 Check the dist/ folder for your application package."