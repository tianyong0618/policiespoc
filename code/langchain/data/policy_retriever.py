import json
import os
import logging
from ..infrastructure.cache_manager import CacheManager
from ..infrastructure.config_manager import ConfigManager
from ..infrastructure.chatbot import ChatBot

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - PolicyRetriever - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PolicyRetriever:
    def __init__(self, cache_manager=None, config_manager=None, job_matcher=None, user_profile_manager=None):
        """初始化政策检索器"""
        # 初始化缓存和配置
        self.cache_manager = cache_manager or CacheManager()
        self.config_manager = config_manager or ConfigManager()
        # 初始化岗位匹配器和用户画像管理器
        self.job_matcher = job_matcher
        self.user_profile_manager = user_profile_manager
        # 缓存数据
        self._policies_cache = None
        self._policies_loaded = False
        self.policies = self.pr_load_policies()
        self.chatbot = ChatBot()
    
    def pr_load_policies(self):
        """加载政策数据（带缓存）"""
        # 尝试从缓存管理器获取
        cached_policies = self.cache_manager.get_policies_cache()
        if cached_policies:
            logger.info("使用缓存的政策数据")
            # 更新本地缓存
            self._policies_cache = cached_policies
            self._policies_loaded = True
            return cached_policies
        
        # 从配置中获取政策文件路径
        policy_file = self.config_manager.get('data.policy_file')
        try:
            with open(policy_file, 'r', encoding='utf-8') as f:
                policies = json.load(f)
                # 缓存数据
                self._policies_cache = policies
                self._policies_loaded = True
                # 缓存到缓存管理器
                self.cache_manager.set_policies_cache(policies)
                logger.info(f"加载政策数据成功，共 {len(policies)} 条政策")
                return policies
        except Exception as e:
            logger.error(f"加载政策数据失败: {e}")
            return []
    
    def pr_retrieve_policies(self, intent, entities, original_input=None):
        """检索相关政策"""
        relevant_policies = []
        logger.info(f"开始检索政策，意图: {intent}, 实体: {entities}")
        
        # 提取实体值和用户可能的需求关键词
        entity_values = [entity["value"] for entity in entities]
        logger.info(f"实体值列表: {entity_values}")
        
        # 检查用户具体条件 - 同时考虑实体值和原始用户输入
        entity_input_str = "".join(entity_values)
        # 使用原始用户输入作为备用，确保所有信息都被考虑
        user_input_str = original_input if original_input else entity_input_str
        logger.info(f"使用的用户输入字符串: {user_input_str}")
        
        # 从实体中提取信息
        has_veteran_entity = False
        has_migrant_entity = False
        for entity in entities:
            entity_type = entity.get('type', '')
            entity_value = entity.get('value', '')
            if entity_type == 'employment_status' and ('退役军人' in entity_value):
                has_veteran_entity = True
            elif entity_type == 'employment_status' and ('返乡农民工' in entity_value or '农民工' in entity_value or '返乡' in entity_value):
                # 避免因为用户提到"返乡创业补贴"政策名称而错误识别为返乡农民工
                if "返乡创业补贴" not in entity_value:
                    has_migrant_entity = True
        
        has_certificate = "电工证" in user_input_str or "证书" in user_input_str
        is_unemployed = "失业" in user_input_str
        # 检查用户是否是在职人员
        is_employed = "在职" in user_input_str or "工作" in user_input_str
        # 检查用户是否明确提到自己是返乡农民工
        # 注意：避免因为用户提到"返乡创业补贴"政策名称而错误识别
        has_return_home = False
        
        # 首先检查用户是否是在职人员，如果是，直接不识别为返乡人员
        if not is_employed:
            # 检查用户是否只是提到政策名称，而不是自己的身份
            mentions_policy_only = "返乡创业补贴" in user_input_str
            mentions_identity = "返乡农民工" in user_input_str or ("返乡" in user_input_str and "农民工" in user_input_str)
            
            # 如果用户只是提到政策名称，而没有提到自己的身份，不识别为返乡人员
            if not (mentions_policy_only and not mentions_identity):
                # 检查用户是否明确表示自己是返乡农民工
                explicitly_mentions_identity = (
                    "返乡农民工" in user_input_str or
                    ("我是" in user_input_str and "返乡" in user_input_str and "农民工" in user_input_str) or
                    ("是" in user_input_str and "返乡" in user_input_str and "农民工" in user_input_str) or
                    ("返乡" in user_input_str and "农民工" in user_input_str) or
                    ("回来" in user_input_str and "农民工" in user_input_str)
                )
                
                # 检查实体中是否包含返乡农民工
                has_migrant_entity_check = has_migrant_entity
                
                # 只有明确提到自己是返乡农民工，才识别为返乡人员
                if explicitly_mentions_identity or has_migrant_entity_check:
                    has_return_home = True
        has_entrepreneurship = "创业" in user_input_str or "小微企业" in user_input_str or "网店运营" in user_input_str
        has_incubator = "孵化基地" in user_input_str or "入驻" in user_input_str
        has_veteran = ("退役军人" in user_input_str or 
                      ("我是" in user_input_str and "退役军人" in user_input_str) or
                      ("是" in user_input_str and "退役军人" in user_input_str) or
                      has_veteran_entity)
        has_individual_business = "个体经营" in user_input_str or "开店" in user_input_str or "汽车维修店" in user_input_str or "维修店" in user_input_str or "经营" in user_input_str
        
        logger.info(f"用户条件检测: 证书={has_certificate}, 失业={is_unemployed}, 在职={is_employed}, 返乡={has_return_home}, 创业={has_entrepreneurship}, 孵化基地={has_incubator}, 退役军人={has_veteran}, 个体经营={has_individual_business}")
        
        # 逐个检查政策是否符合用户条件
        for policy in self.policies:
            policy_id = policy["policy_id"]
            title = policy["title"]
            conditions = policy.get("conditions", [])
            
            logger.info(f"检查政策: {policy_id} - {title}")
            
            # 根据政策ID和用户条件判断是否符合
            is_eligible = False
            
            if policy_id == "POLICY_A02":  # 职业技能提升补贴政策
                # 条件：持有职业资格证书或失业人员
                if has_certificate or is_unemployed:
                    is_eligible = True
                    logger.info(f"用户符合 {policy_id} 条件: 持有证书或失业")
            
            elif policy_id == "POLICY_A03":  # 返乡创业扶持补贴政策
                # 条件：返乡人员，创办小微企业，经营满1年，带动3人以上就业
                logger.info(f"检查POLICY_A03条件: has_return_home={has_return_home}, has_entrepreneurship={has_entrepreneurship}, is_employed={is_employed}")
                if has_return_home and has_entrepreneurship and not is_employed:
                    # 检查是否提到带动就业
                    has_employment = "带动就业" in user_input_str or "就业" in user_input_str
                    if has_employment:
                        is_eligible = True
                        logger.info(f"用户符合 {policy_id} 条件: 返乡创业且提到带动就业")
                    else:
                        # 用户未提带动就业，但仍将政策加入相关列表，后续在展示时指出缺失条件
                        is_eligible = True
                        logger.info(f"用户符合 {policy_id} 基本条件，但未提带动就业，需指出缺失条件")
                else:
                    logger.info(f"用户不符合 {policy_id} 条件: 返乡={has_return_home}, 创业={has_entrepreneurship}, 在职={is_employed}")
            
            elif policy_id == "POLICY_A04":  # 创业场地租金补贴政策
                # 条件：入驻创业孵化基地 + 创办企业
                if has_incubator and (has_entrepreneurship or has_individual_business):
                    is_eligible = True
                    logger.info(f"用户符合 {policy_id} 条件: 入驻孵化基地且创办企业")
                else:
                    logger.info(f"用户不符合 {policy_id} 条件: 入驻孵化基地={has_incubator}, 创办企业={has_entrepreneurship or has_individual_business}")
            
            elif policy_id == "POLICY_A01":  # 创业担保贷款贴息政策
                # 条件：创业者身份（高校毕业生/返乡农民工/退役军人）+ 创业需求
                if (has_return_home or has_veteran) and has_entrepreneurship and not is_employed:
                    is_eligible = True
                    logger.info(f"用户符合 {policy_id} 条件: 返乡人员或退役军人且有创业需求")
                else:
                    # 检查实体中是否有返乡农民工或退役军人
                    has_relevant_entity = False
                    for entity in entities:
                        entity_value = entity.get('value', '')
                        # 避免因为用户提到"返乡创业补贴"政策名称而错误识别
                        if "返乡创业补贴" not in entity_value:
                            if entity.get('type') == 'employment_status' and ('返乡农民工' in entity_value or '退役军人' in entity_value):
                                has_relevant_entity = True
                                break
                    if has_relevant_entity and has_entrepreneurship and not is_employed:
                        is_eligible = True
                        logger.info(f"用户符合 {policy_id} 条件: 实体中包含返乡农民工或退役军人且有创业需求")
                    else:
                        logger.info(f"用户不符合 {policy_id} 条件: 未提及返乡农民工或退役军人身份或创业需求，或为在职人员")
            
            elif policy_id == "POLICY_A05":  # 技能培训生活费补贴政策
                # 条件：脱贫人口、低保家庭成员、残疾人等
                if any(keyword in user_input_str for keyword in ["脱贫", "低保", "残疾"]):
                    is_eligible = True
                    logger.info(f"用户符合 {policy_id} 条件: 特殊群体")
            
            elif policy_id == "POLICY_A06":  # 退役军人创业税收优惠
                # 条件：退役军人且从事个体经营
                if has_veteran and has_individual_business:
                    is_eligible = True
                    logger.info(f"用户符合 {policy_id} 条件: 退役军人且从事个体经营")
            
            # 如果符合条件，添加到相关政策列表
            if is_eligible:
                relevant_policies.append(policy)
                logger.info(f"添加符合条件的政策: {policy_id} - {title}")
        
        # 限制返回的政策数量
        relevant_policies = relevant_policies[:3]
        
        logger.info(f"政策检索完成，找到 {len(relevant_policies)} 条符合条件的政策: {[p['policy_id'] for p in relevant_policies]}")
        return relevant_policies if relevant_policies else []
    
    def pr_process_query(self, user_input, intent_info):
        """处理用户查询"""
        logger.info(f"处理用户查询: {user_input[:50]}...")
        
        # 检查是否需要各项服务
        needs_job_recommendation = intent_info.get("needs_job_recommendation", False)
        needs_course_recommendation = intent_info.get("needs_course_recommendation", False)
        needs_policy_recommendation = intent_info.get("needs_policy_recommendation", False)
        
        # 1. 生成岗位推荐（仅当用户需要时）
        recommended_jobs = []
        if needs_job_recommendation and self.job_matcher:
            logger.info("用户需要岗位推荐，开始处理")
            # 直接基于用户输入和实体匹配岗位，不依赖政策
            # 提取实体信息用于岗位匹配
            entities = intent_info.get("entities", [])
            
            # 基于用户输入和实体匹配岗位
            matched_jobs = self.job_matcher.match_jobs_by_entities(entities, user_input)
            recommended_jobs.extend(matched_jobs)
            
            # 去重
            seen_job_ids = set()
            unique_jobs = []
            for job in recommended_jobs:
                job_id = job.get("job_id")
                if job_id not in seen_job_ids:
                    seen_job_ids.add(job_id)
                    unique_jobs.append(job)
            recommended_jobs = unique_jobs[:3]  # 最多返回3个岗位
            logger.info(f"生成了 {len(recommended_jobs)} 个岗位推荐")
        
        # 2. 检索相关政策（仅当用户需要时）
        relevant_policies = []
        if needs_policy_recommendation:
            logger.info("用户需要政策推荐，开始处理")
            relevant_policies = self.pr_retrieve_policies(intent_info["intent"], intent_info["entities"], user_input)
        

        
        return {
            "relevant_policies": relevant_policies,
            "recommended_jobs": recommended_jobs
        }
    
    def pr_analyze_input(self, user_input, conversation_history=None):
        """分析用户输入，判断是否需要收集更多信息"""
        logger.info(f"分析用户输入: {user_input[:50]}...")
        
        # 直接返回不需要更多信息，去掉追问功能
        logger.info("跳过信息收集，直接进行分析")
        return {
            "matched_user": None,
            "required_info": {},
            "missing_info": [],
            "needs_more_info": False
        }
    
    def pr_process_analysis(self, analysis_result, user_input, session_id=None):
        """处理分析结果，生成最终回答"""
        logger.info(f"处理分析结果, session_id: {session_id}")
        
        # 1. 获取分析结果
        matched_user = analysis_result.get("matched_user")
        
        # 2. 获取所有数据
        all_policies = self.policies
        all_jobs = self.job_matcher.get_all_jobs() if self.job_matcher else []
        
        # 3. 构建分析Prompt
        prompt = self.pr_build_analysis_prompt(user_input, matched_user, all_policies, all_jobs)
        
        # 4. 调用LLM进行分析
        llm_response = self.chatbot.chat_with_memory(prompt)
        
        # 5. 处理LLM响应
        try:
            if isinstance(llm_response, dict):
                content = llm_response.get("content", "")
            else:
                content = llm_response if isinstance(llm_response, str) else str(llm_response)
            
            # 尝试解析JSON响应
            if isinstance(content, dict):
                return content
            else:
                return json.loads(content)
        except Exception as e:
            logger.error(f"解析分析结果失败: {str(e)}")
            return {
                "error": str(e)
            }
    
    def pr_build_analysis_prompt(self, user_input, matched_user, all_policies, all_jobs):
        """构建分析Prompt"""
        prompt = f"""
你是一个专业的政策咨询助手，负责根据用户输入和提供的政策、岗位信息，生成结构化的分析结果。

用户输入: {user_input}

"""
        
        if matched_user:
            user_profile_str = f"匹配用户画像: {matched_user.get('user_id')} - {matched_user.get('description', '')}\n"
            prompt += user_profile_str
        
        prompt += "相关政策:\n"
        for policy in all_policies[:5]:  # 只使用前5个政策，避免输入过长
            prompt += f"- {policy.get('policy_id')}: {policy.get('title')} (分类: {policy.get('category')})\n"
        
        prompt += "\n相关岗位:\n"
        for job in all_jobs[:5]:  # 只使用前5个岗位，避免输入过长
            prompt += f"- {job.get('job_id')}: {job.get('title')}\n"
        

        
        prompt += "\n请根据以上信息，生成结构化的分析结果，包括：\n1. 识别用户的核心需求\n2. 匹配相关的政策和岗位\n3. 提供具体的建议和下一步行动\n\n输出格式为JSON，包含以下字段：\n{\n  \"core_needs\": [\"核心需求1\", \"核心需求2\", ...],\n  \"matched_policies\": [{\"policy_id\": \"政策ID\", \"title\": \"政策标题\", \"relevance\": \"相关性\"}, ...],\n  \"matched_jobs\": [{\"job_id\": \"岗位ID\", \"title\": \"岗位标题\", \"relevance\": \"相关性\"}, ...],\n  \"suggestions\": [\"建议1\", \"建议2\", ...]\n}\n"
        
        return prompt
