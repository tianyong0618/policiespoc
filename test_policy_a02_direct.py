#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
直接测试 POLICY_A02（职业技能提升补贴政策）的匹配逻辑
"""

import sys
import os

# 添加代码目录到 Python 路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'code'))

# 直接测试政策匹配逻辑
def test_policy_a02_match():
    """直接测试 POLICY_A02 的匹配逻辑"""
    print("=== 测试 POLICY_A02 匹配逻辑 ===")
    
    # 测试用户输入
    user_input = "请为一位32岁、失业、持有高级电工证的男性推荐工作，他关注固定时间。"
    
    # 模拟政策匹配逻辑
    print(f"用户输入: {user_input}")
    
    # 检查用户输入是否包含关键词
    has_certificate = "电工证" in user_input or "证书" in user_input
    is_unemployed = "失业" in user_input
    
    print(f"包含证书关键词: {has_certificate}")
    print(f"包含失业关键词: {is_unemployed}")
    
    # 检查是否符合 POLICY_A02 条件
    if has_certificate or is_unemployed:
        print("✅ 用户符合 POLICY_A02（职业技能提升补贴政策）条件")
        print("   理由: 持有电工证或处于失业状态")
    else:
        print("❌ 用户不符合 POLICY_A02（职业技能提升补贴政策）条件")
    
    print()
    
    # 检查政策数据
    policy_file = os.path.join(os.path.dirname(__file__), 'code', 'langchain', 'data', 'policies.json')
    if os.path.exists(policy_file):
        print("=== 政策数据文件 ===")
        print(f"政策数据文件存在: {policy_file}")
        
        # 读取政策数据
        import json
        with open(policy_file, 'r', encoding='utf-8') as f:
            policies = json.load(f)
        
        # 查找 POLICY_A02
        policy_a02 = None
        for policy in policies:
            if policy['policy_id'] == 'POLICY_A02':
                policy_a02 = policy
                break
        
        if policy_a02:
            print(f"\nPOLICY_A02 信息:")
            print(f"政策ID: {policy_a02['policy_id']}")
            print(f"政策标题: {policy_a02['title']}")
            print(f"政策内容: {policy_a02['content']}")
            print(f"关键信息: {policy_a02['key_info']}")
            print(f"条件: {policy_a02['conditions']}")
            print(f"福利: {policy_a02['benefits']}")
        else:
            print("未找到 POLICY_A02")
    else:
        print("政策数据文件不存在")

if __name__ == "__main__":
    test_policy_a02_match()
