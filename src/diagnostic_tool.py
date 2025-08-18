#!/usr/bin/env python3
"""
SmartEmailSender 诊断工具
用于收集系统信息、检测问题并生成诊断报告
"""

import sys
import os
import platform
import subprocess
import json
import traceback
from datetime import datetime
from pathlib import Path

class SmartEmailSenderDiagnostic:
    def __init__(self):
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "system_info": {},
            "python_info": {},
            "dependencies": {},
            "environment": {},
            "errors": [],
            "recommendations": []
        }
    
    def run_full_diagnostic(self):
        """运行完整诊断"""
        print("SmartEmailSender 诊断工具")
        print("=" * 50)
        
        self.collect_system_info()
        self.collect_python_info()
        self.check_dependencies()
        self.check_environment_config()
        self.check_permissions()
        self.run_import_tests()
        
        # 生成报告
        report_file = self.generate_report()
        print(f"\n✅ 诊断完成！报告已保存到: {report_file}")
        
        return report_file
    
    def collect_system_info(self):
        """收集系统信息"""
        print("📊 收集系统信息...")
        
        try:
            self.report["system_info"] = {
                "platform": platform.platform(),
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "architecture": platform.architecture(),
                "hostname": platform.node(),
                "memory_mb": self._get_memory_info(),
                "disk_space_gb": self._get_disk_space()
            }
        except Exception as e:
            self.report["errors"].append(f"系统信息收集失败: {e}")
    
    def collect_python_info(self):
        """收集Python信息"""
        print("🐍 检查Python环境...")
        
        try:
            self.report["python_info"] = {
                "version": sys.version,
                "executable": sys.executable,
                "path": sys.path,
                "prefix": sys.prefix,
                "base_prefix": getattr(sys, 'base_prefix', sys.prefix),
                "real_prefix": getattr(sys, 'real_prefix', None),
                "is_venv": hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
            }
        except Exception as e:
            self.report["errors"].append(f"Python信息收集失败: {e}")
    
    def check_dependencies(self):
        """检查依赖包"""
        print("📦 检查依赖包...")
        
        required_packages = [
            "PySide6", "pandas", "requests", "msal", 
            "jinja2", "python-dotenv", "openpyxl"
        ]
        
        for package in required_packages:
            try:
                if package == "python-dotenv":
                    import dotenv
                    version = getattr(dotenv, '__version__', 'unknown')
                else:
                    module = __import__(package)
                    version = getattr(module, '__version__', 'unknown')
                
                self.report["dependencies"][package] = {
                    "status": "✅ 已安装",
                    "version": version,
                    "location": getattr(module, '__file__', 'unknown')
                }
                print(f"  ✅ {package}: {version}")
                
            except ImportError as e:
                self.report["dependencies"][package] = {
                    "status": "❌ 缺失",
                    "error": str(e)
                }
                self.report["errors"].append(f"缺少依赖包: {package}")
                print(f"  ❌ {package}: 未安装")
    
    def check_environment_config(self):
        """检查环境配置"""
        print("⚙️ 检查配置文件...")
        
        current_dir = os.getcwd()
        env_file = os.path.join(current_dir, '.env')
        
        if os.path.exists(env_file):
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    env_content = f.read()
                
                # 检查必要的配置项（不显示实际值）
                required_vars = ['AZURE_CLIENT_ID', 'AZURE_TENANT_ID', 'TEST_SELF_EMAIL']
                missing_vars = []
                
                for var in required_vars:
                    if var not in env_content:
                        missing_vars.append(var)
                
                self.report["environment"] = {
                    "env_file_exists": True,
                    "env_file_path": env_file,
                    "missing_variables": missing_vars,
                    "config_complete": len(missing_vars) == 0
                }
                
                if missing_vars:
                    self.report["errors"].append(f"缺少环境变量: {', '.join(missing_vars)}")
                    print(f"  ❌ 缺少配置: {', '.join(missing_vars)}")
                else:
                    print("  ✅ 配置文件完整")
                    
            except Exception as e:
                self.report["errors"].append(f"读取配置文件失败: {e}")
                
        else:
            self.report["environment"] = {
                "env_file_exists": False,
                "env_file_path": env_file
            }
            self.report["errors"].append("未找到.env配置文件")
            print("  ❌ 未找到.env文件")
    
    def check_permissions(self):
        """检查文件权限"""
        print("🔐 检查文件权限...")
        
        current_dir = os.getcwd()
        
        # 检查当前目录权限
        permissions = {
            "current_dir_readable": os.access(current_dir, os.R_OK),
            "current_dir_writable": os.access(current_dir, os.W_OK),
            "current_dir_executable": os.access(current_dir, os.X_OK)
        }
        
        self.report["permissions"] = permissions
        
        if not all(permissions.values()):
            self.report["errors"].append("目录权限不足")
            print("  ❌ 目录权限不足")
        else:
            print("  ✅ 权限正常")
    
    def run_import_tests(self):
        """运行导入测试"""
        print("🧪 运行导入测试...")
        
        import_tests = {}
        
        # 测试PySide6组件
        pyside_components = [
            "PySide6.QtWidgets",
            "PySide6.QtCore", 
            "PySide6.QtGui",
            "PySide6.QtWebEngineWidgets"
        ]
        
        for component in pyside_components:
            try:
                __import__(component)
                import_tests[component] = "✅ 成功"
                print(f"  ✅ {component}")
            except Exception as e:
                import_tests[component] = f"❌ 失败: {e}"
                self.report["errors"].append(f"导入失败: {component} - {e}")
                print(f"  ❌ {component}: {e}")
        
        # 测试应用模块
        app_modules = ["ui.main_window", "graph.auth", "graph.api"]
        
        for module in app_modules:
            try:
                # 尝试多种导入方式
                try:
                    __import__(module)
                except ImportError:
                    try:
                        __import__(f"src.{module}")
                    except ImportError:
                        # 添加src路径再试
                        src_path = os.path.join(os.getcwd(), 'src')
                        if src_path not in sys.path:
                            sys.path.insert(0, src_path)
                        __import__(module)
                
                import_tests[module] = "✅ 成功"
                print(f"  ✅ {module}")
                
            except Exception as e:
                import_tests[module] = f"❌ 失败: {e}"
                self.report["errors"].append(f"应用模块导入失败: {module} - {e}")
                print(f"  ❌ {module}: {e}")
        
        self.report["import_tests"] = import_tests
    
    def _get_memory_info(self):
        """获取内存信息"""
        try:
            if platform.system() == "Darwin":  # macOS
                result = subprocess.run(['sysctl', 'hw.memsize'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    memory_bytes = int(result.stdout.split(':')[1].strip())
                    return memory_bytes // (1024 * 1024)  # Convert to MB
            elif platform.system() == "Linux":
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if line.startswith('MemTotal:'):
                            return int(line.split()[1]) // 1024  # Convert KB to MB
        except:
            pass
        return "unknown"
    
    def _get_disk_space(self):
        """获取磁盘空间"""
        try:
            statvfs = os.statvfs('.')
            free_bytes = statvfs.f_frsize * statvfs.f_available
            return free_bytes // (1024 * 1024 * 1024)  # Convert to GB
        except:
            return "unknown"
    
    def generate_recommendations(self):
        """生成修复建议"""
        if self.report["errors"]:
            self.report["recommendations"].append("🔧 发现以下问题需要修复:")
            
            for error in self.report["errors"]:
                if "缺少依赖包" in error:
                    package = error.split(": ")[1]
                    self.report["recommendations"].append(
                        f"  • 安装缺失的包: pip install {package}"
                    )
                elif "未找到.env" in error:
                    self.report["recommendations"].append(
                        "  • 创建.env配置文件，参考.env.template"
                    )
                elif "权限不足" in error:
                    self.report["recommendations"].append(
                        "  • 检查目录权限，确保有读写执行权限"
                    )
                elif "导入失败" in error:
                    self.report["recommendations"].append(
                        "  • 重新安装Python依赖或检查PYTHONPATH"
                    )
        else:
            self.report["recommendations"].append("✅ 未发现严重问题，环境配置正常")
    
    def generate_report(self):
        """生成诊断报告"""
        self.generate_recommendations()
        
        # 创建报告文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"diagnostic_report_{timestamp}.json"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.report, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 保存报告失败: {e}")
            return None
        
        # 生成文本版本
        text_report_file = f"diagnostic_report_{timestamp}.txt"
        self.generate_text_report(text_report_file)
        
        return report_file
    
    def generate_text_report(self, filename):
        """生成易读的文本报告"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("SmartEmailSender 诊断报告\n")
                f.write("=" * 50 + "\n")
                f.write(f"生成时间: {self.report['timestamp']}\n\n")
                
                # 系统信息
                f.write("📊 系统信息:\n")
                for key, value in self.report['system_info'].items():
                    f.write(f"  {key}: {value}\n")
                f.write("\n")
                
                # Python信息
                f.write("🐍 Python环境:\n")
                f.write(f"  版本: {self.report['python_info'].get('version', 'unknown')}\n")
                f.write(f"  可执行文件: {self.report['python_info'].get('executable', 'unknown')}\n")
                f.write(f"  虚拟环境: {self.report['python_info'].get('is_venv', False)}\n\n")
                
                # 依赖检查
                f.write("📦 依赖包状态:\n")
                for pkg, info in self.report['dependencies'].items():
                    f.write(f"  {pkg}: {info['status']}")
                    if 'version' in info:
                        f.write(f" (版本: {info['version']})")
                    f.write("\n")
                f.write("\n")
                
                # 错误汇总
                if self.report['errors']:
                    f.write("❌ 发现的问题:\n")
                    for error in self.report['errors']:
                        f.write(f"  • {error}\n")
                    f.write("\n")
                
                # 修复建议
                f.write("🔧 修复建议:\n")
                for rec in self.report['recommendations']:
                    f.write(f"{rec}\n")
                    
        except Exception as e:
            print(f"❌ 生成文本报告失败: {e}")

def main():
    """主函数"""
    diagnostic = SmartEmailSenderDiagnostic()
    report_file = diagnostic.run_full_diagnostic()
    
    if report_file:
        print(f"\n📋 诊断报告已生成:")
        print(f"   JSON格式: {report_file}")
        print(f"   文本格式: {report_file.replace('.json', '.txt')}")
        print("\n💡 请将这些文件发送给技术支持团队以获得帮助。")

if __name__ == "__main__":
    main()