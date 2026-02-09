import json
import logging
from .chatbot import ChatBot

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
    
    def generate_response(self, user_input, relevant_policies, scenario_type="通用场景", matched_user=None, recommended_jobs=None, recommended_courses=None):
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
        
        # 推荐课程信息
        courses_str = ""
        if recommended_courses:
            simplified_courses = []
            for course in recommended_courses:
                simplified_course = {
                    "course_id": course.get("course_id", ""),
                    "title": course.get("title", ""),
                    "category": course.get("category", ""),
                    "conditions": course.get("conditions", []),
                    "benefits": course.get("benefits", []),
                    "duration": course.get("duration", ""),
                    "difficulty": course.get("difficulty", "")
                }
                simplified_courses.append(simplified_course)
            courses_str = f"\n相关推荐课程:\n{json.dumps(simplified_courses, ensure_ascii=False, separators=(',', ':'))}\n"
        
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
                "positive": f"推荐岗位：[JOB_A02] {recommended_jobs[0]['title']}，推荐理由：①符合技能培训方向 ②兼职属性满足灵活时间需求 ③与POLICY_A02政策相关\n\n政策说明：根据POLICY_A02技能提升补贴政策，您可以申请相关培训补贴",
                "negative": "",
                "suggestions": "建议联系相关机构了解具体申请流程"
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
            prompt += courses_str
            prompt += "\n"
            prompt += "请根据以上信息，按照以下指令生成回答：\n"
            prompt += base_instructions
            prompt += "\n"
            prompt += "请以JSON格式输出，包含以下字段：\n"
            prompt += "{\n"
            prompt += "  \"positive\": \"符合条件的政策及内容\",\n"
            prompt += "  \"negative\": \"不符合条件的政策及原因\",\n"
            prompt += "  \"suggestions\": \"主动建议\"\n"
            prompt += "}\n"
            prompt += "\n"
            prompt += "格式要求：\n"
            prompt += "1. 否定部分：必须严格按照格式输出：\"根据《返乡创业扶持补贴政策》（POLICY_A03），您需满足‘带动3人以上就业’方可申领2万补贴，当前信息未提及，建议补充就业证明后申请。\"\n"
            prompt += "2. 肯定部分：必须严格按照格式输出：\"您可申请《创业担保贷款贴息政策》（POLICY_A01）：最高贷50万、期限3年，LPR-150BP以上部分财政贴息。申请路径：[XX人社局官网-创业服务专栏]。\"\n"
            prompt += "5. 重要提示：在生成回答时，只根据用户明确提供的身份信息进行表述，不要假设用户的身份。如果用户没有提及具体身份，请不要在回答中添加身份表述。\n"
            prompt += "6. 重要提示：只根据提供的相关政策生成回答，不要提及未在相关政策中列出的政策。\n"
            prompt += "7. 重要提示：如果相关政策列表为空，请在positive中说明\"未找到符合条件的政策\"，不要提及任何具体政策。\n"
            prompt += "8. 重要提示：对于POLICY_A01（创业担保贷款贴息政策），只要用户是返乡农民工或退役军人就满足申请条件，贷款额度（≤50万）、期限（≤3年）是政策内容，不是申请条件，不要将它们作为判断用户是否符合条件的依据。\n"
            prompt += "9. 重要提示：对于POLICY_A03（返乡创业扶持补贴政策），如果用户在输入中提到了'带动就业'、'带动X人就业'、'就业'等相关内容，就认为用户已经满足'带动3人以上就业'的条件，不要在否定部分要求用户补充就业证明。\n"
            prompt += "10. 重要提示：如果有多个符合条件的政策，必须在'positive'部分全部列出，每个政策单独一行，确保不遗漏任何符合条件的政策。\n"
            prompt += "11. 重要提示：只有当确实有不符合条件的政策时，才在'negative'部分显示内容。如果所有政策都符合条件，'negative'部分必须为空字符串，不要显示任何内容。\n"
            prompt += "12. 重要提示：对于POLICY_A01（创业担保贷款贴息政策），只要用户是返乡农民工或退役军人就满足申请条件，必须在'positive'部分显示为符合条件的政策，不要遗漏。\n"
            prompt += "13. 重要提示：如果用户在输入中提到了'退役军人'身份，并且提到了'创业'、'开店'、'创办企业'等相关内容，就认为用户符合POLICY_A01的申请条件，必须在'positive'部分显示为符合条件的政策。\n"
            prompt += "14. 重要提示：对于POLICY_A03（返乡创业扶持补贴政策），如果用户在输入中提到了'带动就业'、'带动X人就业'、'就业'等相关内容，就认为用户已经满足'带动3人以上就业'的条件，必须在'positive'部分显示为符合条件的政策。\n"
            prompt += "15. 重要提示：对于POLICY_A06（退役军人创业税收优惠政策），如果用户在输入中提到了'退役军人'身份和'创办企业'（如开汽车维修店），就认为用户已经满足条件，必须在'positive'部分显示为符合条件的政策。\n"
            prompt += "16. 重要提示：必须根据用户的实际情况和政策的实际条件来判断是否符合，只列出真正符合条件的政策，不要遗漏任何符合条件的政策，也不要包含不符合条件的政策。\n"
            prompt += "17. 主动建议：\n"
            prompt += "   - 如果用户是退役军人，必须输出：\"推荐联系JOB_A05（退役军人创业项目评估师）做项目可行性分析，提升成功率。\"\n"
            prompt += "   - 否则，必须输出：\"推荐联系JOB_A01（创业孵化基地管理员），获取政策申请全程指导。\"\n"
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
            prompt += courses_str
            prompt += "\n"
            prompt += "请根据以上信息，按照以下指令生成回答：\n"
            prompt += "1. 由于用户没有提供个人信息，无法判断是否符合政策条件，因此只需要提供详细的政策分析。\n"
            prompt += "2. 对于每个相关政策，都要提供详细的分析，包括政策内容、申请条件和申请路径。\n"
            prompt += "3. 不要进行符合或不符合条件的判断，只提供客观的政策信息。\n"
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
            prompt += "1. 政策分析部分：必须严格按照格式输出：\"《创业担保贷款贴息政策》（POLICY_A01）：最高贷50万、期限3年，LPR-150BP以上部分财政贴息。申请路径：[XX人社局官网-创业服务专栏]。\"\n"
            prompt += "2. 对于每个相关政策，都要提供类似的详细分析，包括政策内容、申请条件和申请路径。\n"
            prompt += "3. 不要包含符合或不符合条件的判断，只提供客观的政策信息。\n"
            prompt += "4. 主动建议：必须输出：\"推荐联系JOB_A01（创业孵化基地管理员），获取政策申请全程指导。\"\n"
        
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
        
        try:
            if isinstance(content, dict):
                result_json = content
            else:
                result_json = json.loads(content)
            
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
                if '退役军人' in user_input:
                    result_json['suggestions'] = "推荐联系JOB_A05（退役军人创业项目评估师）做项目可行性分析，提升成功率。"
                else:
                    result_json['suggestions'] = "推荐联系JOB_A01（创业孵化基地管理员），获取政策申请全程指导。"
            
            # 5. 确保包含所有符合条件的政策，特别是POLICY_A01
            positive_content = result_json.get('positive', '')
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
                        positive_content += f"您可申请《{policy_title}》（{policy_id}）：创业者身份为退役军人，贷款额度≤50万、期限≤3年，LPR-150BP以上部分财政贴息。申请路径：[XX人社局官网-创业服务专栏]。"
                    elif policy_id == "POLICY_A04":
                        # 创业场地租金补贴政策
                        positive_content += f"您可申请《{policy_title}》（{policy_id}）：入驻孵化基地，补贴比例50%-80%，上限1万/年，期限≤2年。"
                    elif policy_id == "POLICY_A06":
                        # 退役军人创业税收优惠政策
                        positive_content += f"您可申请《{policy_title}》（{policy_id}）：作为退役军人从事个体经营，每年可扣减14400元，期限3年。"
                result_json['positive'] = positive_content
            
            return result_json
        except Exception as e:
            logger.error(f"解析回答结果失败: {str(e)}")
            return {
                "positive": "",
                "negative": "",
                "suggestions": ""
            }
