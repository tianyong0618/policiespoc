#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
场景1综合测试：创业扶持政策精准咨询
覆盖所有6个政策（POLICY_A01到POLICY_A06）
"""

import sys
import os
import json
import time

# 添加项目根目录到Python路径
current_file = os.path.abspath(__file__)
test_dir = os.path.dirname(current_file)
code_dir = os.path.dirname(test_dir)
project_root = os.path.dirname(code_dir)
sys.path.insert(0, code_dir)
print(f"添加到Python路径：{code_dir}")

from langchain.policy_agent import PolicyAgent

def test_scenario1_comprehensive():
    """综合测试场景1的所有测试用例"""
    print("=== 场景1综合测试：创业扶持政策精准咨询 ===")
    
    # 初始化政策智能体
    agent = PolicyAgent()
    
    # 测试用例列表
    test_cases = [
        {
            "id": "S1-001",
            "input": "我是去年从广东回来的农民工，想在家开个小加工厂（小微企业），听说有返乡创业补贴，能领2万吗？另外创业贷款怎么申请？",
            "expected_policies": ["POLICY_A01", "POLICY_A03"],
            "description": "返乡农民工创业贷款咨询"
        },
        {
            "id": "S1-002",
            "input": "我想创业，已经入驻了当地的创业孵化基地，听说有租金补贴，具体怎么申请？",
            "expected_policies": ["POLICY_A04"],
            "description": "创业场地租金补贴咨询"
        },
        {
            "id": "S1-003",
            "input": "我是失业人员，刚拿到中级职业资格证书，能申请培训补贴吗？",
            "expected_policies": ["POLICY_A02"],
            "description": "技能培训补贴咨询"
        },
        {
            "id": "S1-004",
            "input": "我是脱贫户，想参加技能培训，有什么补贴政策？",
            "expected_policies": ["POLICY_A05"],
            "description": "特殊群体培训补贴咨询"
        },
        {
            "id": "S1-005",
            "input": "我是退役军人，想开店做生意，有什么税收优惠政策？",
            "expected_policies": ["POLICY_A06"],
            "description": "退役军人创业税收优惠咨询"
        },
        {
            "id": "S1-006",
            "input": "我是在职人员，想创业，能申请返乡创业补贴吗？",
            "expected_policies": [],
            "description": "条件不满足场景"
        }
    ]
    
    # 测试结果记录
    test_results = []
    total_time = 0
    passed_count = 0
    
    for test_case in test_cases:
        print(f"\n=== 测试用例 {test_case['id']}: {test_case['description']} ===")
        print(f"用户输入：{test_case['input']}")
        
        # 记录开始时间
        start_time = time.time()
        
        # 执行测试
        result = agent.process_query(test_case['input'])
        
        # 记录结束时间
        end_time = time.time()
        execution_time = end_time - start_time
        total_time += execution_time
        
        print(f"执行时间：{execution_time:.2f}秒")
        
        # 提取匹配的政策ID
        matched_policies = [policy['policy_id'] for policy in result.get('relevant_policies', [])]
        print(f"匹配的政策：{matched_policies}")
        print(f"预期的政策：{test_case['expected_policies']}")
        
        # 验证测试结果
        passed = set(matched_policies) == set(test_case['expected_policies'])
        if passed:
            passed_count += 1
            print("✅ 测试通过")
        else:
            print("❌ 测试失败")
        
        # 记录测试结果
        test_results.append({
            "id": test_case['id'],
            "description": test_case['description'],
            "input": test_case['input'],
            "expected_policies": test_case['expected_policies'],
            "matched_policies": matched_policies,
            "passed": passed,
            "execution_time": execution_time
        })
        
        # 打印回答内容（简要）
        response = result.get('response', {})
        print(f"\n回答内容：")
        if response.get('positive'):
            print(f"肯定部分：{response['positive'][:100]}...")
        if response.get('negative'):
            print(f"否定部分：{response['negative'][:100]}...")
        if response.get('suggestions'):
            print(f"主动建议：{response['suggestions'][:100]}...")
    
    # 计算测试结果
    total_cases = len(test_cases)
    pass_rate = (passed_count / total_cases) * 100
    average_time = total_time / total_cases
    
    print(f"\n=== 场景1测试结果汇总 ===")
    print(f"总测试用例数：{total_cases}")
    print(f"通过测试用例数：{passed_count}")
    print(f"测试通过率：{pass_rate:.2f}%")
    print(f"平均响应时间：{average_time:.2f}秒")
    
    # 保存测试结果
    with open('test_scenario1_results.json', 'w', encoding='utf-8') as f:
        json.dump({
            "test_results": test_results,
            "summary": {
                "total_cases": total_cases,
                "passed_count": passed_count,
                "pass_rate": pass_rate,
                "average_time": average_time,
                "total_time": total_time
            }
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n测试结果已保存到：test_scenario1_results.json")
    
    return pass_rate >= 80

if __name__ == "__main__":
    success = test_scenario1_comprehensive()
    sys.exit(0 if success else 1)
