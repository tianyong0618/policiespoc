from langchain_openai import ChatOpenAI
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
import time
import logging
import json
from functools import lru_cache

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - ChatBot - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入环境变量库
from dotenv import load_dotenv
import os

# 导入缓存管理器
from .cache_manager import CacheManager

# 加载环境变量
load_dotenv()

# 模拟模式配置
USE_MOCK = False  # 设置为True使用模拟数据，False使用真实LLM

# 加载模拟响应数据
mock_responses = {}
try:
    mock_file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'data_files', 'mock_responses.json')
    with open(mock_file_path, 'r', encoding='utf-8') as f:
        mock_data = json.load(f)
        mock_responses = mock_data.get('mock_responses', {})
    logger.info(f"加载模拟响应数据成功，共 {len(mock_responses)} 条")
except Exception as e:
    logger.error(f"加载模拟响应数据失败: {e}")

# 初始化模型和记忆
# 使用OpenAI兼容API配置Doubao-Seed-1.6模型
# 优化模型参数，减少响应时间
llm = ChatOpenAI(
    temperature=0.5,  # 降低温度，减少模型思考时间
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    # 火山引擎Doubao API端点
    openai_api_base=os.getenv("OPENAI_API_BASE", "https://ark.cn-beijing.volces.com/api/v3"),
    model=os.getenv("LLM_MODEL", "deepseek-v3-2-251201"),  # DeepSeek V3模型ID
    timeout=int(os.getenv("LLM_TIMEOUT", "1800")),  # 深度思考模型耗费时间会较长，推荐30分钟以上
    max_tokens=int(os.getenv("LLM_MAX_TOKENS", "8192"))
)

