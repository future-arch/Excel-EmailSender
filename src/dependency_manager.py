#!/usr/bin/env python3
"""
依赖管理器 - 负责检查和下载必要的运行时依赖
"""

import os
import sys
import json
import hashlib
import platform
import subprocess
import urllib.request
import zipfile
import tarfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class DependencyManager:
    """管理应用程序的运行时依赖"""
    
    # 依赖包的CDN地址（可以配置多个镜像源）
    CDN_URLS = [
        # 国内镜像源（优先）
        "https://gitee.com/smartemailsender/deps/releases/download/v1.0/",  # Gitee
        "https://smartemailsender.oss-cn-beijing.aliyuncs.com/deps/v1.0/",  # 阿里云OSS
        "https://smartemailsender-1234567890.cos.ap-beijing.myqcloud.com/deps/v1.0/",  # 腾讯云COS
        "https://deps.smartemailsender.cn/v1.0/",  # 自建CDN
        
        # 国际镜像源（备用）
        "https://github.com/smartemailsender/deps/releases/download/v1.0/",
        "https://cdn.jsdelivr.net/gh/smartemailsender/deps@v1.0/",
        "https://raw.githubusercontent.com/smartemailsender/deps/v1.0/",
    ]
    
    # 依赖包定义
    DEPENDENCIES = {
        "qtwebengine": {
            "darwin": {
                "url": "qtwebengine-6.5-macos.tar.gz",
                "size": 580 * 1024 * 1024,  # 预估580MB
                "sha256": "TO_BE_CALCULATED",
                "extract_to": "lib/PySide6/Qt/lib",
                "files": [
                    "QtWebEngineCore.framework",
                    "QtWebEngineWidgets.framework",
                    "QtWebChannel.framework"
                ]
            },
            "win32": {
                "url": "qtwebengine-6.5-windows.zip",
                "size": 550 * 1024 * 1024,
                "sha256": "TO_BE_CALCULATED",
                "extract_to": "lib/PySide6/Qt/bin",
                "files": [
                    "QtWebEngineCore.dll",
                    "QtWebEngineWidgets.dll",
                    "QtWebChannel.dll",
                    "QtWebEngineProcess.exe"
                ]
            },
            "linux": {
                "url": "qtwebengine-6.5-linux.tar.gz",
                "size": 600 * 1024 * 1024,
                "sha256": "TO_BE_CALCULATED",
                "extract_to": "lib/PySide6/Qt/lib",
                "files": [
                    "libQtWebEngineCore.so.6",
                    "libQtWebEngineWidgets.so.6",
                    "libQtWebChannel.so.6"
                ]
            }
        }
    }
    
    def __init__(self, app_dir: Path = None):
        """初始化依赖管理器"""
        self.app_dir = app_dir or Path(sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(os.path.abspath(__file__)))
        self.deps_dir = self.app_dir / "deps"
        self.config_file = self.app_dir / "deps_config.json"
        self.platform = self._get_platform()
        self.installed_deps = self._load_installed_deps()
        
    def _get_platform(self) -> str:
        """获取当前平台"""
        system = platform.system().lower()
        if system == "darwin":
            return "darwin"
        elif system == "windows":
            return "win32"
        else:
            return "linux"
            
    def _load_installed_deps(self) -> Dict:
        """加载已安装的依赖信息"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}
        
    def _save_installed_deps(self):
        """保存已安装的依赖信息"""
        with open(self.config_file, 'w') as f:
            json.dump(self.installed_deps, f, indent=2)
            
    def check_dependency(self, dep_name: str) -> bool:
        """检查依赖是否已安装"""
        if dep_name not in self.DEPENDENCIES:
            return True  # 未知依赖，假设已安装
            
        dep_info = self.DEPENDENCIES[dep_name].get(self.platform)
        if not dep_info:
            return True  # 该平台不需要此依赖
            
        # 检查文件是否存在
        extract_path = self.app_dir / dep_info["extract_to"]
        for file_name in dep_info["files"]:
            file_path = extract_path / file_name
            if not file_path.exists():
                return False
                
        # 检查是否在已安装列表中
        return dep_name in self.installed_deps
        
    def get_missing_dependencies(self) -> List[str]:
        """获取缺失的依赖列表"""
        missing = []
        for dep_name in self.DEPENDENCIES:
            if not self.check_dependency(dep_name):
                missing.append(dep_name)
        return missing
        
    def download_file(self, url: str, dest_path: Path, 
                     progress_callback=None) -> bool:
        """下载文件，支持进度回调"""
        try:
            # 尝试多个CDN源
            for cdn_base in self.CDN_URLS:
                full_url = cdn_base + url
                try:
                    response = urllib.request.urlopen(full_url, timeout=30)
                    total_size = int(response.headers.get('Content-Length', 0))
                    
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    downloaded = 0
                    block_size = 8192
                    
                    with open(dest_path, 'wb') as f:
                        while True:
                            chunk = response.read(block_size)
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            if progress_callback and total_size > 0:
                                progress = int(downloaded * 100 / total_size)
                                progress_callback(progress, downloaded, total_size)
                                
                    return True
                except Exception as e:
                    print(f"Failed to download from {cdn_base}: {e}")
                    continue
                    
            return False
        except Exception as e:
            print(f"Download error: {e}")
            return False
            
    def extract_archive(self, archive_path: Path, extract_to: Path) -> bool:
        """解压归档文件"""
        try:
            extract_to.mkdir(parents=True, exist_ok=True)
            
            if archive_path.suffix == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_to)
            elif archive_path.suffix in ['.gz', '.tar']:
                with tarfile.open(archive_path, 'r:*') as tar_ref:
                    tar_ref.extractall(extract_to)
            else:
                return False
                
            return True
        except Exception as e:
            print(f"Extraction error: {e}")
            return False
            
    def install_dependency(self, dep_name: str, progress_callback=None) -> bool:
        """安装指定的依赖"""
        if dep_name not in self.DEPENDENCIES:
            return False
            
        dep_info = self.DEPENDENCIES[dep_name].get(self.platform)
        if not dep_info:
            return True  # 该平台不需要此依赖
            
        # 下载依赖包
        download_path = self.deps_dir / dep_info["url"]
        if not self.download_file(dep_info["url"], download_path, progress_callback):
            return False
            
        # 解压到指定位置
        extract_path = self.app_dir / dep_info["extract_to"]
        if not self.extract_archive(download_path, extract_path):
            return False
            
        # 记录安装信息
        self.installed_deps[dep_name] = {
            "version": "1.0",
            "install_date": str(Path.ctime(download_path)),
            "files": dep_info["files"]
        }
        self._save_installed_deps()
        
        # 清理下载文件
        download_path.unlink(missing_ok=True)
        
        return True
        
    def verify_installation(self) -> Tuple[bool, List[str]]:
        """验证所有依赖是否正确安装"""
        missing = self.get_missing_dependencies()
        return len(missing) == 0, missing


class DependencyInstaller:
    """依赖安装界面（用于首次运行）"""
    
    def __init__(self, parent=None):
        self.manager = DependencyManager()
        self.parent = parent
        
    def check_and_install(self) -> bool:
        """检查并安装缺失的依赖"""
        missing = self.manager.get_missing_dependencies()
        
        if not missing:
            return True
            
        # 如果有Qt可用，显示GUI进度
        try:
            from PySide6.QtWidgets import QMessageBox, QProgressDialog
            from PySide6.QtCore import Qt
            
            # 询问用户是否下载
            msg = QMessageBox(self.parent)
            msg.setWindowTitle("需要下载组件")
            msg.setText(f"首次运行需要下载必要的组件（约580MB）。\n\n缺失组件：{', '.join(missing)}")
            msg.setInformativeText("是否现在下载？您也可以选择下载包含所有组件的完整版。")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setDefaultButton(QMessageBox.Yes)
            
            if msg.exec() != QMessageBox.Yes:
                return False
                
            # 显示下载进度
            progress = QProgressDialog("正在下载组件...", "取消", 0, 100, self.parent)
            progress.setWindowTitle("下载组件")
            progress.setWindowModality(Qt.WindowModal)
            progress.setAutoReset(False)
            progress.setAutoClose(False)
            
            def update_progress(percent, downloaded, total):
                progress.setValue(percent)
                mb_downloaded = downloaded / (1024 * 1024)
                mb_total = total / (1024 * 1024)
                progress.setLabelText(f"正在下载组件...\n{mb_downloaded:.1f} MB / {mb_total:.1f} MB")
                
                if progress.wasCanceled():
                    return False
                return True
                
            # 安装每个缺失的依赖
            for dep in missing:
                progress.setLabelText(f"正在下载 {dep}...")
                if not self.manager.install_dependency(dep, update_progress):
                    QMessageBox.critical(self.parent, "下载失败", 
                                        f"无法下载 {dep}。\n请检查网络连接或下载完整版。")
                    return False
                    
            progress.close()
            QMessageBox.information(self.parent, "安装完成", "所有组件已成功安装！")
            return True
            
        except ImportError:
            # 如果没有GUI，使用命令行
            print(f"需要下载组件：{', '.join(missing)}")
            response = input("是否现在下载？(y/n): ")
            
            if response.lower() != 'y':
                return False
                
            for dep in missing:
                print(f"正在下载 {dep}...")
                
                def print_progress(percent, downloaded, total):
                    mb_downloaded = downloaded / (1024 * 1024)
                    mb_total = total / (1024 * 1024)
                    print(f"\r进度: {percent}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end='')
                    
                if not self.manager.install_dependency(dep, print_progress):
                    print(f"\n错误：无法下载 {dep}")
                    return False
                print()  # 新行
                
            print("所有组件已成功安装！")
            return True