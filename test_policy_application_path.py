#!/usr/bin/env python3
# 测试政策申请路径功能

import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

from code.langchain.orchestrator import Orchestrator

def test_policy_application_path():
    """测试政策申请路径功能"""
    print("开始测试政策申请路径功能...")
    
    # 初始化协调器
    orchestrator = Orchestrator()
    
    # 测试用例1: 测试职业技能提升补贴政策(POLICY_A02)的申请路径
    test_input = "我是失业人员，刚拿到中级职业资格证书，能申请培训补贴吗？"
    print(f"\n测试用例1: {test_input}")
    
    # 处理查询
    result = orchestrator.process_query(test_input)
    
    # 打印结果
    print(f"\n相关政策: {[p['policy_id'] for p in result['relevant_policies']]}")
    print(f"推荐岗位: {[j['job_id'] for j in result['recommended_jobs']]}")
    print(f"主动建议: {result['response']['suggestions']}")
    
    # 验证结果
    policy_ids = [p['policy_id'] for p in result['relevant_policies']]
    suggestions = result['response']['suggestions']
    
    if 'POLICY_A02' in policy_ids:
        print("✓ 成功识别职业技能提升补贴政策(POLICY_A02)")
    else:
        print("✗ 未识别职业技能提升补贴政策(POLICY_A02)")
    
    if 'JOB_A02' in suggestions or 'JOB_A04' in suggestions:
        print("✓ 成功在申请路径中推荐对应的岗位")
    else:
        print("✗ 未在申请路径中推荐对应的岗位")
    
    # 测试用例2: 测试其他政策的申请路径
    test_input2 = "我是退役军人，想创业"
    print(f"\n测试用例2: {test_input2}")
    
    # 处理查询
    result2 = orchestrator.process_query(test_input2)
    
    # 打印结果
    print(f"\n相关政策: {[p['policy_id'] for p in result2['relevant_policies']]}")
    print(f"推荐岗位: {[j['job_id'] for j in result2['recommended_jobs']]}")
    print(f"主动建议: {result2['response']['suggestions']}")
    
    print("\n测试完成！")

if __name__ == "__main__":
    test_policy_application_path()
