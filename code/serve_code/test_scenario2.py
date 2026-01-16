#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试场景二：技能培训岗位个性化推荐
"""

import sys
import os
import json

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
print(f"添加到Python路径：{project_root}")

from langchain.policy_agent import PolicyAgent

def test_scenario2():
    """测试场景二"""
    print("测试场景二：技能培训岗位个性化推荐")
    
    # 初始化政策智能体
    agent = PolicyAgent()
    
    # 测试用例：场景二用户输入
    user_input = "请为一位32岁、失业、持有中级电工证的女性推荐工作，她关注补贴申领和灵活时间。"
    
    print(f"\n用户输入：{user_input}")
    
    # 使用handle_scenario进行测试
    result = agent.handle_scenario("scenario2", user_input)
    
    print(f"\n处理结果：")
    print(f"意图：{json.dumps(result['intent'], ensure_ascii=False, indent=2)}")
    
    print(f"\n相关政策：")
    for policy in result['relevant_policies']:
        print(f"- {policy['policy_id']}：{policy['title']}（分类：{policy['category']}）")
    
    print(f"\n推荐岗位：")
    for job in result.get('recommended_jobs', []):
        print(f"- {job['job_id']}：{job['title']}（特征：{job['features']}）")
    
    print(f"\n回答内容：")
    response = result['response']
    print(json.dumps(response, ensure_ascii=False, indent=2))
    
    # 检查肯定部分是否优先提到岗位推荐
    positive_content = response.get('positive', '')
    print(f"\n肯定部分内容：\n{positive_content}")
    
    # 解析JSON嵌套格式
    if positive_content.strip().startswith('```json'):
        positive_content = positive_content.strip().replace('```json', '').replace('```', '')
        try:
            nested_response = json.loads(positive_content)
            positive_content = nested_response.get('positive', '')
            print(f"\n解析后的肯定部分内容：\n{positive_content}")
        except json.JSONDecodeError:
            print("无法解析嵌套JSON")
    
    # 检查岗位推荐和政策说明的顺序
    job_pos = positive_content.find("JOB_A02")  # 找第一个岗位ID
    policy_pos = positive_content.find("POLICY_A02")  # 找第一个政策ID
    
    if job_pos != -1 and policy_pos != -1:
        if job_pos < policy_pos:
            print("✅ 测试通过：岗位推荐优先于政策说明")
        else:
            print("❌ 测试失败：政策说明优先于岗位推荐")
            print(f"岗位位置：{job_pos}, 政策位置：{policy_pos}")
    else:
        print(f"未找到岗位或政策：岗位位置={job_pos}, 政策位置={policy_pos}")
        print("❌ 测试失败：无法判断顺序")
    
    return "推荐岗位：" in positive_content

if __name__ == "__main__":
    success = test_scenario2()
    sys.exit(0 if success else 1)
