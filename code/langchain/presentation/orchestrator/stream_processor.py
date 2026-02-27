import json
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Generator

from ...infrastructure.chatbot import ChatBot
from ...infrastructure.policy_analyzer import PolicyAnalyzer
from ...infrastructure.cache_manager import CacheManager
from .utils import extract_user_preferences, generate_resume_suggestions, generate_job_reasons

logger = logging.getLogger(__name__)


class StreamProcessor:
    def __init__(self, orchestrator):
        """初始化流式处理器"""
        self.orchestrator = orchestrator
        self.policy_analyzer = PolicyAnalyzer()
        self.cache_manager = CacheManager()  # 类级别缓存管理器
        # 初始化线程池执行器，用于并行处理
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def process_stream_query(self, user_input: str, session_id: str = None, conversation_history: List[Dict] = None) -> Generator[str, None, None]:
        """处理流式查询，支持实时响应"""
        logger.info(f"处理流式查询: {user_input[:50]}..., session_id: {session_id}")
        
        # 生成缓存键
        cache_key = self.cache_manager.generate_cache_key('stream_query', user_input)
        
        # 检查缓存中是否有对应的流式查询结果
        # 临时禁用缓存，以确保获取最新的思考过程
        # cached_result = self._get_cached_result(cache_key)
        # if cached_result:
        #     yield from cached_result
        #     return
        
        # 用于存储流式结果的列表，以便缓存
        stream_results = []
        
        try:
            # 1. 识别意图
            intent_info = self._identify_intent(user_input)
            
            # 提取实体信息用于流式显示
            entities_info = intent_info.get('entities', [])
            entity_descriptions = self._extract_entity_descriptions(entities_info)
            
            # 构建详细的意图与实体识别内容
            intent_content = f"意图与实体识别: 核心意图：{intent_info['intent']}，提取实体：{', '.join(entity_descriptions)}"
            
            # 发送详细的意图识别思考过程
            yield from self._stream_chunk('thinking', intent_content, stream_results)
            
            # 2. 验证意图是否在服务范围内
            needs_job = intent_info.get("needs_job_recommendation", False)
            needs_policy = intent_info.get("needs_policy_recommendation", False)
            
            # 检查是否有至少一项服务需求
            if not (needs_job or needs_policy):
                yield from self._handle_out_of_scope(intent_info, entity_descriptions, stream_results)
            else:
                yield from self._handle_in_scope(user_input, intent_info, entities_info, needs_job, needs_policy, conversation_history, stream_results)
        except Exception as e:
            logger.error(f"流式处理异常: {e}")
            # 发送错误信息
            yield from self._stream_chunk('error', f"处理过程中出现错误: {str(e)}", stream_results)
        finally:
            # 缓存流式查询结果
            self._cache_result(cache_key, stream_results)
    
    def _get_cached_result(self, cache_key: str) -> List[str]:
        """获取缓存的结果"""
        cached_result = self.cache_manager.get(cache_key)
        if cached_result:
            logger.info("使用缓存的流式查询结果")
            return cached_result
        return []
    
    def _stream_chunk(self, chunk_type: str, content: Any, stream_results: List[str]) -> Generator[str, None, None]:
        """流式发送单个chunk"""
        chunk = json.dumps({
            "type": chunk_type,
            "content": content
        }, ensure_ascii=False)
        stream_results.append(chunk)
        yield chunk
    
    def _cache_result(self, cache_key: str, stream_results: List[str]):
        """缓存流式查询结果"""
        if stream_results:
            self.cache_manager.set(cache_key, stream_results, ttl=1800)  # 缓存30分钟
            logger.info("流式查询结果已缓存")
    
    def _identify_intent(self, user_input: str) -> Dict[str, Any]:
        """识别用户意图和实体"""
        try:
            intent_result = self.orchestrator.intent_recognizer.ir_identify_intent(user_input)
            return intent_result["result"]
        except Exception as e:
            logger.error(f"意图识别失败: {e}")
            # 返回默认意图
            return {
                "intent": "通用查询",
                "entities": [],
                "needs_job_recommendation": False,
                "needs_policy_recommendation": False
            }
    
    def _extract_entity_descriptions(self, entities_info: List[Dict]) -> List[str]:
        """提取实体描述"""
        entity_descriptions = []
        for entity in entities_info:
            entity_type = entity.get('type', '')
            entity_value = entity.get('value', '')
            entity_descriptions.append(f"{entity_value}({entity_type})")
        return entity_descriptions
    
    def _handle_out_of_scope(self, intent_info: Dict, entity_descriptions: List[str], stream_results: List[str]) -> Generator[str, None, None]:
        """处理超出服务范围的意图"""
        # 生成超出范围的提示
        response = {
            "positive": [],
            "negative": [],
            "suggestions": [],
            "answer": f"您的意图为{intent_info.get('intent', '未知')}，我暂时无法实现"
        }
        
        # 发送意图验证结果
        yield from self._stream_chunk('thinking', "意图验证: 您的意图超出了系统可提供的服务范围", stream_results)
        
        # 返回分析结果
        analysis_result = {
            "content": response,
            "intent": intent_info,
            "relevant_policies": [],
            "recommended_jobs": [],
            "thinking_process": [
                {
                    "step": "意图与实体识别",
                    "content": f"核心意图：{intent_info['intent']}，提取实体：{', '.join(entity_descriptions)}",
                    "status": "completed"
                },
                {
                    "step": "意图验证",
                    "content": "您的意图超出了系统可提供的服务范围",
                    "status": "completed"
                }
            ]
        }
        yield from self._stream_chunk('analysis_result', analysis_result, stream_results)
        
        # 分析完成
        yield from self._stream_chunk('analysis_complete', "分析完成", stream_results)
    
    def _handle_in_scope(self, user_input: str, intent_info: Dict, entities_info: List[Dict], 
                        needs_job: bool, needs_policy: bool, conversation_history: List[Dict], 
                        stream_results: List[str]) -> Generator[str, None, None]:
        """处理在服务范围内的意图"""
        # 3. 分析用户输入
        analysis_result = self.orchestrator.policy_retriever.pr_analyze_input(user_input, conversation_history)
        
        # 4. 处理分析结果
        if analysis_result.get('needs_more_info', False):
            # 需要追问
            follow_up_data = {
                "content": analysis_result.get('follow_up_question'),
                "missing_info": analysis_result.get('missing_info')
            }
            yield from self._stream_chunk('follow_up', follow_up_data, stream_results)
        else:
            # 开始分析
            yield from self._stream_chunk('analysis_start', "开始分析用户需求...", stream_results)
            
            # 5. 并行检索政策和推荐（仅对需要的服务）
            logger.info("开始并行处理任务")
            
            # 定义并行任务
            def retrieve_policy_data():
                """检索政策数据"""
                if needs_policy:
                    return self.orchestrator.policy_retriever.pr_process_query(user_input, intent_info)
                return {"relevant_policies": [], "recommended_jobs": []}
            
            def generate_suggestions():
                """生成简历优化建议"""
                return generate_resume_suggestions(user_input, [])
            
            # 执行并行任务
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # 提交任务
                policy_future = executor.submit(retrieve_policy_data)
                suggestions_future = executor.submit(generate_suggestions)
                
                # 获取结果
                retrieve_result = policy_future.result()
                suggestions = suggestions_future.result()
            
            relevant_policies = retrieve_result["relevant_policies"]
            recommended_jobs = retrieve_result["recommended_jobs"]
            recommended_courses = []
            
            # 构建精准检索与推理内容
            retrieval_content = self._build_retrieval_content(needs_job, needs_policy)
            
            # 发送精准检索与推理的开始
            yield from self._stream_chunk('thinking', retrieval_content, stream_results)
            
            # 发送岗位检索结果
            if needs_job:
                yield from self._stream_chunk('thinking', f"岗位检索: 生成 {len(recommended_jobs)} 个岗位推荐", stream_results)
            
            # 发送政策检索结果
            if needs_policy:
                yield from self._stream_chunk('thinking', f"政策检索: 分析 {len(relevant_policies)} 条相关政策", stream_results)
            
            # 6. 生成回答
            yield from self._stream_chunk('thinking', "生成结构化回答...", stream_results)
            
            # 生成默认的响应
            response = {
                "positive": "",
                "negative": "",
                "suggestions": suggestions
            }
            
            # 尝试调用response_generator获取更详细的响应
            try:
                generated_response = self.orchestrator.response_generator.rg_generate_response(
                    user_input,
                    relevant_policies,
                    "通用场景",
                    recommended_jobs=recommended_jobs
                )
                
                # 如果生成的响应不为空，使用它
                if generated_response and isinstance(generated_response, dict):
                    # 确保suggestions字段不为空
                    if not generated_response.get('suggestions', ''):
                        generated_response['suggestions'] = suggestions
                    response = generated_response
            except Exception as e:
                logger.error(f"生成响应失败: {e}")
                # 如果生成响应失败，使用默认的响应
                pass
            
            # 构建详细的思考过程
            thinking_process = self._build_thinking_process(needs_job, needs_policy, recommended_jobs, relevant_policies, 
                                                          entities_info, user_input, intent_info, retrieval_content)
            
            # 生成岗位推荐理由
            self._generate_job_recommendations(user_input, intent_info, recommended_jobs)
            
            # 7. 返回分析结果
        # 不符合条件的政策信息已经由response_generator处理，这里不再重复处理
            
            analysis_result_data = {
                "type": "analysis_result",
                "content": response,
                "intent": intent_info,
                "relevant_policies": relevant_policies,
                "recommended_jobs": recommended_jobs,
                "recommended_courses": recommended_courses,
                "thinking_process": thinking_process
            }
            # 确保思考过程不为空
            if not analysis_result_data["thinking_process"]:
                # 添加默认思考过程
                analysis_result_data["thinking_process"] = [
                    {
                        "step": "意图与实体识别",
                        "content": f"核心意图：{intent_info['intent']}，提取实体：{', '.join(self._extract_entity_descriptions(entities_info))}",
                        "status": "completed"
                    },
                    {
                        "step": "分析完成",
                        "content": "已完成分析，未找到相关岗位或政策信息",
                        "status": "completed"
                    }
                ]
            logger.info(f"发送analysis_result事件，思考过程长度: {len(analysis_result_data['thinking_process'])}")
            # 直接发送analysis_result_data，不使用_stream_chunk方法，因为它会添加额外的content字段
            chunk = json.dumps(analysis_result_data, ensure_ascii=False)
            stream_results.append(chunk)
            yield chunk
            
            # 8. 分析完成
            yield from self._stream_chunk('analysis_complete', "分析完成", stream_results)
    
    def _build_retrieval_content(self, needs_job: bool, needs_policy: bool) -> str:
        """构建精准检索与推理内容"""
        retrieval_content = "精准检索与推理: 详细分析相关"
        if needs_job:
            retrieval_content += "岗位、"
        if needs_policy:
            retrieval_content += "政策"
        # 移除最后的逗号
        if retrieval_content.endswith("、"):
            retrieval_content = retrieval_content[:-1]
        return retrieval_content
    
    def _build_thinking_process(self, needs_job: bool, needs_policy: bool, recommended_jobs: List[Dict], 
                               relevant_policies: List[Dict], entities_info: List[Dict], 
                               user_input: str, intent_info: Dict, retrieval_content: str) -> List[Dict]:
        """构建详细的思考过程"""
        substeps = []
        
        # 构建详细的岗位分析
        if needs_job or len(recommended_jobs) > 0:
            job_analysis = self._build_job_analysis(recommended_jobs, entities_info)
            substeps.append({
                "step": "岗位检索",
                "content": job_analysis,
                "status": "completed"
            })
        
        # 构建详细的政策分析
        if needs_policy or len(relevant_policies) > 0:
            policy_substep = self._build_policy_substep(relevant_policies, user_input, intent_info)
            substeps.append(policy_substep)
        
        # 构建完整的思考过程
        thinking_process = [
            {
                "step": "意图与实体识别",
                "content": f"核心意图：{intent_info['intent']}，提取实体：{', '.join(self._extract_entity_descriptions(entities_info))}",
                "status": "completed"
            },
            {
                "step": "精准检索与推理",
                "content": retrieval_content,
                "status": "completed",
                "substeps": substeps
            }
        ]
        
        # 确保思考过程不为空
        if not substeps:
            # 如果没有子步骤，添加一个默认的子步骤
            substeps.append({
                "step": "分析完成",
                "content": "已完成分析，未找到相关岗位或政策信息",
                "status": "completed"
            })
            # 更新思考过程
            thinking_process[1]["substeps"] = substeps
        
        return thinking_process
    
    def _build_job_analysis(self, recommended_jobs: List[Dict], entities_info: List[Dict]) -> str:
        """构建详细的岗位分析"""
        job_analysis = "多维度匹配分析："
        
        # 分析所有推荐的岗位
        if recommended_jobs:
            # 检查用户是否关注固定时间
            has_fixed_time = self._check_entity_condition(entities_info, "固定时间")
            # 检查用户是否关注灵活时间
            has_flexible_time = self._check_entity_condition(entities_info, "灵活时间")
            # 检查用户是否有高级电工证
            has_advanced_cert = self._check_entity_condition(entities_info, "高级电工证")
            # 检查用户是否有中级电工证
            has_middle_cert = self._check_entity_condition(entities_info, "中级电工证")
            # 检查用户是否有电工证
            has_electrician_cert = self._check_entity_condition(entities_info, "电工证")
            
            # 为每个推荐岗位生成分析
            for i, job in enumerate(recommended_jobs):
                job_id = job.get('job_id')
                job_title = job.get('title', '')
                
                # 生成硬性条件分析
                job_analysis += "\n- 硬性条件："
                
                if job_id == 'JOB_A02':
                    if has_advanced_cert:
                        job_analysis += f"{job_id}（{job_title}）接受全职/兼职，且'高级电工证'符合岗位要求"
                    elif has_middle_cert:
                        job_analysis += f"{job_id}（{job_title}）接受全职/兼职，且'中级电工证'符合岗位要求"
                    else:
                        job_analysis += f"{job_id}（{job_title}）接受全职/兼职，符合岗位技能要求"
                else:
                    requirements = job.get('requirements', [])
                    if requirements:
                        req_str = '、'.join(requirements[:2])
                        job_analysis += f"{job_id}（{job_title}）要求：{req_str}"
                    else:
                        job_analysis += f"{job_id}（{job_title}）符合岗位技能要求"
                
                # 生成软性条件分析
                job_analysis += "\n- 软性条件："
                
                if has_fixed_time:
                    job_analysis += "'固定时间'匹配岗位的全职属性"
                elif has_flexible_time:
                    job_analysis += "'灵活时间'匹配岗位的兼职属性"
                else:
                    job_analysis += "岗位可根据需求选择全职或兼职"
                
                # 添加技能补贴相关内容
                if '技能补贴' in job.get('features', '') or 'POLICY_A02' in job.get('policy_relations', []):
                    job_analysis += "，'技能补贴申领'可通过相关工作间接帮助学员"
        else:
            job_analysis += f"\n- 生成 {len(recommended_jobs)} 个岗位推荐，基于技能、经验和政策关联度"
        
        return job_analysis
    
    def _check_entity_condition(self, entities_info: List[Dict], condition: str) -> bool:
        """检查实体中是否包含特定条件"""
        for entity in entities_info:
            entity_value = entity.get('value', '')
            if condition in entity_value or condition.replace('时间', '') in entity_value:
                return True
        return False
    
    def _build_policy_substep(self, relevant_policies: List[Dict], user_input: str, intent_info: Dict) -> Dict:
        """构建详细的政策分析子步骤"""
        policy_substep = {
            "step": "政策检索",
            "content": f"分析 {len(relevant_policies)} 条相关政策",
            "status": "completed",
            "substeps": []
        }
        
        # 为政策检索子步骤添加详细政策分析
        policy_substeps = self._build_policy_substeps(relevant_policies, user_input, intent_info)
        if policy_substeps:
            policy_substep['substeps'] = policy_substeps
        
        return policy_substep
    
    def _build_policy_substeps(self, relevant_policies: List[Dict], user_input: str, intent_info: Dict) -> List[Dict]:
        """构建详细的政策分析子步骤"""
        try:
            return self.policy_analyzer.build_policy_substeps(relevant_policies, user_input, intent_info)
        except Exception as e:
            logger.error(f"构建政策子步骤失败: {e}")
            return []
    
    def _generate_job_recommendations(self, user_input, intent_info, recommended_jobs):
        """生成岗位推荐理由（使用规则引擎）"""
        try:
            logger.info("使用规则引擎生成岗位推荐理由")
            # 为每个岗位生成推荐理由
            for job in recommended_jobs:
                # 直接使用generate_job_reasons函数生成推荐理由，不使用LLM
                job['reasons'] = generate_job_reasons(job)
            logger.info(f"为 {len(recommended_jobs)} 个岗位生成了推荐理由")
        except Exception as e:
            logger.error(f"生成岗位推荐理由失败: {e}")
    
    def _cache_result(self, cache_key: str, stream_results: List[str]):
        """缓存结果"""
        if stream_results:
            try:
                self.cache_manager.set(cache_key, stream_results, ttl=1800)  # 缓存30分钟
                logger.info("流式查询结果已缓存")
            except Exception as e:
                logger.error(f"缓存结果失败: {e}")

