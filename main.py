# Vercel FastAPI 入口点
# 导入现有FastAPI应用
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath('.'))

# 从现有位置导入app实例
from code.serve_code.main import app

# 暴露app实例，供Vercel使用
__all__ = ['app']