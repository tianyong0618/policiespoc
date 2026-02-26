import json
import os
import logging
from ..infrastructure.cache_manager import CacheManager
from ..infrastructure.config_manager import ConfigManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - JobRetriever - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class JobRetriever:
    """岗位数据访问"""
    def __init__(self, cache_manager=None, config_manager=None):
        """初始化岗位数据访问
        
        Args:
            cache_manager: 缓存管理器实例
            config_manager: 配置管理器实例
        """
        self.cache_manager = cache_manager or CacheManager()
        self.config_manager = config_manager or ConfigManager()
        self.jobs = self._load_jobs()
    
    def _load_jobs(self):
        """加载岗位数据
        
        Returns:
            岗位数据列表
        """
        job_file = self.config_manager.get('data.job_file')
        try:
            if os.path.exists(job_file):
                with open(job_file, 'r', encoding='utf-8') as f:
                    jobs = json.load(f)
                logger.info(f"加载岗位数据成功，共 {len(jobs)} 个岗位")
                # 缓存岗位数据
                self.cache_manager.set_jobs_cache(jobs)
                return jobs
            else:
                logger.warning(f"岗位数据文件不存在: {job_file}")
                return []
        except Exception as e:
            logger.error(f"加载岗位数据失败: {e}")
            return []
    
    def get_all_jobs(self):
        """获取所有岗位
        
        Returns:
            岗位数据列表
        """
        # 尝试从缓存获取
        cached_jobs = self.cache_manager.get_jobs_cache()
        if cached_jobs:
            logger.info("使用缓存的岗位数据")
            return cached_jobs
        
        # 缓存不存在，重新加载
        return self._load_jobs()
    
    def get_job_by_id(self, job_id):
        """根据ID获取岗位
        
        Args:
            job_id: 岗位ID
            
        Returns:
            岗位数据字典，如果不存在则返回None
        """
        # 尝试从缓存获取
        cached_job = self.cache_manager.get_job_cache(job_id)
        if cached_job:
            logger.info(f"使用缓存的岗位数据: {job_id}")
            return cached_job
        
        # 缓存不存在，从所有岗位中查找
        jobs = self.get_all_jobs()
        for job in jobs:
            if job.get('job_id') == job_id:
                # 缓存找到的岗位
                self.cache_manager.set_job_cache(job_id, job)
                return job
        
        logger.info(f"岗位不存在: {job_id}")
        return None
    
    def search_jobs(self, keywords=None, filters=None):
        """搜索岗位
        
        Args:
            keywords: 搜索关键词
            filters: 过滤条件
            
        Returns:
            匹配的岗位列表
        """
        jobs = self.get_all_jobs()
        matching_jobs = []
        
        for job in jobs:
            # 关键词匹配
            if keywords:
                job_text = f"{job.get('title', '')} {job.get('description', '')} {job.get('requirements', '')}".lower()
                if not any(keyword.lower() in job_text for keyword in keywords):
                    continue
            
            # 过滤条件匹配
            if filters:
                match = True
                for key, value in filters.items():
                    if job.get(key) != value:
                        match = False
                        break
                if not match:
                    continue
            
            matching_jobs.append(job)
        
        logger.info(f"搜索岗位完成，找到 {len(matching_jobs)} 个匹配岗位")
        return matching_jobs
    
    def get_jobs_by_policy(self, policy_id):
        """根据政策ID获取相关岗位
        
        Args:
            policy_id: 政策ID
            
        Returns:
            相关岗位列表
        """
        jobs = self.get_all_jobs()
        relevant_jobs = []
        
        for job in jobs:
            policy_relations = job.get('policy_relations', [])
            if policy_id in policy_relations:
                relevant_jobs.append(job)
        
        logger.info(f"根据政策 {policy_id} 找到 {len(relevant_jobs)} 个相关岗位")
        return relevant_jobs
    
    def refresh_jobs(self):
        """刷新岗位数据
        
        Returns:
            刷新后的岗位数据列表
        """
        self.jobs = self._load_jobs()
        logger.info("刷新岗位数据完成")
        return self.jobs
