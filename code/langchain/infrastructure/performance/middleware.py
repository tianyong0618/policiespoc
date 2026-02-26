from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from time import time
from .monitor import performance_monitor

class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能监控中间件，用于收集API请求的性能指标"""
    
    async def dispatch(self, request: Request, call_next):
        """
        处理请求并收集性能指标
        
        Args:
            request: FastAPI请求对象
            call_next: 下一个中间件或路由处理函数
            
        Returns:
            响应对象
        """
        # 记录请求开始
        performance_monitor.record_request_start()
        start_time = time()
        
        # 处理请求
        try:
            response = await call_next(request)
            error = False
        except Exception as e:
            # 处理异常
            error = True
            raise
        finally:
            # 计算响应时间
            duration = time() - start_time
            
            # 获取路由路径
            route = request.url.path
            
            # 记录请求结束
            performance_monitor.record_request_end(route, duration, error)
        
        return response
