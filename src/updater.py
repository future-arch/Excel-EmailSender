#!/usr/bin/env python3
"""
SmartEmailSender 自动更新系统
支持增量更新，无需重新下载完整安装包
"""

import os
import sys
import json
import shutil
import hashlib
import zipfile
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from datetime import datetime
import urllib.request
import urllib.error

# 版本信息
CURRENT_VERSION = "1.0.0"
UPDATE_CHECK_URL = "https://api.github.com/repos/smartemailsender/app/releases/latest"
UPDATE_INFO_URLS = [
    # 国内镜像
    "https://gitee.com/smartemailsender/app/raw/main/update_info.json",
    "https://smartemailsender.oss-cn-beijing.aliyuncs.com/updates/info.json",
    # 国际镜像
    "https://raw.githubusercontent.com/smartemailsender/app/main/update_info.json",
]

class Version:
    """版本号处理类"""
    
    def __init__(self, version_string: str):
        """解析版本号 (如 '1.2.3' 或 'v1.2.3')"""
        self.version_string = version_string.strip().lstrip('v').lstrip('V')
        parts = self.version_string.split('.')
        self.major = int(parts[0]) if len(parts) > 0 else 0
        self.minor = int(parts[1]) if len(parts) > 1 else 0
        self.patch = int(parts[2]) if len(parts) > 2 else 0
        
    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"
        
    def __eq__(self, other):
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)
        
    def __lt__(self, other):
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
        
    def __le__(self, other):
        return self < other or self == other


