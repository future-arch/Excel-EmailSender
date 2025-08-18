#!/usr/bin/env python3
"""
SmartEmailSender 日志收集器
自动收集应用运行日志和错误信息
"""

import os
import sys
import json
import logging
import traceback
from datetime import datetime, timedelta
from pathlib import Path
import threading
import queue


class LogCollector:
    def __init__(self):
        self.logs_dir = "logs"
        self.max_log_size = 10 * 1024 * 1024  # 10MB
        self.max_log_files = 5
        self.log_queue = queue.Queue()
        self.setup_logging()
        
    def setup_logging(self):
        """初始化日志系统"""
        # 创建日志目录
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # 设置日志格式
        log_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 应用日志
        self.app_logger = logging.getLogger('SmartEmailSender')
        self.app_logger.setLevel(logging.INFO)
        
        # 轮转日志处理器
        from logging.handlers import RotatingFileHandler
        app_handler = RotatingFileHandler(
            os.path.join(self.logs_dir, 'smartemailsender.log'),
            maxBytes=self.max_log_size,
            backupCount=self.max_log_files,
            encoding='utf-8'
        )
        app_handler.setFormatter(log_format)
        self.app_logger.addHandler(app_handler)
        
        # 错误日志
        self.error_logger = logging.getLogger('SmartEmailSender.Error')
        self.error_logger.setLevel(logging.ERROR)
        
        error_handler = RotatingFileHandler(
            os.path.join(self.logs_dir, 'errors.log'),
            maxBytes=self.max_log_size,
            backupCount=self.max_log_files,
            encoding='utf-8'
        )
        error_handler.setFormatter(log_format)
        self.error_logger.addHandler(error_handler)
        
        # 邮件发送日志
        self.mail_logger = logging.getLogger('SmartEmailSender.Mail')
        self.mail_logger.setLevel(logging.INFO)
        
        mail_handler = RotatingFileHandler(
            os.path.join(self.logs_dir, 'mail_operations.log'),
            maxBytes=self.max_log_size,
            backupCount=self.max_log_files,
            encoding='utf-8'
        )
        mail_handler.setFormatter(log_format)
        self.mail_logger.addHandler(mail_handler)
        
        # 性能日志
        self.perf_logger = logging.getLogger('SmartEmailSender.Performance')
        self.perf_logger.setLevel(logging.INFO)
        
        perf_handler = RotatingFileHandler(
            os.path.join(self.logs_dir, 'performance.log'),
            maxBytes=self.max_log_size,
            backupCount=self.max_log_files,
            encoding='utf-8'
        )
        perf_handler.setFormatter(log_format)
        self.perf_logger.addHandler(perf_handler)
        
        print(f"✅ 日志系统已初始化，日志保存在: {os.path.abspath(self.logs_dir)}")
    
    def log_app_event(self, message, level='info'):
        """记录应用事件"""
        getattr(self.app_logger, level.lower())(message)
    
    def log_error(self, error, context=""):
        """记录错误信息"""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'context': context,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc()
        }
        
        self.error_logger.error(json.dumps(error_info, ensure_ascii=False))
    
    def log_mail_operation(self, operation, recipient=None, success=True, details=None):
        """记录邮件操作"""
        mail_info = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'recipient': recipient,
            'success': success,
            'details': details or {}
        }
        
        self.mail_logger.info(json.dumps(mail_info, ensure_ascii=False))
    
    def log_performance(self, operation, duration, additional_info=None):
        """记录性能信息"""
        perf_info = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'duration_seconds': duration,
            'additional_info': additional_info or {}
        }
        
        self.perf_logger.info(json.dumps(perf_info, ensure_ascii=False))
    
    def get_recent_logs(self, hours=24):
        """获取最近的日志"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_logs = {
            'app_logs': [],
            'errors': [],
            'mail_operations': [],
            'performance': []
        }
        
        log_files = {
            'app_logs': 'smartemailsender.log',
            'errors': 'errors.log',
            'mail_operations': 'mail_operations.log',
            'performance': 'performance.log'
        }
        
        for log_type, filename in log_files.items():
            filepath = os.path.join(self.logs_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                try:
                                    # 检查时间戳
                                    if line.startswith('20'):  # 假设是2000年后的日志
                                        timestamp_str = line.split(' - ')[0]
                                        log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                        if log_time >= cutoff_time:
                                            recent_logs[log_type].append(line.strip())
                                except:
                                    # 如果解析失败，仍然包含这行
                                    recent_logs[log_type].append(line.strip())
                except Exception as e:
                    recent_logs[log_type].append(f"读取日志失败: {e}")
        
        return recent_logs
    
    def export_logs_for_support(self, output_dir):
        """导出日志用于技术支持"""
        print(f"📋 导出日志到: {output_dir}")
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 复制所有日志文件
        import shutil
        import glob
        
        log_files = glob.glob(os.path.join(self.logs_dir, "*.log*"))
        
        for log_file in log_files:
            try:
                dest_file = os.path.join(output_dir, os.path.basename(log_file))
                shutil.copy2(log_file, dest_file)
                print(f"  ✅ 复制日志: {os.path.basename(log_file)}")
            except Exception as e:
                print(f"  ❌ 复制失败 {log_file}: {e}")
        
        # 生成日志摘要
        summary_file = os.path.join(output_dir, "log_summary.json")
        
        try:
            recent_logs = self.get_recent_logs(72)  # 最近3天
            
            summary = {
                'export_time': datetime.now().isoformat(),
                'log_directory': os.path.abspath(self.logs_dir),
                'total_log_files': len(log_files),
                'recent_errors_count': len(recent_logs['errors']),
                'recent_mail_operations_count': len(recent_logs['mail_operations']),
                'log_files_exported': [os.path.basename(f) for f in log_files]
            }
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            print(f"  ✅ 生成摘要: log_summary.json")
            
        except Exception as e:
            print(f"  ❌ 生成摘要失败: {e}")
    
    def cleanup_old_logs(self, days=30):
        """清理旧日志"""
        print(f"🧹 清理 {days} 天前的日志...")
        
        cutoff_time = datetime.now() - timedelta(days=days)
        
        for root, dirs, files in os.walk(self.logs_dir):
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if file_time < cutoff_time:
                        os.remove(filepath)
                        print(f"  🗑️ 删除旧日志: {file}")
                except Exception as e:
                    print(f"  ❌ 删除失败 {file}: {e}")


class CrashReporter:
    """崩溃报告器"""
    
    def __init__(self, log_collector):
        self.log_collector = log_collector
        self.crash_dir = "crash_reports"
        os.makedirs(self.crash_dir, exist_ok=True)
    
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """处理未捕获的异常"""
        if issubclass(exc_type, KeyboardInterrupt):
            # 用户中断，不记录为崩溃
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # 生成崩溃报告
        crash_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        crash_file = os.path.join(self.crash_dir, f"crash_{crash_id}.json")
        
        crash_info = {
            'crash_id': crash_id,
            'timestamp': datetime.now().isoformat(),
            'exception_type': exc_type.__name__,
            'exception_message': str(exc_value),
            'traceback': traceback.format_exception(exc_type, exc_value, exc_traceback),
            'python_version': sys.version,
            'platform': sys.platform
        }
        
        try:
            with open(crash_file, 'w', encoding='utf-8') as f:
                json.dump(crash_info, f, ensure_ascii=False, indent=2)
            
            print(f"\n💥 程序崩溃！崩溃报告已保存到: {crash_file}")
            print("请将此文件发送给技术支持团队。")
            
            # 也记录到错误日志
            self.log_collector.log_error(exc_value, "程序崩溃")
            
        except Exception as e:
            print(f"❌ 保存崩溃报告失败: {e}")
        
        # 调用原始异常处理器
        sys.__excepthook__(exc_type, exc_value, exc_traceback)


# 全局日志收集器实例
_log_collector = None

def get_log_collector():
    """获取全局日志收集器实例"""
    global _log_collector
    if _log_collector is None:
        _log_collector = LogCollector()
        
        # 设置崩溃报告器
        crash_reporter = CrashReporter(_log_collector)
        sys.excepthook = crash_reporter.handle_exception
    
    return _log_collector


# 便捷函数
def log_info(message):
    """记录信息"""
    get_log_collector().log_app_event(message, 'info')

def log_warning(message):
    """记录警告"""
    get_log_collector().log_app_event(message, 'warning')

def log_error(error, context=""):
    """记录错误"""
    get_log_collector().log_error(error, context)

def log_mail_sent(recipient, success=True, details=None):
    """记录邮件发送"""
    get_log_collector().log_mail_operation('send', recipient, success, details)

def log_performance(operation, duration, info=None):
    """记录性能"""
    get_log_collector().log_performance(operation, duration, info)


if __name__ == "__main__":
    # 测试日志系统
    print("🧪 测试日志收集系统...")
    
    collector = get_log_collector()
    
    # 测试各种日志
    log_info("程序启动")
    log_warning("这是一个警告测试")
    log_mail_sent("test@example.com", True, {"subject": "测试邮件"})
    log_performance("邮件发送", 1.23, {"recipients": 1})
    
    try:
        # 测试错误记录
        raise ValueError("这是一个测试错误")
    except Exception as e:
        log_error(e, "测试错误记录")
    
    print("✅ 日志测试完成")
    
    # 显示最近日志
    recent = collector.get_recent_logs(1)
    print(f"\n📋 最近1小时日志摘要:")
    print(f"  应用日志: {len(recent['app_logs'])} 条")
    print(f"  错误日志: {len(recent['errors'])} 条")
    print(f"  邮件日志: {len(recent['mail_operations'])} 条")
    print(f"  性能日志: {len(recent['performance'])} 条")