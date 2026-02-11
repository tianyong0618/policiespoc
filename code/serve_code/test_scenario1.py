#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试场景一：创业扶持政策精准咨询
"""

import sys
import os
import json

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
print(f"添加到Python路径：{project_root}")

from langchain.policy_agent import PolicyAgent

def test_s1_001():
    """测试S1-001测试用例"""
    print("\n=== 测试S1-001测试用例 ===")
    
    # 初始化政策智能体
    agent = PolicyAgent()
    
    # 测试用例：S1-001用户输入
    user_input = "我是去年从广东回来的农民工，想在家开个小加工厂（小微企业），听说有返乡创业补贴，能领2万吗？另外创业贷款怎么申请？"
    
    print(f"\n用户输入：{user_input}")
    
    # 使用fallback_process进行测试，确保retrieve_policies被调用
    result = agent.fallback_process(user_input)
    
    print(f"\n处理结果：")
    print(f"意图：{json.dumps(result['intent'], ensure_ascii=False, indent=2)}")
    
    print(f"\n相关政策：")
    for policy in result['relevant_policies']:
        print(f"- {policy['policy_id']}：{policy['title']}（分类：{policy['category']}）")
    
    # 检查是否包含POLICY_A01
    policy_ids = [policy['policy_id'] for policy in result['relevant_policies']]
    print(f"\n包含的政策ID：{policy_ids}")
    
    if "POLICY_A01" in policy_ids:
        print("✅ 测试通过：S1-001成功匹配到POLICY_A01（创业担保贷款贴息政策）")
    else:
        print("❌ 测试失败：S1-001未匹配到POLICY_A01（创业担保贷款贴息政策）")
    
    return "POLICY_A01" in policy_ids

def test_s1_006():
    """测试S1-006测试用例"""
    print("\n=== 测试S1-006测试用例 ===")
    
    # 初始化政策智能体
    agent = PolicyAgent()
    
    # 测试用例：S1-006用户输入
    user_input = "我是在职人员，想创业，能申请返乡创业补贴吗？"
    
    print(f"\n用户输入：{user_input}")
    
    # 使用fallback_process进行测试，确保retrieve_policies被调用
    result = agent.fallback_process(user_input)
    
    print(f"\n处理结果：")
    print(f"意图：{json.dumps(result['intent'], ensure_ascii=False, indent=2)}")
    
    print(f"\n相关政策：")
    for policy in result['relevant_policies']:
        print(f"- {policy['policy_id']}：{policy['title']}（分类：{policy['category']}）")
    
    # 检查是否不包含任何政策
    policy_ids = [policy['policy_id'] for policy in result['relevant_policies']]
    print(f"\n包含的政策ID：{policy_ids}")
    
    if len(policy_ids) == 0:
        print("✅ 测试通过：S1-006成功识别为不符合条件，未匹配到任何政策")
    else:
        print("❌ 测试失败：S1-006错误匹配到了政策，预期应该不匹配任何政策")
    
    return len(policy_ids) == 0

if __name__ == "__main__":
    success1 = test_s1_001()
    success2 = test_s1_006()
    sys.exit(0 if success1 and success2 else 1)
