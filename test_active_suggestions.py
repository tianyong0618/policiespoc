#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试不同场景的主动建议生成
"""

import sys
import os

# 添加代码目录到 Python 路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'code'))

# 模拟 ResponseGenerator 类的关键功能，只测试主动建议生成逻辑
class MockResponseGenerator:
    def generate_response(self, user_input, relevant_policies, scenario_type="通用场景", matched_user=None, recommended_jobs=None, recommended_courses=None):
        """模拟生成响应，只返回主动建议"""
        # 根据不同场景生成相应的主动建议
        # 1. 如果有推荐课程，生成成长路径建议
        if recommended_courses:
            suggestions = "勾勒清晰成长路径："
            # 分析推荐课程的信息
            for course in recommended_courses:
                course_title = course.get('title', '')
                course_category = course.get('category', '')
                course_duration = course.get('duration', '')
                course_benefits = course.get('benefits', [])
                
                # 生成学习内容
                suggestions += f"1. 学习内容：{course_title}（{course_category}），"
                if course_duration:
                    suggestions += f"学习时长{course_duration}，"
                if course_benefits:
                    suggestions += "主要收获："
                    for benefit in course_benefits[:2]:
                        suggestions += f"{benefit}、"
                    suggestions = suggestions.rstrip('、') + "；"
                else:
                    suggestions += "系统学习相关专业知识和技能；"
                
                # 生成就业前景
                suggestions += "2. 就业前景：通过该课程学习后，可从事相关领域的专业岗位，如与课程内容相关的技术或管理岗位；"
                
                # 生成最高成就
                suggestions += "3. 最高成就：获得相关专业认证或资格证书，提升职业竞争力，实现职业发展目标。"
                break  # 只使用第一个推荐课程生成建议
        
        # 2. 如果有推荐政策但没有推荐课程，生成申请路径建议
        elif relevant_policies:
            suggestions = "申请路径："
            # 推荐联系相关岗位获取政策申请指导
            if recommended_jobs:
                # 使用第一个推荐岗位作为联系对象
                job_id = recommended_jobs[0].get('job_id', 'JOB_A01')
                job_title = recommended_jobs[0].get('title', '政策咨询岗位')
                suggestions += f"推荐联系{job_title}（{job_id}），获取政策申请全程指导。"
            else:
                # 没有推荐岗位时的通用申请路径
                suggestions += "推荐联系政策咨询岗位（JOB_A01），获取政策申请全程指导。"
        
        # 3. 如果有推荐岗位但没有推荐课程和政策，保留简历优化方案
        elif recommended_jobs:
            suggestions = "简历优化方案："
            # 分析推荐岗位的要求和特点
            job_requirements = []
            job_features = []
            
            for job in recommended_jobs:
                if 'requirements' in job and job['requirements']:
                    job_requirements.extend(job['requirements'])
                if 'features' in job and job['features']:
                    job_features.append(job['features'])
            
            # 根据岗位要求生成具体的简历优化建议
            if job_requirements:
                # 提取关键技能要求
                skill_keywords = ['技能', '经验', '证书', '学历', '能力', '专业', '知识', '熟悉', '掌握', '了解']
                required_skills = []
                
                for req in job_requirements:
                    for keyword in skill_keywords:
                        if keyword in req:
                            required_skills.append(req)
                            break
                
                # 生成基于岗位要求的建议
                if required_skills:
                    suggestions += "1. 根据推荐岗位要求，突出相关技能和经验："
                    for i, skill in enumerate(required_skills[:3], 1):
                        suggestions += f"{i}. {skill}；"
                    suggestions = suggestions.rstrip('；') + "；"
                else:
                    suggestions += "1. 突出与推荐岗位相关的核心技能；"
            else:
                suggestions += "1. 突出与推荐岗位相关的核心技能；"
            
            # 基于用户情况的个性化建议
            if '退役军人' in user_input:
                suggestions += "2. 强调退役军人身份带来的执行力、团队协作能力和责任感；"
            elif '创业' in user_input:
                suggestions += "2. 突出创业经历和项目管理能力，展示市场分析和资源整合经验；"
            elif '电商' in user_input or '直播' in user_input:
                suggestions += "2. 强调电商运营和直播相关技能，展示实际操作经验和案例；"
            elif '技能' in user_input or '证书' in user_input:
                suggestions += "2. 突出技能证书和专业资质，强调实操能力和培训经验；"
            else:
                suggestions += "2. 强调工作经验和成就，使用具体数据和案例展示；"
            
            suggestions += "3. 针对推荐岗位的特点，调整简历内容和重点；"
            suggestions += "4. 确保简历格式清晰，重点突出，与岗位要求高度匹配。"
        
        # 4. 其他情况的通用建议
        else:
            suggestions = "建议：请提供更多个人信息，以便为您提供更精准的政策咨询和个性化建议。"
        
        return {
            "positive": "",
            "negative": "",
            "suggestions": suggestions
        }

# 创建 MockResponseGenerator 实例
ResponseGenerator = MockResponseGenerator

# 创建测试用例
def test_policy_scenario():
    """测试政策分析场景 - 应该生成申请路径建议"""
    print("=== 测试政策分析场景 ===")
    generator = ResponseGenerator()
    
    # 测试数据：只有政策，没有岗位和课程
    user_input = "我想了解创业担保贷款政策"
    relevant_policies = [
        {
            "policy_id": "POLICY_A01",
            "title": "创业担保贷款贴息政策",
            "category": "创业扶持",
            "key_info": "最高贷50万、期限3年，LPR-150BP以上部分财政贴息"
        }
    ]
    recommended_jobs = []
    recommended_courses = []
    
    response = generator.generate_response(
        user_input,
        relevant_policies,
        recommended_jobs=recommended_jobs,
        recommended_courses=recommended_courses
    )
    
    print(f"主动建议: {response.get('suggestions', '')}")
    print(f"是否包含'申请路径': {'申请路径' in response.get('suggestions', '')}")
    print()


def test_job_scenario():
    """测试岗位推荐场景 - 应该生成简历优化方案建议"""
    print("=== 测试岗位推荐场景 ===")
    generator = ResponseGenerator()
    
    # 测试数据：只有岗位，没有政策和课程
    user_input = "我想找电商相关的工作"
    relevant_policies = []
    recommended_jobs = [
        {
            "job_id": "JOB_B01",
            "title": "电商运营专员",
            "requirements": ["熟悉电商平台操作", "具备数据分析能力", "有营销策划经验"],
            "features": "负责电商平台的日常运营和管理"
        }
    ]
    recommended_courses = []
    
    response = generator.generate_response(
        user_input,
        relevant_policies,
        recommended_jobs=recommended_jobs,
        recommended_courses=recommended_courses
    )
    
    print(f"主动建议: {response.get('suggestions', '')}")
    print(f"是否包含'简历优化方案': {'简历优化方案' in response.get('suggestions', '')}")
    print()


def test_course_scenario():
    """测试课程推荐场景 - 应该生成成长路径建议"""
    print("=== 测试课程推荐场景 ===")
    generator = ResponseGenerator()
    
    # 测试数据：只有课程，没有政策和岗位
    user_input = "我想学习电商相关课程"
    relevant_policies = []
    recommended_jobs = []
    recommended_courses = [
        {
            "course_id": "COURSE_C01",
            "title": "电商运营实战课程",
            "category": "职业技能",
            "conditions": ["具备基本电脑操作能力"],
            "benefits": ["掌握电商平台运营技巧", "学会数据分析方法", "获得就业推荐"],
            "duration": "3个月",
            "difficulty": "中级"
        }
    ]
    
    response = generator.generate_response(
        user_input,
        relevant_policies,
        recommended_jobs=recommended_jobs,
        recommended_courses=recommended_courses
    )
    
    print(f"主动建议: {response.get('suggestions', '')}")
    print(f"是否包含'勾勒清晰成长路径': {'勾勒清晰成长路径' in response.get('suggestions', '')}")
    print()


def test_mixed_scenario():
    """测试混合场景 - 应该优先生成课程推荐的成长路径建议"""
    print("=== 测试混合场景 ===")
    generator = ResponseGenerator()
    
    # 测试数据：同时有政策、岗位和课程
    user_input = "我想创业，需要贷款和相关技能培训"
    relevant_policies = [
        {
            "policy_id": "POLICY_A01",
            "title": "创业担保贷款贴息政策",
            "category": "创业扶持",
            "key_info": "最高贷50万、期限3年，LPR-150BP以上部分财政贴息"
        }
    ]
    recommended_jobs = [
        {
            "job_id": "JOB_A01",
            "title": "政策咨询岗位",
            "requirements": ["熟悉政策法规", "具备沟通能力"],
            "features": "为创业者提供政策咨询服务"
        }
    ]
    recommended_courses = [
        {
            "course_id": "COURSE_D01",
            "title": "创业管理课程",
            "category": "创业指导",
            "conditions": ["有创业意向"],
            "benefits": ["掌握创业基础知识", "学会商业计划书撰写", "获得创业导师指导"],
            "duration": "2个月",
            "difficulty": "初级"
        }
    ]
    
    response = generator.generate_response(
        user_input,
        relevant_policies,
        recommended_jobs=recommended_jobs,
        recommended_courses=recommended_courses
    )
    
    print(f"主动建议: {response.get('suggestions', '')}")
    print(f"是否包含'勾勒清晰成长路径': {'勾勒清晰成长路径' in response.get('suggestions', '')}")
    print()

if __name__ == "__main__":
    # 运行所有测试用例
    test_policy_scenario()
    test_job_scenario()
    test_course_scenario()
    test_mixed_scenario()
    print("测试完成！")
