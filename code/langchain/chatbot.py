from langchain_openai import ChatOpenAI
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
import time
import logging
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

# 加载环境变量
load_dotenv()

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
    
    def chat_with_memory(self, user_input):
        start_time = time.time()
        logger.info(f"开始生成回复: {user_input[:50]}...")
        
        try:
            # 对于长输入，进行截断处理
            if len(user_input) > 2000:
                user_input = user_input[:2000] + "..."
                logger.info("输入过长，已截断")
            
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
