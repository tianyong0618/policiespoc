import json
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
from langchain.job_matcher import JobMatcher
from langchain.user_profile import UserProfileManager

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
# 初始化岗位匹配器
job_matcher = JobMatcher()
# 初始化用户画像管理器
user_profile_manager = UserProfileManager()

# 请求模型
class ChatRequest(BaseModel):
    message: str
    scenario: str = "general"

class EvaluateRequest(BaseModel):
    user_input: str
    response: dict

class UserProfileRequest(BaseModel):
    basic_info: dict = {}
    skills: list = []
    preferences: dict = {}
    policy_interest: list = []
    job_interest: list = []

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
    recommended_jobs: list = []

class PoliciesResponse(BaseModel):
    policies: list

class EvaluateResponse(BaseModel):
    score: int
    max_score: int
    policy_recall_accuracy: str
    condition_accuracy: str
    user_satisfaction: str

class JobsResponse(BaseModel):
    jobs: list

class UserProfileResponse(BaseModel):
    user_id: str
    basic_info: dict
    skills: list
    preferences: dict
    policy_interest: list
    job_interest: list

class RecommendationsResponse(BaseModel):
    policies: list
    jobs: list

from fastapi.responses import StreamingResponse

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """处理用户对话（流式响应）"""
    async def event_generator():
        try:
            # 获取流式生成器
            stream = agent.process_stream_query(request.message)
            
            # 第一个块是上下文数据
            context_data = next(stream)
            yield f"event: context\ndata: {context_data}\n\n"
            
            # 后续块是文本内容
            for chunk in stream:
                # 简单的文本块，需要转义换行符以便SSE传输
                if chunk:
                    # 使用JSON dump来安全处理字符串
                    json_chunk = json.dumps({"content": chunk}, ensure_ascii=False)
                    yield f"event: message\ndata: {json_chunk}\n\n"
            
            yield "event: done\ndata: {}\n\n"
            
        except Exception as e:
            logger.error(f"流式处理失败: {str(e)}")
            error_msg = json.dumps({"error": str(e)}, ensure_ascii=False)
            yield f"event: error\ndata: {error_msg}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

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

@app.get("/api/jobs", response_model=JobsResponse)
async def get_jobs():
    """获取岗位列表"""
    try:
        jobs = job_matcher.get_all_jobs()
        return JobsResponse(jobs=jobs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取岗位失败: {str(e)}")

@app.get("/api/jobs/{job_id}", response_model=dict)
async def get_job(job_id: str):
    """获取单个岗位详情"""
    try:
        job = job_matcher.get_job_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"岗位不存在: {job_id}")
        return job
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取岗位失败: {str(e)}")

@app.get("/api/users/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(user_id: str):
    """获取用户画像"""
    try:
        profile = user_profile_manager.get_user_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail=f"用户画像不存在: {user_id}")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户画像失败: {str(e)}")

@app.post("/api/users/{user_id}/profile", response_model=UserProfileResponse)
async def create_or_update_user_profile(user_id: str, request: UserProfileRequest):
    """创建或更新用户画像"""
    try:
        profile = user_profile_manager.create_or_update_user_profile(user_id, request.dict())
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"操作用户画像失败: {str(e)}")

@app.get("/api/users/{user_id}/recommendations", response_model=RecommendationsResponse)
async def get_personalized_recommendations(user_id: str):
    """获取个性化推荐"""
    try:
        recommendations = user_profile_manager.get_personalized_recommendations(user_id)
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取推荐失败: {str(e)}")

@app.get("/api/recommendations", response_model=RecommendationsResponse)
async def get_general_recommendations():
    """获取通用推荐"""
    try:
        # 获取所有岗位
        all_jobs = job_matcher.get_all_jobs()
        # 获取所有政策
        all_policies = agent.policies
        
        return {
            "policies": all_policies[:3],  # 返回前3个政策
            "jobs": all_jobs[:3]  # 返回前3个岗位
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取推荐失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
