#!/usr/bin/env python3
"""
测试优化后的精准检索与推理功能
"""
import json
import time
from code.langchain.orchestrator import Orchestrator

def test_police_a03_missing_condition():
    """测试POLICY_A03的缺失条件判断"""
    print("\n=== 测试1: POLICY_A03缺失条件判断 ===")
    orchestrator = Orchestrator()
    
    user_input = "我是去年从广东回来的农民工，想在家开个小加工厂（小微企业），听说有返乡创业补贴，能领2万吗？"
    print(f"用户输入: {user_input}")
    
    result = orchestrator.process_query(user_input)
    
    # 检查意图识别
    print(f"\n1. 意图识别: {result['intent']['intent']}")
    print(f"   实体: {json.dumps(result['intent']['entities'], ensure_ascii=False)}")
    
    # 检查相关政策
    print("\n2. 相关政策:")
    for policy in result['relevant_policies']:
        print(f"   - {policy['policy_id']}: {policy['title']}")
    
    # 检查思考过程
    print("\n3. 思考过程:")
    for step in result['thinking_process']:
        print(f"   - {step['step']}: {step['content']}")
        if 'substeps' in step:
            for substep in step['substeps']:
                print(f"     * {substep['step']}: {substep['content']}")
    
    # 检查结构化输出
    print("\n4. 结构化输出:")
    print(f"   肯定部分: {result['response'].get('positive', ['无'])[0] if result['response'].get('positive') else '无'}")
    print(f"   否定部分: {result['response'].get('negative', ['无'])[0] if result['response'].get('negative') else '无'}")
    print(f"   建议部分: {result['response'].get('suggestions', ['无'])[0] if result['response'].get('suggestions') else '无'}")

def test_job_a02_multi_dimension_match():
    """测试JOB_A02的多维度匹配"""
    print("\n=== 测试2: JOB_A02多维度匹配 ===")
    orchestrator = Orchestrator()
    
    user_input = "我有中级电工证，想找个兼职，时间灵活，能申请技能补贴的工作"
    print(f"用户输入: {user_input}")
    
    result = orchestrator.process_query(user_input)
    
    # 检查意图识别
    print(f"\n1. 意图识别: {result['intent']['intent']}")
    print(f"   实体: {json.dumps(result['intent']['entities'], ensure_ascii=False)}")
    
    # 检查推荐岗位
    print("\n2. 推荐岗位:")
    for job in result['recommended_jobs']:
        print(f"   - {job['job_id']}: {job['title']}")
        if 'reasons' in job:
            print(f"     推荐理由: {job['reasons'].get('positive', '无')}")
    
    # 检查相关政策
    print("\n3. 相关政策:")
    for policy in result['relevant_policies']:
        print(f"   - {policy['policy_id']}: {policy['title']}")
    
    # 检查思考过程
    print("\n4. 思考过程:")
    for step in result['thinking_process']:
        print(f"   - {step['step']}: {step['content']}")

def test_course_matching():
    """测试课程匹配逻辑"""
    print("\n=== 测试3: 课程匹配逻辑 ===")
    orchestrator = Orchestrator()
    
    user_input = "我只有初中毕业证，零电商基础，想转行做电商运营，有什么适合的培训课程吗？"
    print(f"用户输入: {user_input}")
    
    result = orchestrator.process_query(user_input)
    
    # 检查意图识别
    print(f"\n1. 意图识别: {result['intent']['intent']}")
    print(f"   实体: {json.dumps(result['intent']['entities'], ensure_ascii=False)}")
    
    # 检查推荐课程
    print("\n2. 推荐课程:")
    for course in result['recommended_courses']:
        print(f"   - {course['course_id']}: {course['title']}")
        if 'reasons' in course:
            print(f"     推荐理由: {course['reasons'].get('positive', '无')}")
    
    # 检查思考过程
    print("\n3. 思考过程:")
    for step in result['thinking_process']:
        print(f"   - {step['step']}: {step['content']}")
        if 'substeps' in step:
            for substep in step['substeps']:
                print(f"     * {substep['step']}: {substep['content']}")

def test_police_a02_display():
    """测试POLICY_A02的完整信息显示"""
    print("\n=== 测试4: POLICY_A02完整信息显示 ===")
    orchestrator = Orchestrator()
    
    user_input = "我失业了，想参加技能培训，有什么补贴政策吗？"
    print(f"用户输入: {user_input}")
    
    result = orchestrator.process_query(user_input)
    
    # 检查相关政策
    print("\n1. 相关政策:")
    for policy in result['relevant_policies']:
        print(f"   - {policy['policy_id']}: {policy['title']}")
    
    # 检查思考过程中的政策检索
    print("\n2. 政策检索详情:")
    for step in result['thinking_process']:
        if step['step'] == "精准检索与推理" and 'substeps' in step:
            for substep in step['substeps']:
                if substep['step'] == "政策检索" and 'substeps' in substep:
                    for policy_substep in substep['substeps']:
                        if "POLICY_A02" in policy_substep['step']:
                            print(f"   - {policy_substep['step']}: {policy_substep['content']}")

def main():
    """主测试函数"""
    print("开始测试优化后的精准检索与推理功能...")
    start_time = time.time()
    
    # 运行所有测试
    test_police_a03_missing_condition()
    test_job_a02_multi_dimension_match()
    test_course_matching()
    test_police_a02_display()
    
    end_time = time.time()
    print(f"\n=== 测试完成 ===")
    print(f"总耗时: {end_time - start_time:.2f}秒")

if __name__ == "__main__":
    main()
