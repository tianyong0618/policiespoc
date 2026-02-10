#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试 POLICY_A02（职业技能提升补贴政策）的匹配情况
"""

import sys
import os

# 添加代码目录到 Python 路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'code'))

from langchain.intent_recognizer import IntentRecognizer
from langchain.policy_retriever import PolicyRetriever

# 测试意图识别
def test_intent_recognition():
    """测试意图识别器是否能正确识别需要政策推荐"""
    print("=== 测试意图识别 ===")
    recognizer = IntentRecognizer()
    
    # 测试用户输入
    user_input = "请为一位32岁、失业、持有高级电工证的男性推荐工作，他关注固定时间。"
    
    # 识别意图
    intent_result = recognizer.identify_intent(user_input)
    intent_info = intent_result["result"]
    
    print(f"用户输入: {user_input}")
    print(f"意图: {intent_info.get('intent', '')}")
    print(f"需要岗位推荐: {intent_info.get('needs_job_recommendation', False)}")
    print(f"需要课程推荐: {intent_info.get('needs_course_recommendation', False)}")
    print(f"需要政策推荐: {intent_info.get('needs_policy_recommendation', False)}")
    print(f"识别的实体: {intent_info.get('entities', [])}")
    print()
    
    return intent_info

# 测试政策检索
def test_policy_retrieval(intent_info):
    """测试政策检索器是否能正确匹配 POLICY_A02"""
    print("=== 测试政策检索 ===")
    retriever = PolicyRetriever()
    
    # 测试用户输入
    user_input = "请为一位32岁、失业、持有高级电工证的男性推荐工作，他关注固定时间。"
    
    # 检索政策
    retrieve_result = retriever.process_query(user_input, intent_info)
    relevant_policies = retrieve_result["relevant_policies"]
    recommended_jobs = retrieve_result["recommended_jobs"]
    recommended_courses = retrieve_result["recommended_courses"]
    
    print(f"检索到的政策数量: {len(relevant_policies)}")
    for policy in relevant_policies:
        print(f"- {policy.get('policy_id')}: {policy.get('title')}")
    
    print(f"\n推荐的岗位数量: {len(recommended_jobs)}")
    for job in recommended_jobs:
        print(f"- {job.get('job_id')}: {job.get('title')}")
    
    print(f"\n推荐的课程数量: {len(recommended_courses)}")
    for course in recommended_courses:
        print(f"- {course.get('course_id')}: {course.get('title')}")
    print()
    
    return relevant_policies

if __name__ == "__main__":
    # 运行测试
    intent_info = test_intent_recognition()
    relevant_policies = test_policy_retrieval(intent_info)
    
    # 检查是否匹配到 POLICY_A02
    has_policy_a02 = any(policy.get('policy_id') == 'POLICY_A02' for policy in relevant_policies)
    print(f"是否匹配到 POLICY_A02: {has_policy_a02}")
    
    if has_policy_a02:
        print("测试通过！用户输入匹配到了 POLICY_A02（职业技能提升补贴政策）")
    else:
        print("测试失败！用户输入没有匹配到 POLICY_A02（职业技能提升补贴政策）")
