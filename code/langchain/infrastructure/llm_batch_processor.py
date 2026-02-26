import logging
import json
from typing import List, Dict, Any, Optional
from .chatbot import ChatBot
from .cache_manager import CacheManager

logger = logging.getLogger(__name__)

class LMBatchProcessor:
    """LLM批处理处理器，用于优化LLM调用"""
    
    def __init__(self):
        """初始化批处理器"""
        self.chatbot = ChatBot()
        self.cache_manager = CacheManager()
    
    def batch_process(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量处理LLM任务
        
        Args:
            tasks: 任务列表，每个任务包含id、prompt等信息
            
        Returns:
            处理结果列表
        """
        results = []
        
        # 1. 检查缓存
        cached_results = []
        remaining_tasks = []
        
        for task in tasks:
            cache_key = self._generate_task_cache_key(task)
            cached_result = self.cache_manager.get(cache_key)
            if cached_result:
                cached_results.append({
                    "id": task.get("id"),
                    "result": cached_result,
                    "from_cache": True
                })
            else:
                remaining_tasks.append(task)
        
        # 2. 批量处理剩余任务
        if remaining_tasks:
            # 对于不同类型的任务，采用不同的批处理策略
            # 这里我们先实现简单的逐个处理，后续可以根据需要优化为真正的批量API调用
            for task in remaining_tasks:
                try:
                    result = self._process_single_task(task)
                    results.append({
                        "id": task.get("id"),
                        "result": result,
                        "from_cache": False
                    })
                    
                    # 缓存结果
                    cache_key = self._generate_task_cache_key(task)
                    self.cache_manager.set(cache_key, result, ttl=3600)
                except Exception as e:
                    logger.error(f"处理任务失败: {e}")
                    results.append({
                        "id": task.get("id"),
                        "result": None,
                        "error": str(e),
                        "from_cache": False
                    })
        
        # 3. 合并结果
        all_results = cached_results + results
        
        # 4. 按原始顺序排序
        all_results.sort(key=lambda x: x.get("id"))
        
        return all_results
    
    def _process_single_task(self, task: Dict[str, Any]) -> Any:
        """
        处理单个任务
        
        Args:
            task: 任务信息
            
        Returns:
            处理结果
        """
        task_type = task.get("type", "general")
        prompt = task.get("prompt")
        
        if not prompt:
            raise ValueError("任务必须包含prompt")
        
        # 根据任务类型选择不同的处理方式
        if task_type == "job_analysis":
            return self._process_job_analysis(prompt)
        elif task_type == "response_generation":
            return self._process_response_generation(prompt)
        elif task_type == "combined_generation":
            return self._process_combined_generation(prompt)
        else:
            # 通用处理
            return self.chatbot.chat_with_memory(prompt)
    
    def _process_job_analysis(self, prompt: str) -> Dict[str, Any]:
        """
        处理岗位分析任务
        
        Args:
            prompt: 分析提示
            
        Returns:
            分析结果
        """
        response = self.chatbot.chat_with_memory(prompt)
        content = self._process_llm_response(response)
        
        # 清理并解析JSON
        clean_content = content.replace("```json", "").replace("```", "").strip()
        
        try:
            return json.loads(clean_content)
        except json.JSONDecodeError as e:
            logger.error(f"解析岗位分析结果失败: {e}")
            return {"job_analysis": []}
    
    def _process_response_generation(self, prompt: str) -> Dict[str, Any]:
        """
        处理响应生成任务
        
        Args:
            prompt: 生成提示
            
        Returns:
            生成结果
        """
        response = self.chatbot.chat_with_memory(prompt)
        content = self._process_llm_response(response)
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"解析响应结果失败: {e}")
            # 返回一个默认的响应，但是我们会在response_generator.py中生成不符合条件的政策信息
            return {"positive": "", "negative": "", "suggestions": ""}
    
    def _process_combined_generation(self, prompt: str) -> Dict[str, Any]:
        """
        处理合并生成任务，同时生成岗位推荐理由和结构化回答
        
        Args:
            prompt: 生成提示
            
        Returns:
            生成结果，包含job_analysis、positive、negative和suggestions
        """
        response = self.chatbot.chat_with_memory(prompt)
        content = self._process_llm_response(response)
        
        # 清理并解析JSON
        clean_content = content.replace("```json", "").replace("```", "").strip()
        
        try:
            return json.loads(clean_content)
        except json.JSONDecodeError as e:
            logger.error(f"解析合并生成结果失败: {e}")
            # 返回一个默认的响应
            return {
                "job_analysis": [],
                "positive": "",
                "negative": "",
                "suggestions": ""
            }
    
    def _process_llm_response(self, llm_response: Any) -> str:
        """
        处理LLM响应
        
        Args:
            llm_response: LLM响应
            
        Returns:
            处理后的内容
        """
        if isinstance(llm_response, dict):
            return llm_response.get("content", "")
        elif isinstance(llm_response, str):
            return llm_response
        else:
            return str(llm_response)
    
    def _generate_task_cache_key(self, task: Dict[str, Any]) -> str:
        """
        生成任务缓存键
        
        Args:
            task: 任务信息
            
        Returns:
            缓存键
        """
        task_type = task.get("type", "general")
        prompt = task.get("prompt", "")
        
        # 使用任务类型和prompt的哈希作为缓存键
        return self.cache_manager.generate_cache_key("llm_task", task_type, prompt)
