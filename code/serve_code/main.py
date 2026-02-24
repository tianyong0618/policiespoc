import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

# 添加LangChain模块路径，支持不同环境
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(base_dir, 'code'))

# 直接导入模块
from langchain.presentation.orchestrator import Orchestrator
from langchain.business.job_matcher import JobMatcher
from langchain.business.user_matcher import UserMatcher
from langchain.infrastructure.history_manager import HistoryManager

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

# 配置静态文件服务
web_dir = os.path.join(base_dir, 'code', 'web_code')
if os.path.exists(web_dir):
    # 挂载到/static路径，避免覆盖API路由
    app.mount("/static", StaticFiles(directory=web_dir), name="static")
    
    # 添加根路径路由，返回index.html
    @app.get("/")
    async def root():
        return FileResponse(os.path.join(web_dir, "index.html"))
    
    # 添加其他可能的路由
    @app.get("/index.html")
    async def index():
        return FileResponse(os.path.join(web_dir, "index.html"))
else:
    logger.warning(f"Web directory not found: {web_dir}")

# 初始化岗位匹配器 (单例)
job_matcher = JobMatcher()
# 初始化用户画像管理器
try:
    user_profile_manager = UserMatcher(job_matcher)
except Exception as e:
    logger.error(f"初始化用户画像管理器失败: {e}")
    user_profile_manager = None
# 初始化协调器 (单例)
agent = Orchestrator()
# 初始化历史记录管理器
history_manager = HistoryManager()

# 请求模型
class ChatRequest(BaseModel):
    message: str
    scenario: str = "general"
    session_id: str = None  # 新增 session_id 字段

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
    description: str
    core_needs: list
    associated_relations: list

class RecommendationsResponse(BaseModel):
    policies: list
    jobs: list

from fastapi.responses import StreamingResponse

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """处理用户对话（流式响应）"""
    # 1. 获取或创建会话
    session_id = request.session_id
    if not session_id:
        session_id = history_manager.create_session()
    
    # 2. 保存用户消息
    history_manager.add_message(session_id, "user", request.message)
    
    # 3. 获取对话历史（在保存新消息之后）
    session = history_manager.get_session(session_id)
    conversation_history = session.get('messages', []) if session else []

    async def event_generator():
        try:
            # 发送 session_id 给前端，以便后续使用
            yield f"event: session\ndata: {json.dumps({'session_id': session_id})}\n\n"

            # 获取流式生成器
            stream = agent.process_stream_query(request.message, session_id, conversation_history)
            
            # 处理流式响应
            for chunk in stream:
                if chunk:
                    # 解析JSON数据
                    try:
                        data = json.loads(chunk.strip())
                        event_type = data.get("type", "message")
                        
                        # 根据事件类型发送不同的事件
                        if event_type == "follow_up":
                            # 追问事件
                            yield f"event: follow_up\ndata: {chunk}\n\n"
                            
                            # 保存追问到历史记录
                            history_manager.add_message(session_id, "ai", json.dumps(data, ensure_ascii=False))
                        elif event_type == "analysis_start":
                            # 分析开始事件
                            yield f"event: analysis_start\ndata: {chunk}\n\n"
                        elif event_type == "thinking":
                            # 思考过程事件
                            yield f"event: thinking\ndata: {chunk}\n\n"
                        elif event_type == "analysis_result":
                            # 分析结果事件
                            yield f"event: analysis_result\ndata: {chunk}\n\n"
                            
                            # 保存分析结果到历史记录
                            history_manager.add_message(session_id, "ai", json.dumps(data, ensure_ascii=False))
                        elif event_type == "analysis_complete":
                            # 分析完成事件
                            yield f"event: analysis_complete\ndata: {chunk}\n\n"
                        else:
                            # 其他消息事件
                            yield f"event: message\ndata: {chunk}\n\n"
                    except json.JSONDecodeError:
                        # 如果不是有效的JSON，作为普通消息处理
                        json_chunk = json.dumps({"content": chunk}, ensure_ascii=False)
                        yield f"event: message\ndata: {json_chunk}\n\n"

            yield "event: done\ndata: {}\n\n"
            
        except Exception as e:
            logger.error(f"流式处理失败: {str(e)}")
            error_msg = json.dumps({"error": str(e)}, ensure_ascii=False)
            yield f"event: error\ndata: {error_msg}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/history")
async def get_history():
    """获取会话历史列表"""
    return {"sessions": history_manager.get_all_sessions()}

@app.get("/api/history/{session_id}")
async def get_session_history(session_id: str):
    """获取特定会话的历史消息"""
    session = history_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@app.delete("/api/history/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    if history_manager.delete_session(session_id):
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Session not found")

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

# 添加Mangum适配器，支持Vercel部署
from mangum import Mangum

# 创建Mangum处理程序
handler = Mangum(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
