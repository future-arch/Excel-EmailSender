#!/bin/bash
# Build script for macOS .app bundle using py2app

echo "🍎 Building SmartEmailSender for macOS..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/ SmartEmailSender.app/ *.egg-info/

# Check if required files exist
if [ ! -f "src/SmartEmailSender.py" ]; then
    echo "❌ Error: src/SmartEmailSender.py not found"
    exit 1
fi

if [ ! -f "setup.py" ]; then
    echo "❌ Error: setup.py not found"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Create app icon directory if it doesn't exist
mkdir -p assets/

# Build with py2app
echo "🔨 Building .app bundle with py2app..."
python setup.py py2app

# Check if build was successful
if [ -d "dist/SmartEmailSender.app" ]; then
    echo "✅ Build successful! Created: dist/SmartEmailSender.app"
    
    # Show app bundle size
    BUNDLE_SIZE=$(du -sh "dist/SmartEmailSender.app" | cut -f1)
    echo "📦 Bundle size: $BUNDLE_SIZE"
    
    # Create a compressed archive for distribution
    echo "🗜️  Creating distribution archive..."
    cd dist
    zip -r "SmartEmailSender-macOS.zip" "SmartEmailSender.app/"
    ARCHIVE_SIZE=$(du -sh "SmartEmailSender-macOS.zip" | cut -f1)
    echo "📦 Archive size: $ARCHIVE_SIZE"
    cd ..
    
    echo ""
    echo "🎉 macOS build complete!"
    echo "📂 App bundle: dist/SmartEmailSender.app"
    echo "📦 Distribution: dist/SmartEmailSender-macOS.zip"
    echo ""
    echo "To test the app:"
    echo "  open dist/SmartEmailSender.app"
    
else
    echo "❌ Build failed! Check the output above for errors."
    exit 1
fi