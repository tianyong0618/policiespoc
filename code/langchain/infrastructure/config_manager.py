import os
import json
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - ConfigManager - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConfigManager:
    """配置管理器"""
    def __init__(self, config_file=None):
        """初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file or os.path.join(os.path.dirname(__file__), '..', 'config.json')
        self.config = self._load_config()
    
    def _load_config(self):
        """加载配置文件
        
        Returns:
            配置字典
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"加载配置文件: {self.config_file}")
                return config
            else:
                logger.warning(f"配置文件不存在: {self.config_file}，使用默认配置")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}，使用默认配置")
            return self._get_default_config()
    
    def _get_default_config(self):
        """获取默认配置
        
        Returns:
            默认配置字典
        """
        return {
            'api': {
                'timeout': 30,
                'retry_count': 3
            },
            'model': {
                'temperature': 0.7,
                'max_tokens': 2000,
                'top_p': 0.9
            },
            'cache': {
                'default_ttl': 3600,
                'max_size': 1000
            },
            'data': {
                'policy_file': os.path.join(os.path.dirname(__file__), '..', 'data', 'data_files', 'policies.json'),
                'job_file': os.path.join(os.path.dirname(__file__), '..', 'data', 'data_files', 'jobs.json'),
                'user_file': os.path.join(os.path.dirname(__file__), '..', 'data', 'data_files', 'user_profiles.json')
            },
            'log': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        }
    
    def get(self, key, default=None):
        """获取配置项
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                logger.info(f"配置项不存在: {key}，使用默认值: {default}")
                return default
        
        logger.info(f"获取配置项: {key} = {value}")
        return value
    
    def set(self, key, value):
        """设置配置项
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
        """
        keys = key.split('.')
        config = self.config
        
        # 遍历到最后一个键的父级
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
        logger.info(f"设置配置项: {key} = {value}")
    
    def save(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info(f"保存配置文件: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False
    
    def reload(self):
        """重新加载配置文件"""
        self.config = self._load_config()
        logger.info("重新加载配置文件")
    
    def get_all_config(self):
        """获取所有配置
        
        Returns:
            配置字典
        """
        return self.config
