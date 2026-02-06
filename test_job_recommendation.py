import requests
import json

# API基础URL
API_BASE_URL = 'http://127.0.0.1:8000/api'

# 测试用例：退役军人开汽车维修店，没有选择电商创业
test_message = "我是退役军人，开汽车维修店，并没有选择电商创业，能同时享受税收优惠和场地补贴吗？"

print("测试用例：")
print(test_message)
print("\n发送请求到API...")

# 发送请求
try:
    response = requests.post(
        f"{API_BASE_URL}/chat/stream",
        headers={"Content-Type": "application/json"},
        json={"message": test_message}
    )
    
    if response.status_code == 200:
        print("\nAPI响应成功！")
        print("\n解析响应...")
        
        # 处理流式响应
        content = response.text
        lines = content.split('\n')
        
        # 查找analysis_result事件
        for line in lines:
            if line.startswith('event: analysis_result'):
                # 找到数据行
                data_line = next((l for l in lines[lines.index(line)+1:] if l.startswith('data: ')), None)
                if data_line:
                    data_str = data_line.replace('data: ', '')
                    try:
                        data = json.loads(data_str)
                        print("\n分析结果：")
                        print(f"推荐岗位数量: {len(data.get('recommended_jobs', []))}")
                        print("\n推荐岗位：")
                        for job in data.get('recommended_jobs', []):
                            print(f"- {job['title']} ({job['job_id']})")
                        
                        # 检查是否包含电商创业辅导专员（JOB_A03）
                        has_ecommerce_job = any(job['job_id'] == 'JOB_A03' for job in data.get('recommended_jobs', []))
                        print(f"\n是否包含电商创业辅导专员（JOB_A03）: {'是' if has_ecommerce_job else '否'}")
                        
                        if not has_ecommerce_job:
                            print("\n✅ 测试通过！退役军人开汽车维修店，没有选择电商创业时，正确地没有推荐电商创业辅导专员。")
                        else:
                            print("\n❌ 测试失败！退役军人开汽车维修店，没有选择电商创业时，不应该推荐电商创业辅导专员。")
                            
                    except json.JSONDecodeError as e:
                        print(f"解析JSON失败: {e}")
                    break
    else:
        print(f"API请求失败，状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
except Exception as e:
    print(f"请求发生错误: {e}")
