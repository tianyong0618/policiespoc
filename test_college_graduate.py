#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试高校毕业生实体识别功能
"""

import sys
import os

# 添加项目根目录到Python路径
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(current_file)
sys.path.insert(0, os.path.join(project_root, 'code'))

from langchain.business.intent_analyzer import IntentAnalyzer

def test_college_graduate_identification():
    """测试高校毕业生实体识别"""
    print("=== 测试高校毕业生实体识别功能 ===")
    
    # 初始化意图分析器
    analyzer = IntentAnalyzer()
    
    # 测试用例
    test_cases = [
        # 测试不同表达方式
        {"input": "我是一名刚毕业的大学生，专业是市场营销，想创业开网店，需要了解相关补贴政策。", "expected_entities": ["employment_status: 高校毕业生", "employment_status: 创业"]},
        {"input": "我是大学生，刚毕业，想创业", "expected_entities": ["employment_status: 高校毕业生", "employment_status: 创业"]},
        {"input": "我是高校毕业生，想申请创业补贴", "expected_entities": ["employment_status: 高校毕业生", "employment_status: 创业"]},
        {"input": "我刚从大学毕业，想创业开网店", "expected_entities": ["employment_status: 高校毕业生", "employment_status: 创业"]},
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
        
        # 检查是否所有预期实体都被识别
        all_found = all(expected in identified_entities for expected in test_case['expected_entities'])
        if all_found:
            print("✅ 测试通过")
            passed += 1
        else:
            print("❌ 测试失败")
    
    print(f"\n=== 测试结果汇总 ===")
    print(f"总测试用例数: {total}")
    print(f"通过测试用例数: {passed}")
    print(f"测试通过率: {passed/total*100:.2f}%")

if __name__ == "__main__":
    test_college_graduate_identification()
