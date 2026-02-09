import json
import logging
from .chatbot import ChatBot

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - IntentRecognizer - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IntentRecognizer:
    def __init__(self, chatbot=None):
        """初始化意图识别器"""
        self.chatbot = chatbot if chatbot else ChatBot()
    
    def identify_intent(self, user_input):
        """识别用户意图和实体"""
        logger.info("开始识别意图和实体，调用大模型")
        # 使用普通字符串拼接，避免f-string格式化问题
        prompt = """
请分析用户输入，识别核心意图和实体，并判断用户是否需要以下服务：
1. 岗位推荐
2. 课程推荐
3. 政策推荐

用户输入: """
        prompt += user_input
        prompt += """

输出格式：
{
  "intent": "意图描述",
  "needs_job_recommendation": true/false,
  "needs_course_recommendation": true/false,
  "needs_policy_recommendation": true/false,
  "entities": [
    {"type": "实体类型", "value": "实体值"},
    ...
  ]
}

判断规则：
- 当用户明确提到"找工作"、"推荐岗位"、"就业"、"工作机会"、"推荐工作"等相关内容时，needs_job_recommendation 应设置为 true
- 当用户明确提到"课程"、"培训"、"学习"、"技能提升"等相关内容时，needs_course_recommendation 应设置为 true
- 当用户明确提到"政策"、"补贴"、"贷款"、"申请"、"返乡"、"创业"、"小微企业"等相关内容时，needs_policy_recommendation 应设置为 true

请仔细识别以下实体类型：
- age: 年龄
- gender: 性别
- employment_status: 就业状态（如退役军人、返乡农民工等）
- certificate: 证书/资格证
- concern: 关注点（如税收优惠、场地补贴等）
- business_type: 经营类型（如个体经营、小微企业等，注意：小加工厂属于小微企业）
- employment_impact: 就业影响（如带动X人就业、带动就业等）
- location: 场地信息（如入驻孵化基地等）
- investment: 投资信息（如租金、投资额等）
"""

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
        
        try:
            if isinstance(content, dict):
                result_json = content
            else:
                result_json = json.loads(content)
                
            return {
                "result": result_json,
                "time": llm_time
            }
        except Exception as e:
            logger.error(f"解析意图识别结果失败: {str(e)}")
            return {
                "result": {"intent": "政策咨询", "needs_job_recommendation": False, "entities": []},
                "time": llm_time
            }
