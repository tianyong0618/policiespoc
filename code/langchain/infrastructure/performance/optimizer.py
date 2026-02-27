import time
import threading
import json
from datetime import datetime
from collections import defaultdict

class PerformanceOptimizer:
    """性能优化器，用于实现持续性能调优机制"""
    
    def __init__(self, monitor, analyzer):
        """
        初始化性能优化器
        
        Args:
            monitor: PerformanceMonitor实例
            analyzer: PerformanceAnalyzer实例
        """
        self.monitor = monitor
        self.analyzer = analyzer
        self.optimization_history = []
        self.current_strategies = []
        self.thresholds = {
            "response_time": 1.0,  # 响应时间阈值（秒）
            "error_rate": 1.0,  # 错误率阈值（%）
            "memory_usage": 80.0,  # 内存使用率阈值（%）
            "cpu_usage": 80.0,  # CPU使用率阈值（%）
            "concurrent_requests": 100  # 并发请求数阈值
        }
        self.running = False
        self.monitoring_thread = None
        self.optimization_interval = 60  # 优化检查间隔（秒）
    
    def start_optimization(self, interval=60):
        """
        开始持续性能优化
        
        Args:
            interval: 优化检查间隔（秒）
        """
        self.optimization_interval = interval
        self.running = True
        self.monitoring_thread = threading.Thread(target=self._optimization_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
    
    def stop_optimization(self):
        """
        停止持续性能优化
        """
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
    
    def _optimization_loop(self):
        """
        优化循环
        """
        while self.running:
            try:
                # 检查性能指标
                metrics = self.monitor.get_metrics()
                
                # 分析性能趋势
                trend_analysis = self.analyzer.analyze_performance_trends()
                
                # 生成优化建议
                recommendations = self._generate_optimization_recommendations(metrics, trend_analysis)
                
                # 应用优化策略
                applied_strategies = self._apply_optimization_strategies(recommendations)
                
                # 记录优化历史
                if applied_strategies:
                    self._record_optimization_history(metrics, recommendations, applied_strategies)
                
            except Exception as e:
                print(f"优化过程中发生错误: {e}")
            
            # 等待下一次优化检查
            time.sleep(self.optimization_interval)
    
    def _generate_optimization_recommendations(self, metrics, trend_analysis):
        """
        生成优化建议
        
        Args:
            metrics: 当前性能指标
            trend_analysis: 趋势分析结果
            
        Returns:
            list: 优化建议列表
        """
        recommendations = []
        
        # 基于当前指标的建议
        request_metrics = metrics.get("request_metrics", {})
        system_metrics = metrics.get("system_metrics", {})
        
        # 响应时间优化建议
        avg_response_time = request_metrics.get("avg_response_time", 0)
        if avg_response_time > self.thresholds["response_time"]:
            recommendations.append({
                "type": "response_time_optimization",
                "severity": "high",
                "description": f"平均响应时间超过阈值: {avg_response_time:.2f}秒",
                "suggestions": [
                    "实现请求缓存，减少重复计算",
                    "使用异步处理，提高并发能力",
                    "优化数据库查询，添加索引",
                    "考虑使用CDN加速静态资源"
                ],
                "priority": 1
            })
        
        # 错误率优化建议
        error_rate = request_metrics.get("error_rate", 0)
        if error_rate > self.thresholds["error_rate"]:
            recommendations.append({
                "type": "error_rate_optimization",
                "severity": "high",
                "description": f"错误率超过阈值: {error_rate:.2f}%",
                "suggestions": [
                    "增强错误处理机制",
                    "添加请求参数验证",
                    "实现断路器模式，防止级联失败",
                    "增加监控和告警机制"
                ],
                "priority": 1
            })
        
        # 内存使用优化建议
        if system_metrics.get("memory"):
            memory_usage = system_metrics["memory"].get("used_percent", 0)
            if memory_usage > self.thresholds["memory_usage"]:
                recommendations.append({
                    "type": "memory_optimization",
                    "severity": "high",
                    "description": f"内存使用率超过阈值: {memory_usage:.2f}%",
                    "suggestions": [
                        "检查内存泄漏，特别是长时间运行的进程",
                        "优化数据结构，减少内存占用",
                        "实现数据分页，避免一次性加载大量数据",
                        "考虑增加服务器内存"
                    ],
                    "priority": 2
                })
        
        # CPU使用优化建议
        if system_metrics.get("cpu"):
            cpu_usage = system_metrics["cpu"].get("percent", 0)
            if cpu_usage > self.thresholds["cpu_usage"]:
                recommendations.append({
                    "type": "cpu_optimization",
                    "severity": "high",
                    "description": f"CPU使用率超过阈值: {cpu_usage:.2f}%",
                    "suggestions": [
                        "优化CPU密集型算法",
                        "使用多线程或异步处理",
                        "实现任务队列，避免峰值负载",
                        "考虑增加服务器CPU核心数"
                    ],
                    "priority": 2
                })
        
        # 并发请求优化建议
        current_concurrent = request_metrics.get("current_concurrent_requests", 0)
        max_concurrent = request_metrics.get("max_concurrent_requests", 0)
        if max_concurrent > self.thresholds["concurrent_requests"] * 0.8:
            recommendations.append({
                "type": "concurrency_optimization",
                "severity": "medium",
                "description": f"并发请求数接近阈值: {max_concurrent}",
                "suggestions": [
                    "实现请求限流，防止系统过载",
                    "优化线程池配置，提高并发处理能力",
                    "使用异步I/O，减少阻塞操作",
                    "考虑水平扩展，增加服务器实例"
                ],
                "priority": 3
            })
        
        # 基于趋势的建议
        trend_insights = trend_analysis.get("insights", [])
        for insight in trend_insights:
            if insight.get("severity") in ["high", "medium"]:
                recommendations.append({
                    "type": insight.get("type"),
                    "severity": insight.get("severity"),
                    "description": insight.get("description"),
                    "suggestions": [insight.get("suggestion")],
                    "priority": 2 if insight.get("severity") == "high" else 3
                })
        
        # 按优先级排序
        recommendations.sort(key=lambda x: x.get("priority", 3))
        
        return recommendations
    
    def _apply_optimization_strategies(self, recommendations):
        """
        应用优化策略
        
        Args:
            recommendations: 优化建议列表
            
        Returns:
            list: 应用的策略列表
        """
        applied_strategies = []
        
        # 遍历建议，应用可行的策略
        for recommendation in recommendations[:5]:  # 只应用前5个高优先级建议
            strategy = self._map_recommendation_to_strategy(recommendation)
            if strategy and self._is_strategy_applicable(strategy):
                # 应用策略
                success = self._execute_strategy(strategy)
                if success:
                    applied_strategies.append({
                        "strategy": strategy,
                        "recommendation": recommendation,
                        "applied_at": datetime.now().isoformat()
                    })
                    
                    # 将策略添加到当前策略列表
                    self.current_strategies.append(strategy)
        
        return applied_strategies
    
    def _map_recommendation_to_strategy(self, recommendation):
        """
        将建议映射为具体策略
        
        Args:
            recommendation: 优化建议
            
        Returns:
            dict: 优化策略
        """
        strategy_map = {
            "response_time_optimization": {
                "type": "cache_optimization",
                "description": "优化缓存策略，减少重复计算",
                "actions": [
                    "增加缓存大小",
                    "优化缓存过期时间",
                    "实现多级缓存"
                ],
                "impact": "响应时间减少30-50%"
            },
            "memory_optimization": {
                "type": "memory_management",
                "description": "优化内存管理，减少内存占用",
                "actions": [
                    "实现对象池，减少对象创建",
                    "优化数据结构，减少内存占用",
                    "及时释放不再使用的资源"
                ],
                "impact": "内存使用减少20-40%"
            },
            "cpu_optimization": {
                "type": "concurrency_optimization",
                "description": "优化并发处理，提高CPU利用率",
                "actions": [
                    "调整线程池大小",
                    "使用异步I/O",
                    "优化算法复杂度"
                ],
                "impact": "CPU使用效率提高25-45%"
            },
            "error_rate_optimization": {
                "type": "error_handling",
                "description": "优化错误处理，提高系统稳定性",
                "actions": [
                    "实现断路器模式",
                    "添加重试机制",
                    "增强错误日志记录"
                ],
                "impact": "错误率减少50-70%"
            },
            "concurrency_optimization": {
                "type": "request_management",
                "description": "优化请求管理，提高并发处理能力",
                "actions": [
                    "实现请求限流",
                    "优化队列配置",
                    "考虑水平扩展"
                ],
                "impact": "并发处理能力提高40-60%"
            }
        }
        
        return strategy_map.get(recommendation.get("type"))
    
    def _is_strategy_applicable(self, strategy):
        """
        检查策略是否适用
        
        Args:
            strategy: 优化策略
            
        Returns:
            bool: 是否适用
        """
        # 检查策略是否已经应用
        for current_strategy in self.current_strategies:
            if current_strategy.get("type") == strategy.get("type"):
                return False
        
        # 检查策略是否适合当前系统状态
        # 这里可以添加更复杂的检查逻辑
        return True
    
    def _execute_strategy(self, strategy):
        """
        执行优化策略
        
        Args:
            strategy: 优化策略
            
        Returns:
            bool: 是否执行成功
        """
        try:
            # 这里实现具体的策略执行逻辑
            # 例如，调整缓存配置、修改线程池大小等
            print(f"应用优化策略: {strategy.get('description')}")
            print(f"执行动作: {', '.join(strategy.get('actions', []))}")
            
            # 模拟策略执行
            time.sleep(1)  # 模拟执行时间
            
            return True
        except Exception as e:
            print(f"执行策略时发生错误: {e}")
            return False
    
    def _record_optimization_history(self, metrics, recommendations, applied_strategies):
        """
        记录优化历史
        
        Args:
            metrics: 当前性能指标
            recommendations: 优化建议
            applied_strategies: 应用的策略
        """
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "current_metrics": metrics,
            "recommendations": recommendations,
            "applied_strategies": applied_strategies,
            "summary": {
                "recommendation_count": len(recommendations),
                "applied_strategy_count": len(applied_strategies)
            }
        }
        
        self.optimization_history.append(history_entry)
        
        # 限制历史记录大小
        if len(self.optimization_history) > 100:
            self.optimization_history = self.optimization_history[-100:]
        
        # 保存优化历史
        self._save_optimization_history()
    
    def _save_optimization_history(self):
        """
        保存优化历史到文件
        """
        try:
            # 检查文件系统是否可写
            with open("performance_optimization_history.json", "w", encoding="utf-8") as f:
                json.dump(self.optimization_history, f, ensure_ascii=False, indent=2)
        except OSError as e:
            # 忽略只读文件系统错误
            print(f"文件系统只读，跳过保存优化历史: {e}")
        except Exception as e:
            print(f"保存优化历史失败: {e}")
    
    def get_optimization_history(self):
        """
        获取优化历史
        
        Returns:
            list: 优化历史记录
        """
        return self.optimization_history
    
    def get_current_strategies(self):
        """
        获取当前应用的策略
        
        Returns:
            list: 当前策略列表
        """
        return self.current_strategies
    
    def evaluate_optimization_effectiveness(self):
        """
        评估优化效果
        
        Returns:
            dict: 优化效果评估结果
        """
        if not self.optimization_history:
            return {"error": "没有足够的优化历史数据进行评估"}
        
        # 获取最近的优化历史
        recent_history = self.optimization_history[-5:]  # 取最近5次优化记录
        
        # 分析优化效果
        metrics_before = []
        metrics_after = []
        
        for i, history in enumerate(recent_history):
            metrics_before.append(history.get("current_metrics", {}))
            
            # 获取优化后的指标（如果有下一次记录）
            if i < len(recent_history) - 1:
                metrics_after.append(recent_history[i + 1].get("current_metrics", {}))
        
        # 计算优化效果
        effectiveness = self._calculate_optimization_effectiveness(metrics_before, metrics_after)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "effectiveness": effectiveness,
            "history_analyzed": len(recent_history),
            "summary": {
                "overall_effectiveness": "positive" if effectiveness.get("overall_improvement") > 0 else "negative",
                "improvement_percentage": effectiveness.get("overall_improvement", 0)
            }
        }
    
    def _calculate_optimization_effectiveness(self, metrics_before, metrics_after):
        """
        计算优化效果
        
        Args:
            metrics_before: 优化前的指标
            metrics_after: 优化后的指标
            
        Returns:
            dict: 优化效果评估结果
        """
        if not metrics_before or not metrics_after:
            return {"overall_improvement": 0}
        
        # 计算各项指标的变化
        response_time_improvement = 0
        memory_usage_improvement = 0
        cpu_usage_improvement = 0
        error_rate_improvement = 0
        
        for i in range(min(len(metrics_before), len(metrics_after))):
            before = metrics_before[i]
            after = metrics_after[i]
            
            # 响应时间改进
            before_rt = before.get("request_metrics", {}).get("avg_response_time", 0)
            after_rt = after.get("request_metrics", {}).get("avg_response_time", 0)
            if before_rt > 0:
                rt_improvement = (before_rt - after_rt) / before_rt * 100
                response_time_improvement += rt_improvement
            
            # 内存使用改进
            before_memory = before.get("system_metrics", {}).get("memory", {}).get("used_percent", 0)
            after_memory = after.get("system_metrics", {}).get("memory", {}).get("used_percent", 0)
            if before_memory > 0:
                memory_improvement = (before_memory - after_memory) / before_memory * 100
                memory_usage_improvement += memory_improvement
            
            # CPU使用改进
            before_cpu = before.get("system_metrics", {}).get("cpu", {}).get("percent", 0)
            after_cpu = after.get("system_metrics", {}).get("cpu", {}).get("percent", 0)
            if before_cpu > 0:
                cpu_improvement = (before_cpu - after_cpu) / before_cpu * 100
                cpu_usage_improvement += cpu_improvement
            
            # 错误率改进
            before_error = before.get("request_metrics", {}).get("error_rate", 0)
            after_error = after.get("request_metrics", {}).get("error_rate", 0)
            if before_error > 0:
                error_improvement = (before_error - after_error) / before_error * 100
                error_rate_improvement += error_improvement
        
        # 计算平均改进
        count = min(len(metrics_before), len(metrics_after))
        if count > 0:
            response_time_improvement /= count
            memory_usage_improvement /= count
            cpu_usage_improvement /= count
            error_rate_improvement /= count
        
        # 计算整体改进
        overall_improvement = (
            response_time_improvement * 0.4 +  # 响应时间权重最高
            memory_usage_improvement * 0.2 +
            cpu_usage_improvement * 0.2 +
            error_rate_improvement * 0.2
        )
        
        return {
            "response_time_improvement": response_time_improvement,
            "memory_usage_improvement": memory_usage_improvement,
            "cpu_usage_improvement": cpu_usage_improvement,
            "error_rate_improvement": error_rate_improvement,
            "overall_improvement": overall_improvement
        }
    
    def set_thresholds(self, thresholds):
        """
        设置性能阈值
        
        Args:
            thresholds: 阈值字典
        """
        self.thresholds.update(thresholds)
    
    def get_thresholds(self):
        """
        获取当前性能阈值
        
        Returns:
            dict: 阈值字典
        """
        return self.thresholds
