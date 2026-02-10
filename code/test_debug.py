import sys
import os

# 添加langchain模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'langchain'))

from langchain.policy_agent import PolicyAgent
from langchain.response_generator import ResponseGenerator

# 创建PolicyAgent实例
agent = PolicyAgent()

# 创建ResponseGenerator实例
response_generator = ResponseGenerator()

# 测试用例：没有符合条件政策的情况
print("测试用例：没有符合条件政策的情况")
user_input = "我是一名普通上班族，想了解一些政策信息，帮我推荐一个岗位。"

# 识别意图和实体
intent_result = agent.identify_intent(user_input)
print(f"意图识别结果: {intent_result['result']}")

# 检索相关政策
relevant_policies = agent.retrieve_policies(intent_result['result']['intent'], intent_result['result']['entities'], user_input)
print(f"检索到的政策数量: {len(relevant_policies)}")
print(f"检索到的政策: {relevant_policies}")

# 生成岗位推荐
recommended_jobs = []
if intent_result['result'].get("needs_job_recommendation", False):
    # 基于政策关联岗位
    for policy in relevant_policies:
        policy_id = policy.get("policy_id")
        # 简单示例：基于政策ID匹配岗位
        if policy_id == "POLICY_A02":  # 技能提升补贴政策
            # 匹配相关岗位
            matched_jobs = agent.job_matcher.match_jobs_by_policy(policy_id)
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

print(f"推荐的岗位数量: {len(recommended_jobs)}")
print(f"推荐的岗位: {recommended_jobs}")

# 直接调用ResponseGenerator生成响应
response = response_generator.generate_response(user_input, relevant_policies, "通用场景", recommended_jobs=recommended_jobs)
print(f"响应结果:")
print(f"positive: '{response.get('positive', '')}'")
print(f"negative: '{response.get('negative', '')}'")
print(f"suggestions: '{response.get('suggestions', '')}'")
print()