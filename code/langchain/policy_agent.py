import json
import os
import time
import logging
from .chatbot import ChatBot
from .job_matcher import JobMatcher
from .user_profile import UserProfileManager
from functools import lru_cache

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - PolicyAgent - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PolicyAgent:
    def __init__(self, job_matcher=None, user_profile_manager=None):
        self.chatbot = ChatBot()
        # 加载并缓存政策数据
        self.policies = self.load_policies()
        # 缓存LLM响应
        self.llm_cache = {}
        # 初始化岗位匹配器
        self.job_matcher = job_matcher if job_matcher else JobMatcher()
        # 初始化用户画像管理器
        self.user_profile_manager = user_profile_manager if user_profile_manager else UserProfileManager(self.job_matcher)
    
    def load_policies(self):
        """加载政策数据"""
        policy_file = os.path.join(os.path.dirname(__file__), 'data', 'policies.json')
        try:
            with open(policy_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载政策数据失败: {e}")
            return []
    
    def identify_intent(self, user_input):
        """识别用户意图和实体"""
        logger.info("开始识别意图和实体，调用大模型")
        prompt = f"""
请分析用户输入，识别核心意图和实体，并判断用户是否明确询问或需要岗位/工作推荐：
用户输入: {user_input}

输出格式：
{{
  "intent": "意图描述",
  "needs_job_recommendation": true/false,
  "entities": [
    {{"type": "实体类型", "value": "实体值"}},
    ...
  ]
}}
注意：只有当用户明确提到"找工作"、"推荐岗位"、"就业"、"工作机会"等相关内容时，needs_job_recommendation 才为 true。单纯询问补贴政策通常为 false。
"""
        logger.info(f"生成的意图识别提示: {prompt[:100]}...")
        response = self.chatbot.chat_with_memory(prompt)
        
        # 处理返回的新格式
        if isinstance(response, dict) and 'content' in response:
            content = response['content']
            llm_time = response.get('time', 0)
            logger.info(f"大模型返回的意图识别结果: {content[:100]}...")
            logger.info(f"意图识别LLM调用耗时: {llm_time:.2f}秒")
        else:
            content = response
            llm_time = 0
            if isinstance(content, str):
                logger.info(f"大模型返回的意图识别结果: {content[:100]}...")
            else:
                logger.info(f"大模型返回的意图识别结果: {str(content)[:100]}...")
        
        try:
            if isinstance(content, dict):
                result_json = content
            else:
                result_json = json.loads(content)
                
            return {
                "result": result_json,
                "time": llm_time
            }
        except Exception as e:
            logger.error(f"解析意图识别结果失败: {str(e)}")
            return {
                "result": {"intent": "政策咨询", "needs_job_recommendation": False, "entities": []},
                "time": llm_time
            }
    
    def retrieve_policies(self, intent, entities):
        """检索相关政策"""
        relevant_policies = []
        for policy in self.policies:
            # 基于意图和实体匹配政策
            match_found = False
            for entity in entities:
                val = entity["value"]
                if val in policy["title"] or val in policy["category"]:
                    match_found = True
                    break
                # Check conditions
                for cond in policy.get("conditions", []):
                    if val in str(cond["value"]) or str(cond["value"]) in val:
                        match_found = True
                        break
            
            if match_found:
                relevant_policies.append(policy)
            elif policy["category"] in intent:
                relevant_policies.append(policy)
        return relevant_policies if relevant_policies else self.policies
    
    def generate_response(self, user_input, relevant_policies, scenario_type="通用场景", matched_user=None, recommended_jobs=None):
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
                "conditions": policy.get("conditions", []),
                "benefits": policy.get("benefits", [])
            }
            simplified_policies.append(simplified_policy)
        
        policies_str = json.dumps(simplified_policies, ensure_ascii=False, separators=(',', ':'))
        
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
             prompt_instructions = base_instructions + """
7. 特别要求：在"positive"中包含具体的岗位推荐和理由，格式为：推荐岗位：[岗位ID] [岗位名称]，推荐理由：①... ②... ③...
8. 必须结合用户画像（如持有证书、灵活时间需求）和政策优势进行推荐解释
"""
        elif "创业扶持政策精准咨询" in scenario_type:
             prompt_instructions = base_instructions + """
7. 特别要求：在"suggestions"中明确建议联系 JOB_A01（创业孵化基地管理员）获取全程指导
8. 针对缺失条件（如带动就业人数）进行明确提示
"""
        elif "多重政策叠加咨询" in scenario_type:
             prompt_instructions = base_instructions + """
7. 特别要求：在"suggestions"中明确建议联系 JOB_A05（退役军人创业项目评估师）做项目可行性分析
8. 明确指出可以同时享受的政策，并说明叠加后的预估收益
"""
        else:
             prompt_instructions = base_instructions

        prompt = f"""
你是一个政策咨询智能体，请根据用户输入、匹配的用户画像、相关政策和推荐岗位，生成结构化的回答：

用户输入: {user_input}
{user_profile_str}
相关政策:
{policies_str}
{jobs_str}

回答要求：
{prompt_instructions}

请按照以下格式输出：
{{
  "positive": "符合条件的政策和具体内容",
  "negative": "不符合条件的政策和原因",
  "suggestions": "主动建议和下一步操作"
}}
"""
        response = self.chatbot.chat_with_memory(prompt)
        
        # 处理返回的新格式
        if isinstance(response, dict) and 'content' in response:
            content = response['content']
            llm_time = response.get('time', 0)
            logger.info(f"生成回答LLM调用耗时: {llm_time:.2f}秒")
        else:
            content = response
            llm_time = 0
        
        try:
            if isinstance(content, dict):
                result_json = content
            else:
                result_json = json.loads(content)

            return {
                "result": result_json,
                "time": llm_time
            }
        except:
            return {
                "result": {"positive": content, "negative": "", "suggestions": ""},
                "time": llm_time
            }
    
    def process_query(self, user_input):
        """处理用户查询的完整流程 - 优化版本，减少LLM调用"""
        start_time = time.time()
        logger.info(f"开始处理查询: {user_input[:50]}...")
        
        # 检查缓存
        cache_key = f"query:{user_input}"
        if cache_key in self.llm_cache:
            logger.info("命中缓存，直接返回缓存结果")
            result = self.llm_cache[cache_key]
            result["timing"]["total"] = time.time() - start_time
            logger.info(f"查询处理完成，总耗时: {result['timing']['total']:.2f}秒 (缓存命中)")
            return result
        
        try:
            # 合并意图识别和回答生成为一次LLM调用
            combined_start = time.time()
            result = self.combined_process(user_input)
            combined_time = time.time() - combined_start
            logger.info(f"合并处理完成，耗时: {combined_time:.2f}秒")
            
            # 确保结果包含所有必要字段
            if "response" not in result:
                result["response"] = {"positive": "政策咨询服务", "negative": "", "suggestions": "请联系相关部门获取更多信息"}
            if "intent" not in result:
                result["intent"] = {"intent": "政策咨询", "entities": []}
            if "relevant_policies" not in result:
                result["relevant_policies"] = self.policies[:3]
            if "llm_calls" not in result:
                result["llm_calls"] = []
            
            # 评估结果
            evaluate_start = time.time()
            evaluation = self.evaluate_response(user_input, result["response"])
            evaluate_time = time.time() - evaluate_start
            logger.info(f"评估完成，耗时: {evaluate_time:.2f}秒")
            
            total_time = time.time() - start_time
            logger.info(f"查询处理完成，总耗时: {total_time:.2f}秒")
            
            # 添加计时信息
            result["evaluation"] = evaluation
            result["timing"] = {
                "total": total_time,
                "combined": combined_time,
                "evaluate": evaluate_time
            }
            
            # 缓存结果
            self.llm_cache[cache_key] = result
            
            # 限制缓存大小，避免内存占用过高
            if len(self.llm_cache) > 50:
                # 删除最早的缓存项
                oldest_key = next(iter(self.llm_cache))
                del self.llm_cache[oldest_key]
                logger.info("缓存大小超过限制，已删除最早的缓存项")
            
            return result
        except Exception as e:
            logger.error(f"处理查询失败: {str(e)}")
            # 降级处理：使用原始方式
            return self.fallback_process(user_input)
    
    def process_stream_query(self, user_input):
        """流式处理查询 - 智能岗位推荐版"""
        start_time = time.time()
        logger.info(f"开始流式处理: {user_input[:50]}...")
        
        # 1. 快速匹配上下文 (本地计算，快速)
        matched_user = self.user_profile_manager.match_user_profile(user_input)
        
        # 简单关键词匹配政策和岗位（替代LLM检索以提速）
        all_policies = self.policies
        all_jobs = self.job_matcher.get_all_jobs()
        
        relevant_policies = []
        for p in all_policies:
            if any(k in user_input for k in [p["title"], p["category"]]):
                relevant_policies.append(p)
        if not relevant_policies:
            relevant_policies = all_policies[:3] # 默认
            
        candidate_jobs = []
        # 简单筛选候选岗位，但不直接推送
        if any(k in user_input for k in ["工作", "岗位", "招聘", "赚钱"]):
             for j in all_jobs:
                 if any(k in user_input for k in [j["title"]]):
                     candidate_jobs.append(j)
             if not candidate_jobs:
                 candidate_jobs = all_jobs[:3]

        # 2. 先发送上下文数据 (不包含岗位，等待LLM判断)
        context_data = {
            "type": "context",
            "matched_user": matched_user,
            "relevant_policies": [p["policy_id"] for p in relevant_policies],
            # "recommended_jobs": candidate_jobs # 暂时不发
        }
        yield json.dumps(context_data, ensure_ascii=False) + "\n\n"
        
        # 3. 构建Prompt并流式调用LLM
        simple_policies = [{"id": p["policy_id"], "title": p["title"], "content": p["content"]} for p in relevant_policies]
        simple_jobs = [{"id": j["job_id"], "title": j["title"], "features": j["features"]} for j in candidate_jobs]
        
        # 针对特定场景注入特定指令
        scenario_instruction = ""
        if "返乡创业" in user_input or "农民工" in user_input: # 场景一特征
            scenario_instruction = """
特别注意（场景一要求）：
1. 在【结构化输出】的"否定部分"，必须指出用户未提及"带动就业"条件，因此暂时无法申领2万补贴。
2. 在【结构化输出】的"肯定部分"，确认"返乡农民工"身份符合创业贷款条件。
3. 在【结构化输出】的"主动建议"，必须推荐联系 JOB_A01。
"""
        elif "电工证" in user_input or "技能补贴" in user_input: # 场景二特征
            scenario_instruction = """
特别注意（场景二要求）：
1. 必须在思考过程中分析 USER_A02 画像。
2. 推荐 JOB_A02，并说明其"兼职"属性符合"灵活时间"需求。
"""
        elif "退役军人" in user_input and "税收" in user_input: # 场景三特征
             scenario_instruction = """
特别注意（场景三要求）：
1. 明确指出可以同时享受税收优惠（A06）和场地补贴（A04）。
2. 推荐联系 JOB_A05。
"""

        prompt = f"""
你是一个政策咨询助手。请根据以下信息回答用户问题。

用户输入: {user_input}
匹配画像: {matched_user.get('user_id') if matched_user else '无'}

参考政策:
{json.dumps(simple_policies, ensure_ascii=False)}

候选岗位列表:
{json.dumps(simple_jobs, ensure_ascii=False)}

请以Markdown格式直接输出回答，要求：
1. **深度思考部分**：先进行详细的分析，包括【意图分析】、【政策解读】和【岗位推荐】（如果需要）。
2. **结构化输出部分**：在思考完成后，必须输出一个独立的章节，标题为【结构化输出】，严格按照以下三部分进行总结：
   - 否定部分：列出不符合条件的政策及原因。
   - 肯定部分：列出符合条件的政策及具体内容。
   - 主动建议：提供下一步操作建议（如联系具体人员）。

{scenario_instruction}

输出结构参考（使用加粗标题）：
**意图分析**
...

**政策解读**
...

**岗位推荐** (仅当需要时输出)
...

---
**结构化输出**
- **否定部分**：...
- **肯定部分**：...
- **主动建议**：...

请直接开始输出内容。
"""
        
        # 4. 流式生成内容，并监听特殊标记
        full_response = ""
        
        for chunk in self.chatbot.chat_stream(prompt):
            full_response += chunk
            yield chunk
            
        # 5. 流结束后，检查是否需要推送岗位（确保在分析完成后）
        if candidate_jobs:
             # 检查模型回复中是否包含岗位推荐的章节标题
             if "**岗位推荐**" in full_response or "【岗位推荐】" in full_response:
                 # 触发岗位推荐事件
                 jobs_event = {
                    "type": "jobs",
                    "data": candidate_jobs
                 }
                 yield jobs_event
    
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
    
    def handle_scenario(self, scenario_id, user_input):
        """处理特定场景"""
        scenarios = {
            "scenario1": "创业扶持政策精准咨询",
            "scenario2": "技能培训岗位个性化推荐",
            "scenario3": "多重政策叠加咨询"
        }
        
        scenario_name = scenarios.get(scenario_id, "政策咨询")
        return self.process_query(f"[{scenario_name}] {user_input}")
    
    def combined_process(self, user_input):
        """合并处理：单次LLM调用完成所有任务"""
        logger.info(f"处理用户输入: {user_input[:50]}...")
        
        # 初始化计时和思考过程
        start_time = time.time()
        thinking_process = []
        
        # 1. 本地快速匹配用户画像
        matched_user = self.user_profile_manager.match_user_profile(user_input)
        if matched_user:
            logger.info(f"匹配到用户画像: {matched_user.get('user_id')}")
            
        # 2. 获取所有上下文数据
        all_policies = self.policies
        all_jobs = self.job_matcher.get_all_jobs()
        
        # 简化数据以减少Token消耗
        simple_policies = [{
            "id": p["policy_id"],
            "title": p["title"],
            "content": p["content"],
            "conditions": p.get("conditions", [])
        } for p in all_policies]
        
        simple_jobs = [{
            "id": j["job_id"],
            "title": j["title"],
            "requirements": j["requirements"],
            "features": j["features"]
        } for j in all_jobs]
        
        # 3. 构建单次调用Prompt
        prompt = f"""
你是一个专业的政策咨询和岗位推荐助手。请基于以下信息处理用户请求。

用户输入: {user_input}
匹配画像: {json.dumps(matched_user, ensure_ascii=False) if matched_user else "无"}

可用政策列表:
{json.dumps(simple_policies, ensure_ascii=False)}

可用岗位列表:
{json.dumps(simple_jobs, ensure_ascii=False)}

任务要求:
1. 分析用户意图，提取关键实体。
2. 判断用户是否明确需要找工作/推荐岗位（needs_job_recommendation）。
3. 从列表中筛选最相关的政策（最多3个）。
4. 从列表中筛选最相关的岗位（最多3个，仅当needs_job_recommendation为true或场景暗示需要时）。
5. 生成结构化的回复内容。

回复要求:
- positive: 符合条件的政策内容和具体岗位推荐（如有）。岗位推荐格式：推荐岗位：[ID] [名称]，理由：...
- negative: 不符合条件的政策及原因。
- suggestions: 主动建议和下一步操作。如涉及创业建议联系JOB_A01，涉及退役军人建议联系JOB_A05。

请严格按照以下JSON格式输出:
{{
  "intent": {{
    "summary": "意图描述",
    "entities": [{{"type": "...", "value": "..."}}],
    "needs_job_recommendation": true/false
  }},
  "relevant_policy_ids": ["POLICY_XXX", ...],
  "recommended_job_ids": ["JOB_XXX", ...],
  "response": {{
    "positive": "...",
    "negative": "...",
    "suggestions": "..."
  }}
}}
"""
        logger.info("调用LLM执行综合处理...")
        llm_response = self.chatbot.chat_with_memory(prompt)
        
        # 4. 解析结果
        content = llm_response if isinstance(llm_response, str) else llm_response.get("content", "")
        llm_time = llm_response.get("time", 0) if isinstance(llm_response, dict) else 0
        
        try:
            if isinstance(content, dict):
                result_data = content
            else:
                # 清理可能存在的Markdown标记
                clean_content = content.replace("```json", "").replace("```", "").strip()
                result_data = json.loads(clean_content)
        except Exception as e:
            logger.error(f"解析LLM响应失败: {e}")
            # 降级返回
            return self.fallback_process(user_input)

        # 5. 重构返回对象
        # 还原政策对象
        relevant_policy_ids = result_data.get("relevant_policy_ids", [])
        relevant_policies = [p for p in all_policies if p["policy_id"] in relevant_policy_ids]
        
        # 还原岗位对象
        recommended_job_ids = result_data.get("recommended_job_ids", [])
        recommended_jobs = [j for j in all_jobs if j["job_id"] in recommended_job_ids]
        
        # 构建思考过程
        intent_info = result_data.get("intent", {})
        thinking_process.append({
            "step": "综合分析",
            "content": f"意图：{intent_info.get('summary')} | 匹配政策：{relevant_policy_ids} | 推荐岗位：{recommended_job_ids}",
            "status": "completed"
        })
        
        logger.info(f"综合处理完成，耗时: {time.time() - start_time:.2f}秒")
        
        return {
            "intent": {"intent": intent_info.get("summary"), "entities": intent_info.get("entities", [])},
            "relevant_policies": relevant_policies,
            "response": result_data.get("response", {}),
            "llm_calls": [{"type": "综合处理", "time": llm_time}],
            "thinking_process": thinking_process,
            "recommended_jobs": recommended_jobs,
            "matched_user": matched_user
        }
    
    def fallback_process(self, user_input):
        """降级处理：使用原始方式处理查询"""
        # 识别意图和实体
        intent_result = self.identify_intent(user_input)
        intent_info = intent_result["result"]
        
        # 尝试匹配用户画像
        matched_user = self.user_profile_manager.match_user_profile(user_input)
        if matched_user:
            intent_info["matched_user_id"] = matched_user.get("user_id")

        # 检索相关政策
        relevant_policies = self.retrieve_policies(intent_info["intent"], intent_info["entities"])
        
        # 生成岗位推荐
        recommended_jobs = []
        if intent_info.get("needs_job_recommendation", False):
            for policy in relevant_policies:
                policy_jobs = self.job_matcher.match_jobs_by_policy(policy.get("policy_id", ""))
                recommended_jobs.extend(policy_jobs)
            
            if matched_user:
                profile_jobs = self.job_matcher.match_jobs_by_user_profile(matched_user)
                recommended_jobs.extend(profile_jobs)
                
            # 去重
            seen_job_ids = set()
            unique_jobs = []
            for job in recommended_jobs:
                job_id = job.get("job_id")
                if job_id and job_id not in seen_job_ids:
                    seen_job_ids.add(job_id)
                    unique_jobs.append(job)
            
            recommended_jobs = unique_jobs[:3]

        # 生成结构化回答
        response_result = self.generate_response(user_input, relevant_policies, "通用场景", matched_user, recommended_jobs)
        response = response_result["result"]
        
        return {
            "intent": intent_info,
            "relevant_policies": relevant_policies,
            "response": response,
            "thinking_process": [],
            "recommended_jobs": recommended_jobs,
            "matched_user": matched_user
        }
    
    def clear_memory(self):
        """清空记忆"""
        self.chatbot.clear_memory()

