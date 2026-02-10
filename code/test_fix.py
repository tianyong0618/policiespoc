#!/usr/bin/env python3
# 测试修复后的系统，确保能够正确处理"38岁，大专毕业"的用户查询
# 并验证更匹配的课程排在前面

import sys
sys.path.append('/Users/tianyong/Documents/works/workspace/hp/公司文档/AI调研/政策咨询POC/code/langchain')

from langchain.orchestrator import Orchestrator
from langchain.course_matcher import CourseMatcher

# 测试1: 完整系统测试
print("=== 测试1: 完整系统测试 ===")
orchestrator = Orchestrator()

# 测试用户查询
user_input = "我今年38岁，大专毕业，不知道该报什么培训课程？"
print(f"测试用户查询: {user_input}")
print("=" * 60)

# 处理查询
result = orchestrator.process_query(user_input)

# 打印结果
print("\n=== 处理结果 ===")
print(f"意图识别: {result['intent']['intent']}")
print(f"实体信息: {result['intent']['entities']}")
print(f"推荐课程: {[course['course_id'] + ': ' + course['title'] for course in result['recommended_courses']]}")

print("\n=== 思考过程 ===")
for step in result['thinking_process']:
    print(f"步骤: {step['step']}")
    print(f"内容: {step['content']}")
    if 'substeps' in step:
        for substep in step['substeps']:
            print(f"  子步骤: {substep['step']}")
            print(f"  内容: {substep['content']}")
    print()

print("\n=== 回答 ===")
print(f"积极因素: {result['response']['positive']}")
print(f"消极因素: {result['response']['negative']}")
print(f"建议: {result['response']['suggestions']}")

# 测试2: 直接测试课程匹配器
print("\n" + "=" * 80)
print("=== 测试2: 直接测试课程匹配器 ===")
matcher = CourseMatcher()

# 测试用户输入和实体
user_input = "我今年38岁，大专毕业，不知道该报什么培训课程？"
entities = [{'type': 'age', 'value': '38岁'}, {'type': 'education_level', 'value': '大专毕业'}]

print(f"测试用户输入: {user_input}")
print(f"测试实体: {entities}")
print("=" * 60)

# 测试推荐课程
recommended = matcher.recommend_courses(user_input, None, entities)
print("\n=== 课程推荐结果 ===")
print(f"推荐课程数量: {len(recommended)}")
print("推荐课程列表（按匹配度排序）:")
for i, course in enumerate(recommended, 1):
    print(f"{i}. {course['course_id']}: {course['title']}")

print("\n测试完成！")
