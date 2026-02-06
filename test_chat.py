#!/usr/bin/env python3
# 测试脚本：验证创业补贴与贷款咨询场景
import json
import requests

# 测试用户输入
user_input = "我是去年从广东回来的农民工，想在家开个小加工厂（小微企业），听说有返乡创业补贴，能领2万吗？另外创业贷款怎么申请？"

# API端点
api_url = "http://127.0.0.1:8000/api/chat"

# 发送请求
print("发送测试请求...")
print(f"用户输入: {user_input}")
print()

response = requests.post(
    api_url,
    headers={"Content-Type": "application/json"},
    json={"message": user_input}
)

# 处理响应
if response.status_code == 200:
    result = response.json()
    print("=== 测试结果 ===")
    print()
    
    # 意图与实体识别结果
    print("1. 意图与实体识别:")
    print(f"   意图: {result.get('intent', {}).get('intent', 'N/A')}")
    print(f"   实体: {json.dumps(result.get('intent', {}).get('entities', []), ensure_ascii=False)}")
    print()
    
    # 相关政策
    print("2. 相关政策:")
    for policy in result.get('relevant_policies', []):
        print(f"   - {policy.get('policy_id')}: {policy.get('title')} (分类: {policy.get('category')})")
    print()
    
    # 结构化输出
    print("3. 结构化输出:")
    print(f"   肯定部分: {result.get('response', {}).get('positive', 'N/A')}")
    print(f"   否定部分: {result.get('response', {}).get('negative', 'N/A')}")
    print(f"   主动建议: {result.get('response', {}).get('suggestions', 'N/A')}")
    print()
    
    # 推荐岗位
    print("4. 推荐岗位:")
    for job in result.get('recommended_jobs', []):
        print(f"   - {job.get('job_id')}: {job.get('title')}")
    print()
    
    # 评估结果
    print("5. 评估结果:")
    print(f"   得分: {result.get('evaluation', {}).get('score', 'N/A')}/{result.get('evaluation', {}).get('max_score', 'N/A')}")
    print(f"   政策召回准确率: {result.get('evaluation', {}).get('policy_recall_accuracy', 'N/A')}")
    print(f"   条件判断准确率: {result.get('evaluation', {}).get('condition_accuracy', 'N/A')}")
    print(f"   用户满意度: {result.get('evaluation', {}).get('user_satisfaction', 'N/A')}")
    print()
    
    # 执行时间
    print(f"6. 执行时间: {result.get('execution_time', 'N/A')}秒")
else:
    print(f"请求失败: {response.status_code}")
    print(f"错误信息: {response.text}")
