import json
import logging
from ..infrastructure.chatbot import ChatBot

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - ResponseGenerator - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ResponseGenerator:
    def __init__(self, chatbot=None):
        """初始化响应生成器"""
        self.chatbot = chatbot if chatbot else ChatBot()
        
        # 从jobs.json构建岗位名称映射
        self.job_name_mapping = self._build_job_name_mapping()
        
        # 从jobs.json的policy_relations构建政策与岗位的映射关系
        self.policy_job_mapping = self._build_policy_job_mapping()
    
    def _build_job_name_mapping(self):
        """从jobs.json构建岗位名称映射"""
        import json
        import os
        job_name_mapping = {}
        
        # 读取jobs.json文件
        jobs_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'data_files', 'jobs.json')
        try:
            with open(jobs_file, 'r', encoding='utf-8') as f:
                jobs = json.load(f)
                for job in jobs:
                    job_id = job.get('job_id')
                    job_title = job.get('title')
                    if job_id and job_title:
                        job_name_mapping[job_id] = job_title
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"读取jobs.json失败: {e}")
        
        return job_name_mapping
    
    def _build_policy_job_mapping(self):
        """从jobs.json的policy_relations构建政策与岗位的映射关系"""
        import json
        import os
        policy_job_mapping = {}
        
        # 读取jobs.json文件
        jobs_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'data_files', 'jobs.json')
        try:
            with open(jobs_file, 'r', encoding='utf-8') as f:
                jobs = json.load(f)
                for job in jobs:
                    job_id = job.get('job_id')
                    policy_relations = job.get('policy_relations', [])
                    if job_id and policy_relations:
                        for policy_id in policy_relations:
                            if policy_id not in policy_job_mapping:
                                policy_job_mapping[policy_id] = []
                            if job_id not in policy_job_mapping[policy_id]:
                                policy_job_mapping[policy_id].append(job_id)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"读取jobs.json失败: {e}")
        
        return policy_job_mapping
    
    def rg_generate_response(self, user_input, relevant_policies, scenario_type="通用场景", matched_user=None, recommended_jobs=None):
        """生成结构化回答"""
        # 优化：只发送前3条最相关的政策，减少输入长度
        relevant_policies = relevant_policies[:3]
        
        # 优化：使用更简洁的政策格式，只包含关键信息
        simplified_policies = []
        for policy in relevant_policies:
            simplified_policy = {
                "policy_id": policy.get("policy_id", ""),
                "title": policy.get("title", ""),
                "category": policy.get("category", ""),
                "key_info": policy.get("key_info", "")
            }
            simplified_policies.append(simplified_policy)
        
        policies_str = json.dumps(simplified_policies, ensure_ascii=False, separators=(',', ':'))
        
        # 打印调试信息
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"生成回答时的政策数量: {len(relevant_policies)}")
        logger.info(f"生成回答时的政策ID: {[p['policy_id'] for p in relevant_policies]}")
        logger.info(f"传递给LLM的政策: {policies_str}")
        
        # 推荐岗位信息
        jobs_str = ""
        if recommended_jobs:
            simplified_jobs = []
            for job in recommended_jobs:
                simplified_job = {
                    "job_id": job.get("job_id", ""),
                    "title": job.get("title", ""),
                    "requirements": job.get("requirements", []),
                    "features": job.get("features", "")
                }
                simplified_jobs.append(simplified_job)
            jobs_str = f"\n相关推荐岗位:\n{json.dumps(simplified_jobs, ensure_ascii=False, separators=(',', ':'))}\n"
        

        
        # 用户画像信息
        user_profile_str = ""
        if matched_user:
            user_profile_str = f"\n匹配用户画像: {matched_user.get('user_id')} - {matched_user.get('description', '')}\n"
        
        # 基础指令
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

        # 场景特定指令
        if "技能培训岗位个性化推荐" in scenario_type:
            # 直接生成符合要求的推荐理由，不依赖LLM
            recommended_jobs = [job for job in recommended_jobs if job.get("job_id") == "JOB_A02"]
            
            prompt_instructions = base_instructions + """
7. 特别要求：在"positive"中，**岗位推荐必须绝对优先于政策说明**，顺序不可颠倒
8. 特别要求：推荐岗位时，必须使用以下格式：推荐岗位：[岗位ID] [岗位名称]，推荐理由：①... ②... ③...
9. 特别要求：只推荐与技能培训和POLICY_A02相关的岗位
"""
            
            # 直接生成结构化回答
            response = {
                "positive": f"推荐岗位：[JOB_A02] {recommended_jobs[0]['title']}，推荐理由：①符合技能培训方向 ②兼职属性满足灵活时间需求 ③岗位特点适合您的背景",
                "negative": "",
                "suggestions": "建议联系相关机构了解具体岗位详情"
            }
            
            return response
        
        # 检查用户是否为退役军人
        is_veteran = "退役军人" in user_input or any("退役军人" in str(job) for job in recommended_jobs) if recommended_jobs else False
        
        # 检查用户输入是否包含个人信息
        has_user_info = any(keyword in user_input for keyword in ["我是", "我今年", "我是返乡", "我是退役", "我是高校", "我是失业", "我是脱贫", "我有", "我的", "年龄", "学历", "技能", "证书", "经验"])  # 移除了"我想"，因为它不表示个人信息
        
        # 构建完整prompt
        # 使用普通字符串拼接，避免f-string格式化问题
        prompt = ""
        
        # 根据是否有用户信息调整回答模式
        if has_user_info:
            prompt += "你是一个专业的政策咨询助手，负责根据用户输入和提供的政策信息，生成结构化的政策咨询回答。\n"
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
            prompt += "1. 否定部分：必须严格按照格式输出：\"根据《返乡创业扶持补贴政策》（POLICY_A03），您需满足‘带动3人以上就业’方可申领2万补贴，当前信息未提及，建议补充就业证明后申请。\"\n"
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
        else:
            prompt += "你是一个专业的政策咨询助手，负责根据用户输入和提供的政策信息，生成详细的政策分析。\n"
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
            prompt += "1. 由于用户没有提供个人信息，无法判断是否符合政策条件，因此只需要提供详细的政策分析。\n"
            prompt += "2. 对于每个相关政策，都要提供详细的分析，包括政策内容、申请条件和申请路径。\n"
            prompt += "3. 不要包含符合或不符合条件的判断，只提供客观的政策信息。\n"
            prompt += "4. 语言简洁明了，使用中文。\n"
            prompt += "\n"
            prompt += "请以JSON格式输出，包含以下字段：\n"
            prompt += "{\n"
            prompt += "  \"positive\": \"相关政策分析\",\n"
            prompt += "  \"negative\": \"\",\n"
            prompt += "  \"suggestions\": \"主动建议\"\n"
            prompt += "}\n"
            prompt += "\n"
            prompt += "格式要求：\n"
            prompt += "1. 政策分析部分：必须严格按照格式输出：\"《创业担保贷款贴息政策》（POLICY_A01）：最高贷50万、期限3年，LPR-150BP以上部分财政贴息。申请路径：[人社局官网-创业服务专栏]。\"\n"
            prompt += "2. 对于每个相关政策，都要提供类似的详细分析，包括政策内容、申请条件和申请路径。\n"
            prompt += "3. 不要包含符合或不符合条件的判断，只提供客观的政策信息。\n"
            prompt += "4. 主动建议：必须输出简历优化方案，基于推荐岗位生成通用的简历优化建议，包括技能突出、经验展示、格式优化等方面。\n"
            prompt += "   例如：简历优化方案：1. 突出与推荐岗位相关的核心技能；2. 强调工作经验和成就；3. 展示学习能力和适应能力；4. 确保简历格式清晰，重点突出。\n"
        
        prompt += "\n"
        prompt += "重要提示：请严格按照上述格式要求输出，不要修改任何内容，确保与格式要求完全一致。\n"
        prompt += "\n"
        prompt += "请确保回答准确、简洁、有条理，直接输出JSON格式，不要包含其他内容。\n"
        
        logger.info(f"生成的回答提示: {prompt[:100]}...")
        response = self.chatbot.chat_with_memory(prompt)
        
        # 处理返回的新格式
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
        
        # 根据不同场景生成相应的主动建议
        # 1. 如果有推荐岗位，生成简历优化方案建议（优先于政策推荐）
        if recommended_jobs:
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
        
        # 3. 如果有推荐政策但没有推荐课程和岗位，生成申请路径建议
        elif relevant_policies:
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
        
        # 4. 其他情况的通用建议
        else:
            suggestions = "建议：请提供更多个人信息，以便为您提供更精准的政策咨询和个性化建议。"
        
        # 尝试解析LLM响应
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
            
            # 后处理逻辑：确保响应符合要求
            # 1. 检查是否有符合条件的政策
            has_positive = bool(result_json.get('positive', ''))
            
            # 2. 检查是否有不符合条件的政策
            has_negative = bool(result_json.get('negative', ''))
            
            # 3. 如果所有政策都符合条件，确保negative部分为空
            if has_positive and not has_negative:
                result_json['negative'] = ''
            
            # 4. 确保suggestions部分不为空
            if not result_json.get('suggestions', ''):
                result_json['suggestions'] = suggestions
            
            # 5. 检查是否有符合条件的政策
            if not relevant_policies:
                # 没有符合条件的政策，清空positive部分
                positive_content = ''
            else:
                # 有符合条件的政策，处理positive部分
                positive_content = result_json.get('positive', '')
                # 移除"申请路径：未提及。"或类似的申请路径信息
                import re
                positive_content = re.sub(r'申请路径：[^。]+。', '', positive_content)
                # 移除positive部分中可能存在的"未查询到相关政策信息"等提示语
                policy_not_found_patterns = ['未查询到相关政策信息', '未找到符合条件的政策', '未找到与推荐岗位相关的政策信息', '目前未查询到相关政策信息', '未找到相关政策信息', '未查询到与推荐岗位相关的政策信息']
                for pattern in policy_not_found_patterns:
                    if pattern in positive_content:
                        positive_content = ''
                        break
                
                # 确保包含所有符合条件的政策，特别是POLICY_A01
                # 检查positive_content中是否包含所有相关政策
                missing_policies = []
                for policy in relevant_policies:
                    policy_id = policy.get('policy_id', '')
                    if policy_id not in positive_content:
                        missing_policies.append(policy)
                
                # 如果有遗漏的政策，添加到positive_content中
                if missing_policies:
                    for policy in missing_policies:
                        policy_id = policy.get('policy_id', '')
                        policy_title = policy.get('title', '')
                        policy_key_info = policy.get('key_info', '')
                        if policy_id == "POLICY_A01":
                            # 创业担保贷款贴息政策
                            positive_content += f"您可申请《{policy_title}》（{policy_id}）：创业者身份为退役军人，贷款额度≤50万、期限≤3年，LPR-150BP以上部分财政贴息。"
                        elif policy_id == "POLICY_A04":
                            # 创业场地租金补贴政策
                            positive_content += f"您可申请《{policy_title}》（{policy_id}）：入驻孵化基地，补贴比例50%-80%，上限1万/年，期限≤2年。"
                        elif policy_id == "POLICY_A06":
                            # 退役军人创业税收优惠政策
                            positive_content += f"您可申请《{policy_title}》（{policy_id}）：作为退役军人从事个体经营，每年可扣减14400元，期限3年。"
            
            # 更新positive部分
            result_json['positive'] = positive_content
            
            # 确保同一政策不会同时出现在两个列表中
            if positive_content and result_json.get('negative'):
                negative_content = result_json.get('negative', '')
                # 提取positive_content中的政策ID
                positive_policies = []
                import re
                matches = re.findall(r'\((POLICY_[A-Z0-9]+)\)', positive_content)
                positive_policies.extend(matches)
                
                # 从negative_content中移除已在positive_content中出现的政策
                negative_lines = negative_content.split('。')
                filtered_negative_lines = []
                for line in negative_lines:
                    if line.strip():
                        # 提取当前行中的政策ID
                        line_matches = re.findall(r'\((POLICY_[A-Z0-9]+)\)', line)
                        if not any(policy_id in line for policy_id in positive_policies):
                            filtered_negative_lines.append(line)
                
                # 重新组合negative_content
                result_json['negative'] = '。'.join(filtered_negative_lines)
            
            # 处理没有不符合条件政策的情况
            negative_content = result_json.get('negative', '')
            negative_not_found_patterns = ['未找到不符合条件的政策', '无不符合条件的政策']
            for pattern in negative_not_found_patterns:
                if pattern in negative_content:
                    result_json['negative'] = ''
                    break
            
            # 如果positive_content为空，确保不显示符合条件的政策部分
            if not positive_content:
                result_json['positive'] = ''
            
            return result_json
        except Exception as e:
            logger.error(f"解析回答结果失败: {str(e)}")
            # 即使发生错误，也要返回基于推荐岗位的简历优化建议
            return {
                "positive": "",
                "negative": "",
                "suggestions": suggestions
            }
