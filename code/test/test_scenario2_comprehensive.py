#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
场景2综合测试：技能培训岗位个性化推荐
覆盖所有5个岗位（JOB_A01到JOB_A05）
"""

import sys
import os
import json
import time

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'code'))
print(f"添加到Python路径：{os.path.join(project_root, 'code')}")

from langchain.orchestrator import Orchestrator

def test_scenario2_comprehensive():
    """综合测试场景2的所有测试用例"""
    print("=== 场景2综合测试：技能培训岗位个性化推荐 ===")
    
    # 初始化Orchestrator
    agent = Orchestrator()
    
    # 测试用例列表
    test_cases = [
        {
            "id": "S2-001",
            "input": "请为一位32岁、失业、持有中级电工证的女性推荐工作，她关注补贴申领和灵活时间。",
            "expected_jobs": ["JOB_A02"],
            "description": "失业女性电工证持有者岗位推荐"
        },
        {
            "id": "S2-002",
            "input": "我有5年创业服务经验，熟悉创业政策，沟通能力强，想找一份全职工作。",
            "expected_jobs": ["JOB_A01"],
            "description": "创业服务经验岗位推荐"
        },
        {
            "id": "S2-003",
            "input": "我熟悉直播带货和网店运营，有场地补贴落地经验，想从事电商创业相关工作。",
            "expected_jobs": ["JOB_A03"],
            "description": "电商经验岗位推荐"
        },
        {
            "id": "S2-004",
            "input": "我是大专学历，了解职业技能培训政策，善于与人沟通，想从事培训咨询工作。",
            "expected_jobs": ["JOB_A04"],
            "description": "大专学历技能培训咨询岗位推荐"
        },
        {
            "id": "S2-005",
            "input": "我是初中学历，了解职业技能培训政策，善于与人沟通，想从事培训咨询工作。",
            "expected_jobs": [],
            "description": "初中学历技能培训咨询岗位推荐（学历不符合）"
        },
        {
            "id": "S2-006",
            "input": "我是退役军人，有8年企业管理经验，熟悉税收优惠政策，想从事创业项目评估相关工作。",
            "expected_jobs": ["JOB_A05"],
            "description": "退役军人创业评估岗位推荐"
        },
        {
            "id": "S2-007",
            "input": "我不是退役军人，有8年企业管理经验，熟悉税收优惠政策，想从事创业项目评估相关工作。",
            "expected_jobs": [],
            "description": "非退役军人创业评估岗位推荐（不优先推荐）"
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
        # 对于所有场景2的测试用例，使用handle_scenario方法以获得更精确的岗位推荐
        result = agent.handle_scenario("scenario2", test_case['input'])
        
        # 记录结束时间
        end_time = time.time()
        execution_time = end_time - start_time
        total_time += execution_time
        
        print(f"执行时间：{execution_time:.2f}秒")
        
        # 提取匹配的岗位ID
        matched_jobs = [job['job_id'] for job in result.get('recommended_jobs', [])]
        print(f"匹配的岗位：{matched_jobs}")
        print(f"预期的岗位：{test_case['expected_jobs']}")
        
        # 验证测试结果
        passed = set(matched_jobs) == set(test_case['expected_jobs'])
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
            "expected_jobs": test_case['expected_jobs'],
            "matched_jobs": matched_jobs,
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
    
    print(f"\n=== 场景2测试结果汇总 ===")
    print(f"总测试用例数：{total_cases}")
    print(f"通过测试用例数：{passed_count}")
    print(f"测试通过率：{pass_rate:.2f}%")
    print(f"平均响应时间：{average_time:.2f}秒")
    
    # 保存测试结果
    with open('test_scenario2_results.json', 'w', encoding='utf-8') as f:
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
    
    print(f"\n测试结果已保存到：test_scenario2_results.json")
    
    return pass_rate >= 80

if __name__ == "__main__":
    success = test_scenario2_comprehensive()
    sys.exit(0 if success else 1)
