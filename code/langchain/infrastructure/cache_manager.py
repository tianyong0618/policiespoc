import time
import hashlib
import json
import logging
import re
from difflib import SequenceMatcher

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - CacheManager - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CacheManager:
    """缓存管理器（单例模式）"""
    _instance = None
    
    def __new__(cls, max_cache_size=1000):
        """创建单例实例"""
        if cls._instance is None:
            cls._instance = super(CacheManager, cls).__new__(cls)
            # 初始化单例
            cls._instance.cache = {}
            cls._instance.max_cache_size = max_cache_size
            cls._instance.default_ttl = 3600  # 默认缓存时间1小时
            cls._instance.llm_ttl = 7200  # LLM响应缓存时间2小时
            cls._instance.query_ttl = 3600  # 查询结果缓存时间1小时（延长）
            cls._instance.policy_ttl = 86400  # 政策数据缓存时间24小时
            cls._instance.job_ttl = 86400  # 岗位数据缓存时间24小时
            cls._instance.mapping_ttl = 86400  # 映射数据缓存时间24小时（延长）
            
            # 缓存统计
            cls._instance.hit_count = 0
            cls._instance.miss_count = 0
            cls._instance.similarity_hit_count = 0  # 相似度匹配命中次数
            
            # 存储查询文本和缓存键的映射，用于相似度查找
            cls._instance.query_cache_map = {}
            
            # 缓存预热
            cls._instance._prewarm_cache()
        return cls._instance
    
    def __init__(self, max_cache_size=1000):
        """初始化缓存管理器
        
        Args:
            max_cache_size: 最大缓存项数量
        """
        # 单例模式下，__init__可能会被调用多次，所以这里不需要重复初始化
        pass
    
    def set(self, key, value, ttl=None, query_text=None):
        """设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 缓存时间（秒），默认使用默认值
            query_text: 查询文本，用于相似度匹配
        """
        # 清理过期缓存
        self.cleanup_expired()
        
        # 检查缓存大小
        if len(self.cache) >= self.max_cache_size:
            self._evict_oldest()
        
        ttl = ttl or self.default_ttl
        expiry = time.time() + ttl
        self.cache[key] = {
            'value': value,
            'expiry': expiry,
            'created': time.time()
        }
        
        # 如果提供了查询文本，存储查询文本和缓存键的映射
        if query_text:
            self.query_cache_map[query_text] = {
                'key': key,
                'expiry': expiry
            }
        
        logger.debug(f"设置缓存: {key}, 过期时间: {expiry}")
    
    def get(self, key):
        """获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果缓存不存在或已过期则返回None
        """
        item = self.cache.get(key)
        if not item:
            logger.debug(f"缓存不存在: {key}")
            self.miss_count += 1
            return None
        
        # 检查缓存是否过期
        if time.time() > item['expiry']:
            del self.cache[key]
            logger.debug(f"缓存已过期: {key}")
            self.miss_count += 1
            return None
        
        logger.debug(f"获取缓存: {key}")
        self.hit_count += 1
        return item['value']
    
    def delete(self, key):
        """删除缓存
        
        Args:
            key: 缓存键
        """
        if key in self.cache:
            del self.cache[key]
            logger.debug(f"删除缓存: {key}")
    
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
        
        # 清理过期的查询映射
        expired_queries = [query for query, item in self.query_cache_map.items() if current_time > item['expiry']]
        for query in expired_queries:
            del self.query_cache_map[query]
        
        if expired_keys or expired_queries:
            logger.info(f"清理过期缓存: {len(expired_keys)}个缓存项, {len(expired_queries)}个查询映射")
    
    def _calculate_similarity(self, str1, str2):
        """计算两个字符串的相似度
        
        Args:
            str1: 第一个字符串
            str2: 第二个字符串
            
        Returns:
            相似度分数（0-1）
        """
        # 预处理字符串，移除标点符号和多余空格
        def preprocess(s):
            # 移除标点符号
            s = re.sub(r'[\s\p{P}\p{S}]+', ' ', s)
            # 转换为小写
            s = s.lower()
            # 移除多余空格
            s = ' '.join(s.split())
            return s
        
        str1_processed = preprocess(str1)
        str2_processed = preprocess(str2)
        
        # 计算相似度
        return SequenceMatcher(None, str1_processed, str2_processed).ratio()
    
    def find_similar_queries(self, query_text, threshold=0.7):
        """查找相似的查询
        
        Args:
            query_text: 查询文本
            threshold: 相似度阈值
            
        Returns:
            相似查询的列表，按相似度降序排列
        """
        similar_queries = []
        current_time = time.time()
        
        for cached_query, item in list(self.query_cache_map.items()):
            # 检查缓存是否过期
            if current_time > item['expiry']:
                del self.query_cache_map[cached_query]
                continue
            
            # 计算相似度
            similarity = self._calculate_similarity(query_text, cached_query)
            if similarity >= threshold:
                similar_queries.append((cached_query, similarity, item['key']))
        
        # 按相似度降序排序
        similar_queries.sort(key=lambda x: x[1], reverse=True)
        return similar_queries
    
    def get_by_query(self, query_text, threshold=0.7):
        """根据查询文本获取缓存，支持相似度匹配
        
        Args:
            query_text: 查询文本
            threshold: 相似度阈值
            
        Returns:
            缓存值，如果不存在或已过期则返回None
        """
        # 首先尝试精确匹配
        key = self.generate_cache_key('query', query_text)
        result = self.get(key)
        if result:
            return result
        
        # 尝试相似度匹配
        similar_queries = self.find_similar_queries(query_text, threshold)
        if similar_queries:
            # 使用最相似的查询
            most_similar = similar_queries[0]
            similar_key = most_similar[2]
            result = self.get(similar_key)
            if result:
                logger.info(f"使用相似度匹配的缓存，相似度: {most_similar[1]:.2f}")
                self.similarity_hit_count += 1
                return result
        
        self.miss_count += 1
        return None
    
    def set_query_cache(self, user_input, intent_info, response, ttl=None):
        """设置查询结果缓存
        
        Args:
            user_input: 用户输入
            intent_info: 意图信息
            response: 查询结果
            ttl: 缓存时间（秒），默认使用查询缓存时间
        """
        ttl = ttl or self.query_ttl
        key = self.generate_cache_key('query', user_input, intent_info)
        self.set(key, response, ttl, query_text=user_input)
    
    def get_query_cache(self, user_input, intent_info):
        """获取查询结果缓存
        
        Args:
            user_input: 用户输入
            intent_info: 意图信息
            
        Returns:
            缓存的查询结果，如果不存在则返回None
        """
        # 首先尝试基于用户输入的相似度匹配
        result = self.get_by_query(user_input)
        if result:
            return result
        
        # 如果相似度匹配失败，尝试精确匹配
        key = self.generate_cache_key('query', user_input, intent_info)
        return self.get(key)
    
    def _evict_oldest(self):
        """移除最旧的缓存项"""
        if not self.cache:
            return
        
        oldest_key = min(self.cache.items(), key=lambda x: x[1]['created'])[0]
        del self.cache[oldest_key]
        logger.debug(f"缓存达到上限，移除最旧缓存: {oldest_key}")
    
    def _prewarm_cache(self):
        """缓存预热，提前缓存常用数据"""
        logger.info("开始缓存预热...")
        
        # 预热常用查询缓存
        common_queries = [
            "我熟悉直播带货和网店运营，有场地补贴落地经验，想从事电商创业相关工作。",
            "我有中级电工证，想了解技能补贴政策",
            "我想找一份兼职工作",
            "我是一名失业人员，有什么政策可以申请"
        ]
        
        for query in common_queries:
            # 为常用查询生成缓存键，实际缓存会在首次查询时填充
            key = self.generate_cache_key('query_prewarm', query)
            # 设置一个空值，标记为预热
            self.set(key, {}, ttl=3600)
        
        logger.info("缓存预热完成")
    
    def generate_cache_key(self, prefix, *args, **kwargs):
        """生成缓存键
        
        Args:
            prefix: 缓存键前缀
            *args: 用于生成缓存键的参数
            **kwargs: 用于生成缓存键的关键字参数
        
        Returns:
            生成的缓存键
        """
        # 优化：对于简单参数，直接使用参数值作为键的一部分
        if len(args) == 1 and isinstance(args[0], str) and not kwargs:
            # 对于单个字符串参数，直接使用字符串的哈希
            key_str = args[0]
            key_hash = hashlib.md5(key_str.encode('utf-8')).hexdigest()
            return f"{prefix}:{key_hash}"
        
        # 对于复杂参数，使用原来的方法
        # 构建键的内容
        key_content = {
            'prefix': prefix,
            'args': args,
            'kwargs': kwargs
        }
        
        # 序列化并生成哈希
        key_str = json.dumps(key_content, ensure_ascii=False, sort_keys=True)
        key_hash = hashlib.md5(key_str.encode('utf-8')).hexdigest()
        
        # 返回带前缀的缓存键
        return f"{prefix}:{key_hash}"
    
    def set_llm_cache(self, prompt, response, ttl=None):
        """设置LLM响应缓存
        
        Args:
            prompt: LLM提示
            response: LLM响应
            ttl: 缓存时间（秒），默认使用LLM缓存时间
        """
        ttl = ttl or self.llm_ttl
        key = self.generate_cache_key('llm', prompt)
        self.set(key, response, ttl)
    
    def get_llm_cache(self, prompt):
        """获取LLM响应缓存
        
        Args:
            prompt: LLM提示
            
        Returns:
            缓存的LLM响应，如果不存在则返回None
        """
        key = self.generate_cache_key('llm', prompt)
        return self.get(key)
    
    def set_query_cache(self, user_input, intent_info, response, ttl=None):
        """设置查询结果缓存
        
        Args:
            user_input: 用户输入
            intent_info: 意图信息
            response: 查询结果
            ttl: 缓存时间（秒），默认使用查询缓存时间
        """
        ttl = ttl or self.query_ttl
        key = self.generate_cache_key('query', user_input, intent_info)
        self.set(key, response, ttl)
    
    def get_query_cache(self, user_input, intent_info):
        """获取查询结果缓存
        
        Args:
            user_input: 用户输入
            intent_info: 意图信息
            
        Returns:
            缓存的查询结果，如果不存在则返回None
        """
        key = self.generate_cache_key('query', user_input, intent_info)
        return self.get(key)
    
    def set_policy_cache(self, policy_id, policy_data, ttl=None):
        """设置政策数据缓存
        
        Args:
            policy_id: 政策ID
            policy_data: 政策数据
            ttl: 缓存时间（秒），默认使用政策缓存时间
        """
        ttl = ttl or self.policy_ttl
        key = self.generate_cache_key('policy', policy_id)
        self.set(key, policy_data, ttl)
    
    def get_policy_cache(self, policy_id):
        """获取政策数据缓存
        
        Args:
            policy_id: 政策ID
            
        Returns:
            缓存的政策数据，如果不存在则返回None
        """
        key = self.generate_cache_key('policy', policy_id)
        return self.get(key)
    
    def set_policies_cache(self, policies, ttl=None):
        """设置所有政策数据缓存
        
        Args:
            policies: 政策数据列表
            ttl: 缓存时间（秒），默认使用政策缓存时间
        """
        ttl = ttl or self.policy_ttl
        key = 'policies'
        self.set(key, policies, ttl)
        
        # 同时缓存每个政策
        for policy in policies:
            policy_id = policy.get('policy_id')
            if policy_id:
                self.set_policy_cache(policy_id, policy, ttl)
    
    def get_policies_cache(self):
        """获取所有政策数据缓存
        
        Returns:
            缓存的政策数据列表，如果不存在则返回None
        """
        key = 'policies'
        return self.get(key)
    
    def set_job_cache(self, job_id, job_data, ttl=None):
        """设置岗位数据缓存
        
        Args:
            job_id: 岗位ID
            job_data: 岗位数据
            ttl: 缓存时间（秒），默认使用岗位缓存时间
        """
        ttl = ttl or self.job_ttl
        key = self.generate_cache_key('job', job_id)
        self.set(key, job_data, ttl)
    
    def get_job_cache(self, job_id):
        """获取岗位数据缓存
        
        Args:
            job_id: 岗位ID
            
        Returns:
            缓存的岗位数据，如果不存在则返回None
        """
        key = self.generate_cache_key('job', job_id)
        return self.get(key)
    
    def set_jobs_cache(self, jobs, ttl=None):
        """设置所有岗位数据缓存
        
        Args:
            jobs: 岗位数据列表
            ttl: 缓存时间（秒），默认使用岗位缓存时间
        """
        ttl = ttl or self.job_ttl
        key = 'jobs'
        self.set(key, jobs, ttl)
        
        # 同时缓存每个岗位
        for job in jobs:
            job_id = job.get('job_id')
            if job_id:
                self.set_job_cache(job_id, job, ttl)
    
    def get_jobs_cache(self):
        """获取所有岗位数据缓存
        
        Returns:
            缓存的岗位数据列表，如果不存在则返回None
        """
        key = 'jobs'
        return self.get(key)
    
    def set_mapping_cache(self, mapping_type, mapping_data, ttl=None):
        """设置映射数据缓存
        
        Args:
            mapping_type: 映射类型
            mapping_data: 映射数据
            ttl: 缓存时间（秒），默认使用映射缓存时间
        """
        ttl = ttl or self.mapping_ttl
        key = self.generate_cache_key('mapping', mapping_type)
        self.set(key, mapping_data, ttl)
    
    def get_mapping_cache(self, mapping_type):
        """获取映射数据缓存
        
        Args:
            mapping_type: 映射类型
            
        Returns:
            缓存的映射数据，如果不存在则返回None
        """
        key = self.generate_cache_key('mapping', mapping_type)
        return self.get(key)
    
    def get_cache_stats(self):
        """获取缓存统计信息
        
        Returns:
            缓存统计信息字典
        """
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        similarity_hit_rate = (self.similarity_hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'similarity_hit_count': self.similarity_hit_count,
            'total_requests': total_requests,
            'hit_rate': hit_rate,
            'similarity_hit_rate': similarity_hit_rate,
            'cache_size': len(self.cache),
            'query_map_size': len(self.query_cache_map),
            'max_cache_size': self.max_cache_size
        }
    
    def reset_cache_stats(self):
        """重置缓存统计信息"""
        self.hit_count = 0
        self.miss_count = 0
        self.similarity_hit_count = 0
        logger.info("缓存统计信息已重置")
