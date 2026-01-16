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

def test_scenario1():
    """测试场景一"""
    print("测试场景一：创业扶持政策精准咨询")
    
    # 初始化政策智能体
    agent = PolicyAgent()
    
    # 测试用例：场景一用户输入
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
        print("✅ 测试通过：场景一成功匹配到POLICY_A01（创业担保贷款贴息政策）")
    else:
        print("❌ 测试失败：场景一未匹配到POLICY_A01（创业担保贷款贴息政策）")
    
    print(f"\n回答内容：")
    print(json.dumps(result['response'], ensure_ascii=False, indent=2))
    
    return "POLICY_A01" in policy_ids

if __name__ == "__main__":
    success = test_scenario1()
    sys.exit(0 if success else 1)
