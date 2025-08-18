#!/usr/bin/env python3
"""
测试模块导入脚本
"""

import sys
import os

# 添加虚拟环境路径
project_root = os.path.dirname(os.path.abspath(__file__))
venv_path = os.path.join(project_root, 'venv')

if os.path.exists(venv_path):
    if sys.platform == "win32":
        site_packages = os.path.join(venv_path, 'Lib', 'site-packages')
    else:
        python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
        site_packages = os.path.join(venv_path, 'lib', python_version, 'site-packages')
    
    if os.path.exists(site_packages):
        sys.path.insert(0, site_packages)
        print(f"✅ 虚拟环境路径已添加: {site_packages}")

print(f"Python版本: {sys.version}")
print(f"Python路径: {sys.executable}")
print()

# 测试基础依赖
print("测试基础依赖包:")
deps = [
    ('pandas', 'pandas'),
    ('requests', 'requests'), 
    ('msal', 'msal'),
    ('jinja2', 'jinja2'),
    ('python-dotenv', 'dotenv'),
    ('openpyxl', 'openpyxl')
]

for dep_name, import_name in deps:
    try:
        module = __import__(import_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"✅ {dep_name}: {version}")
    except ImportError as e:
        print(f"❌ {dep_name}: {e}")

print()

# 测试PySide6组件
print("测试PySide6组件:")
pyside_components = [
    'PySide6',
    'PySide6.QtCore',
    'PySide6.QtWidgets', 
    'PySide6.QtGui',
    'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebEngineCore'
]

for component in pyside_components:
    try:
        __import__(component)
        print(f"✅ {component}")
    except ImportError as e:
        print(f"❌ {component}: {e}")

print()

# 测试应用模块
print("测试应用模块:")
sys.path.insert(0, project_root)

app_modules = [
    ('src.graph.auth', 'Azure认证模块'),
    ('src.graph.api', 'Graph API模块'),
    ('src.ui.main_window', '主窗口模块'),
    ('src.ui.tinymce_editor', 'TinyMCE编辑器'),
    ('src.config.field_mapper', '字段映射器')
]

for module_name, description in app_modules:
    try:
        __import__(module_name)
        print(f"✅ {description}: {module_name}")
    except ImportError as e:
        print(f"❌ {description}: {module_name} - {e}")

print()
print("导入测试完成!")