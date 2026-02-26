import time
import json
import logging
from ...infrastructure.chatbot import ChatBot
from ...infrastructure.policy_analyzer import PolicyAnalyzer
from .utils import extract_user_preferences, generate_job_reasons, clean_policy_content

logger = logging.getLogger(__name__)


class QueryProcessor:
    def __init__(self, orchestrator):
        """初始化查询处理器"""
        self.orchestrator = orchestrator
        self.policy_analyzer = PolicyAnalyzer()
    
    def process_query(self, user_input):
        """处理用户查询的完整流程"""
        start_time = time.time()
        logger.info(f"处理用户查询: {user_input[:50]}...")
        
        # 1. 检查缓存中是否有对应的查询结果（提前检查缓存，避免不必要的处理）
        from ...infrastructure.cache_manager import CacheManager
        cache_manager = CacheManager()
        
        # 2. 并行执行：意图识别 + 缓存检查
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # 提交意图识别任务
            intent_future = executor.submit(self._identify_intent, user_input)
            # 提交缓存检查任务（使用一个临时的intent_info结构，实际会被真实结果替换）
            temp_intent = {"intent": "temp", "entities": []}
            cache_future = executor.submit(cache_manager.get_query_cache, user_input, temp_intent)
            
            # 等待任务完成
            intent_info = intent_future.result()
            cached_result = cache_future.result()
        
        # 3. 验证意图是否在服务范围内
        out_of_scope_response = self._validate_intent(intent_info, start_time)
        if out_of_scope_response:
            return out_of_scope_response
        
        # 4. 检查缓存中是否有对应的查询结果（使用真实的intent_info）
        cached_result = cache_manager.get_query_cache(user_input, intent_info)
        if cached_result:
            logger.info("使用缓存的查询结果")
            # 更新执行时间
            cached_result["execution_time"] = time.time() - start_time
            cached_result["from_cache"] = True
            # 记录缓存统计
            logger.info(f"缓存命中率: {cache_manager.get_cache_stats()['hit_rate']:.2f}%")
            logger.info(f"查询处理完成（使用缓存），耗时: {cached_result['execution_time']:.2f}秒")
            return cached_result
        
        # 5. 并行检索相关政策和推荐
        relevant_policies, recommended_jobs = self._parallel_retrieve_policies_and_recommendations(user_input, intent_info)
        
        # 6. 合并LLM调用：同时生成岗位推荐理由和结构化回答
        response, recommended_jobs = self._generate_combined_response(user_input, intent_info, relevant_policies, recommended_jobs)
        
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"查询处理完成，耗时: {execution_time:.2f}秒")
        
        # 7. 构建思考过程
        thinking_process = self._build_thinking_process(intent_info, recommended_jobs, relevant_policies, user_input)
        
        # 8. 生成评估结果
        evaluation = self.orchestrator.evaluate_response(user_input, response)
        
        # 9. 构建结果
        result = {
            "intent": intent_info,
            "relevant_policies": relevant_policies,
            "response": response,
            "evaluation": evaluation,
            "execution_time": execution_time,
            "thinking_process": thinking_process,
            "recommended_jobs": recommended_jobs
        }
        
        # 10. 缓存查询结果
        cache_manager.set_query_cache(user_input, intent_info, result)
        
        # 11. 记录缓存统计
        logger.info(f"缓存命中率: {cache_manager.get_cache_stats()['hit_rate']:.2f}%")
        
        # 12. 返回结果
        return result
    
    def _identify_intent(self, user_input):
        """识别用户意图和实体"""
        intent_result = self.orchestrator.intent_recognizer.ir_identify_intent(user_input)
        return intent_result["result"]
    
    def _validate_intent(self, intent_info, start_time):
        """验证意图是否在服务范围内"""
        needs_job = intent_info.get("needs_job_recommendation", False)
        needs_policy = intent_info.get("needs_policy_recommendation", False)
        
        # 检查是否有至少一项服务需求
        if not (needs_job or needs_policy):
            # 生成超出范围的提示
            response = {
                "positive": [],
                "negative": [],
                "suggestions": [],
                "answer": f"您的意图为{intent_info.get('intent', '未知')}，我暂时无法实现"
            }
            
            end_time = time.time()
            execution_time = end_time - start_time
            logger.info(f"查询处理完成，耗时: {execution_time:.2f}秒")
            
            # 构建思考过程
            thinking_process = [
                {
                    "step": "意图与实体识别",
                    "content": f"核心意图：{intent_info['intent']}，提取实体：无",
                    "status": "completed"
                },
                {
                    "step": "意图验证",
                    "content": "您的意图超出了系统可提供的服务范围",
                    "status": "completed"
                }
            ]
            
            return {
                "intent": intent_info,
                "relevant_policies": [],
                "response": response,
                "evaluation": {
                    "score": 0,
                    "max_score": 4,
                    "policy_recall_accuracy": "0%",
                    "condition_accuracy": "0%",
                    "user_satisfaction": "0"
                },
                "execution_time": execution_time,
                "thinking_process": thinking_process,
                "recommended_jobs": [],
                "recommended_courses": []
            }
        
        return None
    
    def _retrieve_policies_and_recommendations(self, user_input, intent_info):
        """检索相关政策和推荐"""
        return self.orchestrator.policy_retriever.pr_process_query(user_input, intent_info)
    
    def _generate_job_recommendations(self, user_input, intent_info, recommended_jobs):
        """生成岗位推荐理由"""
        # 使用通用的generate_job_recommendations函数
        from .utils import generate_job_recommendations
        generate_job_recommendations(user_input, intent_info, recommended_jobs)
    
    def _process_llm_response(self, llm_response):
        """处理LLM响应"""
        if isinstance(llm_response, dict):
            content = llm_response.get("content", "")
        else:
            content = llm_response if isinstance(llm_response, str) else str(llm_response)
        
        logger.info(f"LLM原始响应: {content}")
        return content
    
    def _generate_response(self, user_input, relevant_policies, recommended_jobs):
        """生成结构化回答"""
        return self.orchestrator.response_generator.rg_generate_response(
            user_input,
            relevant_policies,
            "通用场景",
            recommended_jobs=recommended_jobs
        )
    
    def _build_thinking_process(self, intent_info, recommended_jobs, relevant_policies, user_input):
        """构建思考过程"""
        # 提取实体信息
        entities_info = intent_info.get('entities', [])
        entity_descriptions = []
        for entity in entities_info:
            entity_type = entity.get('type', '')
            entity_value = entity.get('value', '')
            entity_descriptions.append(f"{entity_value}({entity_type})")
        
        # 构建详细的思考过程
        substeps = []
        
        # 只有当需要岗位推荐时，才添加岗位检索子步骤
        needs_job_recommendation = intent_info.get("needs_job_recommendation", False)
        if needs_job_recommendation and recommended_jobs:
            # 构建详细的岗位分析内容
            job_analysis = self._build_job_analysis(recommended_jobs, entities_info)
            substeps.append({
                "step": "岗位检索",
                "content": job_analysis,
                "status": "completed"
            })
        
        # 总是添加政策检索子步骤
        if relevant_policies:
            substeps.append({
                "step": "政策检索",
                "content": f"分析 {len(relevant_policies)} 条相关政策",
                "status": "completed",
                "substeps": []
            })
        
        # 构建详细的精准检索与推理内容
        retrieval_content = "基于用户需求进行多维度分析："
        needs_policy_recommendation = intent_info.get("needs_policy_recommendation", False)
        if needs_job_recommendation and recommended_jobs:
            retrieval_content += f"\n- 岗位匹配：分析了{len(recommended_jobs)}个岗位，重点匹配证书、工作模式和补贴需求"
        if needs_policy_recommendation and relevant_policies:
            retrieval_content += f"\n- 政策检索：分析了{len(relevant_policies)}条相关政策，重点检查申请条件和补贴标准"
        
        # 为精准检索与推理步骤的政策检索子步骤添加详细政策分析
        policy_substeps = []
        if relevant_policies:
            policy_substeps = self._build_policy_substeps(relevant_policies, user_input, intent_info)
        
        # 构建完整的思考过程
        thinking_process = [
            {
                "step": "意图与实体识别",
                "content": f"核心意图：{intent_info['intent']}，提取实体：{', '.join(entity_descriptions)}",
                "status": "completed"
            },
            {
                "step": "精准检索与推理",
                "content": retrieval_content,
                "status": "completed",
                "substeps": substeps
            }
        ]
        
        if policy_substeps:
            # 找到政策检索子步骤并添加详细分析
            for substep in thinking_process[1]['substeps']:
                if substep.get('step') == "政策检索":
                    substep['substeps'] = policy_substeps
                    break
        
        return thinking_process
    
    def _build_job_analysis(self, recommended_jobs, entities_info):
        """构建详细的岗位分析内容"""
        job_analysis = ""
        if recommended_jobs:
            job_analysis = "多维度匹配分析："
            # 检查是否有JOB_A02
            job_a02 = next((job for job in recommended_jobs if job.get('job_id') == 'JOB_A02'), None)
            if job_a02:
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
                
                # 生成岗位分析
                if has_advanced_cert:
                    job_analysis += "\n- 硬性条件：JOB_A02（职业技能培训讲师）接受全职/兼职，且'高级电工证'符合岗位要求"
                elif has_middle_cert:
                    job_analysis += "\n- 硬性条件：JOB_A02（职业技能培训讲师）接受全职/兼职，且'中级电工证'符合岗位要求"
                else:
                    job_analysis += "\n- 硬性条件：JOB_A02（职业技能培训讲师）接受全职/兼职，符合岗位技能要求"
                
                if has_fixed_time:
                    job_analysis += "\n- 软性条件：'固定时间'匹配JOB_A02的全职属性，'技能补贴申领'可通过授课间接帮助学员"
                elif has_flexible_time:
                    job_analysis += "\n- 软性条件：'灵活时间'匹配JOB_A02的兼职属性，'技能补贴申领'可通过授课间接帮助学员"
                else:
                    job_analysis += "\n- 软性条件：JOB_A02（职业技能培训讲师）可根据需求选择全职或兼职，'技能补贴申领'可通过授课间接帮助学员"
            else:
                job_analysis += f"\n- 生成 {len(recommended_jobs)} 个岗位推荐，基于技能、经验和政策关联度"
        else:
            job_analysis = "未找到匹配的岗位"
        
        return job_analysis
    
    def _check_entity_condition(self, entities_info, condition):
        """检查实体中是否包含特定条件"""
        for entity in entities_info:
            entity_value = entity.get('value', '')
            if condition in entity_value or condition.replace('时间', '') in entity_value:
                return True
        return False
    
    def _build_policy_substeps(self, relevant_policies, user_input, intent_info):
        """构建详细的政策分析子步骤"""
        return self.policy_analyzer.build_policy_substeps(relevant_policies, user_input, intent_info)
    
    def _generate_combined_response(self, user_input, intent_info, relevant_policies, recommended_jobs):
        """合并生成岗位推荐理由和结构化回答，减少LLM调用次数"""
        # 提取用户偏好
        from .utils import extract_user_preferences
        preferences = extract_user_preferences(intent_info, user_input)
        time_preference = preferences["time_preference"]
        certificate_level = preferences["certificate_level"]
        
        # 准备数据
        relevant_policies = relevant_policies[:3]  # 只使用前3条政策
        
        # 构建合并的prompt
        prompt = self._build_combined_prompt(user_input, intent_info, relevant_policies, recommended_jobs, time_preference, certificate_level)
        
        # 使用批处理器处理任务
        from ...infrastructure.llm_batch_processor import LMBatchProcessor
        batch_processor = LMBatchProcessor()
        tasks = [{
            "id": 1,
            "type": "combined_generation",
            "prompt": prompt
        }]
        
        # 批量处理
        results = batch_processor.batch_process(tasks)
        
        # 处理结果
        job_analysis = []
        response_content = {"positive": "", "negative": "", "suggestions": ""}
        
        if results and results[0].get("result"):
            result = results[0]["result"]
            if isinstance(result, dict):
                # 提取岗位分析结果
                job_analysis = result.get('job_analysis', [])
                # 提取回答结果
                response_content = {
                    "positive": result.get('positive', ""),
                    "negative": result.get('negative', ""),
                    "suggestions": result.get('suggestions', "")
                }
        
        # 将推荐理由添加到推荐岗位中
        for job in recommended_jobs:
            job_id = job.get('job_id')
            if job_id:
                for analysis in job_analysis:
                    # 同时检查'id'和'job_id'字段，确保兼容性
                    analysis_id = analysis.get('id') or analysis.get('job_id')
                    if analysis_id == job_id:
                        # 获取推荐理由
                        reasons = analysis.get('reasons', {'positive': '', 'negative': ''})
                        # 清理岗位推荐理由，移除政策相关内容
                        from .utils import clean_policy_content
                        reasons = clean_policy_content(reasons)
                        # 更新推荐理由
                        job['reasons'] = reasons
                        break
        
        # 为没有推荐理由的岗位添加默认推荐理由
        from .utils import generate_job_reasons
        for job in recommended_jobs:
            if 'reasons' not in job:
                job['reasons'] = generate_job_reasons(job)
        
        # 确保生成不符合条件的政策信息
        if relevant_policies:
            # 提取positive中的政策ID
            import re
            positive_policies = []
            # 同时匹配中文括号和英文括号
            matches = re.findall(r'[\(（](POLICY_[A-Z0-9]+)[\)）]', response_content.get('positive', ''))
            positive_policies.extend(matches)
            
            # 为不在positive中的政策生成negative内容
            negative_content = response_content.get('negative', '')
            if not negative_content:
                for policy in relevant_policies:
                    policy_id = policy.get('policy_id', '')
                    policy_title = policy.get('title', '')
                    if policy_id not in positive_policies:
                        # 生成不符合条件的原因
                        if policy_id == "POLICY_A03":
                            # 返乡创业扶持补贴政策
                            if '带动就业' not in user_input and '就业' not in user_input:
                                negative_content += f"根据《{policy_title}》（{policy_id}），您需满足'带动3人以上就业'方可申领2万补贴，当前信息未提及，建议补充就业证明后申请。"
                        elif policy_id == "POLICY_A04":
                            # 创业场地租金补贴政策
                            if '入驻' not in user_input or '孵化基地' not in user_input:
                                negative_content += f"根据《{policy_title}》（{policy_id}），您需满足'入驻孵化基地'方可申领补贴，当前信息未提及，建议补充入驻证明后申请。"
                        elif policy_id == "POLICY_A05":
                            # 技能培训补贴政策
                            if '技能培训' not in user_input and '证书' not in user_input:
                                negative_content += f"根据《{policy_title}》（{policy_id}），您需满足'参加技能培训并取得证书'方可申领补贴，当前信息未提及，建议参加培训后申请。"
                        elif policy_id == "POLICY_A06":
                            # 退役军人创业税收优惠政策
                            if '退役' not in user_input and '军人' not in user_input:
                                negative_content += f"根据《{policy_title}》（{policy_id}），您需满足'退役军人'身份方可享受税收优惠，当前信息未提及，建议补充身份证明后申请。"
                
                if negative_content:
                    response_content['negative'] = negative_content
        
        return response_content, recommended_jobs
    
    def _build_combined_prompt(self, user_input, intent_info, relevant_policies, recommended_jobs, time_preference, certificate_level):
        """构建合并的prompt，同时生成岗位推荐理由和结构化回答"""
        # 简洁的系统指令
        prompt = f"你是专业政策咨询助手，为用户提供政策咨询和岗位推荐服务。\n\n"
        
        # 限制用户输入长度
        prompt += f"用户输入: {user_input[:80]}...\n\n"
        
        # 只包含必要的政策信息
        simplified_policies = []
        for policy in relevant_policies[:3]:  # 限制最多3个政策
            simplified_policy = {
                "policy_id": policy.get("policy_id"),
                "title": policy.get("title"),
                "category": policy.get("category"),
                "key_info": policy.get("key_info")
            }
            simplified_policies.append(simplified_policy)
        
        prompt += f"政策: {json.dumps(simplified_policies, ensure_ascii=False, separators=(',', ':'))}\n\n"
        
        # 只包含必要的岗位信息
        simplified_jobs = []
        for job in recommended_jobs[:5]:  # 限制最多5个岗位
            simplified_job = {
                "job_id": job.get("job_id"),
                "title": job.get("title"),
                "req": job.get("requirements", [])[:2],  # 只取前2个要求
                "feat": job.get("features", "")[:50]  # 限制特点长度
            }
            simplified_jobs.append(simplified_job)
        
        prompt += f"岗位: {json.dumps(simplified_jobs, ensure_ascii=False, separators=(',', ':'))}\n\n"
        
        # 简洁的用户偏好信息
        pref_str = []
        if time_preference:
            pref_str.append(f"时间:{time_preference}")
        if certificate_level:
            pref_str.append(f"证书:{certificate_level}")
        if pref_str:
            prompt += f"偏好: {'; '.join(pref_str)}\n\n"
        
        # 核心任务要求
        prompt += f"任务: 同时完成以下两个任务\n"
        prompt += f"1. 岗位推荐理由：为每个岗位生成3条简洁推荐理由，使用①②③编号格式\n"
        prompt += f"2. 政策咨询回答：生成结构化的政策咨询回答，包括肯定部分、否定部分和主动建议\n\n"
        
        # 输出格式
        prompt += f"输出格式：\n"
        prompt += f"{{\n"
        prompt += f"  \"job_analysis\":[{{\"id\":\"岗位ID\",\"title\":\"岗位标题\",\"reasons\":{{\"positive\":\"推荐理由\",\"negative\":\"\"}}}}],\n"
        prompt += f"  \"positive\":\"符合条件的政策及内容\",\n"
        prompt += f"  \"negative\":\"不符合条件的政策及原因\",\n"
        prompt += f"  \"suggestions\":\"主动建议\"\n"
        prompt += f"}}\n\n"
        
        # 简洁的示例
        prompt += f"示例：\n"
        prompt += f"{{\n"
        prompt += f"  \"job_analysis\":[{{\"id\":\"JOB_A02\",\"title\":\"职业技能培训讲师\",\"reasons\":{{\"positive\":\"①持有中级电工证符合要求；②兼职模式满足灵活时间；③岗位特点与经验匹配\",\"negative\":\"\"}}}}],\n"
        prompt += f"  \"positive\":\"您可申请《创业担保贷款贴息政策》（POLICY_A01）：最高贷50万、期限3年，LPR-150BP以上部分财政贴息。\",\n"
        prompt += f"  \"negative\":\"根据《返乡创业扶持补贴政策》（POLICY_A03），您需满足'带动3人以上就业'方可申领2万补贴，当前信息未提及，建议补充就业证明后申请。\",\n"
        prompt += f"  \"suggestions\":\"简历优化方案：1. 突出与推荐岗位相关的核心技能；2. 强调工作经验和成就；3. 展示学习能力和适应能力；4. 确保简历格式清晰，重点突出。\"\n"
        prompt += f"}}"
        
        # 严格限制prompt长度
        if len(prompt) > 1000:
            prompt = prompt[:1000] + "...\n\n请直接输出JSON格式回答。"
        
        logger.info(f"生成的合并提示: {prompt[:100]}...")
        return prompt
    
    def _parallel_retrieve_policies_and_recommendations(self, user_input, intent_info):
        """并行检索相关政策和推荐，提高处理效率"""
        import concurrent.futures
        
        # 创建线程池
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # 提交政策检索任务
            policy_future = executor.submit(self.orchestrator.policy_retriever.pr_retrieve_policies, 
                                         intent_info["intent"], intent_info["entities"], user_input)
            # 提交岗位推荐任务
            job_future = executor.submit(self._retrieve_jobs_direct, user_input, intent_info)
            
            # 等待任务完成
            relevant_policies = policy_future.result()
            recommended_jobs = job_future.result()
        
        return relevant_policies, recommended_jobs
    
    def _retrieve_jobs_direct(self, user_input, intent_info):
        """直接检索推荐岗位，避免重复执行"""
        logger.info("开始检索推荐岗位...")
        # 直接使用job_matcher匹配岗位
        from ...business.job_matcher import JobMatcher
        job_matcher = JobMatcher()
        entities = intent_info.get("entities", [])
        matched_jobs = job_matcher.match_jobs_by_entities(entities, user_input)
        
        # 去重
        seen_job_ids = set()
        unique_jobs = []
        for job in matched_jobs:
            job_id = job.get("job_id")
            if job_id not in seen_job_ids:
                seen_job_ids.add(job_id)
                unique_jobs.append(job)
        recommended_jobs = unique_jobs[:3]  # 最多返回3个岗位
        logger.info(f"岗位检索完成，找到 {len(recommended_jobs)} 个推荐岗位")
        return recommended_jobs
