import time
import threading
import json
from datetime import datetime
from collections import defaultdict, deque
import os

# 尝试导入 psutil，如果不可用则禁用系统监控
psutil = None
try:
    import psutil
except ImportError:
    print("psutil module not available, system monitoring will be disabled")

class PerformanceMonitor:
    """性能监控器，用于收集和管理性能指标"""
    
    def __init__(self, max_history=1000):
        """
        初始化性能监控器
        
        Args:
            max_history: 最大历史记录数
        """
        self.max_history = max_history
        # 响应时间历史记录
        self.response_times = deque(maxlen=max_history)
        # API路由响应时间统计
        self.route_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'min_time': float('inf'),
            'max_time': 0,
            'avg_time': 0
        })
        # LLM调用历史记录
        self.llm_calls = deque(maxlen=max_history)
        # LLM调用统计
        self.llm_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'min_time': float('inf'),
            'max_time': 0,
            'avg_time': 0
        })
        # 内存使用历史记录
        self.memory_usage = deque(maxlen=max_history)
        # CPU使用历史记录
        self.cpu_usage = deque(maxlen=max_history)
        # 系统负载历史记录
        self.system_load = deque(maxlen=max_history)
        # 并发请求数
        self.concurrent_requests = 0
        # 最大并发请求数
        self.max_concurrent_requests = 0
        # 锁，用于线程安全
        self.lock = threading.Lock()
        # 启动时间
        self.start_time = datetime.now()
        # 错误率统计
        self.error_counts = defaultdict(int)
        # 请求总数
        self.total_requests = 0
        # 监控线程
        self.monitoring_thread = None
        self.running = False
    
    def start_monitoring(self, interval=5):
        """
        开始系统监控
        
        Args:
            interval: 监控间隔（秒）
        """
        self.running = True
        self.monitoring_thread = threading.Thread(target=self._monitor_system, args=(interval,))
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
    
    def stop_monitoring(self):
        """
        停止系统监控
        """
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
    
    def _monitor_system(self, interval):
        """
        系统监控线程函数
        
        Args:
            interval: 监控间隔（秒）
        """
        # 如果 psutil 不可用，直接返回
        if not psutil:
            return
            
        while self.running:
            try:
                # 收集内存使用情况
                memory = psutil.virtual_memory()
                with self.lock:
                    self.memory_usage.append({
                        'timestamp': datetime.now().isoformat(),
                        'used_percent': memory.percent,
                        'used_mb': memory.used / (1024 * 1024),
                        'total_mb': memory.total / (1024 * 1024)
                    })
                
                # 收集CPU使用情况
                cpu_percent = psutil.cpu_percent(interval=0.1)
                with self.lock:
                    self.cpu_usage.append({
                        'timestamp': datetime.now().isoformat(),
                        'percent': cpu_percent
                    })
                
                # 收集系统负载
                load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
                with self.lock:
                    self.system_load.append({
                        'timestamp': datetime.now().isoformat(),
                        '1min': load_avg[0],
                        '5min': load_avg[1],
                        '15min': load_avg[2]
                    })
                
                time.sleep(interval)
            except Exception as e:
                print(f"Error in system monitoring: {e}")
                time.sleep(interval)
    
    def record_request_start(self):
        """
        记录请求开始
        """
        with self.lock:
            self.concurrent_requests += 1
            if self.concurrent_requests > self.max_concurrent_requests:
                self.max_concurrent_requests = self.concurrent_requests
            self.total_requests += 1
    
    def record_request_end(self, route, duration, error=False):
        """
        记录请求结束
        
        Args:
            route: API路由
            duration: 响应时间（秒）
            error: 是否发生错误
        """
        with self.lock:
            self.concurrent_requests = max(0, self.concurrent_requests - 1)
            
            # 记录响应时间
            self.response_times.append({
                'timestamp': datetime.now().isoformat(),
                'route': route,
                'duration': duration,
                'error': error
            })
            
            # 更新路由统计
            stats = self.route_stats[route]
            stats['count'] += 1
            stats['total_time'] += duration
            stats['min_time'] = min(stats['min_time'], duration)
            stats['max_time'] = max(stats['max_time'], duration)
            stats['avg_time'] = stats['total_time'] / stats['count']
            
            # 记录错误
            if error:
                self.error_counts[route] += 1
    
    def record_llm_call(self, llm_type, duration, error=False):
        """
        记录LLM调用
        
        Args:
            llm_type: LLM调用类型（如intent_recognition, response_generation等）
            duration: 调用时间（秒）
            error: 是否发生错误
        """
        with self.lock:
            # 记录LLM调用
            self.llm_calls.append({
                'timestamp': datetime.now().isoformat(),
                'llm_type': llm_type,
                'duration': duration,
                'error': error
            })
            
            # 更新LLM调用统计
            stats = self.llm_stats[llm_type]
            stats['count'] += 1
            stats['total_time'] += duration
            stats['min_time'] = min(stats['min_time'], duration)
            stats['max_time'] = max(stats['max_time'], duration)
            stats['avg_time'] = stats['total_time'] / stats['count']
    
    def get_metrics(self):
        """
        获取所有性能指标
        
        Returns:
            dict: 性能指标字典
        """
        with self.lock:
            # 计算错误率
            error_rate = sum(self.error_counts.values()) / self.total_requests * 100 if self.total_requests > 0 else 0
            
            # 计算平均响应时间
            avg_response_time = sum(item['duration'] for item in self.response_times) / len(self.response_times) if self.response_times else 0
            
            # 计算P95和P99响应时间
            p95_response_time = 0
            p99_response_time = 0
            if self.response_times:
                sorted_times = sorted(item['duration'] for item in self.response_times)
                p95_index = int(len(sorted_times) * 0.95)
                p99_index = int(len(sorted_times) * 0.99)
                p95_response_time = sorted_times[p95_index] if p95_index < len(sorted_times) else sorted_times[-1]
                p99_response_time = sorted_times[p99_index] if p99_index < len(sorted_times) else sorted_times[-1]
            
            # 获取最新的系统指标
            latest_memory = self.memory_usage[-1] if self.memory_usage else None
            latest_cpu = self.cpu_usage[-1] if self.cpu_usage else None
            latest_load = self.system_load[-1] if self.system_load else None
            
            # 计算LLM调用统计
            total_llm_calls = sum(stats['count'] for stats in self.llm_stats.values())
            avg_llm_time = sum(stats['total_time'] for stats in self.llm_stats.values()) / total_llm_calls if total_llm_calls > 0 else 0
            
            return {
                'timestamp': datetime.now().isoformat(),
                'uptime': (datetime.now() - self.start_time).total_seconds(),
                'request_metrics': {
                    'total_requests': self.total_requests,
                    'error_rate': error_rate,
                    'avg_response_time': avg_response_time,
                    'p95_response_time': p95_response_time,
                    'p99_response_time': p99_response_time,
                    'max_concurrent_requests': self.max_concurrent_requests,
                    'current_concurrent_requests': self.concurrent_requests
                },
                'llm_metrics': {
                    'total_calls': total_llm_calls,
                    'avg_time': avg_llm_time,
                    'call_stats': dict(self.llm_stats)
                },
                'system_metrics': {
                    'memory': latest_memory,
                    'cpu': latest_cpu,
                    'load': latest_load
                },
                'route_stats': dict(self.route_stats),
                'error_counts': dict(self.error_counts)
            }
    
    def generate_report(self):
        """
        生成性能报告
        
        Returns:
            dict: 性能报告
        """
        metrics = self.get_metrics()
        
        # 分析性能瓶颈
        bottlenecks = []
        for route, stats in metrics['route_stats'].items():
            if stats['avg_time'] > 1.0:
                bottlenecks.append({
                    'route': route,
                    'avg_time': stats['avg_time'],
                    'count': stats['count']
                })
        
        # 生成优化建议
        recommendations = []
        
        # 基于响应时间的建议
        if metrics['request_metrics']['avg_response_time'] > 0.5:
            recommendations.append({
                'type': 'response_time',
                'severity': 'high' if metrics['request_metrics']['avg_response_time'] > 1.0 else 'medium',
                'description': f'平均响应时间较高: {metrics["request_metrics"]["avg_response_time"]:.2f}秒',
                'suggestion': '考虑优化API实现，添加缓存，或使用异步处理'
            })
        
        # 基于错误率的建议
        if metrics['request_metrics']['error_rate'] > 1.0:
            recommendations.append({
                'type': 'error_rate',
                'severity': 'high' if metrics['request_metrics']['error_rate'] > 5.0 else 'medium',
                'description': f'错误率较高: {metrics["request_metrics"]["error_rate"]:.2f}%',
                'suggestion': '检查API实现，添加更多错误处理和日志记录'
            })
        
        # 基于内存使用的建议
        if metrics['system_metrics']['memory'] and metrics['system_metrics']['memory']['used_percent'] > 80:
            recommendations.append({
                'type': 'memory_usage',
                'severity': 'high',
                'description': f'内存使用率较高: {metrics["system_metrics"]["memory"]["used_percent"]:.2f}%',
                'suggestion': '检查内存泄漏，优化数据结构，或增加服务器内存'
            })
        
        # 基于CPU使用的建议
        if metrics['system_metrics']['cpu'] and metrics['system_metrics']['cpu']['percent'] > 80:
            recommendations.append({
                'type': 'cpu_usage',
                'severity': 'high',
                'description': f'CPU使用率较高: {metrics["system_metrics"]["cpu"]["percent"]:.2f}%',
                'suggestion': '优化CPU密集型操作，考虑使用异步处理或增加服务器CPU核心数'
            })
        
        # 基于路由的建议
        for bottleneck in bottlenecks:
            recommendations.append({
                'type': 'route_bottleneck',
                'severity': 'medium',
                'description': f'路由 {bottleneck["route"]} 响应时间较长: {bottleneck["avg_time"]:.2f}秒',
                'suggestion': f'优化 {bottleneck["route"]} 路由的实现，考虑添加缓存或异步处理'
            })
        
        # 基于LLM调用的建议
        if metrics['llm_metrics']['total_calls'] > 0:
            avg_llm_time = metrics['llm_metrics']['avg_time']
            if avg_llm_time > 10.0:
                recommendations.append({
                    'type': 'llm_performance',
                    'severity': 'high' if avg_llm_time > 20.0 else 'medium',
                    'description': f'LLM调用平均时间较长: {avg_llm_time:.2f}秒',
                    'suggestion': '考虑优化提示词，使用更轻量级的模型，或实现缓存机制减少LLM调用'
                })
            
            # 分析LLM调用类型
            for llm_type, stats in metrics['llm_metrics']['call_stats'].items():
                if stats['avg_time'] > 15.0:
                    recommendations.append({
                        'type': 'llm_type_performance',
                        'severity': 'medium',
                        'description': f'{llm_type} 类型的LLM调用时间较长: {stats["avg_time"]:.2f}秒',
                        'suggestion': f'优化 {llm_type} 的实现，考虑使用规则引擎或缓存'
                    })
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
            'bottlenecks': bottlenecks,
            'recommendations': recommendations,
            'summary': {
                'total_requests': metrics['request_metrics']['total_requests'],
                'avg_response_time': metrics['request_metrics']['avg_response_time'],
                'error_rate': metrics['request_metrics']['error_rate'],
                'max_concurrent_requests': metrics['request_metrics']['max_concurrent_requests'],
                'total_llm_calls': metrics['llm_metrics']['total_calls'],
                'avg_llm_time': metrics['llm_metrics']['avg_time'],
                'bottleneck_count': len(bottlenecks),
                'recommendation_count': len(recommendations)
            }
        }
        
        return report
    
    def save_report(self, filename=None):
        """
        保存性能报告到文件
        
        Args:
            filename: 文件名，默认为当前时间戳
        """
        report = self.generate_report()
        
        if not filename:
            filename = f'performance_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return filename

# 创建全局性能监控实例
performance_monitor = PerformanceMonitor()
