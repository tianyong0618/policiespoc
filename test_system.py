#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试系统功能，确保系统能够正确处理用户的查询，按照指定的标准答案输出
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from code.langchain.orchestrator import Orchestrator

def test_entrepreneurship_subsidy_loan_query():
    """
    测试返乡创业补贴和贷款咨询场景
    """
    print("测试返乡创业补贴和贷款咨询场景...")
    
    # 初始化协调器
    orchestrator = Orchestrator()
    
    # 用户输入
    user_input = "我是去年从广东回来的农民工，想在家开个小加工厂（小微企业），听说有返乡创业补贴，能领2万吗？另外创业贷款怎么申请？"
    
    # 处理用户查询
    result = orchestrator.process_query(user_input)
    
    # 输出结果
    print("\n用户输入:")
    print(user_input)
    print("\n意图识别结果:")
    print(result["intent"])
    print("\n相关政策:")
    for policy in result["relevant_policies"]:
        print(f"- {policy['policy_id']}: {policy['title']}")
    print("\n思考过程:")
    for step in result["thinking_process"]:
        print(f"{step['step']}: {step['content']}")
    print("\n生成的回答:")
    print(result["response"])
    print("\n评估结果:")
    print(result["evaluation"])
    
    # 检查是否符合标准答案要求
    response = result["response"]
    positive = response.get("positive", "")
    negative = response.get("negative", "")
    suggestions = response.get("suggestions", "")
    
    print("\n验证结果:")
    # 检查否定部分
    if "POLICY_A03" in negative and ("带动3人以上就业" in negative or "带动就业≥3人" in negative):
        print("✓ 否定部分正确，包含POLICY_A03和带动就业条件")
    else:
        print("✗ 否定部分不正确，缺少POLICY_A03或带动就业条件")
    
    # 检查肯定部分
    if "POLICY_A01" in positive and "返乡农民工" in positive and ("最高贷50万" in positive or "最高贷款额度50万元" in positive) and ("期限3年" in positive or "期限不超过3年" in positive or "期限≤3年" in positive):
        print("✓ 肯定部分正确，包含POLICY_A01、返乡农民工身份、贷款额度和期限")
    else:
        print("✗ 肯定部分不正确，缺少POLICY_A01、返乡农民工身份、贷款额度或期限")
    
    # 检查主动建议
    if "创业孵化基地管理员" in suggestions:
        print("✓ 主动建议正确，包含创业孵化基地管理员")
    else:
        print("✗ 主动建议不正确，缺少创业孵化基地管理员")
    
    # 检查回答格式是否符合标准答案要求
    print("\n格式验证:")
    # 检查否定部分格式
    if "根据《" in negative and "》（POLICY_A03）" in negative and "您需满足‘" in negative and ("’方可申领" in negative or "’条件方可申领" in negative):
        print("✓ 否定部分格式正确，符合标准答案要求")
    else:
        print("✗ 否定部分格式不正确，不符合标准答案要求")
    
    # 检查肯定部分格式
    if "您可申请《" in positive and "》（POLICY_A01）" in positive and "作为返乡农民工" in positive and ("最高贷" in positive or "最高贷款额度" in positive):
        print("✓ 肯定部分格式正确，符合标准答案要求")
    else:
        print("✗ 肯定部分格式不正确，不符合标准答案要求")
    
    # 检查主动建议格式
    if "推荐联系" in suggestions and "创业孵化基地管理员" in suggestions:
        print("✓ 主动建议格式正确，符合标准答案要求")
    else:
        print("✗ 主动建议格式不正确，不符合标准答案要求")

if __name__ == "__main__":
    test_entrepreneurship_subsidy_loan_query()
