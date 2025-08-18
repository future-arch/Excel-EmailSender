#!/usr/bin/env python3
"""
SmartEmailSender 远程支持工具
生成支持包，包含所有必要的诊断信息
"""

import os
import sys
import zipfile
import shutil
import json
from datetime import datetime
from pathlib import Path

class RemoteSupportPackage:
    def __init__(self):
        self.package_dir = None
        self.support_info = {
            "created_at": datetime.now().isoformat(),
            "user_info": {},
            "incident_details": {}
        }
    
    def create_support_package(self):
        """创建完整的支持包"""
        print("🔧 SmartEmailSender 远程支持包生成器")
        print("=" * 50)
        
        # 收集用户信息
        self.collect_user_info()
        
        # 收集问题描述
        self.collect_incident_details()
        
        # 创建支持包目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.package_dir = f"SmartEmailSender_Support_{timestamp}"
        os.makedirs(self.package_dir, exist_ok=True)
        
        # 运行诊断
        self.run_diagnostic()
        
        # 收集日志文件
        self.collect_logs()
        
        # 收集配置文件（安全版本）
        self.collect_config_info()
        
        # 收集环境信息
        self.collect_environment_snapshot()
        
        # 生成支持信息文件
        self.generate_support_info()
        
        # 创建压缩包
        zip_file = self.create_zip_package()
        
        # 清理临时目录
        shutil.rmtree(self.package_dir)
        
        print(f"\n✅ 支持包已创建: {zip_file}")
        print("\n📧 请将此文件发送给技术支持:")
        print(f"   文件名: {zip_file}")
        print(f"   大小: {self.get_file_size(zip_file)}")
        print("\n⚠️  注意: 此文件包含系统信息但不包含敏感数据")
        
        return zip_file
    
    def collect_user_info(self):
        """收集用户信息"""
        print("\n👤 请提供以下信息以便更好地协助您:")
        
        self.support_info["user_info"] = {
            "name": input("您的姓名: ").strip(),
            "email": input("您的邮箱: ").strip(),
            "department": input("部门: ").strip(),
            "contact": input("联系电话 (可选): ").strip()
        }
    
    def collect_incident_details(self):
        """收集问题详情"""
        print("\n🐛 请描述遇到的问题:")
        
        self.support_info["incident_details"] = {
            "problem_summary": input("问题简述: ").strip(),
            "steps_to_reproduce": input("重现步骤 (可选): ").strip(),
            "error_message": input("错误信息 (如有): ").strip(),
            "when_occurred": input("何时发生 (可选): ").strip(),
            "frequency": input("发生频率 (总是/有时/偶尔): ").strip() or "未知"
        }
    
    def run_diagnostic(self):
        """运行诊断工具"""
        print("\n🔍 正在运行系统诊断...")
        
        try:
            # 导入并运行诊断工具
            from diagnostic_tool import SmartEmailSenderDiagnostic
            
            diagnostic = SmartEmailSenderDiagnostic()
            
            # 修改诊断工具以在我们的目录中生成报告
            original_cwd = os.getcwd()
            os.chdir(self.package_dir)
            
            try:
                report_file = diagnostic.run_full_diagnostic()
                if report_file:
                    print(f"  ✅ 诊断报告已生成: {report_file}")
            finally:
                os.chdir(original_cwd)
                
        except Exception as e:
            print(f"  ❌ 诊断运行失败: {e}")
            # 创建错误报告
            with open(os.path.join(self.package_dir, "diagnostic_error.txt"), 'w') as f:
                f.write(f"诊断工具运行失败: {e}\n")
                f.write(f"Python版本: {sys.version}\n")
                f.write(f"当前目录: {os.getcwd()}\n")
    
    def collect_logs(self):
        """收集日志文件"""
        print("📋 收集日志文件...")
        
        # 查找可能的日志文件
        log_patterns = [
            "*.log", "SmartEmailSender*.log", "error*.log", 
            "debug*.log", "application*.log"
        ]
        
        logs_dir = os.path.join(self.package_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        found_logs = False
        for pattern in log_patterns:
            import glob
            for log_file in glob.glob(pattern):
                try:
                    shutil.copy2(log_file, logs_dir)
                    found_logs = True
                    print(f"  ✅ 收集日志: {log_file}")
                except Exception as e:
                    print(f"  ❌ 复制日志失败 {log_file}: {e}")
        
        if not found_logs:
            with open(os.path.join(logs_dir, "no_logs_found.txt"), 'w') as f:
                f.write("未找到应用日志文件\n")
                f.write(f"搜索位置: {os.getcwd()}\n")
                f.write(f"搜索模式: {', '.join(log_patterns)}\n")
    
    def collect_config_info(self):
        """收集配置信息（安全版本）"""
        print("⚙️ 收集配置信息...")
        
        config_dir = os.path.join(self.package_dir, "config")
        os.makedirs(config_dir, exist_ok=True)
        
        # 检查.env文件（不复制敏感内容）
        if os.path.exists('.env'):
            with open('.env', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 创建安全版本的配置信息
            safe_config = []
            for line in content.split('\n'):
                if '=' in line and not line.strip().startswith('#'):
                    key = line.split('=')[0].strip()
                    safe_config.append(f"{key}=<隐藏>")
                else:
                    safe_config.append(line)
            
            with open(os.path.join(config_dir, "env_structure.txt"), 'w') as f:
                f.write("配置文件结构 (敏感信息已隐藏):\n")
                f.write('\n'.join(safe_config))
        
        # 复制其他非敏感配置文件
        config_files = ['settings.json', 'field_mapping_config.json']
        for config_file in config_files:
            if os.path.exists(config_file):
                try:
                    shutil.copy2(config_file, config_dir)
                    print(f"  ✅ 收集配置: {config_file}")
                except Exception as e:
                    print(f"  ❌ 复制配置失败 {config_file}: {e}")
    
    def collect_environment_snapshot(self):
        """收集环境快照"""
        print("📸 创建环境快照...")
        
        env_dir = os.path.join(self.package_dir, "environment")
        os.makedirs(env_dir, exist_ok=True)
        
        # 收集Python环境信息
        try:
            import subprocess
            
            # pip list
            result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                with open(os.path.join(env_dir, "pip_list.txt"), 'w') as f:
                    f.write(result.stdout)
        except Exception as e:
            with open(os.path.join(env_dir, "pip_error.txt"), 'w') as f:
                f.write(f"获取pip信息失败: {e}")
        
        # 目录结构
        try:
            dir_structure = []
            for root, dirs, files in os.walk('.'):
                # 跳过某些目录
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['venv', '__pycache__', 'node_modules']]
                level = root.replace('.', '').count(os.sep)
                indent = ' ' * 2 * level
                dir_structure.append(f"{indent}{os.path.basename(root)}/")
                subindent = ' ' * 2 * (level + 1)
                for file in files[:10]:  # 限制文件数量
                    if not file.startswith('.'):
                        dir_structure.append(f"{subindent}{file}")
                if len(files) > 10:
                    dir_structure.append(f"{subindent}... ({len(files)-10} more files)")
            
            with open(os.path.join(env_dir, "directory_structure.txt"), 'w') as f:
                f.write("目录结构:\n")
                f.write('\n'.join(dir_structure))
                
        except Exception as e:
            print(f"  ❌ 收集目录结构失败: {e}")
    
    def generate_support_info(self):
        """生成支持信息文件"""
        print("📝 生成支持信息...")
        
        support_file = os.path.join(self.package_dir, "support_info.json")
        
        try:
            with open(support_file, 'w', encoding='utf-8') as f:
                json.dump(self.support_info, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"  ❌ 生成支持信息失败: {e}")
        
        # 生成README
        readme_file = os.path.join(self.package_dir, "README.txt")
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write("SmartEmailSender 支持包\n")
            f.write("=" * 30 + "\n\n")
            f.write(f"生成时间: {self.support_info['created_at']}\n")
            f.write(f"用户: {self.support_info['user_info'].get('name', '未知')}\n")
            f.write(f"问题: {self.support_info['incident_details'].get('problem_summary', '未描述')}\n\n")
            f.write("包含文件:\n")
            f.write("- diagnostic_report_*.json: 系统诊断报告\n")
            f.write("- diagnostic_report_*.txt: 诊断报告（文本版）\n")
            f.write("- logs/: 应用日志文件\n")
            f.write("- config/: 配置文件信息\n")
            f.write("- environment/: 环境信息\n")
            f.write("- support_info.json: 用户报告的问题详情\n")
    
    def create_zip_package(self):
        """创建压缩包"""
        print("📦 创建压缩包...")
        
        zip_filename = f"{self.package_dir}.zip"
        
        try:
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(self.package_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        archive_path = os.path.relpath(file_path, os.path.dirname(self.package_dir))
                        zipf.write(file_path, archive_path)
            
            return zip_filename
            
        except Exception as e:
            print(f"  ❌ 创建压缩包失败: {e}")
            return None
    
    def get_file_size(self, filename):
        """获取文件大小"""
        try:
            size = os.path.getsize(filename)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        except:
            return "未知"

def main():
    """主函数"""
    try:
        support = RemoteSupportPackage()
        support.create_support_package()
    except KeyboardInterrupt:
        print("\n\n❌ 用户取消操作")
    except Exception as e:
        print(f"\n❌ 生成支持包时发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()