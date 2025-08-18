#!/usr/bin/env python3

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 添加虚拟环境路径
venv_path = os.path.join(project_root, 'venv', 'lib', 'python3.12', 'site-packages')
if os.path.exists(venv_path):
    sys.path.insert(0, venv_path)

print("Python路径配置:")
for i, path in enumerate(sys.path[:5]):
    print(f"  {i}: {path}")

print("\n测试导入:")

try:
    import pandas
    print("✅ pandas:", pandas.__version__)
except Exception as e:
    print("❌ pandas:", e)

try:
    import requests
    print("✅ requests:", requests.__version__)
except Exception as e:
    print("❌ requests:", e)

try:
    from PySide6.QtWidgets import QApplication
    print("✅ PySide6.QtWidgets")
except Exception as e:
    print("❌ PySide6.QtWidgets:", e)

try:
    from src.ui.main_window import MailerApp
    print("✅ src.ui.main_window.MailerApp")
except Exception as e:
    print("❌ src.ui.main_window.MailerApp:", e)

print("\n测试完成")