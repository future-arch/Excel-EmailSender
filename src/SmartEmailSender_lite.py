#!/usr/bin/env python3
"""
SmartEmailSender 轻量版启动器
首次运行时会下载必要的QtWebEngine组件
"""

import os
import sys
from pathlib import Path

# 添加src目录到路径
src_path = Path(__file__).parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

def check_and_install_dependencies():
    """检查并安装依赖"""
    try:
        # 尝试使用智能CDN选择器
        from cdn_selector import SmartDependencyManager
        manager = SmartDependencyManager()
        
        # 优化CDN（会自动检测地区）
        print("正在优化下载源...")
        manager.optimize_cdn_urls(show_progress=True)
        
        # 检查并安装
        missing = manager.base_manager.get_missing_dependencies()
        if not missing:
            return True
            
        # 使用智能下载
        for dep in missing:
            if not manager.download_with_smart_cdn(dep):
                return False
        return True
        
    except ImportError:
        # 如果智能选择器不可用，使用原始方法
        from dependency_manager import DependencyInstaller
        installer = DependencyInstaller()
        return installer.check_and_install()

def main():
    """主入口"""
    # 尝试导入基础Qt组件（这些会包含在轻量版中）
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
        from PySide6.QtCore import Qt
    except ImportError:
        print("错误：基础Qt组件未找到。请安装PySide6。")
        sys.exit(1)
    
    # 创建应用实例（用于显示对话框）
    app = QApplication(sys.argv)
    app.setApplicationName("SmartEmailSender")
    
    # 检查并安装QtWebEngine依赖
    print("检查运行环境...")
    
    # 先尝试导入QtWebEngine，看是否已经存在
    try:
        from PySide6.QtWebEngineWidgets import QWebEngineView
        print("QtWebEngine已安装，直接启动应用...")
    except ImportError:
        print("QtWebEngine未安装，需要下载...")
        
        # 显示欢迎对话框
        welcome = QMessageBox()
        welcome.setWindowTitle("欢迎使用 SmartEmailSender")
        welcome.setText("这是您第一次运行 SmartEmailSender 轻量版。")
        welcome.setInformativeText(
            "轻量版需要下载额外的组件才能运行（约580MB）。\n\n"
            "优点：\n"
            "• 初始安装包小（约50MB）\n"
            "• 按需下载组件\n\n"
            "如果您的网络不稳定，建议下载完整版（包含所有组件）。"
        )
        welcome.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        welcome.setDefaultButton(QMessageBox.Ok)
        
        if welcome.exec() == QMessageBox.Cancel:
            sys.exit(0)
        
        # 安装依赖
        if not check_and_install_dependencies():
            error = QMessageBox()
            error.setIcon(QMessageBox.Critical)
            error.setWindowTitle("安装失败")
            error.setText("无法下载必要的组件。")
            error.setInformativeText(
                "可能的原因：\n"
                "• 网络连接问题\n"
                "• 下载服务器暂时不可用\n\n"
                "请稍后重试，或下载包含所有组件的完整版。"
            )
            error.exec()
            sys.exit(1)
    
    # 现在可以安全地导入和运行主应用
    try:
        # 动态导入主应用（这样可以延迟QtWebEngine的导入）
        import importlib
        main_module = importlib.import_module('SmartEmailSender')
        
        # 运行主应用
        main_module.main()
    except Exception as e:
        error = QMessageBox()
        error.setIcon(QMessageBox.Critical)
        error.setWindowTitle("启动失败")
        error.setText(f"无法启动应用程序：{str(e)}")
        error.setDetailedText(str(e))
        error.exec()
        sys.exit(1)

if __name__ == "__main__":
    main()