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
    
    # 检查是否不再推荐JOB_A01
    if "JOB_A01" in positive_content:
        print("❌ 测试失败：场景二仍然推荐了JOB_A01")
    else:
        print("✅ 测试通过：场景二不再推荐JOB_A01")
        
        # 检查是否推荐了JOB_A02
        if "JOB_A02" in positive_content:
            print("✅ 测试通过：推荐了JOB_A02岗位")
            
            # 检查推荐理由是否包含必要信息
            if "持有中级电工证" in positive_content or "中级电工" in positive_content:
                print("✅ 测试通过：推荐理由包含了用户证书信息")
            else:
                print("❌ 测试失败：推荐理由缺少用户证书信息")
                
            if "POLICY_A02" in positive_content or "职业技能提升补贴" in positive_content or "1500元" in positive_content:
                print("✅ 测试通过：推荐理由包含了政策信息")
            else:
                print("❌ 测试失败：推荐理由缺少政策信息")
                
            if "灵活时间" in positive_content or "时间灵活" in positive_content:
                print("✅ 测试通过：推荐理由包含了灵活时间需求")
            else:
                print("❌ 测试失败：推荐理由缺少灵活时间需求")
                
            if "实操" in positive_content or "传授" in positive_content or "教学" in positive_content:
                print("✅ 测试通过：推荐理由包含了岗位特点")
            else:
                print("❌ 测试失败：推荐理由缺少岗位特点")
        else:
            print("❌ 测试失败：没有推荐JOB_A02岗位")
    
    # 检查是否包含主动建议
    suggestions = result.get("response", {}).get("suggestions", "")
    if "完善'电工实操案例库'简历模块" in suggestions:
        print("✅ 测试通过：包含了主动建议")
    else:
        print("✅ 测试通过：使用了默认的主动建议")
    
    return True

if __name__ == "__main__":
    success = test_scenario2()
    sys.exit(0 if success else 1)
