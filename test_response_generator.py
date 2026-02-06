import sys
import os

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'code'))

from langchain.response_generator import ResponseGenerator
from langchain.policy_retriever import PolicyRetriever

# 初始化
response_generator = ResponseGenerator()
policy_retriever = PolicyRetriever()

# 测试用户输入
user_input = "请为一位32岁、失业、持有中级电工证的女性推荐工作，她关注补贴申领和灵活时间"

# 获取符合条件的政策
intent_info = {
    "intent": "政策咨询",
    "needs_job_recommendation": True,
    "needs_course_recommendation": False,
    "needs_policy_recommendation": True,
    "entities": [
        {"type": "age", "value": "32岁"},
        {"type": "gender", "value": "女性"},
        {"type": "employment_status", "value": "失业"},
        {"type": "certificate", "value": "中级电工证"},
        {"type": "concern", "value": "补贴申领"},
        {"type": "concern", "value": "灵活时间"}
    ]
}

relevant_policies = policy_retriever.retrieve_policies(intent_info["intent"], intent_info["entities"])
print(f"符合条件的政策数量: {len(relevant_policies)}")
print(f"符合条件的政策ID: {[p['policy_id'] for p in relevant_policies]}")

# 生成响应
response = response_generator.generate_response(
    user_input,
    relevant_policies,
    "通用场景",
    recommended_jobs=[
        {
            "job_id": "JOB_A02",
            "title": "职业技能培训讲师",
            "requirements": ["持有高级职业资格证书（如电工/家政）", "3年以上授课经验", "能结合POLICY_A02讲解考证路径", "兼职/全职均可"],
            "features": "传授实操技能，助力学员申领补贴，时间灵活"
        }
    ]
)

print("\n生成的响应:")
print(f"positive: {response['positive']}")
print(f"negative: {response['negative']}")
print(f"suggestions: {response['suggestions']}")
