import time
import json
import logging
from ...business.intent_analyzer import IntentAnalyzer
from ...data.policy_retriever import PolicyRetriever
from ...business.response_generator import ResponseGenerator
from ...business.job_matcher import JobMatcher
from ...business.user_matcher import UserMatcher
from .query_processor import QueryProcessor
from .stream_processor import StreamProcessor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - Orchestrator - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self, intent_recognizer=None, policy_retriever=None, response_generator=None):
        """初始化协调器"""
        # 初始化依赖
        self.job_matcher = JobMatcher()
        self.user_profile_manager = UserMatcher(job_matcher=self.job_matcher)
        
        # 初始化三个核心模块
        self.intent_recognizer = intent_recognizer if intent_recognizer else IntentAnalyzer()
        self.policy_retriever = policy_retriever if policy_retriever else PolicyRetriever(
            job_matcher=self.job_matcher,
            user_profile_manager=self.user_profile_manager
        )
        self.response_generator = response_generator if response_generator else ResponseGenerator()
        
        # 初始化处理器
        self.query_processor = QueryProcessor(self)
        self.stream_processor = StreamProcessor(self)
    
    @property
    def policies(self):
        """获取政策列表"""
        return self.policy_retriever.policies
    
    def process_query(self, user_input):
        """处理用户查询"""
        return self.query_processor.process_query(user_input)
    
    def process_stream_query(self, user_input, session_id=None, conversation_history=None):
        """处理流式查询"""
        return self.stream_processor.process_stream_query(user_input, session_id, conversation_history)
    
    def handle_user_input(self, user_input, session_id=None, conversation_history=None):
        """处理用户输入，基于实时分析生成回答"""
        logger.info(f"处理用户输入: {user_input[:50]}..., session_id: {session_id}")
        
        # 1. 分析用户输入，判断是否需要收集更多信息
        analysis_result = self.policy_retriever.pr_analyze_input(user_input, conversation_history)
        
        # 安全处理analysis_result
        needs_more_info = False
        if isinstance(analysis_result, dict):
            needs_more_info = analysis_result.get('needs_more_info', False)
        
        if needs_more_info:
            # 需要收集更多信息，生成追问
            return {
                "type": "追问",
                "content": analysis_result.get('follow_up_question'),
                "missing_info": analysis_result.get('missing_info')
            }
        
        # 2. 收集到足够信息后，进行分析
        return self.policy_retriever.pr_process_analysis(analysis_result, user_input, session_id)
    
    def evaluate_response(self, user_input, response):
        """评估回答质量"""
        # 简单的评估逻辑
        score = 0
        if response.get("positive"):
            score += 2
        if response.get("negative"):
            score += 1
        if response.get("suggestions"):
            score += 1
        
        return {
            "score": score,
            "max_score": 4,
            "policy_recall_accuracy": "95%",  # 模拟值
            "condition_accuracy": "100%",     # 模拟值
            "user_satisfaction": "4.5"        # 模拟值
        }
