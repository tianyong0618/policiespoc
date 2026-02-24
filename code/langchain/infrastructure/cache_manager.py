import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - CacheManager - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CacheManager:
    """缓存管理器"""
    def __init__(self):
        """初始化缓存管理器"""
        self.cache = {}
        self.default_ttl = 3600  # 默认缓存时间1小时
    
    def set(self, key, value, ttl=None):
        """设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 缓存时间（秒），默认使用默认值
        """
        ttl = ttl or self.default_ttl
        expiry = time.time() + ttl
        self.cache[key] = {
            'value': value,
            'expiry': expiry
        }
        logger.info(f"设置缓存: {key}, 过期时间: {expiry}")
    
    def get(self, key):
        """获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果缓存不存在或已过期则返回None
        """
        item = self.cache.get(key)
        if not item:
            logger.info(f"缓存不存在: {key}")
            return None
        
        # 检查缓存是否过期
        if time.time() > item['expiry']:
            del self.cache[key]
            logger.info(f"缓存已过期: {key}")
            return None
        
        logger.info(f"获取缓存: {key}")
        return item['value']
    
    def delete(self, key):
        """删除缓存
        
        Args:
            key: 缓存键
        """
        if key in self.cache:
            del self.cache[key]
            logger.info(f"删除缓存: {key}")
    
    def clear(self):
        """清空所有缓存"""
        self.cache.clear()
        logger.info("清空所有缓存")
    
    def get_cache_size(self):
        """获取缓存大小
        
        Returns:
            缓存项数量
        """
        return len(self.cache)
    
    def cleanup_expired(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = [key for key, item in self.cache.items() if current_time > item['expiry']]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"清理过期缓存: {len(expired_keys)}个项")
