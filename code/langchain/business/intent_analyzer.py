import json
import logging
import re
from ..infrastructure.chatbot import ChatBot

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - IntentRecognizer - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IntentAnalyzer:
    def __init__(self, chatbot=None):
        """初始化意图识别器"""
        self.chatbot = chatbot if chatbot else ChatBot()
        # 初始化规则引擎
        self._init_rules()
    
    def _init_rules(self):
        """初始化规则引擎"""
        # 意图识别规则
        self.intent_rules = {
            'job_recommendation': [
                '找工作', '推荐岗位', '就业', '工作机会', '推荐工作', '求职',
                '职业推荐', '工作推荐', '岗位匹配', '推荐职位', '想找一份', '想从事'
            ],
            'course_recommendation': [
                '课程', '培训', '学习', '技能提升', '转行'
            ],
            'policy_recommendation': [
                '政策', '补贴', '贷款', '申请', '返乡', '创业', '小微企业',
                '失业', '证书', '资格证'
            ]
        }
        
        # 实体识别规则
        self.entity_rules = {
            'age': r'\d+岁',
            'gender': r'(男|女|男性|女性)',
            'education_level': r'(初中|高中|中专|大专|本科|研究生|博士)\s*(毕业|学历)?',
            'employment_status': [
                '退役军人', '返乡农民工', '失业', '在职', '创业'
            ],
            'certificate': [
                '电工证', '中级电工证', '高级电工证', '技能证书', '资格证'
            ],
            'concern': [
                '税收优惠', '场地补贴', '固定时间', '灵活时间', '技能补贴', '补贴申领'
            ],
            'business_type': [
                '个体经营', '小微企业', '小加工厂'
            ],
            'employment_impact': [
                '带动就业', '带动\d+人就业'
            ],
            'location': [
                '入驻孵化基地', '孵化基地'
            ]
        }
    
    def _rule_based_intent_recognition(self, user_input):
        """基于规则的意图识别"""
        needs_job = any(keyword in user_input for keyword in self.intent_rules['job_recommendation'])
        needs_course = any(keyword in user_input for keyword in self.intent_rules['course_recommendation'])
        needs_policy = any(keyword in user_input for keyword in self.intent_rules['policy_recommendation'])
        
        # 识别实体
        entities = []
        
        # 识别年龄
        age_match = re.search(self.entity_rules['age'], user_input)
        if age_match:
            entities.append({'type': 'age', 'value': age_match.group(0)})
        
        # 识别性别
        gender_match = re.search(self.entity_rules['gender'], user_input)
        if gender_match:
            entities.append({'type': 'gender', 'value': gender_match.group(0)})
        
        # 识别教育水平
        edu_match = re.search(self.entity_rules['education_level'], user_input)
        if edu_match:
            entities.append({'type': 'education_level', 'value': edu_match.group(0)})
        
        # 识别就业状态
        for status in self.entity_rules['employment_status']:
            if status in user_input:
                entities.append({'type': 'employment_status', 'value': status})
        
        # 识别证书
        for cert in self.entity_rules['certificate']:
            if cert in user_input:
                entities.append({'type': 'certificate', 'value': cert})
        
        # 识别关注点
        for concern in self.entity_rules['concern']:
            if concern in user_input:
                entities.append({'type': 'concern', 'value': concern})
        
        # 识别经营类型
        for business in self.entity_rules['business_type']:
            if business in user_input:
                entities.append({'type': 'business_type', 'value': business})
        
        # 识别就业影响
        for impact in self.entity_rules['employment_impact']:
            if re.search(impact, user_input):
                entities.append({'type': 'employment_impact', 'value': '带动就业'})
        
        # 识别场地信息
        for location in self.entity_rules['location']:
            if location in user_input:
                entities.append({'type': 'location', 'value': location})
        
        # 生成意图描述
        intent_parts = []
        if needs_job:
            intent_parts.append('推荐工作')
        if needs_course:
            intent_parts.append('推荐课程')
        if needs_policy:
            intent_parts.append('咨询政策')
        
        intent = ' '.join(intent_parts) if intent_parts else '通用查询'
        
        return {
            "intent": intent,
            "needs_job_recommendation": needs_job,
            "needs_course_recommendation": needs_course,
            "needs_policy_recommendation": needs_policy,
            "entities": entities
        }
    
    def ir_identify_intent(self, user_input):
        """识别用户意图和实体"""
        try:
            # 首先尝试使用基于规则的意图识别
            logger.info("使用基于规则的意图识别")
            result = self._rule_based_intent_recognition(user_input)
            
            # 检查是否需要使用LLM进行更复杂的意图识别
            # 如果规则识别结果不明确或实体信息不足，使用LLM
            if not result['needs_job_recommendation'] and not result['needs_course_recommendation'] and not result['needs_policy_recommendation']:
                logger.info("规则识别结果不明确，使用LLM进行意图识别")
                # 生成意图识别提示
                prompt = f"""
分析用户输入，识别核心意图和实体，并判断需要的服务类型。

用户输入: {user_input}

输出JSON格式：
{{
  "intent": "意图描述",
  "needs_job_recommendation": true/false,
  "needs_course_recommendation": true/false,
  "needs_policy_recommendation": true/false,
  "entities": [
    {{"type": "实体类型", "value": "实体值"}},
    ...
  ]
}}

识别规则：
- 岗位推荐：提到"找工作"、"推荐岗位"、"就业"、"工作机会"等
- 课程推荐：提到"课程"、"培训"、"学习"、"技能提升"等
- 政策推荐：提到"政策"、"补贴"、"贷款"、"申请"、"返乡"、"创业"等

实体类型：age(年龄)、gender(性别)、education_level(教育水平)、employment_status(就业状态)、certificate(证书)、concern(关注点)、business_type(经营类型)、employment_impact(就业影响)、location(场地信息)、investment(投资信息)
"""

                # 检查缓存
                from ..infrastructure.cache_manager import CacheManager
                cache_manager = CacheManager()
                cached_response = cache_manager.get_llm_cache(prompt)
                
                if cached_response:
                    logger.info("使用缓存的LLM响应")
                    # 处理缓存的响应
                    content = cached_response
                    llm_time = 0
                else:
                    logger.info("开始识别意图和实体，调用大模型")
                    logger.info(f"生成的意图识别提示: {prompt[:100]}...")
                    response = self.chatbot.chat_with_memory(prompt)
                    
                    # 处理返回的新格式
                    content = ""
                    llm_time = 0
                    
                    try:
                        if isinstance(response, dict) and 'content' in response:
                            content = response['content']
                            llm_time = response.get('time', 0)
                            logger.info(f"大模型返回的意图识别结果: {content[:100]}...")
                            logger.info(f"意图识别LLM调用耗时: {llm_time:.2f}秒")
                        else:
                            # 处理字符串响应
                            content = response if isinstance(response, str) else str(response)
                            llm_time = 0
                            if isinstance(content, str):
                                logger.info(f"大模型返回的意图识别结果: {content[:100]}...")
                            else:
                                logger.info(f"大模型返回的意图识别结果: {str(content)[:100]}...")
                    except Exception as e:
                        logger.error(f"处理LLM响应失败: {e}")
                        content = ""
                        llm_time = 0
                    
                    # 缓存LLM响应
                    cache_manager.set_llm_cache(prompt, content)
                
                try:
                    if isinstance(content, dict):
                        result_json = content
                    else:
                        # 移除Markdown代码块标记
                        if isinstance(content, str):
                            # 移除开头的```json和结尾的```
                            content = content.strip()
                            if content.startswith('```json'):
                                content = content[7:]
                            if content.endswith('```'):
                                content = content[:-3]
                            content = content.strip()
                        result_json = json.loads(content)
                        result = result_json
                except Exception as e:
                    logger.error(f"解析意图识别结果失败: {str(e)}")
            
            return {
                "result": result,
                "time": 0  # 规则引擎耗时忽略
            }
        except Exception as e:
            logger.error(f"意图识别失败: {str(e)}")
            # 返回默认意图
            return {
                "result": {"intent": "通用查询", "needs_job_recommendation": False, "needs_course_recommendation": False, "needs_policy_recommendation": False, "entities": []},
                "time": 0
            }
