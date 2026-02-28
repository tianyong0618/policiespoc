#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试否定表达的处理功能
"""

import sys
import os

# 添加项目根目录到Python路径
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(current_file)
sys.path.insert(0, os.path.join(project_root, 'code'))

from langchain.business.intent_analyzer import IntentAnalyzer

def test_negation_handling():
    """测试否定表达的处理"""
    print("=== 测试否定表达处理功能 ===")
    
    # 初始化意图分析器
    analyzer = IntentAnalyzer()
    
    # 测试用例
    test_cases = [
        # 测试否定就业状态
        {"input": "我不是退役军人，有8年企业管理经验，熟悉税收优惠政策，想从事创业项目评估相关工作。", "expected_entities": ["employment_status: 创业", "concern: 税收优惠"]},
        {"input": "我不是脱贫户，想参加技能培训", "expected_entities": ["concern: 技能培训"]},
        {"input": "我不是高校毕业生，想创业", "expected_entities": ["employment_status: 创业"]},
        
        # 测试肯定表达（作为对照组）
        {"input": "我是退役军人，想创业", "expected_entities": ["employment_status: 退役军人", "employment_status: 创业"]},
        {"input": "我是脱贫户，想申请补贴", "expected_entities": ["employment_status: 脱贫户"]},
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases):
        print(f"\n测试用例 {i+1}/{total}: {test_case['input']}")
        result = analyzer.ir_identify_intent(test_case['input'])
        intent_info = result['result']
        
        # 格式化识别到的实体
        identified_entities = [f"{entity['type']}: {entity['value']}" for entity in intent_info['entities']]
        print(f"识别到的实体: {identified_entities}")
        print(f"预期的实体: {test_case['expected_entities']}")
        
        # 检查是否所有预期实体都被识别，且没有识别到否定的实体
        all_found = all(expected in identified_entities for expected in test_case['expected_entities'])
        # 检查是否没有识别到否定的实体
        no_negated_entities = True
        if "不是退役军人" in test_case['input'] and "employment_status: 退役军人" in identified_entities:
            no_negated_entities = False
        if "不是脱贫户" in test_case['input'] and "employment_status: 脱贫户" in identified_entities:
            no_negated_entities = False
        if "不是高校毕业生" in test_case['input'] and "employment_status: 高校毕业生" in identified_entities:
            no_negated_entities = False
        
        if all_found and no_negated_entities:
            print("✅ 测试通过")
            passed += 1
        else:
            print("❌ 测试失败")
    
    print(f"\n=== 测试结果汇总 ===")
    print(f"总测试用例数: {total}")
    print(f"通过测试用例数: {passed}")
    print(f"测试通过率: {passed/total*100:.2f}%")

if __name__ == "__main__":
    test_negation_handling()
