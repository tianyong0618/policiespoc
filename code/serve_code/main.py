from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加LangChain模块路径
sys.path.insert(0, os.path.abspath('/Users/tianyong/Documents/works/workspace/hp/公司文档/AI调研/政策咨询POC/code'))

# 直接导入模块
from langchain.policy_agent import PolicyAgent

# 初始化应用
app = FastAPI(title="政策咨询智能体API", description="政策咨询智能体POC服务")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化政策智能体
agent = PolicyAgent()

# 请求模型
class ChatRequest(BaseModel):
    message: str
    scenario: str = "general"

class EvaluateRequest(BaseModel):
    user_input: str
    response: dict

# 响应模型
class ChatResponse(BaseModel):
    intent: dict
    relevant_policies: list
    response: dict
    evaluation: dict
    execution_time: float
    timing: dict = {}
    llm_calls: list = []
    thinking_process: list = []

class PoliciesResponse(BaseModel):
    policies: list

class EvaluateResponse(BaseModel):
    score: int
    max_score: int
    policy_recall_accuracy: str
    condition_accuracy: str
    user_satisfaction: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, raw_request: Request):
    """处理用户对话"""
    start_time = time.time()
    logger.info(f"开始处理请求: scenario={request.scenario}, message={request.message[:50]}...")
    
    try:
        if request.scenario != "general":
            result = agent.handle_scenario(request.scenario, request.message)
        else:
            result = agent.process_query(request.message)
        
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"请求处理完成，耗时: {execution_time:.2f}秒")
        
        # 添加执行时间到结果
        result["execution_time"] = execution_time
        
        return ChatResponse(**result)
    except Exception as e:
        end_time = time.time()
        execution_time = end_time - start_time
        logger.error(f"处理请求失败，耗时: {execution_time:.2f}秒, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理请求失败: {str(e)}")

@app.get("/api/policies", response_model=PoliciesResponse)
async def get_policies():
    """获取政策列表"""
    try:
        return PoliciesResponse(policies=agent.policies)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取政策失败: {str(e)}")

@app.post("/api/evaluate", response_model=EvaluateResponse)
async def evaluate(request: EvaluateRequest):
    """评估演示结果"""
    try:
        evaluation = agent.evaluate_response(request.user_input, request.response)
        return EvaluateResponse(**evaluation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"评估失败: {str(e)}")

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
