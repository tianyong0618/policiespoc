import requests
import json

# API基础URL
API_BASE_URL = 'http://127.0.0.1:8000/api'

# 测试用例：用户明确要求岗位推荐
test_message = "请帮我推荐与技能培训相关的岗位，我有相关经验，希望能获得岗位推荐和简历优化建议。"

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
        
        # 打印完整的响应内容，用于调试
        print("\n完整的响应内容：")
        print(content[:1000])  # 只打印前1000个字符，避免输出过多
        
        # 查找analysis_result事件
        lines = content.split('\n')
        analysis_result_found = False
        current_event = []
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('event: analysis_result'):
                analysis_result_found = True
                current_event = [line]
            elif analysis_result_found:
                current_event.append(line)
                if line == '':  # 事件结束
                    # 提取数据部分
                    data_lines = [l for l in current_event if l.startswith('data: ')]
                    
                    if data_lines:
                        # 合并所有数据行
                        data_str = ''.join([l.replace('data: ', '') for l in data_lines])
                        try:
                            data = json.loads(data_str)
                            print("\n分析结果：")
                            print(f"推荐岗位数量: {len(data.get('recommended_jobs', []))}")
                            print("\n推荐岗位：")
                            for job in data.get('recommended_jobs', []):
                                print(f"- {job['title']} ({job['job_id']})")
                                if 'requirements' in job and job['requirements']:
                                    print("  要求：")
                                    for req in job['requirements']:
                                        print(f"    - {req}")
                            
                            # 检查主动建议部分
                            print("\n主动建议（简历优化方案）：")
                            # 检查data中是否有content字段
                            suggestions = ""
                            if 'content' in data:
                                content = data.get('content', {})
                                if isinstance(content, dict):
                                    suggestions = content.get('suggestions', '')
                                    # 打印完整的content字段，用于调试
                                    print("\n完整的content字段：")
                                    print(content)
                                else:
                                    print("\ncontent字段不是字典类型：")
                                    print(content)
                            # 检查data中是否有response字段
                            if 'response' in data and not suggestions:
                                response = data.get('response', {})
                                if isinstance(response, dict):
                                    suggestions = response.get('suggestions', '')
                                    # 打印完整的response字段，用于调试
                                    print("\n完整的response字段：")
                                    print(response)
                                else:
                                    print("\nresponse字段不是字典类型：")
                                    print(response)
                            print(suggestions)
                            
                            # 验证简历优化建议是否基于推荐岗位
                            if '简历优化方案' in suggestions and len(data.get('recommended_jobs', [])) > 0:
                                print("\n✅ 测试通过！系统成功根据推荐岗位提供了简历优化建议。")
                            else:
                                print("\n❌ 测试失败！系统没有提供基于推荐岗位的简历优化建议。")
                                
                        except json.JSONDecodeError as e:
                            print(f"解析JSON失败: {e}")
                            print(f"数据字符串: {data_str}")
                        break
    else:
        print(f"API请求失败，状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
except Exception as e:
    print(f"请求发生错误: {e}")
