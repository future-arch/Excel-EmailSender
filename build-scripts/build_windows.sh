#!/bin/bash
# Build script for Windows .exe using PyInstaller
# Note: This script should be run on Windows or using a Windows-compatible environment

echo "🪟 Building SmartEmailSender for Windows..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/ __pycache__/ *.spec

# Check if required files exist
if [ ! -f "src/SmartEmailSender.py" ]; then
    echo "❌ Error: src/SmartEmailSender.py not found"
    exit 1
fi

if [ ! -f "SmartEmailSender.spec" ]; then
    echo "❌ Error: SmartEmailSender.spec not found"
    exit 1
fi

# Install PyInstaller if not already installed
echo "📦 Installing PyInstaller and dependencies..."
pip install pyinstaller
pip install -r requirements.txt

# Build with PyInstaller using the spec file
echo "🔨 Building Windows executable with PyInstaller..."
pyinstaller SmartEmailSender.spec

# Check if build was successful
if [ -f "dist/SmartEmailSender.exe" ] || [ -d "dist/SmartEmailSender" ]; then
    echo "✅ Build successful!"
    
    # Determine what was created
    if [ -f "dist/SmartEmailSender.exe" ]; then
        echo "📦 Created: dist/SmartEmailSender.exe"
        EXE_SIZE=$(du -sh "dist/SmartEmailSender.exe" | cut -f1)
        echo "📦 File size: $EXE_SIZE"
    else
        echo "📂 Created: dist/SmartEmailSender/"
        FOLDER_SIZE=$(du -sh "dist/SmartEmailSender" | cut -f1)
        echo "📦 Folder size: $FOLDER_SIZE"
    fi
    
    # Create distribution archive
    echo "🗜️  Creating distribution archive..."
    cd dist
    if [ -f "SmartEmailSender.exe" ]; then
        zip -r "SmartEmailSender-Windows.zip" "SmartEmailSender.exe" -j
    else
        zip -r "SmartEmailSender-Windows.zip" "SmartEmailSender/"
    fi
    ARCHIVE_SIZE=$(du -sh "SmartEmailSender-Windows.zip" | cut -f1)
    echo "📦 Archive size: $ARCHIVE_SIZE"
    cd ..
    
    echo ""
    echo "🎉 Windows build complete!"
    if [ -f "dist/SmartEmailSender.exe" ]; then
        echo "🎯 Executable: dist/SmartEmailSender.exe"
    else
        echo "📂 Application: dist/SmartEmailSender/"
    fi
    echo "📦 Distribution: dist/SmartEmailSender-Windows.zip"
    echo ""
    echo "To test on Windows:"
    if [ -f "dist/SmartEmailSender.exe" ]; then
        echo "  ./dist/SmartEmailSender.exe"
    else
        echo "  ./dist/SmartEmailSender/SmartEmailSender.exe"
    fi
    
else
    echo "❌ Build failed! Check the output above for errors."
    exit 1
fi