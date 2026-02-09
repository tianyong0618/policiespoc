#!/usr/bin/env python3
"""
测试POLICY_A01政策的bug修复
"""
import json
import time
from code.langchain.orchestrator import Orchestrator

def test_policy_a01_with_return_migrant():
    """测试包含返乡农民工实体的情况"""
    print("\n=== 测试1: POLICY_A01包含返乡农民工实体 ===")
    orchestrator = Orchestrator()
    
    # 用户输入：明确提到返乡农民工和创业
    user_input = "我是返乡农民工，想创办小微企业，有什么创业贷款贴息政策吗？"
    print(f"用户输入: {user_input}")
    
    result = orchestrator.process_query(user_input)
    
    # 检查意图识别
    print(f"\n1. 意图识别: {result['intent']['intent']}")
    print(f"   实体: {json.dumps(result['intent']['entities'], ensure_ascii=False)}")
    
    # 检查相关政策
    print("\n2. 相关政策:")
    for policy in result['relevant_policies']:
        print(f"   - {policy['policy_id']}: {policy['title']}")
    
    # 检查思考过程中的政策检索
    print("\n3. 政策检索详情:")
    for step in result['thinking_process']:
        if step['step'] == "精准检索与推理" and 'substeps' in step:
            for substep in step['substeps']:
                if substep['step'] == "政策检索" and 'substeps' in substep:
                    for policy_substep in substep['substeps']:
                        if "POLICY_A01" in policy_substep['step']:
                            print(f"   - {policy_substep['step']}: {policy_substep['content']}")
                            # 检查是否正确识别返乡农民工身份
                            if "未提及返乡农民工" in policy_substep['content']:
                                print("\n❌ 测试失败！系统未正确识别返乡农民工身份")
                            else:
                                print("\n✅ 测试通过！系统正确识别了返乡农民工身份")
    
    # 检查结构化输出
    print("\n4. 结构化输出:")
    print(f"   肯定部分: {result['response'].get('positive', ['无'])[0] if result['response'].get('positive') else '无'}")
    print(f"   否定部分: {result['response'].get('negative', ['无'])[0] if result['response'].get('negative') else '无'}")
    print(f"   建议部分: {result['response'].get('suggestions', ['无'])[0] if result['response'].get('suggestions') else '无'}")

def test_policy_a01_with_veteran():
    """测试包含退役军人实体的情况"""
    print("\n=== 测试2: POLICY_A01包含退役军人实体 ===")
    orchestrator = Orchestrator()
    
    # 用户输入：明确提到退役军人和创业
    user_input = "我是退役军人，想创办小微企业，有什么创业贷款贴息政策吗？"
    print(f"用户输入: {user_input}")
    
    result = orchestrator.process_query(user_input)
    
    # 检查意图识别
    print(f"\n1. 意图识别: {result['intent']['intent']}")
    print(f"   实体: {json.dumps(result['intent']['entities'], ensure_ascii=False)}")
    
    # 检查相关政策
    print("\n2. 相关政策:")
    for policy in result['relevant_policies']:
        print(f"   - {policy['policy_id']}: {policy['title']}")
    
    # 检查思考过程中的政策检索
    print("\n3. 政策检索详情:")
    for step in result['thinking_process']:
        if step['step'] == "精准检索与推理" and 'substeps' in step:
            for substep in step['substeps']:
                if substep['step'] == "政策检索" and 'substeps' in substep:
                    for policy_substep in substep['substeps']:
                        if "POLICY_A01" in policy_substep['step']:
                            print(f"   - {policy_substep['step']}: {policy_substep['content']}")
                            # 检查是否正确识别退役军人身份
                            if "未提及退役军人" in policy_substep['content']:
                                print("\n❌ 测试失败！系统未正确识别退役军人身份")
                            else:
                                print("\n✅ 测试通过！系统正确识别了退役军人身份")

if __name__ == "__main__":
    test_policy_a01_with_return_migrant()
    test_policy_a01_with_veteran()
