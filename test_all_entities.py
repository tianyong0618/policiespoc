#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试所有实体类型的提取功能
"""

import sys
import os

# 添加项目根目录到Python路径
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(current_file)
sys.path.insert(0, os.path.join(project_root, 'code'))

from langchain.business.intent_analyzer import IntentAnalyzer

def test_all_entities():
    """测试所有实体类型"""
    print("=== 测试所有实体类型提取功能 ===")
    
    # 初始化意图分析器
    analyzer = IntentAnalyzer()
    
    # 测试用例，覆盖所有实体类型
    test_cases = [
        # 测试就业状态实体
        {"input": "我是脱贫户，想参加技能培训", "expected_entities": ["employment_status: 脱贫户", "concern: 技能培训"]},
        {"input": "我是高校毕业生，想创业", "expected_entities": ["employment_status: 高校毕业生", "employment_status: 创业"]},
        {"input": "我是低保家庭成员，想申请补贴", "expected_entities": ["employment_status: 低保家庭成员"]},
        {"input": "我是残疾人，想找工作", "expected_entities": ["employment_status: 残疾人"]},
        
        # 测试证书实体
        {"input": "我有初级职业资格证书", "expected_entities": ["certificate: 初级职业资格证书"]},
        {"input": "我有中级职业资格证书", "expected_entities": ["certificate: 中级职业资格证书"]},
        {"input": "我有高级职业资格证书", "expected_entities": ["certificate: 高级职业资格证书"]},
        
        # 测试政策关注点实体
        {"input": "我想申请创业担保贷款", "expected_entities": ["concern: 创业担保贷款"]},
        {"input": "我想申请职业技能提升补贴", "expected_entities": ["concern: 职业技能提升补贴"]},
        {"input": "我想申请返乡创业扶持补贴", "expected_entities": ["concern: 返乡创业扶持补贴"]},
        {"input": "我想申请创业场地租金补贴", "expected_entities": ["concern: 创业场地租金补贴"]},
        {"input": "我想申请技能培训生活费补贴", "expected_entities": ["concern: 技能培训生活费补贴"]},
        {"input": "我是退役军人，想了解创业税收优惠", "expected_entities": ["employment_status: 退役军人", "concern: 退役军人创业税收优惠"]},
        
        # 测试工作类型实体
        {"input": "我想找全职工作", "expected_entities": ["work_type: 全职"]},
        {"input": "我想找兼职工作", "expected_entities": ["work_type: 兼职"]},
        
        # 测试组合实体
        {"input": "我是返乡农民工，想找全职工作，有电工证", "expected_entities": ["employment_status: 返乡农民工", "work_type: 全职", "certificate: 电工证"]},
        {"input": "我是高校毕业生，想创业开小微企业，需要场地补贴", "expected_entities": ["employment_status: 高校毕业生", "employment_status: 创业", "business_type: 小微企业", "concern: 场地补贴"]}
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
    test_all_entities()
