import sys
import os

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'code'))

from langchain.policy_retriever import PolicyRetriever
from langchain.policy_agent import PolicyAgent

# 初始化
policy_retriever = PolicyRetriever()
policy_agent = PolicyAgent()

# 测试用户输入
user_input = "我是退役军人，开汽车维修店，同时入驻创业孵化基地，能同时享受税收优惠和场地补贴吗？"

# 准备实体信息
entities = [
    {"type": "identity", "value": "退役军人"},
    {"type": "business_type", "value": "汽车维修店"},
    {"type": "location", "value": "入驻创业孵化基地"},
    {"type": "concern", "value": "税收优惠"},
    {"type": "concern", "value": "场地补贴"}
]

print("=== 测试 PolicyRetriever ===")
relevant_policies_retriever = policy_retriever.retrieve_policies("政策咨询", entities)
print(f"PolicyRetriever 返回的政策数量: {len(relevant_policies_retriever)}")
print(f"PolicyRetriever 返回的政策: {[(p['policy_id'], p['title']) for p in relevant_policies_retriever]}")

print("\n=== 测试 PolicyAgent ===")
relevant_policies_agent = policy_agent.retrieve_policies("政策咨询", entities)
print(f"PolicyAgent 返回的政策数量: {len(relevant_policies_agent)}")
print(f"PolicyAgent 返回的政策: {[(p['policy_id'], p['title']) for p in relevant_policies_agent]}")

# 检查是否匹配到正确的政策
expected_policies = ['POLICY_A06', 'POLICY_A04']
retriever_policy_ids = [p['policy_id'] for p in relevant_policies_retriever]
agent_policy_ids = [p['policy_id'] for p in relevant_policies_agent]

print("\n=== 验证结果 ===")
print(f"期望匹配的政策: {expected_policies}")
print(f"PolicyRetriever 匹配到的政策: {retriever_policy_ids}")
print(f"PolicyAgent 匹配到的政策: {agent_policy_ids}")

retriever_matches = all(policy_id in retriever_policy_ids for policy_id in expected_policies)
agent_matches = all(policy_id in agent_policy_ids for policy_id in expected_policies)

print(f"\nPolicyRetriever 匹配正确: {retriever_matches}")
print(f"PolicyAgent 匹配正确: {agent_matches}")
