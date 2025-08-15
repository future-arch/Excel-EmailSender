#!/usr/bin/env python3
"""
CDN选择器 - 自动检测最快的下载源
"""

import time
import urllib.request
import urllib.error
import socket
import threading
from typing import List, Tuple, Optional
import json
from pathlib import Path

class CDNSelector:
    """智能选择最快的CDN镜像"""
    
    # 地区检测API
    GEO_DETECTION_APIS = [
        "http://ip-api.com/json",  # 国际
        "https://myip.ipip.net/json",  # 国内IPIP
        "http://ip.taobao.com/service/getIpInfo.php?ip=myip",  # 淘宝IP
    ]
    
    def __init__(self):
        self.location = None
        self.is_china = None
        self.cdn_speeds = {}
        self.cache_file = Path.home() / ".smartemailsender" / "cdn_cache.json"
        self._load_cache()
        
    def _load_cache(self):
        """加载CDN速度缓存"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
                    # 只使用24小时内的缓存
                    if time.time() - cache.get('timestamp', 0) < 86400:
                        self.cdn_speeds = cache.get('speeds', {})
                        self.location = cache.get('location')
                        self.is_china = cache.get('is_china')
            except:
                pass
                
    def _save_cache(self):
        """保存CDN速度缓存"""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump({
                    'timestamp': time.time(),
                    'speeds': self.cdn_speeds,
                    'location': self.location,
                    'is_china': self.is_china
                }, f)
        except:
            pass
            
    def detect_location(self) -> bool:
        """检测用户地理位置，返回是否在中国内地"""
        if self.is_china is not None:
            return self.is_china
            
        for api_url in self.GEO_DETECTION_APIS:
            try:
                with urllib.request.urlopen(api_url, timeout=5) as response:
                    data = json.loads(response.read().decode())
                    
                    # 解析不同API的响应格式
                    if 'country' in data:
                        country = data.get('country', '').upper()
                    elif 'countryCode' in data:
                        country = data.get('countryCode', '').upper()
                    elif 'data' in data and 'country_id' in data['data']:
                        country = data['data'].get('country_id', '').upper()
                    else:
                        continue
                        
                    # 检查是否在中国
                    self.is_china = country in ['CN', 'CHINA', '中国']
                    self.location = country
                    self._save_cache()
                    return self.is_china
                    
            except Exception as e:
                print(f"地理位置检测失败 ({api_url}): {e}")
                continue
                
        # 如果所有API都失败，通过测试连接判断
        return self._detect_by_connectivity()
        
    def _detect_by_connectivity(self) -> bool:
        """通过连接测试判断是否在中国内地"""
        # 测试是否能连接到Google（在中国内地通常不能）
        try:
            socket.create_connection(("www.google.com", 443), timeout=3)
            self.is_china = False
        except:
            # 不能连接Google，可能在中国
            try:
                # 测试是否能连接到百度（在中国内地通常可以）
                socket.create_connection(("www.baidu.com", 443), timeout=3)
                self.is_china = True
            except:
                # 都连不上，默认不在中国
                self.is_china = False
                
        self._save_cache()
        return self.is_china
        
    def test_cdn_speed(self, cdn_url: str, timeout: int = 5) -> Tuple[float, bool]:
        """
        测试CDN速度
        返回: (延迟ms, 是否可用)
        """
        # 检查缓存
        if cdn_url in self.cdn_speeds:
            cached = self.cdn_speeds[cdn_url]
            if time.time() - cached['timestamp'] < 3600:  # 1小时缓存
                return cached['latency'], cached['available']
                
        try:
            # 测试HEAD请求
            test_url = cdn_url + "test.txt"  # 假设有个小测试文件
            start_time = time.time()
            
            req = urllib.request.Request(test_url, method='HEAD')
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status == 200 or response.status == 404:
                    latency = (time.time() - start_time) * 1000
                    available = True
                else:
                    latency = 999999
                    available = False
                    
        except Exception as e:
            latency = 999999
            available = False
            
        # 缓存结果
        self.cdn_speeds[cdn_url] = {
            'latency': latency,
            'available': available,
            'timestamp': time.time()
        }
        self._save_cache()
        
        return latency, available
        
    def select_best_cdn(self, cdn_urls: List[str], 
                       show_progress: bool = True) -> List[str]:
        """
        选择最佳CDN顺序
        返回按速度排序的CDN列表
        """
        # 先检测地理位置
        is_china = self.detect_location()
        
        if show_progress:
            if is_china:
                print("检测到您在中国内地，优先使用国内镜像源...")
            else:
                print("检测到您在海外，优先使用国际镜像源...")
                
        # 根据地区重新排序CDN列表
        china_cdns = []
        international_cdns = []
        
        for url in cdn_urls:
            if any(domain in url for domain in ['gitee.com', 'aliyuncs.com', 
                                                 'myqcloud.com', '.cn/', 
                                                 'oss-cn-', 'cos.ap-']):
                china_cdns.append(url)
            else:
                international_cdns.append(url)
                
        # 根据地区优先级排序
        if is_china:
            ordered_cdns = china_cdns + international_cdns
        else:
            ordered_cdns = international_cdns + china_cdns
            
        # 测试前3个CDN的速度
        test_results = []
        test_threads = []
        
        def test_cdn(url, results):
            latency, available = self.test_cdn_speed(url)
            results.append((url, latency, available))
            
        # 并行测试
        for url in ordered_cdns[:5]:  # 只测试前5个
            thread = threading.Thread(target=test_cdn, args=(url, test_results))
            thread.start()
            test_threads.append(thread)
            
        # 等待测试完成（最多等待10秒）
        for thread in test_threads:
            thread.join(timeout=10)
            
        # 按延迟排序（可用的优先）
        test_results.sort(key=lambda x: (not x[2], x[1]))
        
        # 构建最终列表
        final_cdns = []
        tested_urls = set()
        
        # 先添加测试过的（按速度排序）
        for url, latency, available in test_results:
            if available:
                final_cdns.append(url)
                tested_urls.add(url)
                if show_progress:
                    print(f"  ✓ {self._get_cdn_name(url)}: {latency:.0f}ms")
            else:
                if show_progress:
                    print(f"  ✗ {self._get_cdn_name(url)}: 不可用")
                    
        # 添加未测试的
        for url in ordered_cdns:
            if url not in tested_urls:
                final_cdns.append(url)
                
        return final_cdns if final_cdns else cdn_urls
        
    def _get_cdn_name(self, url: str) -> str:
        """获取CDN的友好名称"""
        if 'gitee.com' in url:
            return "Gitee (码云)"
        elif 'aliyuncs.com' in url:
            return "阿里云 OSS"
        elif 'myqcloud.com' in url:
            return "腾讯云 COS"
        elif 'github.com' in url:
            return "GitHub"
        elif 'jsdelivr.net' in url:
            return "jsDelivr CDN"
        elif '.cn/' in url:
            return "自建CDN (中国)"
        else:
            return "CDN"


class SmartDependencyManager:
    """增强的依赖管理器，支持智能CDN选择"""
    
    def __init__(self, app_dir: Path = None):
        # 导入原始的DependencyManager
        from dependency_manager import DependencyManager
        
        # 继承原有功能
        self.base_manager = DependencyManager(app_dir)
        self.cdn_selector = CDNSelector()
        
        # 优化CDN顺序
        self.optimized_cdns = None
        
    def optimize_cdn_urls(self, show_progress: bool = True):
        """优化CDN URL顺序"""
        if show_progress:
            print("正在检测最快的下载源...")
            
        self.optimized_cdns = self.cdn_selector.select_best_cdn(
            self.base_manager.CDN_URLS, 
            show_progress
        )
        
        # 更新基础管理器的CDN列表
        self.base_manager.CDN_URLS = self.optimized_cdns
        
        if show_progress:
            print(f"已选择最佳下载源: {self.cdn_selector._get_cdn_name(self.optimized_cdns[0])}")
            
    def download_with_smart_cdn(self, dep_name: str, progress_callback=None):
        """使用智能CDN选择下载依赖"""
        # 首次调用时优化CDN
        if self.optimized_cdns is None:
            self.optimize_cdn_urls()
            
        # 使用优化后的CDN下载
        return self.base_manager.install_dependency(dep_name, progress_callback)