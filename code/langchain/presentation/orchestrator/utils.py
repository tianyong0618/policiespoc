import json


def extract_user_preferences(intent_info, user_input):
    """从意图信息和用户输入中提取用户偏好"""
    # 从实体信息中提取用户的时间偏好
    time_preference = ""
    entities_info = intent_info.get('entities', [])
    for entity in entities_info:
        entity_value = entity.get('value', '')
        entity_type = entity.get('type', '')
        if entity_type == 'concern' and ('固定时间' in entity_value or '固定' in entity_value):
            time_preference = "固定时间"
            break
        elif entity_type == 'concern' and ('灵活时间' in entity_value or '灵活' in entity_value):
            time_preference = "灵活时间"
            break
    
    # 如果从实体中没有提取到时间偏好，再从用户输入中提取
    if not time_preference:
        if "固定时间" in user_input:
            time_preference = "固定时间"
        elif "灵活时间" in user_input:
            time_preference = "灵活时间"
    
    # 从实体信息中提取用户的证书情况
    certificate_level = ""
    for entity in entities_info:
        entity_value = entity.get('value', '')
        entity_type = entity.get('type', '')
        if entity_type == 'certificate':
            certificate_level = entity_value
            break
    
    # 如果从实体中没有提取到证书情况，再从用户输入中提取
    if not certificate_level:
        if "高级电工证" in user_input:
            certificate_level = "高级电工证"
        elif "中级电工证" in user_input:
            certificate_level = "中级电工证"
    
    return {
        "time_preference": time_preference,
        "certificate_level": certificate_level
    }


def generate_resume_suggestions(user_input, recommended_jobs):
    """基于用户输入和推荐岗位生成个性化简历优化建议"""
    suggestions = "简历优化方案："
    
    if recommended_jobs:
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
    else:
        # 没有推荐岗位时的通用建议
        if '退役军人' in user_input:
            suggestions += "1. 突出退役军人身份和相关技能；2. 强调执行力和团队协作能力；3. 展示与目标岗位相关的经验；4. 提及对创业或相关领域的热情。"
        elif '创业' in user_input:
            suggestions += "1. 突出创业经历和项目管理能力；2. 强调市场分析和资源整合能力；3. 展示与目标岗位相关的技能；4. 提及对政策的了解和应用能力。"
        elif '电商' in user_input or '直播' in user_input:
            suggestions += "1. 突出电商运营和直播相关技能；2. 强调数据分析和用户运营能力；3. 展示实际操作经验和案例；4. 提及对行业趋势的了解。"
        elif '技能' in user_input or '证书' in user_input:
            suggestions += "1. 突出技能证书和专业资质；2. 强调实操能力和培训经验；3. 展示与目标岗位相关的技能匹配度；4. 提及对技能提升的持续学习态度。"
        else:
            suggestions += "1. 突出与目标岗位相关的核心技能；2. 强调工作经验和成就；3. 展示学习能力和适应能力；4. 确保简历格式清晰，重点突出。"
    
    return suggestions


def generate_job_reasons(job, entity_info=None):
    """基于岗位信息生成详细的推荐理由"""
    # 基于岗位信息生成详细的推荐理由
    job_features = job.get('features', '')
    job_requirements = job.get('requirements', [])
    job_policy_relations = job.get('policy_relations', [])
    entity_info = entity_info or job.get('entity_info', {})
    
    # 生成推荐理由
    reasons = []
    
    # 岗位特点
    if job_features:
        reasons.append(f"①岗位特点：{job_features}")
    else:
        reasons.append("①岗位特点：符合市场需求")
    
    # 工作模式
    if '兼职' in str(job_requirements) or '灵活' in job_features:
        reasons.append("②工作模式：支持兼职/灵活时间")
    else:
        reasons.append("②工作模式：稳定的工作时间")
    
    # 经验匹配
    has_match = False
    if entity_info:
        # 检查证书匹配
        if entity_info.get('certificates'):
            reasons.append(f"③经验匹配：您的证书与岗位要求相匹配")
            has_match = True
        # 检查技能匹配
        elif entity_info.get('skills'):
            reasons.append(f"③经验匹配：您的技能与岗位要求相匹配")
            has_match = True
        # 检查就业状态匹配
        elif entity_info.get('employment_status'):
            reasons.append(f"③经验匹配：您的就业状态适合该岗位")
            has_match = True
    if not has_match:
        reasons.append("③经验匹配：岗位要求与您的背景相符合")
    
    return {
        'positive': '；'.join(reasons),
        'negative': ''
    }


def clean_policy_content(reasons):
    """清理岗位推荐理由，移除政策相关内容"""
    policy_keywords = ['POLICY_A02', '职业技能提升补贴', '补贴申请', '补贴政策', '申请补贴', '技能提升补贴政策', '补贴标准', '申领时限', '可按', '申请补贴', '职业资格证书', '证书核发之日起12个月内', '双重收入', '补贴', '政策']
    
    positive_reasons = reasons.get('positive', '')
    
    # 检查是否包含任何政策关键词
    has_policy_content = any(keyword in positive_reasons for keyword in policy_keywords)
    
    # 检查是否包含"补贴申请情况"这样的部分
    has_subsidy_section = '补贴申请情况' in positive_reasons
    
    # 如果包含政策内容或补贴申请部分，重新生成推荐理由
    if has_policy_content or has_subsidy_section:
        # 分割推荐理由，按序号分割
        reason_parts = positive_reasons.split('。')
        
        # 过滤掉包含政策内容的部分
        filtered_parts = []
        for part in reason_parts:
            if part.strip():
                # 检查该部分是否包含政策相关内容
                part_has_policy = any(keyword in part for keyword in policy_keywords)
                part_has_subsidy = '补贴申请情况' in part
                
                if not part_has_policy and not part_has_subsidy:
                    filtered_parts.append(part.strip())
        
        # 如果有过滤后的部分，使用它们
        if filtered_parts:
            positive_reasons = '。'.join(filtered_parts)
        else:
            # 如果没有有效的理由，生成默认理由
            positive_reasons = '①证书匹配情况：您的证书符合岗位要求，能为您的工作提供有力支持；②工作模式：岗位提供灵活的工作模式，满足您的时间需求；③收入情况：您从事该岗位可获得稳定的课时费收入；④岗位特点与经验匹配度：岗位特点与您的经验高度匹配'
    
    # 更新推荐理由
    reasons['positive'] = positive_reasons
    return reasons
