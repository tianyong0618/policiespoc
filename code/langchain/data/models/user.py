class UserProfile:
    """用户画像模型"""
    def __init__(self, user_data):
        """初始化用户画像模型
        
        Args:
            user_data: 用户数据字典
        """
        self.user_id = user_data.get('user_id')
        self.description = user_data.get('description', '')
        self.basic_info = user_data.get('basic_info', {})
        self.core_needs = user_data.get('core_needs', [])
        self.data = user_data.get('data', {})
        self.tags = user_data.get('tags', [])
    
    def to_dict(self):
        """转换为字典
        
        Returns:
            用户数据字典
        """
        return {
            'user_id': self.user_id,
            'description': self.description,
            'basic_info': self.basic_info,
            'core_needs': self.core_needs,
            'data': self.data,
            'tags': self.tags
        }
    
    def get_identity(self):
        """获取用户身份
        
        Returns:
            用户身份字符串
        """
        return self.basic_info.get('identity', '')
    
    def get_needs(self):
        """获取用户核心需求
        
        Returns:
            核心需求列表
        """
        return self.core_needs
    
    def match_policy(self, policy):
        """匹配政策
        
        Args:
            policy: 政策对象
            
        Returns:
            匹配度分数（0-100）和匹配详情
        """
        score = 0
        details = []
        
        # 检查用户身份与政策条件的匹配
        identity = self.get_identity()
        policy_conditions = ' '.join([cond.get('condition', '') for cond in policy.conditions])
        
        if identity:
            if identity in policy_conditions:
                score += 30
                details.append(f'身份符合政策条件: {identity}')
            else:
                details.append('身份可能不符合政策条件')
        
        # 检查用户需求与政策收益的匹配
        needs = self.get_needs()
        policy_benefits = ' '.join([benefit.get('benefit', '') for benefit in policy.benefits])
        
        matched_needs = []
        for need in needs:
            if need in policy_benefits:
                matched_needs.append(need)
                score += 20
        
        if matched_needs:
            details.append(f'需求匹配: {matched_needs}')
        else:
            details.append('未发现匹配的需求')
        
        # 检查用户标签与政策标签的匹配
        if self.tags:
            policy_tags = policy.tags
            matched_tags = [tag for tag in self.tags if tag in policy_tags]
            if matched_tags:
                score += len(matched_tags) * 5
                details.append(f'标签匹配: {matched_tags}')
        
        # 确保分数在0-100之间
        score = min(100, max(0, score))
        
        return score, details
    
    def get_user_profile_summary(self):
        """获取用户画像摘要
        
        Returns:
            用户画像摘要字符串
        """
        identity = self.get_identity()
        needs = ', '.join(self.get_needs()[:3])  # 只取前3个需求
        return f"{identity}，需求: {needs}"
