import json
from code.langchain.job_matcher import JobMatcher

# 初始化岗位匹配器
job_matcher = JobMatcher()

# 测试用例1：与技能培训相关的岗位匹配
print("测试用例1：与技能培训相关的岗位匹配")
user_input = "请帮我推荐与技能培训相关的岗位，我有相关经验"

# 模拟实体信息
entities = [
    {"type": "concern", "value": "技能培训"},
    {"type": "employment_status", "value": "有相关经验"}
]

# 测试match_jobs_by_entities方法
matched_jobs = job_matcher.match_jobs_by_entities(entities)
print(f"匹配到的岗位数量: {len(matched_jobs)}")
for job in matched_jobs:
    print(f"- {job['title']} ({job['job_id']})")
    if 'requirements' in job and job['requirements']:
        print("  要求：")
        for req in job['requirements']:
            print(f"    - {req}")

# 测试match_jobs_by_user_input方法
print("\n测试用例2：基于用户输入的岗位匹配")
matched_jobs_by_input = job_matcher.match_jobs_by_user_input(user_input)
print(f"匹配到的岗位数量: {len(matched_jobs_by_input)}")
for job in matched_jobs_by_input:
    print(f"- {job['title']} ({job['job_id']})")
    if 'requirements' in job and job['requirements']:
        print("  要求：")
        for req in job['requirements']:
            print(f"    - {req}")
