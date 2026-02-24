class Policy:
    """政策模型"""
    def __init__(self, policy_data):
        """初始化政策模型
        
        Args:
            policy_data: 政策数据字典
        """
        self.policy_id = policy_data.get('policy_id')
        self.title = policy_data.get('title')
        self.category = policy_data.get('category')
        self.conditions = policy_data.get('conditions', [])
        self.benefits = policy_data.get('benefits', [])
        self.description = policy_data.get('description', '')
        self.application_process = policy_data.get('application_process', [])
        self.validity_period = policy_data.get('validity_period', '')
        self.source = policy_data.get('source', '')
        self.tags = policy_data.get('tags', [])
    
    def to_dict(self):
        """转换为字典
        
        Returns:
            政策数据字典
        """
        return {
            'policy_id': self.policy_id,
            'title': self.title,
            'category': self.category,
            'conditions': self.conditions,
            'benefits': self.benefits,
            'description': self.description,
            'application_process': self.application_process,
            'validity_period': self.validity_period,
            'source': self.source,
            'tags': self.tags
        }
    
    def check_eligibility(self, user_conditions):
        """检查用户是否符合政策条件
        
        Args:
            user_conditions: 用户条件字典
            
        Returns:
            符合条件的条件列表和不符合条件的条件列表
        """
        met_conditions = []
        unmet_conditions = []
        
        for condition in self.conditions:
            condition_text = condition.get('condition', '')
            # 简单的条件检查逻辑，实际应用中可能需要更复杂的规则引擎
            # 这里只是一个示例，根据实际情况扩展
            condition_met = True
            
            # 检查条件是否包含特定关键词
            if '退役军人' in condition_text and not user_conditions.get('is_veteran', False):
                condition_met = False
            elif '返乡农民工' in condition_text and not user_conditions.get('is_migrant_worker', False):
                condition_met = False
            elif '失业' in condition_text and not user_conditions.get('is_unemployed', False):
                condition_met = False
            elif '创业' in condition_text and not user_conditions.get('is_entrepreneur', False):
                condition_met = False
            
            if condition_met:
                met_conditions.append(condition)
            else:
                unmet_conditions.append(condition)
        
        return met_conditions, unmet_conditions
    
    def get_benefits_summary(self):
        """获取政策收益摘要
        
        Returns:
            收益摘要列表
        """
        return [benefit.get('benefit', '') for benefit in self.benefits]
