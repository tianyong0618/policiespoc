#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：验证返乡农民工实体识别修复效果
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'code')))

from langchain.orchestrator import Orchestrator


def test_migrant_worker_entity_recognition():
    """
    测试返乡农民工实体识别
    """
    print("=== 测试返乡农民工实体识别 ===")
    
    # 初始化协调器
    orchestrator = Orchestrator()
    
    # 测试用例1：直接提及返乡农民工
    user_input1 = "我是返乡农民工，想创业，有什么政策支持？"
    print(f"\n测试用例1: {user_input1}")
    result1 = orchestrator.process_query(user_input1)
    
    # 检查结果
    print(f"意图: {result1['intent']['intent']}")
    print(f"提取实体: {[f'{e["value"]}({e["type"]})' for e in result1['intent']['entities']]}")
    print(f"相关政策数量: {len(result1['relevant_policies'])}")
    
    # 检查思考过程中的政策分析
    print("\n思考过程中的政策分析:")
    for step in result1['thinking_process']:
        if step['step'] == '精准检索与推理':
            for substep in step['substeps']:
                if substep['step'] == '政策检索':
                    for policy_substep in substep['substeps']:
                        if 'POLICY_A01' in policy_substep['step']:
                            print(f"POLICY_A01分析: {policy_substep['content']}")
                            # 验证是否正确识别了返乡农民工身份
                            if '用户已提及相关条件，符合条件' in policy_substep['content']:
                                print("✓ 测试通过: 正确识别了返乡农民工身份")
                            else:
                                print("✗ 测试失败: 未正确识别返乡农民工身份")
    
    # 测试用例2：间接提及返乡农民工（通过实体识别）
    user_input2 = "我刚从外地回来，以前在工地打工，现在想自己开店，有什么优惠政策？"
    print(f"\n测试用例2: {user_input2}")
    result2 = orchestrator.process_query(user_input2)
    
    # 检查结果
    print(f"意图: {result2['intent']['intent']}")
    print(f"提取实体: {[f'{e["value"]}({e["type"]})' for e in result2['intent']['entities']]}")
    print(f"相关政策数量: {len(result2['relevant_policies'])}")
    
    # 检查思考过程中的政策分析
    print("\n思考过程中的政策分析:")
    for step in result2['thinking_process']:
        if step['step'] == '精准检索与推理':
            for substep in step['substeps']:
                if substep['step'] == '政策检索':
                    for policy_substep in substep['substeps']:
                        if 'POLICY_A01' in policy_substep['step']:
                            print(f"POLICY_A01分析: {policy_substep['content']}")
                            # 验证是否正确识别了返乡农民工身份
                            if '用户已提及相关条件，符合条件' in policy_substep['content']:
                                print("✓ 测试通过: 正确识别了返乡农民工身份")
                            else:
                                print("✗ 测试失败: 未正确识别返乡农民工身份")


if __name__ == "__main__":
    test_migrant_worker_entity_recognition()
