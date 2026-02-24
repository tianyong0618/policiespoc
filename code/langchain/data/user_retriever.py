import json
import os
import logging
from ..infrastructure.cache_manager import CacheManager
from ..infrastructure.config_manager import ConfigManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - UserRetriever - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UserRetriever:
    """用户数据访问"""
    def __init__(self, cache_manager=None, config_manager=None):
        """初始化用户数据访问
        
        Args:
            cache_manager: 缓存管理器实例
            config_manager: 配置管理器实例
        """
        self.cache_manager = cache_manager or CacheManager()
        self.config_manager = config_manager or ConfigManager()
        self.user_profiles = self._load_user_profiles()
    
    def _load_user_profiles(self):
        """加载用户画像数据
        
        Returns:
            用户画像数据列表
        """
        user_file = self.config_manager.get('data.user_file')
        try:
            if os.path.exists(user_file):
                with open(user_file, 'r', encoding='utf-8') as f:
                    user_profiles = json.load(f)
                logger.info(f"加载用户画像数据成功，共 {len(user_profiles)} 个用户画像")
                # 缓存用户画像数据
                self.cache_manager.set('user_profiles', user_profiles)
                return user_profiles
            else:
                logger.warning(f"用户画像数据文件不存在: {user_file}")
                return []
        except Exception as e:
            logger.error(f"加载用户画像数据失败: {e}")
            return []
    
    def get_all_user_profiles(self):
        """获取所有用户画像
        
        Returns:
            用户画像数据列表
        """
        # 尝试从缓存获取
        cached_profiles = self.cache_manager.get('user_profiles')
        if cached_profiles:
            return cached_profiles
        
        # 缓存不存在，重新加载
        return self._load_user_profiles()
    
    def get_user_profile_by_id(self, user_id):
        """根据ID获取用户画像
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户画像数据字典，如果不存在则返回None
        """
        # 尝试从缓存获取
        cache_key = f'user_{user_id}'
        cached_profile = self.cache_manager.get(cache_key)
        if cached_profile:
            return cached_profile
        
        # 缓存不存在，从所有用户画像中查找
        user_profiles = self.get_all_user_profiles()
        for profile in user_profiles:
            if profile.get('user_id') == user_id:
                # 缓存找到的用户画像
                self.cache_manager.set(cache_key, profile)
                return profile
        
        logger.info(f"用户画像不存在: {user_id}")
        return None
    
    def search_user_profiles(self, keywords=None, filters=None):
        """搜索用户画像
        
        Args:
            keywords: 搜索关键词
            filters: 过滤条件
            
        Returns:
            匹配的用户画像列表
        """
        user_profiles = self.get_all_user_profiles()
        matching_profiles = []
        
        for profile in user_profiles:
            # 关键词匹配
            if keywords:
                profile_text = f"{profile.get('description', '')} {profile.get('basic_info', {}).get('identity', '')}".lower()
                if not any(keyword.lower() in profile_text for keyword in keywords):
                    continue
            
            # 过滤条件匹配
            if filters:
                match = True
                for key, value in filters.items():
                    # 支持嵌套字段匹配
                    if '.' in key:
                        parts = key.split('.')
                        current = profile
                        for part in parts:
                            if isinstance(current, dict) and part in current:
                                current = current[part]
                            else:
                                match = False
                                break
                        if current != value:
                            match = False
                    else:
                        if profile.get(key) != value:
                            match = False
                            break
                if not match:
                    continue
            
            matching_profiles.append(profile)
        
        logger.info(f"搜索用户画像完成，找到 {len(matching_profiles)} 个匹配用户画像")
        return matching_profiles
    
    def match_user_profile(self, user_input):
        """根据用户输入匹配用户画像
        
        Args:
            user_input: 用户输入文本
            
        Returns:
            匹配度最高的用户画像，如果没有匹配则返回None
        """
        user_profiles = self.get_all_user_profiles()
        if not user_profiles:
            return None
        
        best_match = None
        best_score = 0
        
        user_input_lower = user_input.lower()
        
        for profile in user_profiles:
            score = 0
            
            # 检查用户描述
            description = profile.get('description', '').lower()
            if description:
                # 计算关键词匹配度
                words = description.split()
                matched_words = [word for word in words if word in user_input_lower]
                score += len(matched_words) * 2
            
            # 检查用户身份
            identity = profile.get('basic_info', {}).get('identity', '').lower()
            if identity and identity in user_input_lower:
                score += 5
            
            # 检查核心需求
            core_needs = profile.get('core_needs', [])
            for need in core_needs:
                if need.lower() in user_input_lower:
                    score += 3
            
            # 更新最佳匹配
            if score > best_score:
                best_score = score
                best_match = profile
        
        if best_match and best_score > 0:
            logger.info(f"匹配到用户画像: {best_match.get('user_id')}, 匹配度: {best_score}")
            return best_match
        else:
            logger.info("未匹配到用户画像")
            return None
    
    def refresh_user_profiles(self):
        """刷新用户画像数据
        
        Returns:
            刷新后的用户画像数据列表
        """
        self.user_profiles = self._load_user_profiles()
        logger.info("刷新用户画像数据完成")
        return self.user_profiles
