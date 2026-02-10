import sys
import os

# 添加langchain模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'langchain'))

from langchain.policy_agent import PolicyAgent

# 创建PolicyAgent实例
agent = PolicyAgent()

# 测试用例1：32岁、失业、持有中级电工证的女性
print("测试用例1：32岁、失业、持有中级电工证的女性")
user_input1 = "请为一位32岁、失业、持有中级电工证的女性推荐工作，她关注补贴申领和灵活时间。"
result1 = agent.process_query(user_input1)
print(f"匹配到的政策数量: {len(result1['relevant_policies'])}")
for policy in result1['relevant_policies']:
    print(f"- {policy['policy_id']}: {policy['title']}")
print()

# 测试用例2：退役军人
print("测试用例2：退役军人")
user_input2 = "我是个退役军人，熟悉退役军人创业税收优惠，能评估创业项目可行性，5年以上企业管理经验，帮我推荐一个岗位。"
result2 = agent.process_query(user_input2)
print(f"匹配到的政策数量: {len(result2['relevant_policies'])}")
for policy in result2['relevant_policies']:
    print(f"- {policy['policy_id']}: {policy['title']}")
print()