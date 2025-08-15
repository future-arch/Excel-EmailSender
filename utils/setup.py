"""
Setup script for creating SmartEmailSender installation packages.
Supports both macOS (.app with py2app) and Windows (.exe with PyInstaller).
"""

from setuptools import setup, find_packages
import sys
import os

# Application metadata
APP_NAME = "SmartEmailSender"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "A professional bulk email sending application with Excel and Microsoft 365 Groups integration"
APP_AUTHOR = "Your Name"
APP_AUTHOR_EMAIL = "your.email@domain.com"

# Main application script
MAIN_SCRIPT = "src/SmartEmailSender.py"

# Read requirements
def get_requirements():
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Additional data files to include
DATA_FILES = [
    ('assets', ['assets/tinymce_like_editor.html', 'assets/tinymce_editor_no_toolbar.html']),
]

# For py2app (macOS)
if sys.platform == 'darwin':
    import py2app
    
    OPTIONS = {
        'py2app': {
            'argv_emulation': True,
            'iconfile': 'assets/SmartEmailSender.icns',  # App icon
            'plist': {
                'CFBundleName': APP_NAME,
                'CFBundleDisplayName': APP_NAME,
                'CFBundleVersion': APP_VERSION,
                'CFBundleShortVersionString': APP_VERSION,
                'CFBundleIdentifier': 'com.yourcompany.smartemailsender',
                'NSHighResolutionCapable': True,
                'NSRequiresAquaSystemAppearance': False,  # Support dark mode
                'CFBundleDocumentTypes': [{
                    'CFBundleTypeExtensions': ['xlsx', 'xls'],
                    'CFBundleTypeName': 'Excel Files',
                    'CFBundleTypeRole': 'Viewer'
                }],
            },
            'packages': ['PySide6', 'pandas', 'msal', 'jinja2', 'openpyxl', 'dotenv', 'requests'],
            'includes': ['src'],
            'excludes': ['tkinter', 'numpy'],  # Exclude unnecessary packages
            'resources': ['assets/'],
            'optimize': 2,
        }
    }
    
    setup(
        name=APP_NAME,
        version=APP_VERSION,
        description=APP_DESCRIPTION,
        author=APP_AUTHOR,
        author_email=APP_AUTHOR_EMAIL,
        app=[MAIN_SCRIPT],
        data_files=DATA_FILES,
        options=OPTIONS,
        setup_requires=['py2app'],
        install_requires=get_requirements(),
    )

# For PyInstaller (Windows and cross-platform)
else:
    setup(
        name=APP_NAME,
        version=APP_VERSION,
        description=APP_DESCRIPTION,
        author=APP_AUTHOR,
        author_email=APP_AUTHOR_EMAIL,
        packages=find_packages(),
        install_requires=get_requirements(),
        entry_points={
            'console_scripts': [
                f'{APP_NAME.lower()}=src.SmartEmailSender:main',
            ],
        },
        data_files=DATA_FILES,
        include_package_data=True,
        python_requires='>=3.8',
        classifiers=[
            'Development Status :: 4 - Beta',
            'Intended Audience :: End Users/Desktop',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: 3.11',
            'Operating System :: OS Independent',
        ],
    )