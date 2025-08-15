#!/usr/bin/env python3
"""
测试构建的最小版本
"""

import sys
from pathlib import Path

try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
    from PySide6.QtCore import Qt
    print("✅ PySide6 导入成功")
except ImportError as e:
    print(f"❌ PySide6 导入失败: {e}")
    sys.exit(1)

try:
    import pandas as pd
    print("✅ pandas 导入成功")
except ImportError as e:
    print(f"❌ pandas 导入失败: {e}")

try:
    import msal
    print("✅ msal 导入成功")
except ImportError as e:
    print(f"❌ msal 导入失败: {e}")

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SmartEmailSender 构建测试")
        self.setFixedSize(400, 300)
        
        label = QLabel("🎉 SmartEmailSender 构建测试成功！\n\n所有依赖都已正确加载。", self)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16px; padding: 20px;")
        self.setCentralWidget(label)

def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    print("✅ 应用界面启动成功")
    print("按Ctrl+C或关闭窗口退出...")
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\n用户取消")
        sys.exit(0)

if __name__ == "__main__":
    main()