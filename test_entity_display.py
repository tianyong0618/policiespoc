#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试实体显示格式
"""

import sys
import os

# 添加项目根目录到Python路径
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(current_file)
sys.path.insert(0, os.path.join(project_root, 'code'))

from langchain.presentation.orchestrator.stream_processor import StreamProcessor
from langchain.presentation.orchestrator.base import Orchestrator

def test_entity_display_format():
    """测试实体显示格式"""
    print("=== 测试实体显示格式 ===")
    
    # 初始化协调器和流处理器
    orchestrator = Orchestrator()
    stream_processor = StreamProcessor(orchestrator)
    
    # 测试用例
    test_input = "我是退役军人，想创业，有电工证"
    
    print(f"测试输入: {test_input}")
    
    # 识别意图
    intent_info = orchestrator.intent_recognizer.ir_identify_intent(test_input)
    entities_info = intent_info['result']['entities']
    
    # 提取实体描述
    entity_descriptions = stream_processor._extract_entity_descriptions(entities_info)
    
    print(f"提取的实体: {', '.join(entity_descriptions)}")
    
    # 检查是否包含括号
    for entity in entity_descriptions:
        if '(' in entity or ')' in entity:
            print("❌ 实体显示格式错误，包含括号")
            return False
    
    print("✅ 实体显示格式正确，不包含括号")
    return True

if __name__ == "__main__":
    success = test_entity_display_format()
    sys.exit(0 if success else 1)
