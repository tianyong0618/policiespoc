import json
import logging
from ...infrastructure.chatbot import ChatBot
from .utils import extract_user_preferences, generate_resume_suggestions, generate_job_reasons

logger = logging.getLogger(__name__)


class StreamProcessor:
    def __init__(self, orchestrator):
        """初始化流式处理器"""
        self.orchestrator = orchestrator
    
    def process_stream_query(self, user_input, session_id=None, conversation_history=None):
        """处理流式查询，支持实时响应"""
        logger.info(f"处理流式查询: {user_input[:50]}..., session_id: {session_id}")
        
        # 1. 识别意图
        intent_info = self._identify_intent(user_input)
        
        # 提取实体信息用于流式显示
        entities_info = intent_info.get('entities', [])
        entity_descriptions = self._extract_entity_descriptions(entities_info)
        
        # 构建详细的意图与实体识别内容
        intent_content = f"意图与实体识别: 核心意图：{intent_info['intent']}，提取实体：{', '.join(entity_descriptions)}"
        
        # 发送详细的意图识别思考过程
        yield json.dumps({
            "type": "thinking",
            "content": intent_content
        }, ensure_ascii=False)
        
        # 2. 验证意图是否在服务范围内
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
            
            # 发送意图验证结果
            yield json.dumps({
                "type": "thinking",
                "content": "意图验证: 您的意图超出了系统可提供的服务范围"
            }, ensure_ascii=False)
            
            # 返回分析结果
            yield json.dumps({
                "type": "analysis_result",
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
            }, ensure_ascii=False)
            
            # 分析完成
            yield json.dumps({
                "type": "analysis_complete",
                "content": "分析完成"
            }, ensure_ascii=False)
        else:
            # 3. 分析用户输入
            analysis_result = self.orchestrator.policy_retriever.pr_analyze_input(user_input, conversation_history)
            
            # 4. 处理分析结果
            if analysis_result.get('needs_more_info', False):
                # 需要追问
                yield json.dumps({
                    "type": "follow_up",
                    "content": analysis_result.get('follow_up_question'),
                    "missing_info": analysis_result.get('missing_info')
                }, ensure_ascii=False)
            else:
                # 开始分析
                yield json.dumps({
                    "type": "analysis_start",
                    "content": "开始分析用户需求..."
                }, ensure_ascii=False)
                
                # 5. 检索政策和推荐（仅对需要的服务）
                retrieve_result = self.orchestrator.policy_retriever.pr_process_query(user_input, intent_info)
                relevant_policies = retrieve_result["relevant_policies"]
                recommended_jobs = retrieve_result["recommended_jobs"]
                recommended_courses = []
                
                # 构建精准检索与推理内容
                retrieval_content = self._build_retrieval_content(needs_job, needs_policy)
                
                # 发送精准检索与推理的开始
                yield json.dumps({
                    "type": "thinking",
                    "content": retrieval_content
                }, ensure_ascii=False)
                
                # 只有当需要岗位推荐时，才发送岗位检索结果
                if needs_job:
                    yield json.dumps({
                        "type": "thinking",
                        "content": f"岗位检索: 生成 {len(recommended_jobs)} 个岗位推荐"
                    }, ensure_ascii=False)
                
                # 只有当需要政策推荐时，才发送政策检索结果
                if needs_policy:
                    yield json.dumps({
                        "type": "thinking",
                        "content": f"政策检索: 分析 {len(relevant_policies)} 条相关政策"
                    }, ensure_ascii=False)
                
                # 6. 生成回答
                yield json.dumps({
                    "type": "thinking",
                    "content": "生成结构化回答..."
                }, ensure_ascii=False)
                
                # 生成基于推荐岗位的简历优化建议
                suggestions = generate_resume_suggestions(user_input, recommended_jobs)
                
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
                
                # 生成岗位推荐理由
                self._generate_job_recommendations(user_input, intent_info, recommended_jobs)
                
                # 7. 返回分析结果
                yield json.dumps({
                    "type": "analysis_result",
                    "content": "",
                    "intent": intent_info,
                    "relevant_policies": relevant_policies,
                    "recommended_jobs": recommended_jobs,
                    "recommended_courses": recommended_courses,
                    "response": response,
                    "thinking_process": thinking_process
                }, ensure_ascii=False)
                
                # 8. 分析完成
                yield json.dumps({
                    "type": "analysis_complete",
                    "content": "分析完成"
                }, ensure_ascii=False)
    
    def _identify_intent(self, user_input):
        """识别用户意图和实体"""
        intent_result = self.orchestrator.intent_recognizer.ir_identify_intent(user_input)
        return intent_result["result"]
    
    def _extract_entity_descriptions(self, entities_info):
        """提取实体描述"""
        entity_descriptions = []
        for entity in entities_info:
            entity_type = entity.get('type', '')
            entity_value = entity.get('value', '')
            entity_descriptions.append(f"{entity_value}({entity_type})")
        return entity_descriptions
    
    def _build_retrieval_content(self, needs_job, needs_policy):
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
    
    def _build_job_analysis(self, recommended_jobs, entities_info):
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
                if i == 0:
                    job_analysis += "\n- 硬性条件："
                else:
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
                if i == 0:
                    job_analysis += "\n- 软性条件："
                else:
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
    
    def _check_entity_condition(self, entities_info, condition):
        """检查实体中是否包含特定条件"""
        for entity in entities_info:
            entity_value = entity.get('value', '')
            if condition in entity_value or condition.replace('时间', '') in entity_value:
                return True
        return False
    
    def _build_policy_substep(self, relevant_policies, user_input, intent_info):
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
    
    def _build_policy_substeps(self, relevant_policies, user_input, intent_info):
        """构建详细的政策分析子步骤"""
        policy_substeps = []
        # 检查用户是否提到带动就业
        user_input_str = user_input if isinstance(user_input, str) else str(user_input)
        has_employment = "带动就业" in user_input_str or "就业" in user_input_str or "带动" in user_input_str
        
        for policy in relevant_policies:
            policy_id = policy.get('policy_id', '')
            policy_title = policy.get('title', '')
            
            if policy_id == "POLICY_A03":
                # 返乡创业扶持补贴政策
                substep = self._analyze_policy_a03(user_input_str, has_employment)
            elif policy_id == "POLICY_A01":
                # 创业担保贷款贴息政策
                substep = self._analyze_policy_a01(user_input_str, intent_info)
            elif policy_id == "POLICY_A02":
                # 失业人员职业培训补贴政策
                substep = self._analyze_policy_a02(user_input_str)
            elif policy_id == "POLICY_A04":
                # 创业场地租金补贴政策
                substep = self._analyze_policy_a04(user_input_str)
            elif policy_id == "POLICY_A06":
                # 退役军人创业税收优惠政策
                substep = self._analyze_policy_a06(user_input_str)
            else:
                # 其他政策
                substep = {
                    "step": f"检索{policy_id}",
                    "content": f"分析{policy_title}的适用条件"
                }
            
            policy_substeps.append(substep)
        
        return policy_substeps
    
    def _analyze_policy_a03(self, user_input_str, has_employment):
        """分析 POLICY_A03 政策"""
        has_business = "小微企业" in user_input_str or "小加工厂" in user_input_str
        has_operation_time = "经营" in user_input_str or "正常经营" in user_input_str or "经营时间" in user_input_str
        
        if has_employment and has_business and has_operation_time:
            return {
                "step": "检索POLICY_A03",
                "content": "判断\"创办小微企业+正常经营1年+带动3人以上就业\"可申领2万一次性补贴，用户已提及所有条件，符合条件"
            }
        elif has_employment:
            missing_conditions = []
            if not has_business:
                missing_conditions.append("创办主体为小微企业")
            if not has_operation_time:
                missing_conditions.append("经营时间≥1年")
            if missing_conditions:
                return {
                    "step": "检索POLICY_A03",
                    "content": f"判断\"创办小微企业+正常经营1年+带动3人以上就业\"可申领2万一次性补贴，用户已提及带动就业，但未提及{', '.join(missing_conditions)}，需指出缺失条件"
                }
            else:
                return {
                    "step": "检索POLICY_A03",
                    "content": "判断\"创办小微企业+正常经营1年+带动3人以上就业\"可申领2万一次性补贴，用户已提及带动就业，符合条件"
                }
        else:
            return {
                "step": "检索POLICY_A03",
                "content": "判断\"创办小微企业+正常经营1年+带动3人以上就业\"可申领2万一次性补贴，用户未提\"带动就业\"，需指出缺失条件"
            }
    
    def _analyze_policy_a01(self, user_input_str, intent_info):
        """分析 POLICY_A01 政策"""
        # 从实体中提取信息
        has_veteran_entity = False
        has_migrant_entity = False
        has_business_entity = False
        
        for entity in intent_info.get('entities', []):
            entity_type = entity.get('type', '')
            entity_value = entity.get('value', '')
            if entity_type == 'employment_status' and ('退役军人' in entity_value):
                has_veteran_entity = True
            elif entity_type == 'employment_status' and ('返乡农民工' in entity_value or '农民工' in entity_value or '返乡' in entity_value):
                has_migrant_entity = True
            elif entity_type == 'business_type' and ('小微企业' in entity_value or '小加工厂' in entity_value):
                has_business_entity = True
            elif entity_type == 'concern' and ('创业' in entity_value or '创业贷款' in entity_value):
                has_business_entity = True
        
        # 从用户输入中提取信息（作为备用）
        has_veteran_input = "退役军人" in user_input_str
        has_migrant_input = ("返乡农民工" in user_input_str or 
                           ("回来" in user_input_str and "农民工" in user_input_str) or
                           ("返乡" in user_input_str and "农民工" in user_input_str))
        has_business_input = "创业" in user_input_str or "企业" in user_input_str or "开店" in user_input_str or "汽车维修店" in user_input_str or "小微企业" in user_input_str or "小加工厂" in user_input_str
        
        # 综合判断
        has_veteran = has_veteran_entity or has_veteran_input
        has_migrant = has_migrant_entity or has_migrant_input
        has_identity = has_veteran or has_migrant
        has_business = has_business_entity or has_business_input
        
        if has_identity and has_business:
            identity_type = "退役军人" if has_veteran else "返乡农民工"
            return {
                "step": "检索POLICY_A01",
                "content": f"判断\"{identity_type}+创业\"可申请创业担保贷款贴息，用户已提及相关条件，符合条件"
            }
        else:
            missing_conditions = []
            if not has_identity:
                missing_conditions.append("返乡农民工或退役军人身份")
            if not has_business:
                missing_conditions.append("创业需求")
            if missing_conditions:
                return {
                    "step": "检索POLICY_A01",
                    "content": f"判断\"返乡农民工或退役军人+创业\"可申请创业担保贷款贴息，用户未提及{', '.join(missing_conditions)}，需指出缺失条件"
                }
            else:
                return {
                    "step": "检索POLICY_A01",
                    "content": "判断\"返乡农民工或退役军人+创业\"可申请创业担保贷款贴息，用户已提及所有条件，符合条件"
                }
    
    def _analyze_policy_a02(self, user_input_str):
        """分析 POLICY_A02 政策"""
        has_certificate = "证书" in user_input_str or "职业资格" in user_input_str or "技能等级" in user_input_str or "证" in user_input_str
        has_employment = "在职" in user_input_str or "失业" in user_input_str or "就业" in user_input_str
        
        if has_certificate and has_employment:
            return {
                "step": "检索POLICY_A02",
                "content": "判断\"在职职工或失业人员+取得职业资格证书\"可申领技能提升补贴，用户已提及相关条件，符合条件"
            }
        else:
            missing_conditions = []
            if not has_certificate:
                missing_conditions.append("取得职业资格证书或职业技能等级证书")
            if not has_employment:
                missing_conditions.append("在职职工或失业人员身份")
            if missing_conditions:
                return {
                    "step": "检索POLICY_A02",
                    "content": f"判断\"在职职工或失业人员+取得职业资格证书\"可申领技能提升补贴，用户未提及{', '.join(missing_conditions)}，需指出缺失条件"
                }
            else:
                return {
                    "step": "检索POLICY_A02",
                    "content": "判断\"在职职工或失业人员+取得职业资格证书\"可申领技能提升补贴，用户已提及所有条件，符合条件"
                }
    
    def _analyze_policy_a04(self, user_input_str):
        """分析 POLICY_A04 政策"""
        has_employment_base = "创业孵化基地" in user_input_str or "入驻" in user_input_str or "场地" in user_input_str
        has_business = "汽车维修店" in user_input_str or "小微企业" in user_input_str or "企业" in user_input_str
        
        if has_employment_base and has_business:
            return {
                "step": "检索POLICY_A04",
                "content": "判断\"入驻创业孵化基地+创办企业\"可申领场地租金补贴，用户已提及入驻创业孵化基地和开汽车维修店，符合条件"
            }
        else:
            missing_conditions = []
            if not has_employment_base:
                missing_conditions.append("入驻创业孵化基地")
            if not has_business:
                missing_conditions.append("创办企业")
            if missing_conditions:
                return {
                    "step": "检索POLICY_A04",
                    "content": f"判断\"入驻创业孵化基地+创办企业\"可申领场地租金补贴，用户未提及{', '.join(missing_conditions)}，需指出缺失条件"
                }
            else:
                return {
                    "step": "检索POLICY_A04",
                    "content": "判断\"入驻创业孵化基地+创办企业\"可申领场地租金补贴，用户已提及所有条件，符合条件"
                }
    
    def _analyze_policy_a06(self, user_input_str):
        """分析 POLICY_A06 政策"""
        has_veteran = "退役军人" in user_input_str
        has_individual_business = "个体经营" in user_input_str or "汽车维修店" in user_input_str or "开店" in user_input_str or "维修店" in user_input_str
        
        if has_veteran and has_individual_business:
            return {
                "step": "检索POLICY_A06",
                "content": "判断\"退役军人+从事个体经营\"可享受税收优惠政策，用户已提及退役军人身份和从事个体经营，符合条件"
            }
        else:
            missing_conditions = []
            if not has_veteran:
                missing_conditions.append("退役军人身份")
            if not has_individual_business:
                missing_conditions.append("从事个体经营")
            if missing_conditions:
                return {
                    "step": "检索POLICY_A06",
                    "content": f"判断\"退役军人+从事个体经营\"可享受税收优惠政策，用户未提及{', '.join(missing_conditions)}，需指出缺失条件"
                }
            else:
                return {
                    "step": "检索POLICY_A06",
                    "content": "判断\"退役军人+从事个体经营\"可享受税收优惠政策，用户已提及所有条件，符合条件"
                }
    
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
            analysis_result = json.loads(clean_content)
            
            logger.info(f"获取到分析结果: {analysis_result}")
            
            # 从LLM分析结果中提取推荐理由
            job_analysis = analysis_result.get('job_analysis', [])
            course_analysis = analysis_result.get('course_analysis', [])
            
            # 将推荐理由添加到推荐岗位中
            for job in recommended_jobs:
                job_id = job.get('job_id')
                if job_id:
                    found = False
                    for analysis in job_analysis:
                        if analysis.get('id') == job_id:
                            job['reasons'] = analysis.get('reasons', {
                                'positive': '',
                                'negative': ''
                            })
                            found = True
                            break
                    # 如果没有找到推荐理由，添加默认推荐理由
                    if not found:
                        job['reasons'] = {
                            'positive': f"①符合岗位要求\n②与您的技能匹配\n③有相关政策支持",
                            'negative': ''
                        }
        except Exception as e:
            logger.error(f"获取分析结果失败: {e}")
            # 为没有推荐理由的岗位和课程添加默认推荐理由
            for job in recommended_jobs:
                if 'reasons' not in job:
                    job['reasons'] = {
                        'positive': f"①符合岗位要求\n②与您的技能匹配\n③有相关政策支持",
                        'negative': ''
                    }
    
    def _build_job_analysis_prompt(self, user_input, recommended_jobs, time_preference, certificate_level):
        """构建岗位分析的prompt"""
        prompt = f"你是一个专业的政策咨询助手，负责为用户生成详细的推荐理由。\n\n"
        prompt += f"用户输入: {user_input}\n\n"
        prompt += f"推荐岗位: {json.dumps(recommended_jobs, ensure_ascii=False)}\n\n"
        prompt += f"推荐课程: []\n\n"
        prompt += f"相关政策: [{{\"policy_id\": \"POLICY_A02\", \"title\": \"职业技能提升补贴政策\", \"content\": \"企业在职职工或失业人员取得初级/中级/高级职业资格证书（或职业技能等级证书），可在证书核发之日起12个月内申请补贴，标准分别为1000元/1500元/2000元\"}}]\n\n"
        prompt += f"用户时间偏好: {time_preference if time_preference else '未指定'}\n\n"
        prompt += f"用户证书情况: {certificate_level if certificate_level else '未指定'}\n\n"
        prompt += f"分析要求：\n"
        prompt += f"1. 对于每个推荐的岗位，提供详细的推荐理由，必须包含以下具体内容：\n"
        if certificate_level:
            prompt += f"   - 证书匹配情况：明确指出用户持有{certificate_level}符合岗位要求，并强调其价值和匹配度\n"
        else:
            prompt += f"   - 证书匹配情况：明确指出用户的证书符合岗位要求，并强调其价值和匹配度\n"
        if time_preference:
            if time_preference == "固定时间":
                prompt += f"   - 工作模式：明确指出全职模式满足固定时间需求\n"
            else:
                prompt += f"   - 工作模式：明确指出兼职模式满足灵活时间需求\n"
        else:
            prompt += f"   - 工作模式：明确指出可根据需求选择全职或兼职\n"
        prompt += f"   - 收入情况：明确指出课时费+补贴双重收入\n"
        if certificate_level:
            prompt += f"   - 岗位特点与经验匹配度：明确指出岗位特点'传授实操技能'与用户持有{certificate_level}的经验高度匹配\n"
        else:
            prompt += f"   - 岗位特点与经验匹配度：明确指出岗位特点'传授实操技能'与用户的经验高度匹配\n"
        
        # 输出格式要求
        prompt += f"2. 输出格式要求：\n"
        prompt += f"   - 严格按照示例格式生成推荐理由\n"
        prompt += f"   - 使用数字编号（如①②③）列出每个推荐理由\n"
        prompt += f"   - 岗位推荐理由要具体详细，包含具体的政策名称、金额、条件等\n"
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
        prompt += f"  ],\n"
        prompt += f"  \"course_analysis\": [\n"
        prompt += f"    {{\n"
        prompt += f"      \"id\": \"课程ID\",\n"
        prompt += f"      \"title\": \"课程标题\",\n"
        prompt += f"      \"reasons\": {{\n"
        prompt += f"        \"positive\": \"详细的推荐理由，使用数字编号列出\",\n"
        prompt += f"        \"negative\": \"不推荐理由\"\n"
        prompt += f"      }},\n"
        prompt += f"      \"growth_path\": \"详细的成长路径信息，包含学习内容、就业前景、可获得的最高成就\"\n"
        prompt += f"    }}\n"
        prompt += f"  ]\n"
        prompt += f"}}\n\n"
        
        # 示例推荐理由
        prompt += f"示例推荐理由：\n"
        prompt += f"①持有中级电工证符合岗位要求，可按POLICY_A02申请1500元技能补贴（若以企业在职职工身份参保，需在证书核发之日起12个月内申请）；②兼职模式满足灵活时间需求，课时费+补贴双重收入；③岗位特点'传授实操技能'，与您的经验高度匹配。\n\n"
        
        # 注意事项
        prompt += f"请严格按照上述示例格式生成详细的推荐理由，确保每个理由都具体明确，包含所有必要的信息，特别是具体的补贴金额、申请条件、收入构成和证书匹配情况。\n"
        prompt += f"注意：生成的推荐理由必须完全按照示例格式，使用数字编号列出，包含所有要求的信息点，语言要简洁明了，重点突出。每个理由之间用分号分隔，不要包含任何冗余信息。\n"
        
        return prompt
    
    def _process_llm_response(self, llm_response):
        """处理LLM响应"""
        if isinstance(llm_response, dict):
            content = llm_response.get("content", "")
        else:
            content = llm_response if isinstance(llm_response, str) else str(llm_response)
        return content
