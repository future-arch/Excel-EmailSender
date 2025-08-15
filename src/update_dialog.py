#!/usr/bin/env python3
"""
更新对话框UI
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                              QLabel, QProgressBar, QTextEdit, QCheckBox,
                              QMessageBox, QFrame, QSizePolicy, QApplication)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap, QPalette

from updater import UpdateManager, Version

class UpdateThread(QThread):
    """更新下载线程"""
    
    progress_updated = Signal(int, int, int)  # percent, downloaded, total
    status_updated = Signal(str)
    download_finished = Signal(bool, str)  # success, message
    
    def __init__(self, update_manager: UpdateManager, update_info: dict):
        super().__init__()
        self.update_manager = update_manager
        self.update_info = update_info
        self.should_cancel = False
        
    def run(self):
        """执行更新下载"""
        try:
            self.status_updated.emit("正在下载更新...")
            
            # 下载更新包
            update_file = self.update_manager.download_update(
                self.update_info, 
                self.progress_callback
            )
            
            if self.should_cancel:
                if update_file and update_file.exists():
                    update_file.unlink()
                self.download_finished.emit(False, "用户取消")
                return
                
            if not update_file:
                self.download_finished.emit(False, "下载失败")
                return
                
            self.status_updated.emit("正在应用更新...")
            
            # 应用更新
            success = self.update_manager.apply_update(update_file, self.update_info)
            
            if success:
                self.download_finished.emit(True, "更新完成！即将重启应用...")
            else:
                self.download_finished.emit(False, "应用更新失败，已恢复到原版本")
                
        except Exception as e:
            self.download_finished.emit(False, f"更新过程出错：{str(e)}")
            
    def progress_callback(self, percent, downloaded, total):
        """进度回调"""
        if not self.should_cancel:
            self.progress_updated.emit(percent, downloaded, total)
            
    def cancel(self):
        """取消更新"""
        self.should_cancel = True


class UpdateDialog(QDialog):
    """更新对话框"""
    
    def __init__(self, update_info: dict, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.update_manager = UpdateManager()
        self.update_thread = None
        
        self.setWindowTitle("软件更新")
        self.setFixedSize(500, 400)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("🎉 发现新版本！")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 版本信息
        version_frame = QFrame()
        version_frame.setFrameStyle(QFrame.Box)
        version_frame.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        version_layout = QVBoxLayout(version_frame)
        
        current_version = self.update_manager.current_version
        new_version = Version(self.update_info['version'])
        
        version_info = QLabel(f"""
