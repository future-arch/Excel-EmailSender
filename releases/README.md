# Releases Directory

This directory contains release packages for distribution.

## Install Files (Not included in repository)

The actual install files are not stored in the repository due to their large size:

### macOS Version
- **SmartEmailSender-macOS.zip** (~1.1GB)
  - Contains: SmartEmailSender.app 
  - Installation: Download, extract, drag to Applications folder

### Windows Version  
- **SmartEmailSender_Windows_Complete_Builder.zip** (~1.6MB)
  - Contains: Complete build environment with auto-build scripts
  - Installation: Download, extract, run "双击开始构建.bat"
  - Output: Creates SmartEmailSender-Windows.zip and setup executables

## Building Release Files

To create the install files:

### For macOS:
```bash
./build-scripts/build_final.sh
```

### For Windows:
Use the complete builder package or run:
```cmd
./build-scripts/build_windows.bat
```

## Distribution

Install files should be distributed through:
- Direct download links
- Cloud storage services
- Internal distribution systems

**Note**: Install files are excluded from git due to size constraints.