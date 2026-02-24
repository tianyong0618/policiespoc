class Job:
    """岗位模型"""
    def __init__(self, job_data):
        """初始化岗位模型
        
        Args:
            job_data: 岗位数据字典
        """
        self.job_id = job_data.get('job_id')
        self.title = job_data.get('title')
        self.description = job_data.get('description', '')
        self.requirements = job_data.get('requirements', [])
        self.benefits = job_data.get('benefits', [])
        self.salary = job_data.get('salary', '')
        self.location = job_data.get('location', '')
        self.type = job_data.get('type', '')  # 全职、兼职等
        self.experience = job_data.get('experience', '')
        self.education = job_data.get('education', '')
        self.features = job_data.get('features', '')
        self.policy_relations = job_data.get('policy_relations', [])
    
    def to_dict(self):
        """转换为字典
        
        Returns:
            岗位数据字典
        """
        return {
            'job_id': self.job_id,
            'title': self.title,
            'description': self.description,
            'requirements': self.requirements,
            'benefits': self.benefits,
            'salary': self.salary,
            'location': self.location,
            'type': self.type,
            'experience': self.experience,
            'education': self.education,
            'features': self.features,
            'policy_relations': self.policy_relations
        }
    
    def match_candidate(self, candidate_profile):
        """匹配候选人
        
        Args:
            candidate_profile: 候选人资料字典
            
        Returns:
            匹配度分数（0-100）和匹配详情
        """
        score = 0
        details = []
        
        # 检查学历要求
        education = candidate_profile.get('education', '')
        if education:
            if '本科' in self.education and '本科' in education:
                score += 20
                details.append('学历符合要求')
            elif '大专' in self.education and ('大专' in education or '本科' in education):
                score += 15
                details.append('学历符合要求')
            elif '高中' in self.education and ('高中' in education or '大专' in education or '本科' in education):
                score += 10
                details.append('学历符合要求')
            else:
                details.append('学历可能不符合要求')
        
        # 检查工作经验
        experience = candidate_profile.get('experience', '')
        if experience:
            if '3-5年' in self.experience and ('3年' in experience or '4年' in experience or '5年' in experience):
                score += 15
                details.append('工作经验符合要求')
            elif '1-3年' in self.experience and ('1年' in experience or '2年' in experience or '3年' in experience):
                score += 15
                details.append('工作经验符合要求')
            elif '应届' in self.experience:
                score += 15
                details.append('工作经验符合要求')
            else:
                details.append('工作经验可能不符合要求')
        
        # 检查技能要求
        skills = candidate_profile.get('skills', [])
        requirements = ' '.join(self.requirements)
        matched_skills = []
        for skill in skills:
            if skill in requirements:
                matched_skills.append(skill)
                score += 5
        if matched_skills:
            details.append(f'技能匹配: {matched_skills}')
        else:
            details.append('未发现匹配的技能')
        
        # 检查政策关联
        if self.policy_relations:
            score += 10
            details.append(f'与政策相关: {self.policy_relations}')
        
        # 确保分数在0-100之间
        score = min(100, max(0, score))
        
        return score, details
    
    def get_requirements_summary(self):
        """获取岗位要求摘要
        
        Returns:
            要求摘要列表
        """
        return self.requirements
    
    def get_benefits_summary(self):
        """获取岗位福利摘要
        
        Returns:
            福利摘要列表
        """
        return self.benefits
