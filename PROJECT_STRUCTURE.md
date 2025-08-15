# SmartEmailSender Project Structure

This document outlines the organized structure of the SmartEmailSender project after cleanup.

## 📁 Directory Structure

```
SmartEmailSender/
├── 🏗️  Core Development
│   ├── src/                           # Application source code
│   │   ├── SmartEmailSender.py        # Main application entry
│   │   ├── ui/                        # User interface components
│   │   ├── graph/                     # Microsoft Graph API integration
│   │   ├── config/                    # Configuration management
│   │   └── *.py                       # Other core modules
│   ├── assets/                        # Application resources
│   │   ├── SmartEmailSender.icns      # macOS icon
│   │   ├── SmartEmailSender.ico       # Windows icon
│   │   ├── tinymce/                   # HTML editor resources
│   │   └── *.html                     # HTML templates
│   ├── requirements.txt               # Python dependencies
│   ├── field_mapping_config.json      # Field mapping configuration
│   ├── version.json                   # Version information
│   └── settings.json                  # Application settings
│
├── 🔧 Build & Deployment
│   ├── build-scripts/                 # Build automation scripts
│   │   ├── build_final.sh             # macOS build script
│   │   ├── build_windows.bat          # Windows build script
│   │   ├── SmartEmailSender_Windows_Builder.bat # Complete Windows builder
│   │   └── security_check.sh          # Security validation
│   ├── deployment/                    # Deployment configurations
│   │   ├── SmartEmailSender_final.spec # macOS PyInstaller spec
│   │   ├── SmartEmailSender_windows.spec # Windows PyInstaller spec
│   │   ├── SmartEmailSender_advanced.nsi # NSIS installer script
│   │   ├── SmartEmailSender.iss       # Inno Setup script
│   │   └── *.txt                      # License, version info
│   ├── hooks/                         # PyInstaller hooks
│   └── releases/                      # Release packages (empty)
│       └── README.md                  # Release distribution guide
│
├── 📚 Documentation
│   ├── docs/                          # Technical documentation
│   │   ├── AUTO_UPDATE_GUIDE.md       # Auto-update system guide
│   │   ├── AZURE_SETUP_GUIDE.md       # Azure configuration guide
│   │   ├── CDN_DEPLOYMENT_GUIDE.md    # CDN setup guide
│   │   ├── WINDOWS_BUILD_GUIDE.md     # Windows build instructions
│   │   └── WINDOWS_DEPLOYMENT_SUMMARY.md # Windows deployment summary
│   ├── user-guides/                   # User documentation
│   │   ├── Mac用户介绍.txt             # macOS user guide
│   │   ├── Windows用户介绍.txt         # Windows user guide
│   │   └── SmartEmailSender_用户介绍.md # Complete user manual
│   ├── README.md                      # Main project readme
│   ├── CLAUDE.md                      # Claude development context
│   └── PROJECT_STRUCTURE.md           # This file
│
└── 🧪 Development Tools
    ├── tests/                         # Test files
    ├── utils/                         # Utility scripts
    │   ├── create_update_package.py   # Update package creator
    │   └── setup.py                   # Setup utilities
    ├── updates/                       # Auto-update system
    │   └── update_info.json          # Update configuration
    └── data/                          # Data files (empty)
```

## 🎯 Key Benefits of This Structure

### ✅ Clear Separation of Concerns
- **Development**: Core source code and assets
- **Build**: All build and deployment scripts organized
- **Documentation**: User guides and technical docs separated
- **Tools**: Development utilities and testing

### ✅ Git-Friendly
- **Small Size**: 9.7MB (down from 1.7GB)
- **No Large Binaries**: Install files excluded from repository
- **Clean History**: Build artifacts removed

### ✅ Development Ready
- **Easy Navigation**: Logical folder structure
- **Quick Building**: All scripts in `build-scripts/`
- **Clear Documentation**: Comprehensive guides in `docs/`
- **Flexible Deployment**: Multiple deployment options in `deployment/`

## 🚀 Quick Start Commands

### Development
```bash
# Run the application
python src/SmartEmailSender.py

# Install dependencies
pip install -r requirements.txt
```

### Building
```bash
# macOS build
./build-scripts/build_final.sh

# Windows build (on Windows)
./build-scripts/build_windows.bat
```

### Documentation
```bash
# View user guides
open user-guides/

# View technical docs
open docs/
```

## 📝 Notes

1. **Install Files**: Large install packages are not stored in the repository. See `releases/README.md` for distribution strategy.

2. **Build Artifacts**: `build/` and `dist/` folders are automatically created during builds and should not be committed.

3. **Security**: Sensitive files like `token_cache.json` and `.env` are automatically excluded from builds.

4. **Cross-Platform**: The structure supports both macOS and Windows development and deployment.

## 🔄 Future Development

This organized structure makes it easy to:
- Add new features to the `src/` directory
- Create new build configurations in `deployment/`
- Add documentation to appropriate folders
- Maintain clean git history without large files

The project is now ready for efficient development and collaboration!