class ChatBot:
    def __init__(self):
        self.memory = InMemoryChatMessageHistory()
        self.cache_manager = CacheManager()
    
    def chat_with_memory(self, user_input):
        start_time = time.time()
        logger.info(f"开始生成回复: {user_input[:50]}...")
        
        try:
            # 对于长输入，进行截断处理
            if len(user_input) > 2000:
                user_input = user_input[:2000] + "..."
                logger.info("输入过长，已截断")
            
            # 检查缓存中是否有对应的响应
            cached_response = self.cache_manager.get_llm_cache(user_input)
            if cached_response:
                logger.info("使用缓存的LLM响应")
                # 添加用户消息到记忆
                self.memory.add_user_message(user_input)
                # 添加AI回复到记忆
                self.memory.add_ai_message(cached_response["content"])
                
                total_time = time.time() - start_time
                logger.info(f"回复生成完成（使用缓存），总耗时: {total_time:.2f}秒")
                
                return {
                    "content": cached_response["content"],
                    "time": 0,
                    "from_cache": True
                }
            
            # 检查是否使用模拟模式
            if USE_MOCK:
                logger.info("使用模拟数据生成响应")
                
                # 根据输入类型返回不同格式的模拟数据
                if "请分析用户输入，识别核心意图和实体" in user_input:
                    # 意图分析器的模拟响应
                    mock_content = self._get_intent_analyzer_mock_response(user_input)
                else:
                    # 响应生成器的模拟响应
                    mock_content = self._get_response_generator_mock_response(user_input)
                
                # 添加用户消息到记忆
                self.memory.add_user_message(user_input)
                # 添加AI回复到记忆
                self.memory.add_ai_message(mock_content)
                
                # 缓存模拟响应
                self.cache_manager.set_llm_cache(user_input, {
                    "content": mock_content,
                    "time": 0
                })
                
                total_time = time.time() - start_time
                logger.info(f"模拟响应生成完成，总耗时: {total_time:.2f}秒")
                
                return {
                    "content": mock_content,
                    "time": 0,
                    "from_mock": True
                }
            
            # 添加用户消息到记忆
            self.memory.add_user_message(user_input)
            
            # 限制历史消息数量，避免上下文过长
            if len(self.memory.messages) > 10:
                self.memory.messages = self.memory.messages[-10:]
                logger.info("历史消息过多，已裁剪")
            
            # 生成AI回复
            llm_start = time.time()
            # 优化：只发送最新的消息，减少上下文长度
            simple_message = HumanMessage(content=self.memory.messages[-1].content)
            response = llm.invoke([simple_message])
            llm_time = time.time() - llm_start
            logger.info(f"LLM调用完成，耗时: {llm_time:.2f}秒")
            
            # 添加AI回复到记忆
            self.memory.add_ai_message(response.content)
            
            # 缓存LLM响应
            self.cache_manager.set_llm_cache(user_input, {
                "content": response.content,
                "time": llm_time
            })
            
            total_time = time.time() - start_time
            logger.info(f"回复生成完成，总耗时: {total_time:.2f}秒")
            
            return {
                "content": response.content,
                "time": llm_time
            }
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"发生错误，耗时: {total_time:.2f}秒, 错误: {type(e).__name__}: {str(e)}")
            # 返回错误信息作为字典，确保上层调用不会因为类型错误而失败
            return {
                "content": "抱歉，我暂时无法回答你的问题，请稍后再试。",
                "time": 0,
                "error": str(e)
            }
            
            # 添加用户消息到记忆
            self.memory.add_user_message(user_input)
            
            # 限制历史消息数量，避免上下文过长
            if len(self.memory.messages) > 10:
                self.memory.messages = self.memory.messages[-10:]
                logger.info("历史消息过多，已裁剪")
            
            # 生成AI回复
            llm_start = time.time()
            # 优化：只发送最新的消息，减少上下文长度
            simple_message = HumanMessage(content=self.memory.messages[-1].content)
            response = llm.invoke([simple_message])
            llm_time = time.time() - llm_start
            logger.info(f"LLM调用完成，耗时: {llm_time:.2f}秒")
            
            # 添加AI回复到记忆
            self.memory.add_ai_message(response.content)
            
            # 缓存LLM响应
            self.cache_manager.set_llm_cache(user_input, {
                "content": response.content,
                "time": llm_time
            })
            
            total_time = time.time() - start_time
            logger.info(f"回复生成完成，总耗时: {total_time:.2f}秒")
            
            return {
                "content": response.content,
                "time": llm_time
            }
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"发生错误，耗时: {total_time:.2f}秒, 错误: {type(e).__name__}: {str(e)}")
            # 返回错误信息作为字典，确保上层调用不会因为类型错误而失败
            return {
                "content": "抱歉，我暂时无法回答你的问题，请稍后再试。",
                "time": 0,
                "error": str(e)
            }
    
    def get_model_status(self):
        """检查模型状态"""
        try:
            # 发送一个简单的测试请求
            test_message = HumanMessage(content="你好")
            response = llm.invoke([test_message])
            return {
                "status": "healthy",
                "response": response.content[:50]
            }
        except Exception as e:
            logger.error(f"模型状态检查失败: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def chat_stream(self, user_input):
        """流式生成回复"""
        try:
            # 对于长输入，进行截断处理
            if len(user_input) > 2000:
                user_input = user_input[:2000] + "..."
            
            # 检查是否使用模拟模式
            if USE_MOCK:
                logger.info("使用模拟数据生成流式响应")
                # 查找匹配的模拟响应
                matched_response = None
                for key, response in mock_responses.items():
                    if key in user_input:
                        matched_response = response
                        break
                
                if matched_response:
                    # 模拟流式输出
                    content = json.dumps(matched_response, ensure_ascii=False)
                else:
                    # 默认模拟响应
                    content = json.dumps({
                        "positive": "",
                        "negative": "",
                        "suggestions": "建议：请提供更多个人信息，以便为您提供更精准的政策咨询和个性化建议。"
                    }, ensure_ascii=False)
                
                # 模拟流式输出，逐字符或逐词发送
                for i in range(0, len(content), 50):
                    yield content[i:i+50]
                    time.sleep(0.05)  # 模拟流式延迟
            else:
                simple_message = HumanMessage(content=user_input)
                for chunk in llm.stream([simple_message]):
                    # 优先提取 DeepSeek 的深度思考内容
                    reasoning = chunk.additional_kwargs.get("reasoning_content", "")
                    if reasoning:
                        yield reasoning
                    
                    # 再提取常规回复内容
                    if chunk.content:
                        yield chunk.content
        except Exception as e:
            logger.error(f"流式生成错误: {e}")
            yield f"错误: {str(e)}"
    
    def _get_intent_analyzer_mock_response(self, user_input):
        """获取意图分析器的模拟响应"""
        # 提取实体
        entities = []
        
        # 提取年龄
        import re
        age_match = re.search(r'(\d+)岁', user_input)
        if age_match:
            entities.append({"type": "年龄", "value": age_match.group(1)})
        
        # 提取性别
        if "女性" in user_input:
            entities.append({"type": "性别", "value": "女性"})
        elif "男性" in user_input:
            entities.append({"type": "性别", "value": "男性"})
        
        # 提取职业技能证书
        if "中级电工证" in user_input:
            entities.append({"type": "证书", "value": "中级电工证"})
        elif "高级电工证" in user_input:
            entities.append({"type": "证书", "value": "高级电工证"})
        elif "电工证" in user_input:
            entities.append({"type": "证书", "value": "电工证"})
        
        # 提取就业状态
        if "失业" in user_input:
            entities.append({"type": "就业状态", "value": "失业"})
        elif "在职" in user_input:
            entities.append({"type": "就业状态", "value": "在职"})
        
        # 提取关注点
        if "补贴" in user_input:
            entities.append({"type": "关注点", "value": "补贴申领"})
        if "灵活时间" in user_input:
            entities.append({"type": "关注点", "value": "灵活时间"})
        
        # 根据用户输入内容返回不同的意图识别结果
        # 优先检查政策相关关键词
        if "政策" in user_input or "补贴" in user_input or "创业" in user_input or "贷款" in user_input or "返乡" in user_input:
            return json.dumps({
                "intent": "政策咨询",
                "needs_job_recommendation": False,
                "needs_course_recommendation": False,
                "needs_policy_recommendation": True,
                "entities": entities
            }, ensure_ascii=False)
        # 然后检查求职相关关键词
        elif "推荐工作" in user_input or "找工作" in user_input or "兼职工作" in user_input or "想找一份" in user_input:
            return json.dumps({
                "intent": "求职咨询",
                "needs_job_recommendation": True,
                "needs_course_recommendation": False,
                "needs_policy_recommendation": True,  # 同时需要政策咨询（因为关注补贴）
                "entities": entities
            }, ensure_ascii=False)
        elif "课程" in user_input or "培训" in user_input or "学习" in user_input:
            return json.dumps({
                "intent": "培训咨询",
                "needs_job_recommendation": False,
                "needs_course_recommendation": True,
                "needs_policy_recommendation": False,
                "entities": entities
            }, ensure_ascii=False)
        else:
            # 默认意图
            return json.dumps({
                "intent": "政策咨询",
                "needs_job_recommendation": False,
                "needs_course_recommendation": False,
                "needs_policy_recommendation": False,
                "entities": entities
            }, ensure_ascii=False)
    
    def _get_response_generator_mock_response(self, user_input):
        """获取响应生成器的模拟响应"""
        # 查找匹配的模拟响应
        matched_response = None
        for key, response in mock_responses.items():
            if key in user_input:
                matched_response = response
                break
        
        if matched_response:
            # 将模拟响应转换为JSON字符串
            return json.dumps(matched_response, ensure_ascii=False)
        else:
            # 默认模拟响应
            return json.dumps({
                "positive": "",
                "negative": "",
                "suggestions": "建议：请提供更多个人信息，以便为您提供更精准的政策咨询和个性化建议。"
            }, ensure_ascii=False)
    
    def clear_memory(self):
        """清空对话记忆"""
        self.memory = InMemoryChatMessageHistory()

# 测试代码
if __name__ == "__main__":
    bot = ChatBot()
    print("开始测试对话...")
    print("用户: 你好，我叫小明")
    print("AI:", bot.chat_with_memory("你好，我叫小明"))
    print("用户: 我刚才说了我的名字吗？")
    print("AI:", bot.chat_with_memory("我刚才说了我的名字吗？"))  # 模型会记住名字
    print("测试完成！")