class UpdateManager:
    """更新管理器"""
    
    def __init__(self, app_dir: Path = None):
        """初始化更新管理器"""
        self.app_dir = app_dir or self._get_app_dir()
        self.config_dir = Path.home() / ".smartemailsender"
        self.config_dir.mkdir(exist_ok=True)
        
        self.version_file = self.app_dir / "version.json"
        self.backup_dir = self.config_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        self.current_version = self._load_current_version()
        
    def _get_app_dir(self) -> Path:
        """获取应用程序目录"""
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller打包后的路径
            return Path(sys._MEIPASS)
        else:
            # 开发环境
            return Path(__file__).parent
            
    def _load_current_version(self) -> Version:
        """加载当前版本"""
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r') as f:
                    data = json.load(f)
                    return Version(data.get('version', CURRENT_VERSION))
            except:
                pass
        return Version(CURRENT_VERSION)
        
    def _save_version_info(self, version: str, info: Dict):
        """保存版本信息"""
        data = {
            'version': version,
            'updated_at': datetime.now().isoformat(),
            'update_info': info
        }
        with open(self.version_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    def check_for_updates(self) -> Tuple[bool, Optional[Dict]]:
        """
        检查是否有新版本
        返回: (是否有更新, 更新信息)
        """
        for url in UPDATE_INFO_URLS:
            try:
                with urllib.request.urlopen(url, timeout=10) as response:
                    update_info = json.loads(response.read().decode())
                    
                    latest_version = Version(update_info['version'])
                    
                    if latest_version > self.current_version:
                        return True, update_info
                    else:
                        return False, None
                        
            except Exception as e:
                print(f"检查更新失败 ({url}): {e}")
                continue
                
        return False, None
        
    def download_update(self, update_info: Dict, progress_callback=None) -> Optional[Path]:
        """
        下载更新包
        支持增量更新和完整更新
        """
        # 确定更新类型
        update_type = self._determine_update_type(update_info)
        
        if update_type == 'incremental':
            # 增量更新 - 只下载改变的文件
            return self._download_incremental_update(update_info, progress_callback)
        else:
            # 完整更新 - 下载完整包
            return self._download_full_update(update_info, progress_callback)
            
    def _determine_update_type(self, update_info: Dict) -> str:
        """确定更新类型"""
        # 检查是否有增量更新包
        incremental_updates = update_info.get('incremental_updates', {})
        current_ver_str = str(self.current_version)
        
        if current_ver_str in incremental_updates:
            # 有针对当前版本的增量更新
            return 'incremental'
        else:
            # 需要完整更新
            return 'full'
            
    def _download_incremental_update(self, update_info: Dict, 
                                    progress_callback=None) -> Optional[Path]:
        """下载增量更新包"""
        incremental_updates = update_info.get('incremental_updates', {})
        current_ver_str = str(self.current_version)
        
        if current_ver_str not in incremental_updates:
            return None
            
        update_package = incremental_updates[current_ver_str]
        download_url = update_package['url']
        expected_hash = update_package.get('sha256')
        file_size = update_package.get('size', 0)
        
        # 下载到临时文件
        temp_file = self.config_dir / f"update_{update_info['version']}_incremental.zip"
        
        try:
            # 下载文件
            response = urllib.request.urlopen(download_url, timeout=30)
            total_size = int(response.headers.get('Content-Length', file_size))
            
            downloaded = 0
            block_size = 8192
            
            with open(temp_file, 'wb') as f:
                while True:
                    chunk = response.read(block_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback and total_size > 0:
                        progress = int(downloaded * 100 / total_size)
                        progress_callback(progress, downloaded, total_size)
                        
            # 验证文件完整性
            if expected_hash:
                actual_hash = self._calculate_file_hash(temp_file)
                if actual_hash != expected_hash:
                    temp_file.unlink()
                    raise ValueError("文件校验失败，可能已损坏")
                    
            return temp_file
            
        except Exception as e:
            print(f"下载增量更新失败: {e}")
            if temp_file.exists():
                temp_file.unlink()
            return None
            
    def _download_full_update(self, update_info: Dict, 
                             progress_callback=None) -> Optional[Path]:
        """下载完整更新包"""
        download_url = update_info['download_url']
        file_size = update_info.get('size', 0)
        expected_hash = update_info.get('sha256')
        
        # 下载到临时文件
        temp_file = self.config_dir / f"update_{update_info['version']}_full.zip"
        
        try:
            # 使用cdn_selector选择最快的下载源
            from cdn_selector import CDNSelector
            selector = CDNSelector()
            
            # 如果有多个下载URL，选择最快的
            if isinstance(download_url, list):
                download_urls = selector.select_best_cdn(download_url)
                download_url = download_urls[0]
                
            # 下载文件
            response = urllib.request.urlopen(download_url, timeout=30)
            total_size = int(response.headers.get('Content-Length', file_size))
            
            downloaded = 0
            block_size = 8192
            
            with open(temp_file, 'wb') as f:
                while True:
                    chunk = response.read(block_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback and total_size > 0:
                        progress = int(downloaded * 100 / total_size)
                        progress_callback(progress, downloaded, total_size)
                        
            # 验证文件完整性
            if expected_hash:
                actual_hash = self._calculate_file_hash(temp_file)
                if actual_hash != expected_hash:
                    temp_file.unlink()
                    raise ValueError("文件校验失败")
                    
            return temp_file
            
        except Exception as e:
            print(f"下载完整更新失败: {e}")
            if temp_file.exists():
                temp_file.unlink()
            return None
            
    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件SHA256哈希"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
        
    def backup_current_version(self) -> Optional[Path]:
        """备份当前版本"""
        backup_name = f"backup_{self.current_version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        try:
            # 备份关键文件
            files_to_backup = [
                "SmartEmailSender.py",
                "version.json",
                "settings.json",
                "field_mapping_config.json"
            ]
            
            for file_name in files_to_backup:
                src_file = self.app_dir / file_name
                if src_file.exists():
                    shutil.copy2(src_file, backup_path / file_name)
                    
            # 备份src目录
            src_dir = self.app_dir / "src"
            if src_dir.exists():
                shutil.copytree(src_dir, backup_path / "src", dirs_exist_ok=True)
                
            return backup_path
            
        except Exception as e:
            print(f"备份失败: {e}")
            if backup_path.exists():
                shutil.rmtree(backup_path)
            return None
            
    def apply_update(self, update_file: Path, update_info: Dict) -> bool:
        """
        应用更新
        """
        try:
            # 1. 创建备份
            backup_path = self.backup_current_version()
            if not backup_path:
                print("创建备份失败，取消更新")
                return False
                
            # 2. 解压更新文件
            temp_extract_dir = self.config_dir / "temp_update"
            if temp_extract_dir.exists():
                shutil.rmtree(temp_extract_dir)
            temp_extract_dir.mkdir()
            
            with zipfile.ZipFile(update_file, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_dir)
                
            # 3. 应用更新
            update_type = self._determine_update_type(update_info)
            
            if update_type == 'incremental':
                # 增量更新 - 只替换改变的文件
                success = self._apply_incremental_update(temp_extract_dir)
            else:
                # 完整更新 - 替换所有文件
                success = self._apply_full_update(temp_extract_dir)
                
            if success:
                # 4. 更新版本信息
                self._save_version_info(update_info['version'], update_info)
                
                # 5. 清理临时文件
                shutil.rmtree(temp_extract_dir)
                update_file.unlink()
                
                return True
            else:
                # 更新失败，恢复备份
                self.restore_backup(backup_path)
                return False
                
        except Exception as e:
            print(f"应用更新失败: {e}")
            # 尝试恢复备份
            if backup_path and backup_path.exists():
                self.restore_backup(backup_path)
            return False
            
    def _apply_incremental_update(self, update_dir: Path) -> bool:
        """应用增量更新"""
        try:
            # 读取更新清单
            manifest_file = update_dir / "update_manifest.json"
            if not manifest_file.exists():
                return False
                
            with open(manifest_file, 'r') as f:
                manifest = json.load(f)
                
            # 处理每个更新项
            for item in manifest['updates']:
                action = item['action']
                file_path = item['path']
                
                if action == 'add' or action == 'update':
                    # 添加或更新文件
                    src_file = update_dir / file_path
                    dst_file = self.app_dir / file_path
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, dst_file)
                    
                elif action == 'delete':
                    # 删除文件
                    dst_file = self.app_dir / file_path
                    if dst_file.exists():
                        dst_file.unlink()
                        
            return True
            
        except Exception as e:
            print(f"应用增量更新失败: {e}")
            return False
            
    def _apply_full_update(self, update_dir: Path) -> bool:
        """应用完整更新"""
        try:
            # 复制所有文件
            for item in update_dir.iterdir():
                if item.name in ['.DS_Store', 'Thumbs.db']:
                    continue
                    
                dst_path = self.app_dir / item.name
                
                if item.is_dir():
                    if dst_path.exists():
                        shutil.rmtree(dst_path)
                    shutil.copytree(item, dst_path)
                else:
                    shutil.copy2(item, dst_path)
                    
            return True
            
        except Exception as e:
            print(f"应用完整更新失败: {e}")
            return False
            
    def restore_backup(self, backup_path: Path) -> bool:
        """恢复备份"""
        try:
            # 恢复所有备份的文件
            for item in backup_path.iterdir():
                dst_path = self.app_dir / item.name
                
                if item.is_dir():
                    if dst_path.exists():
                        shutil.rmtree(dst_path)
                    shutil.copytree(item, dst_path)
                else:
                    shutil.copy2(item, dst_path)
                    
            return True
            
        except Exception as e:
            print(f"恢复备份失败: {e}")
            return False
            
    def cleanup_old_backups(self, keep_count: int = 3):
        """清理旧的备份，只保留最近的几个"""
        backups = sorted(self.backup_dir.glob("backup_*"), 
                        key=lambda p: p.stat().st_mtime, 
                        reverse=True)
        
        for backup in backups[keep_count:]:
            try:
                shutil.rmtree(backup)
            except:
                pass
                
    def restart_application(self):
        """重启应用程序"""
        if sys.platform == 'darwin':
            # macOS
            if hasattr(sys, '_MEIPASS'):
                # 打包后的应用
                app_path = Path(sys.executable).parent.parent.parent
                subprocess.Popen(['open', str(app_path)])
            else:
                # 开发环境
                subprocess.Popen([sys.executable] + sys.argv)
                
        elif sys.platform == 'win32':
            # Windows
            subprocess.Popen([sys.executable] + sys.argv)
            
        else:
            # Linux
            subprocess.Popen([sys.executable] + sys.argv)
            
        # 退出当前进程
        sys.exit(0)