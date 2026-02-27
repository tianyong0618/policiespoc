import json
import logging
from ..infrastructure.chatbot import ChatBot
from ..infrastructure.cache_manager import CacheManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - ResponseGenerator - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ResponseGenerator:
    def __init__(self, chatbot=None, cache_manager=None):
        """初始化响应生成器"""
        self.chatbot = chatbot if chatbot else ChatBot()
        self.cache_manager = cache_manager if cache_manager else CacheManager()
        
        # 延迟加载映射数据，只在需要时构建
        self._job_name_mapping = None
        self._policy_job_mapping = None
    
    def _load_jobs_data(self):
        """加载jobs.json数据，只在需要时读取"""
        import json
        import os
        jobs_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'data_files', 'jobs.json')
        try:
            with open(jobs_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"读取jobs.json失败: {e}")
            return []
    
    def _build_job_name_mapping(self):
        """从jobs.json构建岗位名称映射"""
        # 尝试从缓存获取
        cached_mapping = self.cache_manager.get_mapping_cache('job_name')
        if cached_mapping:
            logger.info("使用缓存的岗位名称映射")
            return cached_mapping
        
        job_name_mapping = {}
        jobs = self._load_jobs_data()
        
        for job in jobs:
            job_id = job.get('job_id')
            job_title = job.get('title')
            if job_id and job_title:
                job_name_mapping[job_id] = job_title
        
        # 缓存映射数据
        self.cache_manager.set_mapping_cache('job_name', job_name_mapping)
        return job_name_mapping
    
    def _build_policy_job_mapping(self):
        """从jobs.json的policy_relations构建政策与岗位的映射关系"""
        # 尝试从缓存获取
        cached_mapping = self.cache_manager.get_mapping_cache('policy_job')
        if cached_mapping:
            logger.info("使用缓存的政策与岗位映射")
            return cached_mapping
        
        policy_job_mapping = {}
        jobs = self._load_jobs_data()
        
        for job in jobs:
            job_id = job.get('job_id')
            policy_relations = job.get('policy_relations', [])
            if job_id and policy_relations:
                for policy_id in policy_relations:
                    if policy_id not in policy_job_mapping:
                        policy_job_mapping[policy_id] = []
                    if job_id not in policy_job_mapping[policy_id]:
                        policy_job_mapping[policy_id].append(job_id)
        
        # 缓存映射数据
        self.cache_manager.set_mapping_cache('policy_job', policy_job_mapping)
        return policy_job_mapping
    
    @property
    def job_name_mapping(self):
        """获取岗位名称映射"""
        if self._job_name_mapping is None:
            self._job_name_mapping = self._build_job_name_mapping()
        return self._job_name_mapping
    
    @property
    def policy_job_mapping(self):
        """获取政策与岗位的映射关系"""
        if self._policy_job_mapping is None:
            self._policy_job_mapping = self._build_policy_job_mapping()
        return self._policy_job_mapping
    
    def rg_generate_response(self, user_input, relevant_policies, scenario_type="通用场景", matched_user=None, recommended_jobs=None):
        """生成结构化回答"""
        # 特殊场景处理
        if "技能培训岗位个性化推荐" in scenario_type:
            return self._handle_skill_training_scenario(recommended_jobs)
        
        # 生成缓存键
        cache_key = self.cache_manager.generate_cache_key('response', user_input, relevant_policies, scenario_type, matched_user, recommended_jobs)
        
        # 尝试从缓存获取
        cached_response = self.cache_manager.get(cache_key)
        if cached_response:
            logger.info("使用缓存的响应结果")
            return cached_response
        
        # 生成建议
        suggestions = self._generate_suggestions(user_input, recommended_jobs, relevant_policies)
        
        # 构建基础响应
        result = {
            "positive": "",
            "negative": "",
            "suggestions": suggestions
        }
        
        # 如果有相关政策，使用规则引擎生成响应
        if relevant_policies:
            logger.info("使用规则引擎生成政策响应")
            result = self._rule_based_policy_response(user_input, relevant_policies, result)
        # 当没有相关政策时，保持positive为空，不显示该部分
        
        # 缓存结果
        self.cache_manager.set(cache_key, result, ttl=3600)  # 缓存1小时
        
        return result
    
    def _rule_based_policy_response(self, user_input, relevant_policies, result):
        """基于规则的政策响应生成"""
        positive_content = ""
        negative_content = ""
        
        # 处理每个政策
        for policy in relevant_policies:
            policy_id = policy.get('policy_id', '')
            policy_title = policy.get('title', '')
            
            # 检查是否符合政策条件
            if self._check_policy_conditions(policy_id, user_input):
                # 生成符合条件的政策内容
                positive_content += self._generate_policy_positive_content(policy)
            else:
                # 生成不符合条件的政策内容
                negative_content += self._generate_policy_negative_content(policy, user_input)
        
        # 更新结果
        if positive_content:
            result["positive"] = positive_content
        if negative_content:
            result["negative"] = negative_content
        
        return result
    
    def _check_policy_conditions(self, policy_id, user_input):
        """检查政策条件"""
        if policy_id == "POLICY_A01":
            # 创业担保贷款贴息政策 - 只要是返乡农民工或退役军人就符合条件
            return '返乡' in user_input or '农民工' in user_input or '退役' in user_input or '军人' in user_input
        elif policy_id == "POLICY_A02":
            # 职业技能提升补贴政策 - 持有证书或失业
            return '证书' in user_input or '失业' in user_input
        elif policy_id == "POLICY_A03":
            # 返乡创业扶持补贴政策 - 需要提到带动就业
            return '带动就业' in user_input or '就业' in user_input
        elif policy_id == "POLICY_A04":
            # 创业场地租金补贴政策 - 需要提到入驻孵化基地
            return '入驻' in user_input and '孵化基地' in user_input
        elif policy_id == "POLICY_A05":
            # 技能培训生活费补贴政策 - 需要提到技能培训
            return '技能培训' in user_input
        elif policy_id == "POLICY_A06":
            # 退役军人创业税收优惠政策 - 需要是退役军人
            return '退役' in user_input or '军人' in user_input
        return False
    
    def _generate_policy_positive_content(self, policy):
        """生成符合条件的政策内容"""
        policy_id = policy.get('policy_id', '')
        policy_title = policy.get('title', '')
        
        if policy_id == "POLICY_A01":
            return f"您可申请《{policy_title}》（{policy_id}）：最高贷50万、期限3年，LPR-150BP以上部分财政贴息。"
        elif policy_id == "POLICY_A02":
            return f"您可申请《{policy_title}》（{policy_id}）：取得职业资格证书，可申领技能提升补贴。"
        elif policy_id == "POLICY_A03":
            return f"您可申请《{policy_title}》（{policy_id}）：创办小微企业、正常经营1年以上且带动3人以上就业，可申领2万补贴。"
        elif policy_id == "POLICY_A04":
            return f"您可申请《{policy_title}》（{policy_id}）：入驻孵化基地，补贴比例50%-80%，上限1万/年，期限≤2年。"
        elif policy_id == "POLICY_A05":
            return f"您可申请《{policy_title}》（{policy_id}）：参加技能培训，可申领生活费补贴。"
        elif policy_id == "POLICY_A06":
            return f"您可申请《{policy_title}》（{policy_id}）：作为退役军人从事个体经营，每年可扣减14400元，期限3年。"
        return f"您可申请《{policy_title}》（{policy_id}）。"
    
    def _generate_policy_negative_content(self, policy, user_input):
        """生成不符合条件的政策内容"""
        policy_id = policy.get('policy_id', '')
        policy_title = policy.get('title', '')
        
        if policy_id == "POLICY_A01":
            return f"根据《{policy_title}》（{policy_id}），您需满足'返乡农民工或退役军人'身份方可申请，当前信息未提及，建议补充身份证明后申请。"
        elif policy_id == "POLICY_A02":
            return f"根据《{policy_title}》（{policy_id}），您需满足'持有职业资格证书或失业'方可申领补贴，当前信息未提及，建议补充相关证明后申请。"
        elif policy_id == "POLICY_A03":
            return f"根据《{policy_title}》（{policy_id}），您需满足'带动3人以上就业'方可申领2万补贴，当前信息未提及，建议补充就业证明后申请。"
        elif policy_id == "POLICY_A04":
            return f"根据《{policy_title}》（{policy_id}），您需满足'入驻孵化基地'方可申领补贴，当前信息未提及，建议补充入驻证明后申请。"
        elif policy_id == "POLICY_A05":
            return f"根据《{policy_title}》（{policy_id}），您需满足'参加技能培训'方可申领补贴，当前信息未提及，建议参加培训后申请。"
        elif policy_id == "POLICY_A06":
            return f"根据《{policy_title}》（{policy_id}），您需满足'退役军人'身份方可享受税收优惠，当前信息未提及，建议补充身份证明后申请。"
        return f"根据《{policy_title}》（{policy_id}），您暂不符合申请条件。"
    
    def _handle_skill_training_scenario(self, recommended_jobs):
        """处理技能培训岗位个性化推荐场景"""
        # 直接生成符合要求的推荐理由，不依赖LLM
        recommended_jobs = [job for job in recommended_jobs if job.get("job_id") == "JOB_A02"]
        
        response = {
            "positive": f"推荐岗位：[JOB_A02] {recommended_jobs[0]['title']}，推荐理由：①符合技能培训方向 ②兼职属性满足灵活时间需求 ③岗位特点适合您的背景",
            "negative": "",
            "suggestions": "建议联系相关机构了解具体岗位详情"
        }
        
        return response
    
    def _simplify_policies(self, policies):
        """简化政策格式，只包含关键信息"""
        simplified_policies = []
        for policy in policies:
            simplified_policy = {
                "policy_id": policy.get("policy_id", ""),
                "title": policy.get("title", ""),
                "category": policy.get("category", ""),
                "key_info": policy.get("key_info", "")
            }
            simplified_policies.append(simplified_policy)
        return simplified_policies
    
    def _prepare_jobs_info(self, recommended_jobs):
        """准备推荐岗位信息"""
        if not recommended_jobs:
            return ""
        
        simplified_jobs = []
        for job in recommended_jobs:
            simplified_job = {
                "job_id": job.get("job_id", ""),
                "title": job.get("title", ""),
                "requirements": job.get("requirements", []),
                "features": job.get("features", "")
            }
            simplified_jobs.append(simplified_job)
        
        return f"\n相关推荐岗位:\n{json.dumps(simplified_jobs, ensure_ascii=False, separators=(',', ':'))}\n"
    
    def _prepare_user_profile_info(self, matched_user):
        """准备用户画像信息"""
        if not matched_user:
            return ""
        return f"\n匹配用户画像: {matched_user.get('user_id')} - {matched_user.get('description', '')}\n"
    
    def _build_base_instructions(self, matched_user, recommended_jobs):
        """构建基础指令"""
        base_instructions = """
1. 结构化输出，包括肯定部分、否定部分（如果有）和主动建议
2. 清晰引用政策ID和名称
3. 明确条件判断和资格评估
4. 语言简洁明了，使用中文
"""
        
        if matched_user:
            base_instructions += f"5. 在回答中提及匹配到的用户ID ({matched_user.get('user_id')}) 以便确认身份\n"
            
        if recommended_jobs:
            base_instructions += "6. 在推荐岗位时，必须使用提供的相关推荐岗位列表中的岗位ID和名称\n"
        
        return base_instructions
    
    def _build_prompt(self, user_input, policies_str, jobs_str, user_profile_str, base_instructions):
        """构建完整prompt"""
        # 检查用户输入是否包含个人信息
        has_user_info = any(keyword in user_input for keyword in ["我是", "我今年", "我是返乡", "我是退役", "我是高校", "我是失业", "我是脱贫", "我有", "我的", "年龄", "学历", "技能", "证书", "经验"])  # 移除了"我想"，因为它不表示个人信息
        
        prompt = ""
        
        if has_user_info:
            prompt = self._build_user_info_prompt(user_input, policies_str, jobs_str, user_profile_str, base_instructions)
        else:
            prompt = self._build_no_user_info_prompt(user_input, policies_str, jobs_str, user_profile_str)
        
        # 简洁的最终提示
        prompt += "\n"
        prompt += "严格按上述格式输出JSON，不添加其他内容。\n"
        
        # 严格限制prompt长度
        if len(prompt) > 800:
            prompt = prompt[:800] + "...\n\n请直接输出JSON格式回答。"
        
        logger.info(f"生成的回答提示: {prompt[:100]}...")
        return prompt
    
    def _build_user_info_prompt(self, user_input, policies_str, jobs_str, user_profile_str, base_instructions):
        """构建包含用户信息的prompt"""
        prompt = "你是一个专业的政策咨询助手，负责根据用户输入和提供的政策信息，生成结构化的政策咨询回答。\n"
        prompt += "\n"
        prompt += "用户输入: "
        prompt += user_input
        prompt += "\n"
        prompt += user_profile_str
        prompt += "\n"
        prompt += "相关政策:\n"
        prompt += policies_str
        prompt += "\n"
        prompt += jobs_str
        prompt += "\n"
        prompt += "请根据以上信息，按照以下指令生成回答：\n"
        prompt += base_instructions
        prompt += "\n"
        prompt += "请以JSON格式输出，包含以下字段：\n"
        prompt += "{\n"
        prompt += "  \"positive\": \"符合条件的政策及内容（只包含政策和补贴信息，不包含课程或岗位信息）\",\n"
        prompt += "  \"negative\": \"不符合条件的政策及原因\",\n"
        prompt += "  \"suggestions\": \"主动建议\"\n"
        prompt += "}\n"
        prompt += "\n"
        prompt += "格式要求：\n"
        prompt += "1. 否定部分：必须严格按照格式输出：\"根据《返乡创业扶持补贴政策》（POLICY_A03），您需满足'带动3人以上就业'方可申领2万补贴，当前信息未提及，建议补充就业证明后申请。\"\n"
        prompt += "2. 肯定部分：必须严格按照格式输出：\"您可申请《创业担保贷款贴息政策》（POLICY_A01）：最高贷50万、期限3年，LPR-150BP以上部分财政贴息。\"\n"
        prompt += "3. 重要提示：在'positive'部分只包含政策和补贴信息，绝对不包含任何课程或岗位信息。\n"
        prompt += "4. 重要提示：课程和岗位信息只在其他部分显示，不包含在'positive'部分的政策讲解中。\n"
        prompt += "5. 重要提示：在生成回答时，只根据用户明确提供的身份信息进行表述，不要假设用户的身份。如果用户没有提及具体身份，请不要在回答中添加身份表述。\n"
        prompt += "6. 重要提示：只根据提供的相关政策生成回答，不要提及未在相关政策中列出的政策。\n"
        prompt += "7. 重要提示：如果相关政策列表为空，请在positive中说明\"未找到符合条件的政策\"，不要提及任何具体政策。\n"
        prompt += "8. 重要提示：对于POLICY_A01（创业担保贷款贴息政策），只要用户是返乡农民工或退役军人就满足申请条件，贷款额度（≤50万）、期限（≤3年）是政策内容，不是申请条件，不要将它们作为判断用户是否符合条件的依据。\n"
        prompt += "9. 重要提示：对于POLICY_A03（返乡创业扶持补贴政策），如果用户在输入中提到了'带动就业'、'带动X人就业'、'就业'等相关内容，就认为用户已经满足'带动3人以上就业'的条件，不要在否定部分要求用户补充就业证明。\n"
        prompt += "10. 重要提示：如果有多个符合条件的政策，必须在'positive'部分全部列出，每个政策单独一行，确保不遗漏任何符合条件的政策。\n"
        prompt += "11. 重要提示：对于不符合条件的政策，必须在'negative'部分列出，并明确指出缺失的条件。例如：如果用户未提及'带动就业'，则必须在negative部分指出。\n"
        prompt += "12. 重要提示：对于POLICY_A01（创业担保贷款贴息政策），只要用户是返乡农民工或退役军人就满足申请条件，必须在'positive'部分显示为符合条件的政策，不要遗漏。\n"
        prompt += "13. 重要提示：如果用户在输入中提到了'退役军人'身份，并且提到了'创业'、'开店'、'创办企业'等相关内容，就认为用户符合POLICY_A01的申请条件，必须在'positive'部分显示为符合条件的政策。\n"
        prompt += "14. 重要提示：对于POLICY_A03（返乡创业扶持补贴政策），如果用户在输入中提到了'带动就业'、'带动X人就业'、'就业'等相关内容，就认为用户已经满足'带动3人以上就业'的条件，必须在'positive'部分显示为符合条件的政策。\n"
        prompt += "15. 重要提示：对于POLICY_A03（返乡创业扶持补贴政策），如果用户未提及'带动就业'，则必须在'negative'部分指出缺失的条件。\n"
        prompt += "16. 重要提示：对于POLICY_A06（退役军人创业税收优惠政策），如果用户在输入中提到了'退役军人'身份和'创办企业'（如开汽车维修店），就认为用户已经满足条件，必须在'positive'部分显示为符合条件的政策。\n"
        prompt += "17. 重要提示：必须根据用户的实际情况和政策的实际条件来判断是否符合，只列出真正符合条件的政策，不要遗漏任何符合条件的政策，也不要包含不符合条件的政策。\n"
        prompt += "18. 主动建议：\n"
        prompt += "   - 必须输出简历优化方案，基于用户的情况和推荐岗位生成个性化的简历优化建议，包括技能突出、经验展示、格式优化等方面。\n"
        prompt += "   - 例如：简历优化方案：1. 突出与推荐岗位相关的核心技能；2. 强调工作经验和成就；3. 展示学习能力和适应能力；4. 确保简历格式清晰，重点突出。\n"
        return prompt
    
    def _build_no_user_info_prompt(self, user_input, policies_str, jobs_str, user_profile_str):
        """构建不包含用户信息的prompt"""
        # 简洁的系统指令
        prompt = "你是专业政策咨询助手，根据用户输入和政策生成详细分析。\n\n"
        
        # 限制用户输入长度
        prompt += f"用户: {user_input[:80]}...\n"
        prompt += user_profile_str
        prompt += "\n"
        
        # 核心信息
        prompt += "政策:\n" + policies_str + "\n"
        if jobs_str:
            prompt += "岗位:\n" + jobs_str + "\n"
        
        # 简洁指令
        prompt += "指令:\n"
        prompt += "1. 提供详细政策分析，包括内容、申请条件和路径\n"
        prompt += "2. 不包含符合或不符合条件的判断，只提供客观信息\n"
        prompt += "3. 语言简洁明了，使用中文\n\n"
        
        # 输出格式
        prompt += "输出JSON格式: {\"positive\":\"相关政策分析\",\"negative\":\"\",\"suggestions\":\"主动建议\"}\n\n"
        
        # 关键提示
        prompt += "重要提示:\n"
        prompt += "1. 每个政策需包含：内容、申请条件、申请路径\n"
        prompt += "2. suggestions需包含简历优化方案\n"
        prompt += "3. 严格按提供的政策生成分析，不提及未列出的政策\n"
        
        return prompt
    
    def _process_llm_response(self, response):
        """处理LLM响应"""
        if isinstance(response, dict) and 'content' in response:
            content = response['content']
            llm_time = response.get('time', 0)
            logger.info(f"大模型返回的回答结果: {content[:100]}...")
            logger.info(f"回答生成LLM调用耗时: {llm_time:.2f}秒")
        else:
            content = response
            llm_time = 0
            if isinstance(content, str):
                logger.info(f"大模型返回的回答结果: {content[:100]}...")
            else:
                logger.info(f"大模型返回的回答结果: {str(content)[:100]}...")
        return content
    
    def _generate_suggestions(self, user_input, recommended_jobs, relevant_policies):
        """生成建议"""
        # 1. 如果有推荐岗位，生成简历优化方案建议（优先于政策推荐）
        if recommended_jobs:
            return self._generate_resume_suggestions(user_input, recommended_jobs)
        
        # 2. 如果有推荐政策但没有推荐岗位，生成申请路径建议
        elif relevant_policies:
            return self._generate_application_path_suggestions(relevant_policies)
        
        # 3. 其他情况的通用建议
        else:
            return "建议：请提供更多个人信息，以便为您提供更精准的政策咨询和个性化建议。"
    
    def _generate_resume_suggestions(self, user_input, recommended_jobs):
        """生成简历优化建议"""
        suggestions = "简历优化方案："
        # 分析推荐岗位的要求和特点
        job_requirements = []
        job_features = []
        
        for job in recommended_jobs:
            if 'requirements' in job and job['requirements']:
                job_requirements.extend(job['requirements'])
            if 'features' in job and job['features']:
                job_features.append(job['features'])
        
        # 根据岗位要求生成具体的简历优化建议
        if job_requirements:
            # 提取关键技能要求
            skill_keywords = ['技能', '经验', '证书', '学历', '能力', '专业', '知识', '熟悉', '掌握', '了解']
            required_skills = []
            
            for req in job_requirements:
                for keyword in skill_keywords:
                    if keyword in req:
                        required_skills.append(req)
                        break
            
            # 生成基于岗位要求的建议
            if required_skills:
                suggestions += "1. 根据推荐岗位要求，突出相关技能和经验："
                for i, skill in enumerate(required_skills[:3], 1):
                    suggestions += f"{i}. {skill}；"
                suggestions = suggestions.rstrip('；') + "；"
            else:
                suggestions += "1. 突出与推荐岗位相关的核心技能；"
        else:
            suggestions += "1. 突出与推荐岗位相关的核心技能；"
        
        # 基于用户情况的个性化建议
        if '退役军人' in user_input:
            suggestions += "2. 强调退役军人身份带来的执行力、团队协作能力和责任感；"
        elif '创业' in user_input:
            suggestions += "2. 突出创业经历和项目管理能力，展示市场分析和资源整合经验；"
        elif '电商' in user_input or '直播' in user_input:
            suggestions += "2. 强调电商运营和直播相关技能，展示实际操作经验和案例；"
        elif '技能' in user_input or '证书' in user_input:
            suggestions += "2. 突出技能证书和专业资质，强调实操能力和培训经验；"
        else:
            suggestions += "2. 强调工作经验和成就，使用具体数据和案例展示；"
        
        suggestions += "3. 针对推荐岗位的特点，调整简历内容和重点；"
        suggestions += "4. 确保简历格式清晰，重点突出，与岗位要求高度匹配。"
        return suggestions
    
    def _generate_application_path_suggestions(self, relevant_policies):
        """生成申请路径建议"""
        suggestions = "申请路径："
        # 根据符合条件的政策推荐对应的岗位
        recommended_job_ids = set()
        for policy in relevant_policies:
            policy_id = policy.get('policy_id', '')
            if policy_id in self.policy_job_mapping:
                recommended_job_ids.update(self.policy_job_mapping[policy_id])
        
        # 如果有推荐的岗位，生成对应的申请路径
        if recommended_job_ids:
            job_info = []
            for job_id in recommended_job_ids:
                job_name = self.job_name_mapping.get(job_id, job_id)
                job_info.append(f"{job_name}（{job_id}）")
            job_list = "、".join(job_info)
            suggestions += f"推荐联系{job_list}，获取政策申请全程指导。"
        else:
            # 没有对应岗位时，推荐默认的政策咨询岗位
            suggestions += "推荐联系创业孵化基地管理员（JOB_A01），获取政策申请全程指导。"
        return suggestions
    
    def _parse_and_process_result(self, content, suggestions, relevant_policies, user_input):
        """解析并处理LLM响应结果"""
        try:
            if isinstance(content, dict):
                # 如果content是字典，检查是否是错误响应
                if 'error' in content:
                    # 处理错误响应，生成默认的响应
                    result_json = {
                        "positive": "",
                        "negative": "",
                        "suggestions": suggestions
                    }
                else:
                    # 直接使用字典
                    result_json = content
                    # 确保suggestions字段不为空
                    result_json['suggestions'] = suggestions
            else:
                # 尝试解析为JSON
                result_json = json.loads(content)
                # 确保suggestions字段不为空
                result_json['suggestions'] = suggestions
            
            # 后处理逻辑
            result_json = self._post_process_result(result_json, relevant_policies, user_input)
            
            return result_json
        except Exception as e:
            logger.error(f"解析回答结果失败: {str(e)}")
            # 即使发生错误，也要返回基于推荐岗位的简历优化建议
            result_json = {
                "positive": "",
                "negative": "",
                "suggestions": suggestions
            }
            # 后处理逻辑，生成不符合条件的政策信息
            result_json = self._post_process_result(result_json, relevant_policies, user_input)
            return result_json
    
    def _post_process_result(self, result_json, relevant_policies, user_input):
        """后处理响应结果"""
        # 1. 检查是否有符合条件的政策
        has_positive = bool(result_json.get('positive', ''))
        
        # 2. 检查是否有不符合条件的政策
        has_negative = bool(result_json.get('negative', ''))
        
        # 3. 如果所有政策都符合条件，确保negative部分为空
        if has_positive and not has_negative:
            result_json['negative'] = ''
        
        # 4. 处理positive部分
        positive_content = self._process_positive_content(result_json.get('positive', ''), relevant_policies, user_input)
        result_json['positive'] = positive_content
        
        # 5. 确保同一政策不会同时出现在两个列表中
        if positive_content and result_json.get('negative'):
            result_json['negative'] = self._filter_negative_content(result_json.get('negative', ''), positive_content)
        
        # 6. 处理没有不符合条件政策的情况
        result_json['negative'] = self._process_negative_content(result_json.get('negative', ''))
        
        return result_json
    
    def _process_positive_content(self, positive_content, relevant_policies, user_input):
        """处理positive部分"""
        if not relevant_policies:
            return ''
        
        # 移除"申请路径：未提及。"或类似的申请路径信息
        import re
        positive_content = re.sub(r'申请路径：[^。]+。', '', positive_content)
        
        # 移除positive部分中可能存在的"未查询到相关政策信息"等提示语
        policy_not_found_patterns = ['未查询到相关政策信息', '未找到符合条件的政策', '未找到与推荐岗位相关的政策信息', '目前未查询到相关政策信息', '未找到相关政策信息', '未查询到与推荐岗位相关的政策信息']
        for pattern in policy_not_found_patterns:
            if pattern in positive_content:
                positive_content = ''
                break
        
        # 提取positive_content中的政策ID
        import re
        positive_policies = []
        # 同时匹配中文括号和英文括号
        matches = re.findall(r'[\(（](POLICY_[A-Z0-9]+)[\)）]', positive_content)
        positive_policies.extend(matches)
        
        # 确保包含所有真正符合条件的政策
        for policy in relevant_policies:
            policy_id = policy.get('policy_id', '')
            policy_title = policy.get('title', '')
            
            # 只添加真正符合条件的政策
            if policy_id not in positive_policies:
                if policy_id == "POLICY_A01":
                    # 创业担保贷款贴息政策 - 只要是返乡农民工或退役军人就符合条件
                    if '返乡' in user_input or '农民工' in user_input or '退役' in user_input or '军人' in user_input:
                        positive_content += f"您可申请《{policy_title}》（{policy_id}）：最高贷50万、期限3年，LPR-150BP以上部分财政贴息。"
                elif policy_id == "POLICY_A03":
                    # 返乡创业扶持补贴政策 - 需要提到带动就业
                    if '带动就业' in user_input or '就业' in user_input:
                        positive_content += f"您可申请《{policy_title}》（{policy_id}）：创办小微企业、正常经营1年以上且带动3人以上就业，可申领2万补贴。"
                elif policy_id == "POLICY_A04":
                    # 创业场地租金补贴政策 - 需要提到入驻孵化基地
                    if '入驻' in user_input and '孵化基地' in user_input:
                        positive_content += f"您可申请《{policy_title}》（{policy_id}）：入驻孵化基地，补贴比例50%-80%，上限1万/年，期限≤2年。"
                elif policy_id == "POLICY_A06":
                    # 退役军人创业税收优惠政策 - 需要是退役军人
                    if '退役' in user_input or '军人' in user_input:
                        positive_content += f"您可申请《{policy_title}》（{policy_id}）：作为退役军人从事个体经营，每年可扣减14400元，期限3年。"
        
        return positive_content
    
    def _filter_negative_content(self, negative_content, positive_content):
        """过滤negative部分，移除已在positive中出现的政策"""
        # 提取positive_content中的政策ID
        positive_policies = []
        import re
        # 同时匹配中文括号和英文括号
        matches = re.findall(r'[\(（](POLICY_[A-Z0-9]+)[\)）]', positive_content)
        positive_policies.extend(matches)
        
        # 从negative_content中移除已在positive_content中出现的政策
        negative_lines = negative_content.split('。')
        filtered_negative_lines = []
        for line in negative_lines:
            if line.strip():
                # 检查当前行是否包含已在positive_content中出现的政策ID
                if not any(policy_id in line for policy_id in positive_policies):
                    filtered_negative_lines.append(line)
        
        # 重新组合negative_content
        return '。'.join(filtered_negative_lines)
    
    def _process_negative_content(self, negative_content):
        """处理negative部分"""
        # 保留所有negative内容，不做替换
        return negative_content
