#!/usr/bin/env python3
# 测试固定时间的岗位推荐

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath('.'))

from code.langchain.orchestrator import Orchestrator

# 创建协调器实例
orchestrator = Orchestrator()

# 测试用例1：用户关注固定时间
print("测试用例1：用户关注固定时间")
user_input = "为一位32岁、失业、持有高级电工证且关注固定时间的男性推荐工作"

# 处理查询
result = orchestrator.process_query(user_input)

# 打印结果
print(f"用户输入: {user_input}")
print(f"推荐岗位数量: {len(result['recommended_jobs'])}")
print("\n推荐岗位：")
for job in result['recommended_jobs']:
    print(f"- {job['job_id']}: {job['title']}")
    print(f"  推荐理由: {job['reasons']['positive']}")
    print()

print("\n思考过程：")
for step in result['thinking_process']:
    print(f"{step['step']}: {step['content']}")
    if 'substeps' in step:
        for substep in step['substeps']:
            print(f"  - {substep['step']}: {substep['content']}")

print("\n测试完成！")
