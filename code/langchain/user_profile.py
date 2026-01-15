import json
import os
import logging
from .job_matcher import JobMatcher

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - UserProfile - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UserProfileManager:
    def __init__(self, job_matcher=None):
        self.user_profiles = self.load_user_profiles()
        self.job_matcher = job_matcher if job_matcher else JobMatcher()
        logger.info(f"加载用户画像数据完成，共 {len(self.user_profiles)} 个用户")
    
    def load_user_profiles(self):
        """加载用户画像数据"""
        profile_file = os.path.join(os.path.dirname(__file__), 'data', 'user_profiles.json')
        try:
            with open(profile_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载用户画像数据失败: {e}")
            return []
    
    def get_user_profile(self, user_id):
        """根据用户ID获取用户画像"""
        for profile in self.user_profiles:
            if profile.get("user_id") == user_id:
                return profile
        return None
    
    def create_or_update_user_profile(self, user_id, profile_data):
        """创建或更新用户画像"""
        existing_profile = self.get_user_profile(user_id)
        
        if existing_profile:
            # 更新现有画像
            existing_profile.update(profile_data)
            logger.info(f"更新用户画像: {user_id}")
        else:
            # 创建新画像
            new_profile = profile_data.copy()
            new_profile["user_id"] = user_id
            self.user_profiles.append(new_profile)
            logger.info(f"创建新用户画像: {user_id}")
        
        # 保存到文件
        self.save_user_profiles()
        return self.get_user_profile(user_id)
    
    def save_user_profiles(self):
        """保存用户画像数据到文件"""
        profile_file = os.path.join(os.path.dirname(__file__), 'data', 'user_profiles.json')
        try:
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_profiles, f, ensure_ascii=False, indent=2)
            logger.info("用户画像数据保存成功")
        except Exception as e:
            logger.error(f"保存用户画像数据失败: {e}")
    
    def build_user_profile_from_input(self, user_input):
        """从用户输入构建用户画像"""
        # 这里简化处理，实际应该使用NLP技术从用户输入中提取信息
        # 目前返回一个默认的用户画像模板
        return {
            "basic_info": {
                "age": 30,
                "gender": "未知",
                "education": "未知",
                "work_experience": "未知"
            },
            "skills": [],
            "preferences": {
                "salary_range": [],
                "work_location": [],
                "work_type": []
            },
            "policy_interest": [],
            "job_interest": []
        }
    
    def get_personalized_recommendations(self, user_id):
        """获取个性化推荐（政策和岗位）"""
        user_profile = self.get_user_profile(user_id)
        if not user_profile:
            return {
                "policies": [],
                "jobs": []
            }
        
        # 获取推荐岗位
        recommended_jobs = self.job_matcher.match_jobs_by_user_profile(user_profile)
        
        # 获取推荐政策（简化处理，实际应该基于用户兴趣匹配政策）
        recommended_policies = self.get_recommended_policies(user_profile)
        
        return {
            "policies": recommended_policies,
            "jobs": recommended_jobs
        }
    
    def get_recommended_policies(self, user_profile):
        """基于用户画像推荐政策"""
        # 简化处理，实际应该加载政策数据并进行匹配
        # 这里返回一个空列表，实际实现时需要从policies.json加载数据
        return []
    
    def update_user_interest(self, user_id, policy_interest=None, job_interest=None):
        """更新用户兴趣"""
        user_profile = self.get_user_profile(user_id)
        if not user_profile:
            return None
        
        if policy_interest:
            user_profile["policy_interest"] = policy_interest
        
        if job_interest:
            user_profile["job_interest"] = job_interest
        
        self.save_user_profiles()
        return user_profile
    
    def match_user_profile(self, user_input):
        """根据用户输入匹配最相似的用户画像"""
        best_match = None
        max_score = 0
        
        for profile in self.user_profiles:
            score = 0
            # 匹配基本信息
            basic_info = profile.get("basic_info", {})
            identity = basic_info.get("identity", "")
            if identity and identity in user_input:
                score += 3
            
            gender = basic_info.get("gender", "")
            if gender and gender in user_input:
                score += 1
                
            age = str(basic_info.get("age", ""))
            if age and age in user_input:
                score += 1
            
            # 匹配技能
            for skill in profile.get("skills", []):
                if skill in user_input:
                    score += 2
            
            # 匹配描述关键词
            description = profile.get("description", "")
            # 简单的关键词提取（这里只是示例，实际可以使用jieba分词）
            keywords = ["失业", "创业", "退役军人", "高校毕业生", "农民工", "贷款", "补贴"]
            for kw in keywords:
                if kw in description and kw in user_input:
                    score += 1
            
            if score > max_score:
                max_score = score
                best_match = profile
        
        # 设置一个匹配阈值，避免错误匹配
        if best_match and max_score >= 3:
            logger.info(f"匹配到用户画像: {best_match.get('user_id')} (得分: {max_score})")
            return best_match
        
        return None
    
    def analyze_user_skills(self, user_input):
        """分析用户技能"""
        # 简化处理，实际应该使用NLP技术从用户输入中提取技能信息
        skills = []
        
        # 关键词匹配
        skill_keywords = [
            "电工证", "汽车维修", "创业", "技能培训", 
            "计算机", "英语", "管理", "销售"
        ]
        
        for keyword in skill_keywords:
            if keyword in user_input:
                skills.append(keyword)
        
        return skills