<b>当前版本:</b> {current_version}<br>
<b>最新版本:</b> {new_version}<br>
<b>发布日期:</b> {self.update_info.get('release_date', '未知')}<br>
<b>更新大小:</b> {self._format_size(self.update_info.get('size', 0))}
        """)
        version_layout.addWidget(version_info)
        layout.addWidget(version_frame)
        
        # 更新日志
        changelog_label = QLabel("📝 更新内容:")
        changelog_label.setFont(QFont("", 11, QFont.Bold))
        layout.addWidget(changelog_label)
        
        self.changelog_text = QTextEdit()
        self.changelog_text.setMaximumHeight(120)
        self.changelog_text.setPlainText(self.update_info.get('changelog', '无更新说明'))
        self.changelog_text.setReadOnly(True)
        layout.addWidget(self.changelog_text)
        
        # 更新类型说明
        update_type = self._get_update_type()
        type_label = QLabel(f"📦 更新类型: {update_type}")
        layout.addWidget(type_label)
        
        # 自动更新选项
        self.auto_update_check = QCheckBox("自动检查更新")
        self.auto_update_check.setChecked(True)
        layout.addWidget(self.auto_update_check)
        
        # 进度条和状态
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.later_button = QPushButton("稍后提醒")
        self.later_button.clicked.connect(self.later_clicked)
        
        self.skip_button = QPushButton("跳过此版本")
        self.skip_button.clicked.connect(self.skip_clicked)
        
        self.update_button = QPushButton("立即更新")
        self.update_button.clicked.connect(self.update_clicked)
        self.update_button.setDefault(True)
        self.update_button.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                font-weight: bold;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
            QPushButton:pressed {
                background-color: #004299;
            }
        """)
        
        button_layout.addWidget(self.later_button)
        button_layout.addWidget(self.skip_button)
        button_layout.addStretch()
        button_layout.addWidget(self.update_button)
        
        layout.addLayout(button_layout)
        
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "未知"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
        
    def _get_update_type(self) -> str:
        """获取更新类型描述"""
        current_ver_str = str(self.update_manager.current_version)
        incremental_updates = self.update_info.get('incremental_updates', {})
        
        if current_ver_str in incremental_updates:
            size = incremental_updates[current_ver_str].get('size', 0)
            return f"增量更新 ({self._format_size(size)}) - 只下载改变的文件"
        else:
            size = self.update_info.get('size', 0)
            return f"完整更新 ({self._format_size(size)}) - 下载完整更新包"
            
    def later_clicked(self):
        """稍后提醒"""
        self.reject()
        
    def skip_clicked(self):
        """跳过此版本"""
        # 保存跳过的版本号
        skip_file = self.update_manager.config_dir / "skipped_versions.txt"
        with open(skip_file, 'a') as f:
            f.write(f"{self.update_info['version']}\n")
        
        QMessageBox.information(self, "已跳过", f"已跳过版本 {self.update_info['version']}")
        self.reject()
        
    def update_clicked(self):
        """开始更新"""
        # 切换UI到更新模式
        self.later_button.setEnabled(False)
        self.skip_button.setEnabled(False)
        self.update_button.setText("取消")
        self.update_button.clicked.disconnect()
        self.update_button.clicked.connect(self.cancel_update)
        
        self.progress_bar.setVisible(True)
        self.status_label.setVisible(True)
        self.status_label.setText("准备下载...")
        
        # 启动更新线程
        self.update_thread = UpdateThread(self.update_manager, self.update_info)
        self.update_thread.progress_updated.connect(self.update_progress)
        self.update_thread.status_updated.connect(self.update_status)
        self.update_thread.download_finished.connect(self.update_finished)
        self.update_thread.start()
        
    def cancel_update(self):
        """取消更新"""
        if self.update_thread:
            self.update_thread.cancel()
            
    def update_progress(self, percent, downloaded, total):
        """更新进度"""
        self.progress_bar.setValue(percent)
        
        downloaded_mb = downloaded / (1024 * 1024)
        total_mb = total / (1024 * 1024)
        
        self.status_label.setText(f"下载中... {downloaded_mb:.1f} MB / {total_mb:.1f} MB")
        
    def update_status(self, status):
        """更新状态"""
        self.status_label.setText(status)
        
    def update_finished(self, success, message):
        """更新完成"""
        if success:
            # 显示成功消息
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("更新成功")
            msg.setText("更新已成功安装！")
            msg.setInformativeText("应用程序将在 3 秒后重启...")
            msg.setStandardButtons(QMessageBox.Ok)
            
            # 3秒后自动重启
            restart_timer = QTimer()
            restart_timer.timeout.connect(lambda: self.restart_app())
            restart_timer.setSingleShot(True)
            restart_timer.start(3000)
            
            msg.exec()
            
        else:
            # 显示错误消息
            QMessageBox.critical(self, "更新失败", f"更新失败：{message}")
            
            # 恢复按钮状态
            self.later_button.setEnabled(True)
            self.skip_button.setEnabled(True)
            self.update_button.setText("立即更新")
            self.update_button.clicked.disconnect()
            self.update_button.clicked.connect(self.update_clicked)
            
            self.progress_bar.setVisible(False)
            self.status_label.setVisible(False)
            
    def restart_app(self):
        """重启应用"""
        self.update_manager.restart_application()
        
    def closeEvent(self, event):
        """关闭事件"""
        if self.update_thread and self.update_thread.isRunning():
            reply = QMessageBox.question(
                self, 
                "确认", 
                "更新正在进行中，确定要取消吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.update_thread.cancel()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def check_for_updates_with_ui(parent=None, silent=False):
    """
    检查更新并显示UI
    
    Args:
        parent: 父窗口
        silent: 如果为True，没有更新时不显示消息
    """
    try:
        update_manager = UpdateManager()
        
        # 检查是否有更新
        has_update, update_info = update_manager.check_for_updates()
        
        if has_update:
            # 检查是否已跳过此版本
            skip_file = update_manager.config_dir / "skipped_versions.txt"
            if skip_file.exists():
                with open(skip_file, 'r') as f:
                    skipped_versions = f.read().strip().split('\n')
                    if update_info['version'] in skipped_versions:
                        if not silent:
                            QMessageBox.information(parent, "已跳过", 
                                                  f"版本 {update_info['version']} 已被跳过")
                        return
            
            # 显示更新对话框
            dialog = UpdateDialog(update_info, parent)
            dialog.exec()
            
        else:
            if not silent:
                QMessageBox.information(parent, "检查更新", "当前已是最新版本！")
                
    except Exception as e:
        if not silent:
            QMessageBox.warning(parent, "检查更新失败", f"无法检查更新：{str(e)}")


# 测试代码
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 模拟更新信息
    test_update_info = {
        "version": "1.1.0",
        "release_date": "2024-01-15",
        "size": 15728640,  # 15MB
        "changelog": "• 修复邮件发送失败的问题\n• 优化UI界面响应速度\n• 增加新的模板功能\n• 修复若干已知bug",
        "download_url": "https://example.com/update.zip",
        "sha256": "abcd1234...",
        "incremental_updates": {
            "1.0.0": {
                "url": "https://example.com/patch_1.0.0_to_1.1.0.zip",
                "size": 2097152,  # 2MB
                "sha256": "efgh5678..."
            }
        }
    }
    
    dialog = UpdateDialog(test_update_info)
    dialog.show()
    
    sys.exit(app.exec())