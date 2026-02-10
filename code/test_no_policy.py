import sys
import os

# 添加langchain模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'langchain'))

from langchain.policy_agent import PolicyAgent

# 创建PolicyAgent实例
agent = PolicyAgent()

# 测试用例：没有符合条件政策的情况
print("测试用例：没有符合条件政策的情况")
user_input = "我是一名普通上班族，想了解一些政策信息，帮我推荐一个岗位。"
result = agent.process_query(user_input)
print(f"匹配到的政策数量: {len(result['relevant_policies'])}")
print(f"响应结果:")
print(f"positive: '{result['response'].get('positive', '')}'")
print(f"negative: '{result['response'].get('negative', '')}'")
print(f"suggestions: '{result['response'].get('suggestions', '')}'")
print()