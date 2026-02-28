#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试实体提取功能
"""

import sys
import os

# 添加项目根目录到Python路径
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(current_file)
sys.path.insert(0, os.path.join(project_root, 'code'))

from langchain.business.intent_analyzer import IntentAnalyzer

def test_entity_extraction():
    """测试实体提取"""
    print("=== 测试实体提取功能 ===")
    
    # 初始化意图分析器
    analyzer = IntentAnalyzer()
    
    # 测试用例
    test_cases = [
        "我是脱贫户，想参加技能培训，有什么补贴政策？",
        "我是返乡农民工，想创业，有什么政策？",
        "我是退役军人，想开店，有什么税收优惠？"
    ]
    
    for test_input in test_cases:
        print(f"\n测试输入：{test_input}")
        result = analyzer.ir_identify_intent(test_input)
        intent_info = result['result']
        print(f"意图：{intent_info['intent']}")
        print(f"实体：{intent_info['entities']}")

if __name__ == "__main__":
    test_entity_extraction()
