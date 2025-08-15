#!/usr/bin/env python3
"""
更新包生成工具
用于生成增量更新包和完整更新包
"""

import os
import json
import hashlib
import zipfile
import shutil
from pathlib import Path
from typing import Dict, List, Set
from datetime import datetime
import argparse

class UpdatePackageCreator:
    """更新包创建器"""
    
    def __init__(self, old_version: str, new_version: str):
        self.old_version = old_version
        self.new_version = new_version
        self.project_root = Path.cwd()
        self.src_dir = self.project_root / "src"
        self.output_dir = self.project_root / "updates"
        self.output_dir.mkdir(exist_ok=True)
        
    def calculate_file_hash(self, file_path: Path) -> str:
        """计算文件SHA256哈希"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
        
    def get_file_list(self, directory: Path) -> Dict[str, Dict]:
        """获取目录中所有文件的信息"""
        files_info = {}
        
        for file_path in directory.rglob("*"):
            if file_path.is_file() and not self._should_ignore_file(file_path):
                relative_path = file_path.relative_to(directory)
                files_info[str(relative_path)] = {
                    'hash': self.calculate_file_hash(file_path),
                    'size': file_path.stat().st_size,
                    'modified': file_path.stat().st_mtime
                }
                
        return files_info
        
    def _should_ignore_file(self, file_path: Path) -> bool:
        """判断是否应该忽略的文件"""
        ignore_patterns = [
            '.DS_Store', 'Thumbs.db', '.git', '__pycache__',
            '.pyc', '.pyo', '.pyd', 'token_cache.json',
            'settings.json'  # 用户配置文件不更新
        ]
        
        return any(pattern in str(file_path) for pattern in ignore_patterns)
        
    def compare_versions(self, old_files: Dict, new_files: Dict) -> Dict:
        """比较两个版本的差异"""
        changes = {
            'added': [],      # 新增文件
            'modified': [],   # 修改文件
            'deleted': []     # 删除文件
        }
        
        # 检查新增和修改的文件
        for file_path, info in new_files.items():
            if file_path not in old_files:
                changes['added'].append(file_path)
            elif old_files[file_path]['hash'] != info['hash']:
                changes['modified'].append(file_path)
                
        # 检查删除的文件
        for file_path in old_files:
            if file_path not in new_files:
                changes['deleted'].append(file_path)
                
        return changes
        
    def create_incremental_package(self, changes: Dict) -> Path:
        """创建增量更新包"""
        package_name = f"update_{self.old_version}_to_{self.new_version}_incremental.zip"
        package_path = self.output_dir / package_name
        
        # 创建更新清单
        manifest = {
            'from_version': self.old_version,
            'to_version': self.new_version,
            'created_at': datetime.now().isoformat(),
            'type': 'incremental',
            'updates': []
        }
        
        # 创建临时目录
        temp_dir = self.output_dir / "temp_incremental"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir()
        
        try:
            # 复制需要更新的文件
            for action, files in changes.items():
                for file_path in files:
                    update_item = {
                        'action': action,
                        'path': file_path
                    }
                    
                    if action in ['added', 'modified']:
                        # 复制文件到临时目录
                        src_file = self.src_dir / file_path
                        dst_file = temp_dir / file_path
                        dst_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_file, dst_file)
                        
                        update_item['size'] = src_file.stat().st_size
                        update_item['hash'] = self.calculate_file_hash(src_file)
                    
                    manifest['updates'].append(update_item)
                    
            # 保存更新清单
            manifest_file = temp_dir / "update_manifest.json"
            with open(manifest_file, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
                
            # 创建ZIP包
            with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in temp_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(temp_dir)
                        zipf.write(file_path, arcname)
                        
        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir)
            
        return package_path
        
    def create_full_package(self) -> Path:
        """创建完整更新包"""
        package_name = f"update_{self.new_version}_full.zip"
        package_path = self.output_dir / package_name
        
        # 创建ZIP包
        with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in self.src_dir.rglob("*"):
                if file_path.is_file() and not self._should_ignore_file(file_path):
                    arcname = file_path.relative_to(self.src_dir)
                    zipf.write(file_path, arcname)
                    
        return package_path
        
    def update_info_json(self, incremental_package: Path, full_package: Path, 
                        changelog: str = ""):
        """更新info.json文件"""
        info_file = self.output_dir / "update_info.json"
        
        # 计算包信息
        incremental_hash = self.calculate_file_hash(incremental_package)
        incremental_size = incremental_package.stat().st_size
        
        full_hash = self.calculate_file_hash(full_package)
        full_size = full_package.stat().st_size
        
        update_info = {
            "version": self.new_version,
            "release_date": datetime.now().strftime("%Y-%m-%d"),
            "changelog": changelog,
            "download_url": [
                # 这里需要替换为实际的CDN地址
                f"https://gitee.com/smartemailsender/app/releases/download/v{self.new_version}/{full_package.name}",
                f"https://github.com/smartemailsender/app/releases/download/v{self.new_version}/{full_package.name}",
            ],
            "size": full_size,
            "sha256": full_hash,
            "incremental_updates": {
                self.old_version: {
                    "url": f"https://gitee.com/smartemailsender/app/releases/download/v{self.new_version}/{incremental_package.name}",
                    "size": incremental_size,
                    "sha256": incremental_hash
                }
            }
        }
        
        # 如果已有info文件，合并增量更新信息
        if info_file.exists():
            with open(info_file, 'r', encoding='utf-8') as f:
                existing_info = json.load(f)
                
            # 保留其他版本的增量更新信息
            if 'incremental_updates' in existing_info:
                for version, info in existing_info['incremental_updates'].items():
                    if version != self.old_version:  # 避免重复
                        update_info['incremental_updates'][version] = info
                        
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(update_info, f, indent=2, ensure_ascii=False)
            
        return info_file
        
    def generate_release_notes(self, changes: Dict) -> str:
        """生成发布说明"""
        notes = []
        
        if changes['added']:
            notes.append(f"新增 {len(changes['added'])} 个文件:")
            for file_path in changes['added'][:5]:  # 只显示前5个
                notes.append(f"  + {file_path}")
            if len(changes['added']) > 5:
                notes.append(f"  ... 还有 {len(changes['added']) - 5} 个文件")
            notes.append("")
            
        if changes['modified']:
            notes.append(f"修改 {len(changes['modified'])} 个文件:")
            for file_path in changes['modified'][:5]:
                notes.append(f"  * {file_path}")
            if len(changes['modified']) > 5:
                notes.append(f"  ... 还有 {len(changes['modified']) - 5} 个文件")
            notes.append("")
            
        if changes['deleted']:
            notes.append(f"删除 {len(changes['deleted'])} 个文件:")
            for file_path in changes['deleted'][:5]:
                notes.append(f"  - {file_path}")
            if len(changes['deleted']) > 5:
                notes.append(f"  ... 还有 {len(changes['deleted']) - 5} 个文件")
                
        return "\n".join(notes)
        
    def create_update_packages(self, changelog: str = ""):
        """创建所有更新包"""
        print(f"正在创建从 {self.old_version} 到 {self.new_version} 的更新包...")
        
        # 获取当前版本的文件列表（模拟旧版本，实际应该从版本控制获取）
        print("分析文件差异...")
        current_files = self.get_file_list(self.src_dir)
        
        # 这里应该从版本控制系统或备份获取旧版本的文件列表
        # 为了演示，我们创建一个模拟的差异
        changes = {
            'added': ['new_feature.py', 'templates/new_template.html'],
            'modified': ['SmartEmailSender.py', 'updater.py', 'main_window.py'],
            'deleted': ['deprecated_module.py']
        }
        
        # 创建增量更新包
        print("创建增量更新包...")
        incremental_package = self.create_incremental_package(changes)
        print(f"增量更新包: {incremental_package}")
        
        # 创建完整更新包
        print("创建完整更新包...")
        full_package = self.create_full_package()
        print(f"完整更新包: {full_package}")
        
        # 生成自动发布说明（如果没有提供changelog）
        if not changelog:
            changelog = self.generate_release_notes(changes)
            
        # 更新info.json
        print("更新版本信息...")
        info_file = self.update_info_json(incremental_package, full_package, changelog)
        print(f"版本信息文件: {info_file}")
        
        print("\n" + "="*50)
        print("更新包创建完成！")
        print("="*50)
        print(f"增量更新包: {incremental_package.name}")
        print(f"  大小: {self._format_size(incremental_package.stat().st_size)}")
        print(f"完整更新包: {full_package.name}")
        print(f"  大小: {self._format_size(full_package.stat().st_size)}")
        print(f"版本信息: {info_file.name}")
        print("\n请将这些文件上传到您的CDN服务器")
        
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="创建SmartEmailSender更新包")
    parser.add_argument("--old-version", required=True, help="旧版本号 (如: 1.0.0)")
    parser.add_argument("--new-version", required=True, help="新版本号 (如: 1.1.0)")
    parser.add_argument("--changelog", default="", help="更新日志")
    
    args = parser.parse_args()
    
    creator = UpdatePackageCreator(args.old_version, args.new_version)
    creator.create_update_packages(args.changelog)


if __name__ == "__main__":
    main()