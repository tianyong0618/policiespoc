#!/usr/bin/env python3
"""
测试不同形式的返乡农民工实体值
"""
import json
import time
from code.langchain.orchestrator import Orchestrator

def test_policy_a01_with_different_entity_values():
    """测试不同形式的返乡农民工实体值"""
    test_cases = [
        {
            "name": "标准形式：返乡农民工",
            "user_input": "返乡农民工想创办小微企业，有什么创业贷款贴息政策吗？"
        },
        {
            "name": "简化形式：农民工返乡",
            "user_input": "农民工返乡想创办小微企业，有什么创业贷款贴息政策吗？"
        },
        {
            "name": "返乡创业农民工",
            "user_input": "返乡创业农民工想创办小微企业，有什么创业贷款贴息政策吗？"
        },
        {
            "name": "从外地回来的农民工",
            "user_input": "从外地回来的农民工想创办小微企业，有什么创业贷款贴息政策吗？"
        },
        {
            "name": "返乡人员",
            "user_input": "返乡人员想创办小微企业，有什么创业贷款贴息政策吗？"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n=== 测试: {test_case['name']} ===")
        print(f"用户输入: {test_case['user_input']}")
        
        orchestrator = Orchestrator()
        result = orchestrator.process_query(test_case['user_input'])
        
        # 检查意图识别
        print(f"\n1. 意图识别: {result['intent']['intent']}")
        print(f"   实体: {json.dumps(result['intent']['entities'], ensure_ascii=False)}")
        
        # 检查相关政策
        print("\n2. 相关政策:")
        for policy in result['relevant_policies']:
            print(f"   - {policy['policy_id']}: {policy['title']}")
        
        # 检查思考过程中的政策检索
        print("\n3. 政策检索详情:")
        policy_a01_found = False
        for step in result['thinking_process']:
            if step['step'] == "精准检索与推理" and 'substeps' in step:
                for substep in step['substeps']:
                    if substep['step'] == "政策检索" and 'substeps' in substep:
                        for policy_substep in substep['substeps']:
                            if "POLICY_A01" in policy_substep['step']:
                                policy_a01_found = True
                                print(f"   - {policy_substep['step']}: {policy_substep['content']}")
                                # 检查是否正确识别返乡农民工身份
                                if "未提及返乡农民工" in policy_substep['content']:
                                    print("\n❌ 测试失败！系统未正确识别返乡农民工身份")
                                else:
                                    print("\n✅ 测试通过！系统正确识别了返乡农民工身份")
        
        if not policy_a01_found:
            print("\n❌ 测试失败！系统未匹配到POLICY_A01政策")

if __name__ == "__main__":
    test_policy_a01_with_different_entity_values()
