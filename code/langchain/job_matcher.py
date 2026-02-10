import json
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - JobMatcher - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class JobMatcher:
    def __init__(self):
        self.jobs = self.load_jobs()
        logger.info(f"加载岗位数据完成，共 {len(self.jobs)} 个岗位")
    
    def load_jobs(self):
        """加载岗位数据"""
        job_file = os.path.join(os.path.dirname(__file__), 'data', 'jobs.json')
        try:
            with open(job_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载岗位数据失败: {e}")
            return []
    
    def match_jobs_by_user_profile(self, user_profile):
        """基于用户画像匹配岗位"""
        matched_jobs = []
        
        for job in self.jobs:
            score = self.calculate_match_score(job, user_profile)
            if score > 0:
                matched_jobs.append({
                    "job": job,
                    "match_score": score
                })
        
        # 按匹配度排序
        matched_jobs.sort(key=lambda x: x["match_score"], reverse=True)
        
        # 返回匹配度最高的3个岗位
        return [item["job"] for item in matched_jobs[:3]]
    
    def match_jobs_by_policy(self, policy_id):
        """基于政策匹配相关岗位"""
        matched_jobs = []
        
        for job in self.jobs:
            if policy_id in job.get("policy_relations", []):
                matched_jobs.append(job)
        
        return matched_jobs
    
    def calculate_match_score(self, job, user_profile):
        """计算岗位与用户的匹配度"""
        score = 0
        
        # 技能匹配
        user_skills = user_profile.get("skills", [])
        job_requirements = job.get("requirements", [])
        
        for skill in user_skills:
            for requirement in job_requirements:
                if skill in requirement:
                    score += 3
        
        # 基于用户描述的匹配
        user_description = user_profile.get("description", "")
        job_title = job.get("title", "")
        
        # 简单的关键词匹配
        job_keywords = job_title.split(" ")
        for keyword in job_keywords:
            if keyword in user_description:
                score += 2
        
        return score
    

    
    def get_all_jobs(self):
        """获取所有岗位信息"""
        return self.jobs
    
    def get_job_by_id(self, job_id):
        """根据ID获取岗位信息"""
        for job in self.jobs:
            if job.get("job_id") == job_id:
                return job
        return None
    
    def match_jobs_by_user_input(self, user_input):
        """基于用户输入信息直接匹配岗位"""
        matched_jobs = []
        
        # 从用户输入中提取关键词
        keywords = self.extract_keywords_from_input(user_input)
        logger.info(f"从用户输入中提取的关键词: {keywords}")
        
        for job in self.jobs:
            # 计算岗位与用户输入的匹配度
            match_score = self.calculate_job_input_match(job, keywords)
            if match_score > 0:
                matched_jobs.append({
                    "job": job,
                    "match_score": match_score
                })
        
        # 按匹配度排序
        matched_jobs.sort(key=lambda x: x["match_score"], reverse=True)
        
        # 返回匹配度最高的岗位
        return [item["job"] for item in matched_jobs]
    
    def extract_keywords_from_input(self, user_input):
        """从用户输入中提取关键词"""
        import re
        
        # 提取基本信息关键词
        keywords = []
        
        # 提取证书信息
        cert_pattern = re.compile(r'(中级|高级|初级)?(电工|焊工|厨师|会计|教师|护士|消防|计算机|软件|设计|营销|管理|创业|电商)证', re.IGNORECASE)
        cert_matches = cert_pattern.findall(user_input)
        for cert in cert_matches:
            keywords.append(''.join(cert))
        
        # 提取就业状态
        if '失业' in user_input:
            keywords.append('失业')
        if '在职' in user_input:
            keywords.append('在职')
        if '待业' in user_input:
            keywords.append('待业')
        if '灵活' in user_input or '兼职' in user_input:
            keywords.append('灵活')
            keywords.append('兼职')
        if '全职' in user_input:
            keywords.append('全职')
        if '退役军人' in user_input:
            keywords.append('退役军人')
        if '返乡' in user_input or '农民工' in user_input:
            keywords.append('返乡农民工')
        
        # 提取关注点
        if '补贴' in user_input:
            keywords.append('补贴')
        if '时间' in user_input:
            keywords.append('时间')
        if '收入' in user_input:
            keywords.append('收入')
        if '创业' in user_input:
            keywords.append('创业')
        if '电商' in user_input:
            keywords.append('电商')
        if '技能' in user_input:
            keywords.append('技能')
        if '培训' in user_input:
            keywords.append('培训')
        
        # 提取技能相关词
        skill_pattern = re.compile(r'(电工|焊工|厨师|会计|教师|护士|消防|计算机|软件|设计|营销|管理|实操|技术|创业|电商|直播|运营)', re.IGNORECASE)
        skill_matches = skill_pattern.findall(user_input)
        for skill in skill_matches:
            keywords.append(skill)
        
        # 去重
        return list(set(keywords))
    
    def calculate_job_input_match(self, job, keywords):
        """计算岗位与用户输入关键词的匹配度"""
        score = 0
        
        # 检查岗位需求
        job_requirements = job.get("requirements", [])
        for req in job_requirements:
            for keyword in keywords:
                if keyword in req:
                    score += 3
        
        # 检查岗位特征
        job_features = job.get("features", "")
        for keyword in keywords:
            if keyword in job_features:
                score += 2
        
        # 检查岗位政策关系
        job_policy_relations = job.get("policy_relations", [])
        # 如果用户关注补贴，优先匹配有政策关系的岗位
        if '补贴' in keywords:
            if job_policy_relations:
                score += 3
        
        # 检查岗位是否为兼职/灵活
        if any(keyword in ['灵活', '兼职'] for keyword in keywords):
            if '灵活' in job_features or '兼职' in job_features:
                score += 3
        # 检查岗位是否为全职/固定时间
        if any(keyword in ['固定', '全职'] for keyword in keywords):
            if '全职' in str(job_requirements):
                score += 3
        
        # 检查岗位是否与创业相关
        if '创业' in keywords:
            if '创业' in job_features or '创业' in str(job_requirements):
                score += 3
        
        # 检查岗位是否与电商相关
        if '电商' in keywords:
            if '电商' in job_features or '电商' in str(job_requirements):
                score += 3
        
        # 检查岗位是否与退役军人相关
        if '退役军人' in keywords:
            if '退役军人' in str(job_requirements):
                score += 5
        
        # 检查岗位是否与返乡农民工相关
        if '返乡农民工' in keywords:
            if '创业' in job_features or '创业' in str(job_requirements):
                score += 3
        
        return score
    
    def match_jobs_by_entities(self, entities, user_input=""):
        """基于实体信息匹配岗位"""
        logger.info(f"基于实体匹配岗位，实体: {entities}")
        matched_jobs = []
        
        # 从实体中提取关键词
        keywords = []
        entity_info = {
            "certificates": [],
            "skills": [],
            "employment_status": [],
            "concerns": [],
            "has_middle_electrician_cert": False,
            "has_flexible_time": False,
            "has_fixed_time": False,
            "has_skill_subsidy": False,
            "has_veteran_status": False,
            "has_entrepreneurship": False,
            "has_ecommerce": False,
            "has_veteran_tax_benefit": False  # 新增：是否了解退役军人创业税收优惠
        }
        
        for entity in entities:
            entity_value = entity.get("value", "")
            entity_type = entity.get("type", "")
            keywords.append(entity_value)
            
            # 基于实体类型添加额外关键词
            if entity_type == "certificate":
                keywords.append("证书")
                entity_info["certificates"].append(entity_value)
                # 检查是否有中级电工证
                if "中级电工证" in entity_value or ("中级" in entity_value and "电工" in entity_value):
                    entity_info["has_middle_electrician_cert"] = True
            elif entity_type == "employment_status":
                keywords.append("就业状态")
                entity_info["employment_status"].append(entity_value)
                # 检查是否有退役军人身份
                if "退役军人" in entity_value:
                    entity_info["has_veteran_status"] = True
            elif entity_type == "skill":
                keywords.append("技能")
                entity_info["skills"].append(entity_value)
                # 检查是否有创业或电商技能
                if "创业" in entity_value:
                    entity_info["has_entrepreneurship"] = True
                if "电商" in entity_value or "直播" in entity_value or "运营" in entity_value:
                    entity_info["has_ecommerce"] = True
            elif entity_type == "concern":
                keywords.append("关注点")
                entity_info["concerns"].append(entity_value)
                # 额外处理技能培训相关的关注点
                if "技能培训" in entity_value or "培训" in entity_value:
                    keywords.append("技能")
                    keywords.append("培训")
            
            # 检查其他关键词
            if "灵活时间" in entity_value or "灵活" in entity_value:
                entity_info["has_flexible_time"] = True
            if "固定时间" in entity_value or "固定" in entity_value:
                entity_info["has_fixed_time"] = True
            if "技能补贴" in entity_value or "补贴" in entity_value:
                entity_info["has_skill_subsidy"] = True
            if "创业" in entity_value:
                entity_info["has_entrepreneurship"] = True
            if "电商" in entity_value:
                entity_info["has_ecommerce"] = True
            # 检查是否了解退役军人创业税收优惠
            if "退役军人创业税收优惠" in entity_value or ("退役军人" in entity_value and "税收优惠" in entity_value):
                entity_info["has_veteran_tax_benefit"] = True
            # 额外处理技能培训相关的关键词
            if "技能培训" in entity_value or "培训" in entity_value:
                keywords.append("技能")
                keywords.append("培训")
        
        # 检查用户输入中是否包含退役军人创业税收优惠
        if "退役军人创业税收优惠" in user_input or ("退役军人" in user_input and "税收优惠" in user_input):
            entity_info["has_veteran_tax_benefit"] = True
        
        logger.info(f"从实体中提取的关键词: {keywords}")
        logger.info(f"实体信息: {entity_info}")
        
        # 基于关键词匹配岗位
        for job in self.jobs:
            job_id = job.get("job_id")
            match_score = self.calculate_job_input_match(job, keywords)
            
            # 特殊处理不同岗位
            if job_id == "JOB_A02":
                # 只有当用户没有提到退役军人创业税收优惠时，才考虑该岗位
                if not entity_info["has_veteran_tax_benefit"]:
                    # 硬性条件：中级电工证符合岗位要求
                    if entity_info["has_middle_electrician_cert"]:
                        match_score += 5
                        logger.info("JOB_A02: 中级电工证符合岗位要求，增加匹配度")
                    # 检查高级电工证
                    if any("高级电工证" in cert for cert in entity_info["certificates"]):
                        match_score += 5
                        logger.info("JOB_A02: 高级电工证符合岗位要求，增加匹配度")
                    # 软性条件：灵活时间匹配兼职属性
                    if entity_info["has_flexible_time"] and "兼职" in str(job.get("requirements", [])):
                        match_score += 3
                        logger.info("JOB_A02: 灵活时间匹配兼职属性，增加匹配度")
                    # 软性条件：固定时间匹配全职属性
                    if entity_info["has_fixed_time"] and "全职" in str(job.get("requirements", [])):
                        match_score += 3
                        logger.info("JOB_A02: 固定时间匹配全职属性，增加匹配度")
                    # 软性条件：技能补贴申领相关
                    if entity_info["has_skill_subsidy"] and "POLICY_A02" in job.get("policy_relations", []):
                        match_score += 3
                        logger.info("JOB_A02: 技能补贴申领与政策关联，增加匹配度")
                else:
                    # 如果用户提到了退役军人创业税收优惠，不推荐该岗位
                    match_score = 0
                    logger.info("JOB_A02: 用户关注退役军人创业税收优惠，不推荐该岗位")
            elif job_id == "JOB_A05":
                # 退役军人创业项目评估师
                if entity_info["has_veteran_status"]:
                    match_score += 5
                    logger.info("JOB_A05: 退役军人身份符合岗位要求，增加匹配度")
                if entity_info["has_entrepreneurship"]:
                    match_score += 3
                    logger.info("JOB_A05: 创业意向符合岗位要求，增加匹配度")
                # 增加对退役军人创业税收优惠的匹配
                if entity_info["has_veteran_tax_benefit"]:
                    match_score += 10  # 大幅增加匹配度
                    logger.info("JOB_A05: 熟悉退役军人创业税收优惠，大幅增加匹配度")
            elif job_id == "JOB_A03":
                # 电商创业辅导专员
                # 只有当用户没有提到退役军人创业税收优惠时，才考虑该岗位
                if not entity_info["has_veteran_tax_benefit"]:
                    if entity_info["has_ecommerce"]:
                        match_score += 5
                        logger.info("JOB_A03: 电商技能符合岗位要求，增加匹配度")
                    if entity_info["has_entrepreneurship"]:
                        match_score += 3
                        logger.info("JOB_A03: 创业意向符合岗位要求，增加匹配度")
                else:
                    # 如果用户提到了退役军人创业税收优惠，降低该岗位的匹配度
                    match_score = 0
                    logger.info("JOB_A03: 用户关注退役军人创业税收优惠，不推荐该岗位")
            elif job_id == "JOB_A01":
                # 创业孵化基地管理员
                # 只有当用户没有提到退役军人创业税收优惠时，才考虑该岗位
                if not entity_info["has_veteran_tax_benefit"]:
                    if entity_info["has_entrepreneurship"]:
                        match_score += 4
                        logger.info("JOB_A01: 创业意向符合岗位要求，增加匹配度")
                else:
                    # 如果用户提到了退役军人创业税收优惠，降低该岗位的匹配度
                    match_score = 0
                    logger.info("JOB_A01: 用户关注退役军人创业税收优惠，不推荐该岗位")
            elif job_id == "JOB_A04":
                # 技能培训课程顾问
                # 只有当用户的输入或实体中包含相关政策信息时，才增加匹配度
                # 检查用户是否了解POLICY_A02/A05
                has_policy_info = False
                # 检查实体中是否有政策相关信息
                for entity in entities:
                    entity_value = entity.get("value", "")
                    if "POLICY_A02" in entity_value or "POLICY_A05" in entity_value or "政策" in entity_value:
                        has_policy_info = True
                        break
                # 检查用户输入中是否有政策相关信息
                if not has_policy_info:
                    if "POLICY_A02" in user_input or "POLICY_A05" in user_input or "政策" in user_input:
                        has_policy_info = True
                
                # 如果用户没有政策相关信息，JOB_A04的匹配分数为0
                if not has_policy_info:
                    match_score = 0
                    logger.info("JOB_A04: 用户无政策相关信息，不推荐该岗位")
                else:
                    # 只有当用户有政策相关信息时，才增加匹配度
                    match_score += 3
                    logger.info("JOB_A04: 政策信息符合岗位要求，增加匹配度")
                    # 技能补贴关注点只有在用户了解政策的情况下才增加匹配度
                    if entity_info["has_skill_subsidy"]:
                        match_score += 2
                        logger.info("JOB_A04: 技能补贴关注点符合岗位要求，增加匹配度")
            
            if match_score > 0:
                matched_jobs.append({
                    "job": job,
                    "match_score": match_score,
                    "entity_info": entity_info
                })
        
        # 按匹配度排序
        matched_jobs.sort(key=lambda x: x["match_score"], reverse=True)
        
        # 返回匹配度最高的3个岗位，并添加实体信息用于生成推荐理由
        result = []
        for item in matched_jobs[:3]:
            job = item["job"]
            job["entity_info"] = item["entity_info"]
            result.append(job)
        
        return result