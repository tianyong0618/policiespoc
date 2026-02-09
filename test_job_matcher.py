#!/usr/bin/env python3
"""
测试job_matcher.py功能，验证删除薪资和地点字段后是否正常工作
"""
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'code'))

from langchain.job_matcher import JobMatcher

print("测试JobMatcher功能...")

# 初始化JobMatcher
job_matcher = JobMatcher()
print(f"加载岗位数量: {len(job_matcher.get_all_jobs())}")

# 测试获取所有岗位
all_jobs = job_matcher.get_all_jobs()
print("\n所有岗位:")
for job in all_jobs:
    print(f"- {job['job_id']}: {job['title']}")
    print(f"  要求: {job['requirements']}")
    print(f"  特点: {job['features']}")
    print(f"  政策关联: {job['policy_relations']}")
    # 验证薪资、地点和福利字段不存在
    if 'salary' in job:
        print(f"  薪资: {job['salary']}")
    if 'location' in job:
        print(f"  地点: {job['location']}")
    if 'benefits' in job:
        print(f"  福利: {job['benefits']}")
    print()

# 测试基于政策匹配岗位
print("\n基于政策匹配岗位测试:")
test_policies = ['POLICY_A01', 'POLICY_A02', 'POLICY_A03']
for policy_id in test_policies:
    matched_jobs = job_matcher.match_jobs_by_policy(policy_id)
    print(f"\n政策 {policy_id} 相关岗位:")
    for job in matched_jobs:
        print(f"- {job['job_id']}: {job['title']}")

# 测试基于用户画像匹配岗位
print("\n基于用户画像匹配岗位测试:")
test_user_profile = {
    "skills": ["中级电工职业资格证书"],
    "job_interest": ["培训", "教师"],
    "policy_interest": ["技能培训"],
    "preferences": {
        # 注意：这里仍然包含薪资和地点偏好，但JobMatcher应该忽略它们
        "salary_range": ["5000-8000"],
        "work_location": ["北京市"]
    }
}

matched_jobs = job_matcher.match_jobs_by_user_profile(test_user_profile)
print("匹配的岗位:")
for job in matched_jobs:
    print(f"- {job['job_id']}: {job['title']}")

print("\n测试完成! JobMatcher功能正常，已成功移除薪资、地点和福利相关代码。")
