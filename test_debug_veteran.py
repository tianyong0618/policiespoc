import requests
import json

# API基础URL
API_BASE_URL = 'http://127.0.0.1:8000/api'

# 测试用例：退役军人开汽车维修店，同时入驻创业孵化基地
test_message = "我是退役军人，开汽车维修店，同时入驻创业孵化基地，能同时享受税收优惠和场地补贴吗？"

print("测试用例：")
print(test_message)
print("\n发送请求到API...")

# 发送请求
try:
    response = requests.post(
        f"{API_BASE_URL}/chat",
        headers={"Content-Type": "application/json"},
        json={"message": test_message}
    )
    
    if response.status_code == 200:
        print("\nAPI响应成功！")
        print("\n完整响应：")
        
        # 解析响应
        data = response.json()
        
        # 打印详细信息
        print(f"意图识别：{json.dumps(data.get('intent', {}), ensure_ascii=False)}")
        print(f"\n相关政策：")
        for policy in data.get('relevant_policies', []):
            print(f"- {policy.get('policy_id', '')}: {policy.get('title', '')}")
        
        print(f"\n肯定部分: {data.get('response', {}).get('positive', '')}")
        print(f"否定部分: {data.get('response', {}).get('negative', '')}")
        print(f"建议部分: {data.get('response', {}).get('suggestions', '')}")
        print(f"回答部分: {data.get('response', {}).get('answer', '')}")
        
        # 检查是否包含POLICY_A06
        relevant_policies = data.get('relevant_policies', [])
        has_policy_a06 = any(policy.get('policy_id') == 'POLICY_A06' for policy in relevant_policies)
        print(f"\n是否包含POLICY_A06: {'是' if has_policy_a06 else '否'}")
        
        if has_policy_a06:
            print("\n✅ 测试通过！系统正确识别了开汽车维修店属于个体经营，匹配到了POLICY_A06政策。")
        else:
            print("\n❌ 测试失败！系统没有识别开汽车维修店属于个体经营，未匹配到POLICY_A06政策。")
            print("\n调试信息：")
            print(f"意图识别结果：{json.dumps(data.get('intent', {}), ensure_ascii=False)}")
            print(f"政策推荐需求：{data.get('intent', {}).get('needs_policy_recommendation', False)}")
            print(f"思考过程：{json.dumps(data.get('thinking_process', []), ensure_ascii=False)}")
    else:
        print(f"API请求失败，状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
except Exception as e:
    print(f"请求发生错误: {e}")
