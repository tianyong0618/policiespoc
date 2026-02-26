import time
import json
import logging
import sys
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - TestCache - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.append('/Users/tianyong/Documents/works/workspace/hp/公司文档/AI调研/政策咨询POC/code')

# 直接导入缓存管理器进行测试
from langchain.infrastructure.cache_manager import CacheManager

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
