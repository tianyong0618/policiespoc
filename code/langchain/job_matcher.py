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