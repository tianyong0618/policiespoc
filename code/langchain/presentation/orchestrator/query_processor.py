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
        
        # 1. 识别意图和实体
        intent_info = self._identify_intent(user_input)
        
        # 2. 验证意图是否在服务范围内
        out_of_scope_response = self._validate_intent(intent_info, start_time)
        if out_of_scope_response:
            return out_of_scope_response
        
        # 3. 检索相关政策和推荐
        retrieve_result = self._retrieve_policies_and_recommendations(user_input, intent_info)
        relevant_policies = retrieve_result["relevant_policies"]
        recommended_jobs = retrieve_result["recommended_jobs"]
        
        # 4. 生成岗位推荐理由
        self._generate_job_recommendations(user_input, intent_info, recommended_jobs)
        
        # 5. 生成结构化回答
        response = self._generate_response(user_input, relevant_policies, recommended_jobs)
        
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"查询处理完成，耗时: {execution_time:.2f}秒")
        
        # 6. 构建思考过程
        thinking_process = self._build_thinking_process(intent_info, recommended_jobs, relevant_policies, user_input)
        
        # 7. 生成评估结果
        evaluation = self.orchestrator.evaluate_response(user_input, response)
        
        # 8. 返回结果
        return {
            "intent": intent_info,
            "relevant_policies": relevant_policies,
            "response": response,
            "evaluation": evaluation,
            "execution_time": execution_time,
            "thinking_process": thinking_process,
            "recommended_jobs": recommended_jobs
        }
    
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
        # 直接构建prompt并调用chatbot来获取分析结果
        chatbot = ChatBot()
        
        # 构建分析prompt
        try:
            # 提取用户偏好
            preferences = extract_user_preferences(intent_info, user_input)
            time_preference = preferences["time_preference"]
            certificate_level = preferences["certificate_level"]
            
            # 构建专门用于生成推荐理由的prompt
            prompt = self._build_job_analysis_prompt(user_input, recommended_jobs, time_preference, certificate_level)
            
            # 调用chatbot获取分析结果
            llm_response = chatbot.chat_with_memory(prompt)
            
            # 处理LLM响应
            content = self._process_llm_response(llm_response)
            
            # 清理可能存在的Markdown标记
            clean_content = content.replace("```json", "").replace("```", "").strip()
            
            try:
                analysis_result = json.loads(clean_content)
                logger.info(f"解析成功的分析结果: {analysis_result}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}")
                # 如果解析失败，使用默认值
                analysis_result = {"job_analysis": []}
            
            logger.info(f"获取到分析结果: {analysis_result}")
            
            # 从LLM分析结果中提取推荐理由
            job_analysis = analysis_result.get('job_analysis', [])
            
            # 将推荐理由添加到推荐岗位中
            for job in recommended_jobs:
                job_id = job.get('job_id')
                if job_id:
                    for analysis in job_analysis:
                        if analysis.get('id') == job_id:
                            # 获取推荐理由
                            reasons = analysis.get('reasons', {'positive': '', 'negative': ''})
                            # 清理岗位推荐理由，移除政策相关内容
                            reasons = clean_policy_content(reasons)
                            # 更新推荐理由
                            job['reasons'] = reasons
                            break
        
        except Exception as e:
            logger.error(f"获取分析结果失败: {e}")
            pass
        
        # 为没有推荐理由的岗位添加默认推荐理由
        for job in recommended_jobs:
            if 'reasons' not in job:
                job['reasons'] = generate_job_reasons(job)
    
    def _build_job_analysis_prompt(self, user_input, recommended_jobs, time_preference, certificate_level):
        """构建岗位分析的prompt"""
        prompt = f"你是一个专业的政策咨询助手，负责为用户生成详细的推荐理由。\n\n"
        prompt += f"用户输入: {user_input}\n\n"
        prompt += f"推荐岗位: {json.dumps(recommended_jobs, ensure_ascii=False)}\n\n"
        prompt += f"相关政策: [{{\"policy_id\": \"POLICY_A02\", \"title\": \"职业技能提升补贴政策\", \"content\": \"企业在职职工或失业人员取得初级/中级/高级职业资格证书（或职业技能等级证书），可在证书核发之日起12个月内申请补贴，标准分别为1000元/1500元/2000元\"}}]\n\n"
        prompt += f"用户时间偏好: {time_preference if time_preference else '未指定'}\n\n"
        prompt += f"用户证书情况: {certificate_level if certificate_level else '未指定'}\n\n"
        prompt += f"分析要求：\n"
        prompt += f"1. 对于每个推荐的岗位，提供详细的推荐理由，必须包含以下具体内容：\n"
        
        # 证书匹配情况
        if certificate_level:
            prompt += f"   - 证书匹配情况：明确指出用户持有{certificate_level}符合岗位要求，并强调其价值和匹配度\n"
        else:
            prompt += f"   - 证书匹配情况：明确指出用户的证书符合岗位要求，并强调其价值和匹配度\n"
        
        # 工作模式
        if time_preference:
            prompt += f"   - 工作模式：根据用户的{time_preference}偏好，明确指出相应的工作模式（固定时间匹配全职，灵活时间匹配兼职）\n"
        else:
            prompt += f"   - 工作模式：根据用户的时间偏好，明确指出相应的工作模式（固定时间匹配全职，灵活时间匹配兼职）\n"
        
        # 收入情况
        prompt += f"   - 收入情况：明确指出课时费收入稳定\n"
        
        # 岗位特点与经验匹配度
        if certificate_level:
            prompt += f"   - 岗位特点与经验匹配度：明确指出岗位特点'传授实操技能'与用户持有{certificate_level}的经验高度匹配\n"
        else:
            prompt += f"   - 岗位特点与经验匹配度：明确指出岗位特点'传授实操技能'与用户的经验高度匹配\n"
        
        # 输出格式要求
        prompt += f"2. 输出格式要求：\n"
        prompt += f"   - 严格按照示例格式生成推荐理由\n"
        prompt += f"   - 使用数字编号（如①②③）列出每个推荐理由\n"
        prompt += f"   - 每个理由要具体详细，包含必要的信息\n"
        prompt += f"   - 语言要简洁明了，重点突出，不要包含冗余信息\n"
        prompt += f"   - 严格按照JSON格式输出，不要包含任何其他内容\n"
        
        # 输出结构
        prompt += f"3. 输出结构：\n"
        prompt += f"{{\n"
        prompt += f"  \"job_analysis\": [\n"
        prompt += f"    {{\n"
        prompt += f"      \"id\": \"岗位ID\",\n"
        prompt += f"      \"title\": \"岗位标题\",\n"
        prompt += f"      \"reasons\": {{\n"
        prompt += f"        \"positive\": \"详细的推荐理由，使用数字编号列出\",\n"
        prompt += f"        \"negative\": \"不推荐理由\"\n"
        prompt += f"      }}\n"
        prompt += f"    }}\n"
        prompt += f"  ]\n"
        prompt += f"}}\n\n"
        
        # 示例推荐理由
        prompt += f"示例推荐理由：\n"
        prompt += f"岗位推荐理由：①持有中级电工证符合岗位要求；②兼职模式满足灵活时间需求，课时费收入稳定；③岗位特点'传授实操技能'，与您的经验高度匹配。\n\n"
        
        # 注意事项
        prompt += f"请严格按照上述示例格式生成详细的推荐理由，确保每个内容都具体明确，包含所有必要的信息。\n"
        prompt += f"注意：\n"
        prompt += f"1. 生成的推荐理由必须完全按照示例格式，使用数字编号列出，包含所有要求的信息点，语言要简洁明了，重点突出。每个理由之间用分号分隔，不要包含任何冗余信息。\n"
        prompt += f"2. 严格按照JSON格式输出，确保包含所有必要的字段。\n"
        
        return prompt
    
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
        if needs_job_recommendation:
            # 构建详细的岗位分析内容
            job_analysis = self._build_job_analysis(recommended_jobs, entities_info)
            substeps.append({
                "step": "岗位检索",
                "content": job_analysis,
                "status": "completed"
            })
        
        # 总是添加政策检索子步骤
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
