from code.langchain.orchestrator import Orchestrator

# 创建Orchestrator实例
orchestrator = Orchestrator()

# 测试正常的政策咨询请求
print("测试输入: 我想了解创业政策")
print("=" * 50)

# 处理流式查询
results = orchestrator.process_stream_query('我想了解创业政策')

# 打印所有输出
for i, result in enumerate(results):
    print(f'输出 {i}:')
    print(result)
    print("-" * 50)
    
    # 只显示前3个输出，避免输出过多
    if i >= 2:
        print("... 后续输出省略 ...")
        break