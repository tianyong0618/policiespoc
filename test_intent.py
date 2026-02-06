from code.langchain.orchestrator import Orchestrator

# 创建Orchestrator实例
orchestrator = Orchestrator()

# 测试"帮我做个ppt"输入
print("测试输入: 帮我做个ppt")
print("=" * 50)

# 处理流式查询
results = orchestrator.process_stream_query('帮我做个ppt')

# 打印所有输出
for i, result in enumerate(results):
    print(f'输出 {i}:')
    print(result)
    print("-" * 50)