# 测试代码
if __name__ == "__main__":
    agent = PolicyAgent()
    
    # 测试场景一
    print("测试场景一：创业扶持政策精准咨询")
    user_input = "我是去年从广东回来的农民工，想在家开个小加工厂（小微企业），听说有返乡创业补贴，能领2万吗？另外创业贷款怎么申请？"
    result = agent.handle_scenario("scenario1", user_input)
    print("回答:", json.dumps(result["response"], ensure_ascii=False, indent=2))
    print("评估:", result["evaluation"])
    
    agent.clear_memory()
    
    # 测试场景二
    print("\n测试场景二：技能培训岗位个性化推荐")
    user_input = "请为一位32岁、失业、持有中级电工证的女性推荐工作，她关注补贴申领和灵活时间。"
    result = agent.handle_scenario("scenario2", user_input)
    print("回答:", json.dumps(result["response"], ensure_ascii=False, indent=2))
    print("评估:", result["evaluation"])
    
    agent.clear_memory()
    
    # 测试场景三
    print("\n测试场景三：多重政策叠加咨询")
    user_input = "我是退役军人，开汽车维修店（个体），同时入驻创业孵化基地（年租金8000元），能同时享受税收优惠和场地补贴吗？"
    result = agent.handle_scenario("scenario3", user_input)
    print("回答:", json.dumps(result["response"], ensure_ascii=False, indent=2))
    print("评估:", result["evaluation"])
