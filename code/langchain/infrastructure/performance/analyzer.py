import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

# 尝试导入 matplotlib，如果不可用则禁用可视化功能
plt = None
try:
    import matplotlib.pyplot as plt
except ImportError:
    print("matplotlib module not available, visualization will be disabled")

class PerformanceAnalyzer:
    """性能分析器，用于生成详细的性能分析报告"""
    
    def __init__(self, monitor):
        """
        初始化性能分析器
        
        Args:
            monitor: PerformanceMonitor实例
        """
        self.monitor = monitor
        self.report_history = []
        self.report_dir = "performance_reports"
        
        # 创建报告目录
        if not os.path.exists(self.report_dir):
            os.makedirs(self.report_dir)
    
    def analyze_performance_trends(self, hours=24):
        """
        分析性能趋势
        
        Args:
            hours: 分析过去多少小时的性能趋势
            
        Returns:
            dict: 性能趋势分析结果
        """
        # 加载历史报告
        self._load_report_history(hours)
        
        if not self.report_history:
            return {"error": "没有足够的历史数据进行趋势分析"}
        
        # 按时间排序
        self.report_history.sort(key=lambda x: x.get("timestamp"))
        
        # 提取关键指标
        timestamps = []
        avg_response_times = []
        error_rates = []
        memory_usages = []
        cpu_usages = []
        request_counts = []
        
        for report in self.report_history:
            metrics = report.get("metrics", {})
            request_metrics = metrics.get("request_metrics", {})
            system_metrics = metrics.get("system_metrics", {})
            
            timestamps.append(report.get("timestamp"))
            avg_response_times.append(request_metrics.get("avg_response_time", 0))
            error_rates.append(request_metrics.get("error_rate", 0))
            request_counts.append(request_metrics.get("total_requests", 0))
            
            if system_metrics.get("memory"):
                memory_usages.append(system_metrics["memory"].get("used_percent", 0))
            else:
                memory_usages.append(0)
            
            if system_metrics.get("cpu"):
                cpu_usages.append(system_metrics["cpu"].get("percent", 0))
            else:
                cpu_usages.append(0)
        
        # 计算趋势
        trends = {
            "response_time": self._calculate_trend(avg_response_times),
            "error_rate": self._calculate_trend(error_rates),
            "memory_usage": self._calculate_trend(memory_usages),
            "cpu_usage": self._calculate_trend(cpu_usages),
            "request_count": self._calculate_trend(request_counts)
        }
        
        # 生成趋势分析
        trend_analysis = {
            "timestamps": timestamps,
            "metrics": {
                "avg_response_time": avg_response_times,
                "error_rate": error_rates,
                "memory_usage": memory_usages,
                "cpu_usage": cpu_usages,
                "request_count": request_counts
            },
            "trends": trends,
            "insights": self._generate_trend_insights(trends)
        }
        
        return trend_analysis
    
    def _calculate_trend(self, values):
        """
        计算指标趋势
        
        Args:
            values: 指标值列表
            
        Returns:
            dict: 趋势分析结果
        """
        if len(values) < 2:
            return {"direction": "insufficient_data", "magnitude": 0}
        
        # 计算线性回归斜率
        x = np.arange(len(values))
        slope, _ = np.polyfit(x, values, 1)
        
        # 计算变化百分比
        if values[0] > 0:
            percent_change = (values[-1] - values[0]) / values[0] * 100
        else:
            percent_change = 0
        
        # 确定趋势方向
        if abs(slope) < 0.001:
            direction = "stable"
        elif slope > 0:
            direction = "increasing"
        else:
            direction = "decreasing"
        
        return {
            "direction": direction,
            "magnitude": abs(percent_change),
            "slope": slope,
            "percent_change": percent_change
        }
    
    def _generate_trend_insights(self, trends):
        """
        生成趋势洞察
        
        Args:
            trends: 趋势分析结果
            
        Returns:
            list: 趋势洞察列表
        """
        insights = []
        
        # 响应时间趋势洞察
        rt_trend = trends.get("response_time", {})
        if rt_trend.get("direction") == "increasing" and rt_trend.get("magnitude") > 10:
            insights.append({
                "type": "response_time_increasing",
                "severity": "high" if rt_trend.get("magnitude") > 50 else "medium",
                "description": f"响应时间呈上升趋势，增加了 {rt_trend.get('percent_change', 0):.2f}%",
                "suggestion": "需要优化API实现，考虑添加缓存或异步处理"
            })
        elif rt_trend.get("direction") == "decreasing" and rt_trend.get("magnitude") > 10:
            insights.append({
                "type": "response_time_decreasing",
                "severity": "low",
                "description": f"响应时间呈下降趋势，减少了 {abs(rt_trend.get('percent_change', 0)):.2f}%",
                "suggestion": "当前优化策略有效，继续保持"
            })
        
        # 错误率趋势洞察
        er_trend = trends.get("error_rate", {})
        if er_trend.get("direction") == "increasing" and er_trend.get("magnitude") > 10:
            insights.append({
                "type": "error_rate_increasing",
                "severity": "high",
                "description": f"错误率呈上升趋势，增加了 {er_trend.get('percent_change', 0):.2f}%",
                "suggestion": "需要检查API实现，添加更多错误处理和日志记录"
            })
        
        # 内存使用趋势洞察
        mem_trend = trends.get("memory_usage", {})
        if mem_trend.get("direction") == "increasing" and mem_trend.get("magnitude") > 10:
            insights.append({
                "type": "memory_usage_increasing",
                "severity": "high" if mem_trend.get("magnitude") > 50 else "medium",
                "description": f"内存使用率呈上升趋势，增加了 {mem_trend.get('percent_change', 0):.2f}%",
                "suggestion": "需要检查内存泄漏，优化数据结构，或增加服务器内存"
            })
        
        # CPU使用趋势洞察
        cpu_trend = trends.get("cpu_usage", {})
        if cpu_trend.get("direction") == "increasing" and cpu_trend.get("magnitude") > 10:
            insights.append({
                "type": "cpu_usage_increasing",
                "severity": "high" if cpu_trend.get("magnitude") > 50 else "medium",
                "description": f"CPU使用率呈上升趋势，增加了 {cpu_trend.get('percent_change', 0):.2f}%",
                "suggestion": "需要优化CPU密集型操作，考虑使用异步处理或增加服务器CPU核心数"
            })
        
        return insights
    
    def generate_comprehensive_report(self):
        """
        生成综合性能报告
        
        Returns:
            dict: 综合性能报告
        """
        # 获取当前性能指标
        current_metrics = self.monitor.get_metrics()
        
        # 生成基础报告
        base_report = self.monitor.generate_report()
        
        # 分析性能趋势
        trend_analysis = self.analyze_performance_trends()
        
        # 生成详细的优化建议
        detailed_recommendations = self._generate_detailed_recommendations(current_metrics, trend_analysis)
        
        # 生成性能评分
        performance_score = self._calculate_performance_score(current_metrics, trend_analysis)
        
        # 生成综合报告
        comprehensive_report = {
            "timestamp": datetime.now().isoformat(),
            "current_metrics": current_metrics,
            "base_report": base_report,
            "trend_analysis": trend_analysis,
            "detailed_recommendations": detailed_recommendations,
            "performance_score": performance_score,
            "summary": {
                "overall_performance": self._get_performance_rating(performance_score),
                "key_issues": self._identify_key_issues(detailed_recommendations),
                "priority_actions": self._prioritize_actions(detailed_recommendations),
                "report_generated_at": datetime.now().isoformat()
            }
        }
        
        # 保存综合报告
        report_filename = self._save_comprehensive_report(comprehensive_report)
        comprehensive_report["report_filename"] = report_filename
        
        # 生成可视化图表
        self._generate_visualizations(comprehensive_report, report_filename)
        
        return comprehensive_report
    
    def _generate_detailed_recommendations(self, current_metrics, trend_analysis):
        """
        生成详细的优化建议
        
        Args:
            current_metrics: 当前性能指标
            trend_analysis: 趋势分析结果
            
        Returns:
            list: 详细优化建议列表
        """
        recommendations = []
        
        # 基于当前指标的建议
        request_metrics = current_metrics.get("request_metrics", {})
        system_metrics = current_metrics.get("system_metrics", {})
        route_stats = current_metrics.get("route_stats", {})
        
        # 响应时间优化建议
        avg_response_time = request_metrics.get("avg_response_time", 0)
        if avg_response_time > 0.5:
            recommendations.append({
                "type": "response_time_optimization",
                "severity": "high" if avg_response_time > 1.0 else "medium",
                "description": f"平均响应时间较高: {avg_response_time:.2f}秒",
                "suggestions": [
                    "实现请求缓存，减少重复计算",
                    "使用异步处理，提高并发能力",
                    "优化数据库查询，添加索引",
                    "考虑使用CDN加速静态资源"
                ],
                "expected_improvement": "30-50% 响应时间减少"
            })
        
        # 内存使用优化建议
        if system_metrics.get("memory"):
            memory_usage = system_metrics["memory"].get("used_percent", 0)
            if memory_usage > 70:
                recommendations.append({
                    "type": "memory_optimization",
                    "severity": "high" if memory_usage > 90 else "medium",
                    "description": f"内存使用率较高: {memory_usage:.2f}%",
                    "suggestions": [
                        "检查内存泄漏，特别是长时间运行的进程",
                        "优化数据结构，减少内存占用",
                        "实现数据分页，避免一次性加载大量数据",
                        "考虑增加服务器内存"
                    ],
                    "expected_improvement": "20-40% 内存使用减少"
                })
        
        # CPU使用优化建议
        if system_metrics.get("cpu"):
            cpu_usage = system_metrics["cpu"].get("percent", 0)
            if cpu_usage > 70:
                recommendations.append({
                    "type": "cpu_optimization",
                    "severity": "high" if cpu_usage > 90 else "medium",
                    "description": f"CPU使用率较高: {cpu_usage:.2f}%",
                    "suggestions": [
                        "优化CPU密集型算法",
                        "使用多线程或异步处理",
                        "实现任务队列，避免峰值负载",
                        "考虑增加服务器CPU核心数"
                    ],
                    "expected_improvement": "25-45% CPU使用减少"
                })
        
        # 路由优化建议
        slow_routes = []
        for route, stats in route_stats.items():
            if stats.get("avg_time", 0) > 1.0:
                slow_routes.append((route, stats.get("avg_time", 0), stats.get("count", 0)))
        
        if slow_routes:
            # 按平均响应时间排序
            slow_routes.sort(key=lambda x: x[1], reverse=True)
            
            for route, avg_time, count in slow_routes[:3]:  # 只取前3个最慢的路由
                recommendations.append({
                    "type": "route_optimization",
                    "severity": "medium",
                    "description": f"路由 {route} 响应时间较长: {avg_time:.2f}秒",
                    "suggestions": [
                        f"优化 {route} 路由的实现逻辑",
                        f"为 {route} 路由添加缓存",
                        f"考虑将 {route} 路由的处理逻辑异步化",
                        f"检查 {route} 路由的数据库查询效率"
                    ],
                    "expected_improvement": f"40-60% {route} 路由响应时间减少"
                })
        
        # 基于趋势的建议
        trend_insights = trend_analysis.get("insights", [])
        recommendations.extend(trend_insights)
        
        return recommendations
    
    def _calculate_performance_score(self, current_metrics, trend_analysis):
        """
        计算性能评分
        
        Args:
            current_metrics: 当前性能指标
            trend_analysis: 趋势分析结果
            
        Returns:
            int: 性能评分 (0-100)
        """
        # 基础评分
        base_score = 100
        
        # 响应时间扣分
        request_metrics = current_metrics.get("request_metrics", {})
        avg_response_time = request_metrics.get("avg_response_time", 0)
        if avg_response_time > 0.1:
            base_score -= min(30, (avg_response_time - 0.1) * 100)
        
        # 错误率扣分
        error_rate = request_metrics.get("error_rate", 0)
        base_score -= min(20, error_rate * 2)
        
        # 内存使用率扣分
        system_metrics = current_metrics.get("system_metrics", {})
        if system_metrics.get("memory"):
            memory_usage = system_metrics["memory"].get("used_percent", 0)
            if memory_usage > 50:
                base_score -= min(15, (memory_usage - 50) * 0.3)
        
        # CPU使用率扣分
        if system_metrics.get("cpu"):
            cpu_usage = system_metrics["cpu"].get("percent", 0)
            if cpu_usage > 50:
                base_score -= min(15, (cpu_usage - 50) * 0.3)
        
        # 趋势加分/扣分
        trends = trend_analysis.get("trends", {})
        for metric_name, trend in trends.items():
            if trend.get("direction") == "decreasing" and metric_name in ["response_time", "error_rate"]:
                base_score += min(10, trend.get("magnitude", 0) * 0.1)
            elif trend.get("direction") == "increasing" and metric_name in ["response_time", "error_rate"]:
                base_score -= min(10, trend.get("magnitude", 0) * 0.1)
            elif trend.get("direction") == "decreasing" and metric_name in ["memory_usage", "cpu_usage"]:
                base_score += min(5, trend.get("magnitude", 0) * 0.05)
            elif trend.get("direction") == "increasing" and metric_name in ["memory_usage", "cpu_usage"]:
                base_score -= min(5, trend.get("magnitude", 0) * 0.05)
        
        # 确保分数在0-100之间
        return max(0, min(100, int(base_score)))
    
    def _get_performance_rating(self, score):
        """
        根据评分获取性能等级
        
        Args:
            score: 性能评分
            
        Returns:
            str: 性能等级
        """
        if score >= 90:
            return "优秀"
        elif score >= 80:
            return "良好"
        elif score >= 70:
            return "一般"
        elif score >= 60:
            return "需要改进"
        else:
            return "差"
    
    def _identify_key_issues(self, recommendations):
        """
        识别关键问题
        
        Args:
            recommendations: 优化建议列表
            
        Returns:
            list: 关键问题列表
        """
        key_issues = []
        for recommendation in recommendations:
            if recommendation.get("severity") == "high":
                key_issues.append(recommendation.get("description"))
        return key_issues[:5]  # 只返回前5个关键问题
    
    def _prioritize_actions(self, recommendations):
        """
        优先级排序行动
        
        Args:
            recommendations: 优化建议列表
            
        Returns:
            list: 优先级排序的行动列表
        """
        # 按严重程度排序
        priority_map = {"high": 0, "medium": 1, "low": 2}
        sorted_recommendations = sorted(
            recommendations,
            key=lambda x: priority_map.get(x.get("severity", "low"))
        )
        
        priority_actions = []
        for recommendation in sorted_recommendations[:5]:  # 只返回前5个优先行动
            priority_actions.append({
                "action": recommendation.get("description"),
                "severity": recommendation.get("severity"),
                "suggestion": recommendation.get("suggestion", recommendation.get("suggestions", ["无"])[0])
            })
        
        return priority_actions
    
    def _save_comprehensive_report(self, report):
        """
        保存综合报告
        
        Args:
            report: 综合报告
            
        Returns:
            str: 报告文件名
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = os.path.join(self.report_dir, f"comprehensive_report_{timestamp}.json")
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report_filename
    
    def _generate_visualizations(self, report, report_filename):
        """
        生成可视化图表
        
        Args:
            report: 综合报告
            report_filename: 报告文件名
        """
        # 如果 matplotlib 不可用，直接返回
        if not plt:
            return
            
        # 提取文件名（不含扩展名）
        base_filename = os.path.splitext(os.path.basename(report_filename))[0]
        chart_dir = os.path.join(self.report_dir, "charts")
        
        if not os.path.exists(chart_dir):
            os.makedirs(chart_dir)
        
        # 生成响应时间趋势图
        self._generate_response_time_chart(report, chart_dir, base_filename)
        
        # 生成系统资源使用图
        self._generate_system_resources_chart(report, chart_dir, base_filename)
        
        # 生成路由性能对比图
        self._generate_route_performance_chart(report, chart_dir, base_filename)
    
    def _generate_response_time_chart(self, report, chart_dir, base_filename):
        """
        生成响应时间趋势图
        """
        trend_analysis = report.get("trend_analysis", {})
        metrics = trend_analysis.get("metrics", {})
        timestamps = trend_analysis.get("timestamps", [])
        avg_response_times = metrics.get("avg_response_time", [])
        
        if len(timestamps) > 1:
            # 转换时间戳为可读格式
            readable_times = []
            for ts in timestamps:
                try:
                    dt = datetime.fromisoformat(ts)
                    readable_times.append(dt.strftime("%H:%M:%S"))
                except:
                    readable_times.append(ts)
            
            plt.figure(figsize=(12, 6))
            plt.plot(readable_times, avg_response_times, 'b-o', label='平均响应时间 (秒)')
            plt.xlabel('时间')
            plt.ylabel('响应时间 (秒)')
            plt.title('响应时间趋势')
            plt.xticks(rotation=45)
            plt.grid(True)
            plt.tight_layout()
            
            chart_filename = os.path.join(chart_dir, f"{base_filename}_response_time.png")
            plt.savefig(chart_filename)
            plt.close()
    
    def _generate_system_resources_chart(self, report, chart_dir, base_filename):
        """
        生成系统资源使用图
        """
        trend_analysis = report.get("trend_analysis", {})
        metrics = trend_analysis.get("metrics", {})
        timestamps = trend_analysis.get("timestamps", [])
        memory_usages = metrics.get("memory_usage", [])
        cpu_usages = metrics.get("cpu_usage", [])
        
        if len(timestamps) > 1:
            # 转换时间戳为可读格式
            readable_times = []
            for ts in timestamps:
                try:
                    dt = datetime.fromisoformat(ts)
                    readable_times.append(dt.strftime("%H:%M:%S"))
                except:
                    readable_times.append(ts)
            
            fig, ax1 = plt.subplots(figsize=(12, 6))
            
            # 内存使用
            ax1.plot(readable_times, memory_usages, 'g-o', label='内存使用率 (%)')
            ax1.set_xlabel('时间')
            ax1.set_ylabel('内存使用率 (%)', color='g')
            ax1.tick_params(axis='y', labelcolor='g')
            
            # CPU使用
            ax2 = ax1.twinx()
            ax2.plot(readable_times, cpu_usages, 'r-o', label='CPU使用率 (%)')
            ax2.set_ylabel('CPU使用率 (%)', color='r')
            ax2.tick_params(axis='y', labelcolor='r')
            
            plt.title('系统资源使用趋势')
            ax1.set_xticklabels(readable_times, rotation=45)
            fig.tight_layout()
            
            chart_filename = os.path.join(chart_dir, f"{base_filename}_system_resources.png")
            plt.savefig(chart_filename)
            plt.close()
    
    def _generate_route_performance_chart(self, report, chart_dir, base_filename):
        """
        生成路由性能对比图
        """
        current_metrics = report.get("current_metrics", {})
        route_stats = current_metrics.get("route_stats", {})
        
        if route_stats:
            # 提取路由和平均响应时间
            routes = []
            avg_times = []
            counts = []
            
            for route, stats in route_stats.items():
                if stats.get("count", 0) > 0:
                    routes.append(route)
                    avg_times.append(stats.get("avg_time", 0))
                    counts.append(stats.get("count", 0))
            
            if routes:
                # 按平均响应时间排序
                sorted_indices = sorted(range(len(avg_times)), key=lambda i: avg_times[i], reverse=True)
                sorted_routes = [routes[i] for i in sorted_indices[:10]]  # 只取前10个
                sorted_avg_times = [avg_times[i] for i in sorted_indices[:10]]
                
                plt.figure(figsize=(12, 6))
                plt.barh(sorted_routes, sorted_avg_times, color='skyblue')
                plt.xlabel('平均响应时间 (秒)')
                plt.ylabel('路由')
                plt.title('路由性能对比 (前10个最慢路由)')
                plt.grid(True, axis='x')
                plt.tight_layout()
                
                chart_filename = os.path.join(chart_dir, f"{base_filename}_route_performance.png")
                plt.savefig(chart_filename)
                plt.close()
    
    def _load_report_history(self, hours=24):
        """
        加载历史报告
        
        Args:
            hours: 加载过去多少小时的报告
        """
        self.report_history = []
        
        # 检查报告目录是否存在
        if not os.path.exists(self.report_dir):
            return
        
        # 计算时间阈值
        time_threshold = datetime.now() - timedelta(hours=hours)
        
        # 加载报告文件
        for filename in os.listdir(self.report_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.report_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        report = json.load(f)
                        
                    # 检查报告时间
                    report_time = datetime.fromisoformat(report.get("timestamp", ""))
                    if report_time >= time_threshold:
                        self.report_history.append(report)
                except Exception as e:
                    pass  # 忽略无法加载的报告
    
    def _get_performance_rating(self, score):
        """
        根据评分获取性能等级
        
        Args:
            score: 性能评分
            
        Returns:
            str: 性能等级
        """
        if score >= 90:
            return "优秀"
        elif score >= 80:
            return "良好"
        elif score >= 70:
            return "一般"
        elif score >= 60:
            return "需要改进"
        else:
            return "差"
