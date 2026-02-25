# 协调器模块 - 兼容层
# 保留原始导入路径，确保现有代码不受影响
from .orchestrator import Orchestrator, QueryProcessor, StreamProcessor, generate_resume_suggestions, extract_user_preferences

__all__ = [
    "Orchestrator",
    "QueryProcessor",
    "StreamProcessor",
    "generate_resume_suggestions",
    "extract_user_preferences"
]
