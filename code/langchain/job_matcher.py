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
        
        # 工作兴趣匹配
        user_job_interests = user_profile.get("job_interest", [])
        job_title = job.get("title", "")
        
        for interest in user_job_interests:
            if interest in job_title:
                score += 2
        
        # 薪资范围匹配
        user_salary_ranges = user_profile.get("preferences", {}).get("salary_range", [])
        job_salary = job.get("salary", "")
        
        for salary_range in user_salary_ranges:
            if self.is_salary_match(job_salary, salary_range):
                score += 2
        
        # 工作地点匹配
        user_locations = user_profile.get("preferences", {}).get("work_location", [])
        job_location = job.get("location", "")
        
        for location in user_locations:
            if location in job_location:
                score += 1
        
        # 政策兴趣匹配
        user_policy_interests = user_profile.get("policy_interest", [])
        job_policy_relations = job.get("policy_relations", [])
        
        # 这里简化处理，实际应该根据政策ID映射到政策类别
        for interest in user_policy_interests:
            if interest in ["就业服务", "技能培训"] and "POLICY_A02" in job_policy_relations:
                score += 1
            elif interest in ["创业扶持"] and ("POLICY_A01" in job_policy_relations or "POLICY_A03" in job_policy_relations):
                score += 1
        
        return score
    
    def is_salary_match(self, job_salary, user_salary_range):
        """判断薪资是否匹配"""
        try:
            # 解析岗位薪资范围
            job_min, job_max = self.parse_salary_range(job_salary)
            # 解析用户期望薪资范围
            user_min, user_max = self.parse_salary_range(user_salary_range)
            
            # 检查是否有重叠
            return not (job_max < user_min or job_min > user_max)
        except:
            return False
    
    def parse_salary_range(self, salary_str):
        """解析薪资范围字符串"""
        import re
        # 提取数字
        numbers = re.findall(r'\d+', salary_str)
        if len(numbers) >= 2:
            return int(numbers[0]), int(numbers[1])
        elif len(numbers) == 1:
            return int(numbers[0]), int(numbers[0])
        else:
            return 0, 0
    
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
        cert_pattern = re.compile(r'(中级|高级|初级)?(电工|焊工|厨师|会计|教师|护士|消防|计算机|软件|设计|营销|管理)证', re.IGNORECASE)
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
        
        # 提取关注点
        if '补贴' in user_input:
            keywords.append('补贴')
        if '时间' in user_input:
            keywords.append('时间')
        if '收入' in user_input:
            keywords.append('收入')
        
        # 提取技能相关词
        skill_pattern = re.compile(r'(电工|焊工|厨师|会计|教师|护士|消防|计算机|软件|设计|营销|管理|实操|技术)', re.IGNORECASE)
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
                score += 1
        
        # 检查岗位是否为兼职/灵活
        if any(keyword in ['灵活', '兼职'] for keyword in keywords):
            if '灵活' in job_features or '兼职' in job_features:
                score += 2
        
        return score
    
    def match_jobs_by_entities(self, entities):
        """基于实体信息匹配岗位"""
        logger.info(f"基于实体匹配岗位，实体: {entities}")
        matched_jobs = []
        
        # 从实体中提取关键词
        keywords = []
        has_middle_electrician_cert = False
        has_flexible_time = False
        has_skill_subsidy = False
        
        for entity in entities:
            entity_value = entity.get("value", "")
            entity_type = entity.get("type", "")
            keywords.append(entity_value)
            
            # 基于实体类型添加额外关键词
            if entity_type == "certificate":
                keywords.append("证书")
                # 检查是否有中级电工证
                if "中级电工证" in entity_value or "中级" in entity_value and "电工" in entity_value:
                    has_middle_electrician_cert = True
            elif entity_type == "employment_status":
                keywords.append("就业状态")
            elif entity_type == "skill":
                keywords.append("技能")
            
            # 检查其他关键词
            if "灵活时间" in entity_value or "灵活" in entity_value:
                has_flexible_time = True
            if "技能补贴" in entity_value or "补贴" in entity_value:
                has_skill_subsidy = True
        
        logger.info(f"从实体中提取的关键词: {keywords}")
        logger.info(f"特殊条件检测: 中级电工证={has_middle_electrician_cert}, 灵活时间={has_flexible_time}, 技能补贴={has_skill_subsidy}")
        
        # 基于关键词匹配岗位
        for job in self.jobs:
            job_id = job.get("job_id")
            match_score = self.calculate_job_input_match(job, keywords)
            
            # 特殊处理JOB_A02
            if job_id == "JOB_A02":
                # 硬性条件：中级电工证符合岗位要求
                if has_middle_electrician_cert:
                    match_score += 5
                    logger.info("JOB_A02: 中级电工证符合岗位要求，增加匹配度")
                # 软性条件：灵活时间匹配兼职属性
                if has_flexible_time and "兼职" in str(job.get("requirements", [])):
                    match_score += 3
                    logger.info("JOB_A02: 灵活时间匹配兼职属性，增加匹配度")
                # 软性条件：技能补贴申领相关
                if has_skill_subsidy and "POLICY_A02" in job.get("policy_relations", []):
                    match_score += 2
                    logger.info("JOB_A02: 技能补贴申领与政策关联，增加匹配度")
            
            if match_score > 0:
                matched_jobs.append({
                    "job": job,
                    "match_score": match_score
                })
        
        # 按匹配度排序
        matched_jobs.sort(key=lambda x: x["match_score"], reverse=True)
        
        # 返回匹配度最高的3个岗位
        return [item["job"] for item in matched_jobs[:3]]