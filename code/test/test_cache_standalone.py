import time
import hashlib
import json
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - TestCache - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CacheManager:
    """缓存管理器"""
    def __init__(self, max_cache_size=1000):
        """初始化缓存管理器
        
        Args:
            max_cache_size: 最大缓存项数量
        """
        self.cache = {}
        self.max_cache_size = max_cache_size
        self.default_ttl = 3600  # 默认缓存时间1小时
        self.llm_ttl = 7200  # LLM响应缓存时间2小时
        self.query_ttl = 1800  # 查询结果缓存时间30分钟
        self.policy_ttl = 86400  # 政策数据缓存时间24小时
        self.job_ttl = 86400  # 岗位数据缓存时间24小时
        self.mapping_ttl = 43200  # 映射数据缓存时间12小时
    
    def set(self, key, value, ttl=None):
        """设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 缓存时间（秒），默认使用默认值
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
            return None
        
        # 检查缓存是否过期
        if time.time() > item['expiry']:
            del self.cache[key]
            logger.debug(f"缓存已过期: {key}")
            return None
        
        logger.debug(f"获取缓存: {key}")
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
        
        if expired_keys:
            logger.info(f"清理过期缓存: {len(expired_keys)}个项")
    
    def _evict_oldest(self):
        """移除最旧的缓存项"""
        if not self.cache:
            return
        
        oldest_key = min(self.cache.items(), key=lambda x: x[1]['created'])[0]
        del self.cache[oldest_key]
        logger.debug(f"缓存达到上限，移除最旧缓存: {oldest_key}")
    
    def generate_cache_key(self, prefix, *args, **kwargs):
        """生成缓存键
        
        Args:
            prefix: 缓存键前缀
            *args: 用于生成缓存键的参数
            **kwargs: 用于生成缓存键的关键字参数
        
        Returns:
            生成的缓存键
        """
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

class TestCacheMechanism:
    def __init__(self):
        """初始化测试类"""
        self.cache_manager = CacheManager()
    
    def test_cache_basic(self):
        """测试基本缓存功能"""
        logger.info("开始测试基本缓存功能...")
        
        # 设置缓存
        test_key = "test_key"
        test_value = "test_value"
        self.cache_manager.set(test_key, test_value)
        
        # 获取缓存
        cached_value = self.cache_manager.get(test_key)
        assert cached_value == test_value, "缓存设置或获取失败"
        logger.info("基本缓存功能测试通过！")
        
        return True
    
    def test_cache_expiry(self):
        """测试缓存过期机制"""
        logger.info("开始测试缓存过期机制...")
        
        # 设置一个短期缓存
        test_key = "test_expiry_key"
        test_value = "test_expiry_value"
        self.cache_manager.set(test_key, test_value, ttl=1)  # 1秒过期
        
        # 立即获取缓存（应该存在）
        value1 = self.cache_manager.get(test_key)
        assert value1 == test_value, "缓存设置失败"
        logger.info("缓存设置成功！")
        
        # 等待缓存过期
        time.sleep(2)
        
        # 再次获取缓存（应该不存在）
        value2 = self.cache_manager.get(test_key)
        assert value2 is None, "缓存过期机制失败"
        logger.info("缓存过期机制测试通过！")
        
        return True
    
    def test_cache_size(self):
        """测试缓存大小限制"""
        logger.info("开始测试缓存大小限制...")
        
        # 创建一个小容量的缓存管理器
        small_cache = CacheManager(max_cache_size=3)
        
        # 添加多个缓存项
        for i in range(5):
            small_cache.set(f"key_{i}", f"value_{i}")
        
        # 检查缓存大小
        cache_size = small_cache.get_cache_size()
        assert cache_size <= 3, "缓存大小限制失败"
        logger.info(f"缓存大小限制测试通过！当前缓存大小: {cache_size}")
        
        return True
    
    def test_llm_cache(self):
        """测试LLM响应缓存"""
        logger.info("开始测试LLM响应缓存...")
        
        # 模拟LLM提示和响应
        test_prompt = "What is the capital of France?"
        test_response = "The capital of France is Paris."
        
        # 设置LLM缓存
        self.cache_manager.set_llm_cache(test_prompt, test_response)
        
        # 获取LLM缓存
        cached_response = self.cache_manager.get_llm_cache(test_prompt)
        assert cached_response == test_response, "LLM缓存设置或获取失败"
        logger.info("LLM响应缓存测试通过！")
        
        return True
    
    def test_policy_cache(self):
        """测试政策数据缓存"""
        logger.info("开始测试政策数据缓存...")
        
        # 模拟政策数据
        test_policy = {
            "policy_id": "POLICY_A01",
            "title": "创业担保贷款贴息政策",
            "category": "创业扶持",
            "key_info": "最高贷50万、期限3年，LPR-150BP以上部分财政贴息"
        }
        
        # 设置政策缓存
        self.cache_manager.set_policy_cache(test_policy["policy_id"], test_policy)
        
        # 获取政策缓存
        cached_policy = self.cache_manager.get_policy_cache(test_policy["policy_id"])
        assert cached_policy == test_policy, "政策缓存设置或获取失败"
        logger.info("政策数据缓存测试通过！")
        
        return True
    
    def test_jobs_cache(self):
        """测试岗位数据缓存"""
        logger.info("开始测试岗位数据缓存...")
        
        # 模拟岗位数据
        test_jobs = [
            {
                "job_id": "JOB_A01",
                "title": "创业孵化基地管理员",
                "requirements": ["有创业经验", "熟悉政策法规"],
                "features": "稳定工作环境"
            },
            {
                "job_id": "JOB_A02",
                "title": "兼职电工",
                "requirements": ["持有电工证", "有相关工作经验"],
                "features": "灵活工作时间"
            }
        ]
        
        # 设置岗位数据缓存
        self.cache_manager.set_jobs_cache(test_jobs)
        
        # 获取岗位数据缓存
        cached_jobs = self.cache_manager.get_jobs_cache()
        assert cached_jobs == test_jobs, "岗位数据缓存设置或获取失败"
        logger.info("岗位数据缓存测试通过！")
        
        return True
    
    def test_mapping_cache(self):
        """测试映射数据缓存"""
        logger.info("开始测试映射数据缓存...")
        
        # 模拟映射数据
        test_mapping = {
            "JOB_A01": "创业孵化基地管理员",
            "JOB_A02": "兼职电工"
        }
        
        # 设置映射缓存
        self.cache_manager.set_mapping_cache('job_name', test_mapping)
        
        # 获取映射缓存
        cached_mapping = self.cache_manager.get_mapping_cache('job_name')
        assert cached_mapping == test_mapping, "映射数据缓存设置或获取失败"
        logger.info("映射数据缓存测试通过！")
        
        return True
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("开始运行所有缓存机制测试...")
        
        # 运行各项测试
        self.test_cache_basic()
        self.test_cache_expiry()
        self.test_cache_size()
        self.test_llm_cache()
        self.test_policy_cache()
        self.test_jobs_cache()
        self.test_mapping_cache()
        
        logger.info("所有缓存机制测试通过！")

if __name__ == "__main__":
    # 运行测试
    tester = TestCacheMechanism()
    tester.run_all_tests()
