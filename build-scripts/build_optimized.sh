#!/bin/bash

echo "Building optimized SmartEmailSender..."

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist

# Build with optimized spec
echo "Building with PyInstaller (optimized)..."
pyinstaller SmartEmailSender_optimized.spec --clean --noconfirm

# Additional cleanup of unnecessary files in the app bundle
if [ -d "dist/SmartEmailSender.app" ]; then
    echo "Performing additional cleanup..."
    
    # Remove unnecessary Qt frameworks and plugins
    find dist/SmartEmailSender.app -type d -name "Qt3D*" -exec rm -rf {} + 2>/dev/null
    find dist/SmartEmailSender.app -type d -name "QtQuick*" -exec rm -rf {} + 2>/dev/null
    find dist/SmartEmailSender.app -type d -name "QtMultimedia*" -exec rm -rf {} + 2>/dev/null
    find dist/SmartEmailSender.app -type d -name "qml" -exec rm -rf {} + 2>/dev/null
    find dist/SmartEmailSender.app -type d -name "QtCharts*" -exec rm -rf {} + 2>/dev/null
    find dist/SmartEmailSender.app -type d -name "QtDataVisualization*" -exec rm -rf {} + 2>/dev/null
    find dist/SmartEmailSender.app -type d -name "QtPdf*" -exec rm -rf {} + 2>/dev/null
    find dist/SmartEmailSender.app -type d -name "QtSensors*" -exec rm -rf {} + 2>/dev/null
    find dist/SmartEmailSender.app -type d -name "QtBluetooth*" -exec rm -rf {} + 2>/dev/null
    find dist/SmartEmailSender.app -type d -name "QtNfc*" -exec rm -rf {} + 2>/dev/null
    find dist/SmartEmailSender.app -type d -name "QtPositioning*" -exec rm -rf {} + 2>/dev/null
    find dist/SmartEmailSender.app -type d -name "QtLocation*" -exec rm -rf {} + 2>/dev/null
    find dist/SmartEmailSender.app -type d -name "QtSerialPort*" -exec rm -rf {} + 2>/dev/null
    find dist/SmartEmailSender.app -type d -name "QtSerialBus*" -exec rm -rf {} + 2>/dev/null
    find dist/SmartEmailSender.app -type d -name "QtWebSockets*" -exec rm -rf {} + 2>/dev/null
    find dist/SmartEmailSender.app -type d -name "QtRemoteObjects*" -exec rm -rf {} + 2>/dev/null
    find dist/SmartEmailSender.app -type d -name "QtScxml*" -exec rm -rf {} + 2>/dev/null
    find dist/SmartEmailSender.app -type d -name "QtSql*" -exec rm -rf {} + 2>/dev/null
    find dist/SmartEmailSender.app -type d -name "QtTest*" -exec rm -rf {} + 2>/dev/null
    find dist/SmartEmailSender.app -type d -name "QtHelp*" -exec rm -rf {} + 2>/dev/null
    find dist/SmartEmailSender.app -type d -name "VirtualKeyboard" -exec rm -rf {} + 2>/dev/null
    
    # Remove video/audio codecs
    find dist/SmartEmailSender.app -name "libavcodec*" -exec rm -f {} + 2>/dev/null
    find dist/SmartEmailSender.app -name "libavformat*" -exec rm -f {} + 2>/dev/null
    find dist/SmartEmailSender.app -name "libavutil*" -exec rm -f {} + 2>/dev/null
    find dist/SmartEmailSender.app -name "libswscale*" -exec rm -f {} + 2>/dev/null
    find dist/SmartEmailSender.app -name "libavfilter*" -exec rm -f {} + 2>/dev/null
    find dist/SmartEmailSender.app -name "libavdevice*" -exec rm -f {} + 2>/dev/null
    find dist/SmartEmailSender.app -name "libswresample*" -exec rm -f {} + 2>/dev/null
    
    # Remove 3D libraries
    find dist/SmartEmailSender.app -name "libassimp*" -exec rm -f {} + 2>/dev/null
    find dist/SmartEmailSender.app -name "*3D*" -exec rm -f {} + 2>/dev/null
    find dist/SmartEmailSender.app -name "*opengl*" -exec rm -f {} + 2>/dev/null
    
    # Remove test and example files
    find dist/SmartEmailSender.app -type d -name "tests" -exec rm -rf {} + 2>/dev/null
    find dist/SmartEmailSender.app -type d -name "test" -exec rm -rf {} + 2>/dev/null
    find dist/SmartEmailSender.app -type d -name "examples" -exec rm -rf {} + 2>/dev/null
    find dist/SmartEmailSender.app -type d -name "example" -exec rm -rf {} + 2>/dev/null
    find dist/SmartEmailSender.app -type d -name "doc" -exec rm -rf {} + 2>/dev/null
    find dist/SmartEmailSender.app -type d -name "docs" -exec rm -rf {} + 2>/dev/null
    
    # Remove unnecessary plugin directories
    find dist/SmartEmailSender.app -type d -name "sceneparsers" -exec rm -rf {} + 2>/dev/null
    find dist/SmartEmailSender.app -type d -name "assetimporters" -exec rm -rf {} + 2>/dev/null
    find dist/SmartEmailSender.app -type d -name "renderers" -exec rm -rf {} + 2>/dev/null
    find dist/SmartEmailSender.app -type d -name "geometryloaders" -exec rm -rf {} + 2>/dev/null
    find dist/SmartEmailSender.app -type d -name "sqldrivers" -exec rm -rf {} + 2>/dev/null
    
    echo "Final app size:"
    du -sh dist/SmartEmailSender.app
    
    # Create DMG for distribution
    echo "Creating DMG..."
    create-dmg \
        --volname "SmartEmailSender" \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 100 \
        --icon "SmartEmailSender.app" 175 190 \
        --hide-extension "SmartEmailSender.app" \
        --app-drop-link 425 190 \
        "dist/SmartEmailSender.dmg" \
        "dist/SmartEmailSender.app" 2>/dev/null || {
            echo "create-dmg not installed, creating zip instead..."
            cd dist
            zip -r SmartEmailSender-macOS-optimized.zip SmartEmailSender.app
            cd ..
            echo "Created dist/SmartEmailSender-macOS-optimized.zip"
        }
fi

echo "Build complete!"
echo "Final sizes:"
ls -lh dist/SmartEmailSender* 2>/dev/null