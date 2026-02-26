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

# 导入性能监控组件
from langchain.infrastructure.performance import PerformanceMiddleware, performance_monitor, PerformanceAnalyzer, PerformanceOptimizer

# 初始化性能分析器
performance_analyzer = PerformanceAnalyzer(performance_monitor)

# 初始化性能优化器
performance_optimizer = PerformanceOptimizer(performance_monitor, performance_analyzer)

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

# 添加性能监控中间件
app.add_middleware(PerformanceMiddleware)

# 启动性能监控器
performance_monitor.start_monitoring(interval=5)

# 启动性能优化器
performance_optimizer.start_optimization(interval=30)

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

class BatchRequest(BaseModel):
    requests: list

class BatchItem(BaseModel):
    type: str  # 支持的类型: chat, policies, jobs, user_profile, recommendations
    params: dict = {}

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

class BatchResponse(BaseModel):
    results: list
    total_execution_time: float

class OptimizedResponse(BaseModel):
    success: bool
    data: dict = {}
    error: str = None
    execution_time: float = 0

class CombinedDataResponse(BaseModel):
    policies: list = []
    jobs: list = []
    recommendations: dict = {}
    execution_time: float = 0

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

@app.post("/api/chat", response_model=OptimizedResponse)
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
        
        # 优化响应数据，只返回必要的字段
        optimized_result = {
            "intent": result.get("intent", {}),
            "relevant_policies": result.get("relevant_policies", []),
            "response": result.get("response", {}),
            "recommended_jobs": result.get("recommended_jobs", [])
        }
        
        return OptimizedResponse(
            success=True,
            data=optimized_result,
            execution_time=execution_time
        )
    except Exception as e:
        end_time = time.time()
        execution_time = end_time - start_time
        logger.error(f"处理请求失败，耗时: {execution_time:.2f}秒, 错误: {str(e)}")
        return OptimizedResponse(
            success=False,
            error=str(e),
            execution_time=execution_time
        )

@app.get("/api/policies", response_model=OptimizedResponse)
async def get_policies():
    """获取政策列表"""
    start_time = time.time()
    try:
        policies = agent.policies
        # 优化政策数据，只返回必要字段
        optimized_policies = []
        for policy in policies:
            optimized_policy = {
                "id": policy.get("id"),
                "title": policy.get("title"),
                "category": policy.get("category"),
                "summary": policy.get("summary")
            }
            optimized_policies.append(optimized_policy)
        
        end_time = time.time()
        return OptimizedResponse(
            success=True,
            data={"policies": optimized_policies},
            execution_time=end_time - start_time
        )
    except Exception as e:
        end_time = time.time()
        return OptimizedResponse(
            success=False,
            error=str(e),
            execution_time=end_time - start_time
        )

@app.post("/api/evaluate", response_model=OptimizedResponse)
async def evaluate(request: EvaluateRequest):
    """评估演示结果"""
    start_time = time.time()
    try:
        evaluation = agent.evaluate_response(request.user_input, request.response)
        end_time = time.time()
        return OptimizedResponse(
            success=True,
            data=evaluation,
            execution_time=end_time - start_time
        )
    except Exception as e:
        end_time = time.time()
        return OptimizedResponse(
            success=False,
            error=str(e),
            execution_time=end_time - start_time
        )

@app.get("/api/health", response_model=OptimizedResponse)
async def health_check():
    """健康检查"""
    return OptimizedResponse(
        success=True,
        data={"status": "healthy"}
    )

@app.get("/api/performance/metrics", response_model=OptimizedResponse)
async def get_performance_metrics():
    """获取性能指标"""
    try:
        metrics = performance_monitor.get_metrics()
        return OptimizedResponse(
            success=True,
            data=metrics
        )
    except Exception as e:
        return OptimizedResponse(
            success=False,
            error=str(e)
        )

@app.get("/api/performance/report", response_model=OptimizedResponse)
async def get_performance_report():
    """获取性能报告"""
    try:
        report = performance_monitor.generate_report()
        return OptimizedResponse(
            success=True,
            data=report
        )
    except Exception as e:
        return OptimizedResponse(
            success=False,
            error=str(e)
        )

@app.post("/api/performance/save-report", response_model=OptimizedResponse)
async def save_performance_report():
    """保存性能报告到文件"""
    try:
        filename = performance_monitor.save_report()
        return OptimizedResponse(
            success=True,
            data={"filename": filename}
        )
    except Exception as e:
        return OptimizedResponse(
            success=False,
            error=str(e)
        )

@app.get("/api/performance/comprehensive-report", response_model=OptimizedResponse)
async def get_comprehensive_report():
    """获取综合性能报告"""
    try:
        report = performance_analyzer.generate_comprehensive_report()
        return OptimizedResponse(
            success=True,
            data=report
        )
    except Exception as e:
        return OptimizedResponse(
            success=False,
            error=str(e)
        )

@app.get("/api/performance/optimization/strategies", response_model=OptimizedResponse)
async def get_optimization_strategies():
    """获取当前应用的优化策略"""
    try:
        strategies = performance_optimizer.get_current_strategies()
        return OptimizedResponse(
            success=True,
            data={"strategies": strategies}
        )
    except Exception as e:
        return OptimizedResponse(
            success=False,
            error=str(e)
        )

@app.get("/api/performance/optimization/history", response_model=OptimizedResponse)
async def get_optimization_history():
    """获取优化历史"""
    try:
        history = performance_optimizer.get_optimization_history()
        return OptimizedResponse(
            success=True,
            data={"history": history}
        )
    except Exception as e:
        return OptimizedResponse(
            success=False,
            error=str(e)
        )

@app.get("/api/performance/optimization/effectiveness", response_model=OptimizedResponse)
async def get_optimization_effectiveness():
    """评估优化效果"""
    try:
        effectiveness = performance_optimizer.evaluate_optimization_effectiveness()
        return OptimizedResponse(
            success=True,
            data=effectiveness
        )
    except Exception as e:
        return OptimizedResponse(
            success=False,
            error=str(e)
        )

@app.post("/api/performance/optimization/thresholds", response_model=OptimizedResponse)
async def set_optimization_thresholds(thresholds: dict):
    """设置性能优化阈值"""
    try:
        performance_optimizer.set_thresholds(thresholds)
        return OptimizedResponse(
            success=True,
            data={"thresholds": performance_optimizer.get_thresholds()}
        )
    except Exception as e:
        return OptimizedResponse(
            success=False,
            error=str(e)
        )

@app.get("/api/jobs", response_model=OptimizedResponse)
async def get_jobs():
    """获取岗位列表"""
    start_time = time.time()
    try:
        jobs = job_matcher.get_all_jobs()
        # 优化岗位数据，只返回必要字段
        optimized_jobs = []
        for job in jobs:
            optimized_job = {
                "id": job.get("id"),
                "title": job.get("title"),
                "company": job.get("company"),
                "salary": job.get("salary"),
                "location": job.get("location")
            }
            optimized_jobs.append(optimized_job)
        
        end_time = time.time()
        return OptimizedResponse(
            success=True,
            data={"jobs": optimized_jobs},
            execution_time=end_time - start_time
        )
    except Exception as e:
        end_time = time.time()
        return OptimizedResponse(
            success=False,
            error=str(e),
            execution_time=end_time - start_time
        )

@app.get("/api/jobs/{job_id}", response_model=OptimizedResponse)
async def get_job(job_id: str):
    """获取单个岗位详情"""
    start_time = time.time()
    try:
        job = job_matcher.get_job_by_id(job_id)
        if not job:
            end_time = time.time()
            return OptimizedResponse(
                success=False,
                error=f"岗位不存在: {job_id}",
                execution_time=end_time - start_time
            )
        
        end_time = time.time()
        return OptimizedResponse(
            success=True,
            data=job,
            execution_time=end_time - start_time
        )
    except Exception as e:
        end_time = time.time()
        return OptimizedResponse(
            success=False,
            error=str(e),
            execution_time=end_time - start_time
        )

@app.get("/api/users/{user_id}/profile", response_model=OptimizedResponse)
async def get_user_profile(user_id: str):
    """获取用户画像"""
    start_time = time.time()
    try:
        profile = user_profile_manager.get_user_profile(user_id)
        if not profile:
            end_time = time.time()
            return OptimizedResponse(
                success=False,
                error=f"用户画像不存在: {user_id}",
                execution_time=end_time - start_time
            )
        
        end_time = time.time()
        return OptimizedResponse(
            success=True,
            data=profile,
            execution_time=end_time - start_time
        )
    except Exception as e:
        end_time = time.time()
        return OptimizedResponse(
            success=False,
            error=str(e),
            execution_time=end_time - start_time
        )

@app.post("/api/users/{user_id}/profile", response_model=OptimizedResponse)
async def create_or_update_user_profile(user_id: str, request: UserProfileRequest):
    """创建或更新用户画像"""
    start_time = time.time()
    try:
        profile = user_profile_manager.create_or_update_user_profile(user_id, request.dict())
        end_time = time.time()
        return OptimizedResponse(
            success=True,
            data=profile,
            execution_time=end_time - start_time
        )
    except Exception as e:
        end_time = time.time()
        return OptimizedResponse(
            success=False,
            error=str(e),
            execution_time=end_time - start_time
        )

@app.get("/api/users/{user_id}/recommendations", response_model=OptimizedResponse)
async def get_personalized_recommendations(user_id: str):
    """获取个性化推荐"""
    start_time = time.time()
    try:
        recommendations = user_profile_manager.get_personalized_recommendations(user_id)
        end_time = time.time()
        return OptimizedResponse(
            success=True,
            data=recommendations,
            execution_time=end_time - start_time
        )
    except Exception as e:
        end_time = time.time()
        return OptimizedResponse(
            success=False,
            error=str(e),
            execution_time=end_time - start_time
        )

@app.get("/api/recommendations", response_model=OptimizedResponse)
async def get_general_recommendations():
    """获取通用推荐"""
    start_time = time.time()
    try:
        # 获取所有岗位
        all_jobs = job_matcher.get_all_jobs()
        # 获取所有政策
        all_policies = agent.policies
        
        # 优化推荐数据，只返回必要字段
        optimized_jobs = []
        for job in all_jobs[:3]:
            optimized_job = {
                "id": job.get("id"),
                "title": job.get("title"),
                "company": job.get("company"),
                "salary": job.get("salary")
            }
            optimized_jobs.append(optimized_job)
        
        optimized_policies = []
        for policy in all_policies[:3]:
            optimized_policy = {
                "id": policy.get("id"),
                "title": policy.get("title"),
                "category": policy.get("category")
            }
            optimized_policies.append(optimized_policy)
        
        recommendations = {
            "policies": optimized_policies,
            "jobs": optimized_jobs
        }
        
        end_time = time.time()
        return OptimizedResponse(
            success=True,
            data=recommendations,
            execution_time=end_time - start_time
        )
    except Exception as e:
        end_time = time.time()
        return OptimizedResponse(
            success=False,
            error=str(e),
            execution_time=end_time - start_time
        )



@app.post("/api/batch", response_model=BatchResponse)
async def batch_process(request: BatchRequest):
    """批量处理API请求，减少网络往返时间"""
    start_time = time.time()
    results = []
    
    try:
        for item in request.requests:
            item_start = time.time()
            item_result = {}
            
            try:
                if item.type == "chat":
                    # 处理聊天请求
                    chat_request = ChatRequest(**item.params)
                    if chat_request.scenario != "general":
                        result = agent.handle_scenario(chat_request.scenario, chat_request.message)
                    else:
                        result = agent.process_query(chat_request.message)
                    item_result = result
                
                elif item.type == "policies":
                    # 获取政策列表
                    item_result = {"policies": agent.policies}
                
                elif item.type == "jobs":
                    # 获取岗位列表
                    item_result = {"jobs": job_matcher.get_all_jobs()}
                
                elif item.type == "user_profile":
                    # 获取用户画像
                    user_id = item.params.get("user_id")
                    if user_id:
                        profile = user_profile_manager.get_user_profile(user_id)
                        item_result = profile
                
                elif item.type == "recommendations":
                    # 获取推荐
                    user_id = item.params.get("user_id")
                    if user_id:
                        recommendations = user_profile_manager.get_personalized_recommendations(user_id)
                        item_result = recommendations
                    else:
                        # 获取通用推荐
                        all_jobs = job_matcher.get_all_jobs()
                        all_policies = agent.policies
                        item_result = {
                            "policies": all_policies[:3],
                            "jobs": all_jobs[:3]
                        }
                
                item_result["success"] = True
            except Exception as e:
                item_result = {
                    "success": False,
                    "error": str(e)
                }
            
            item_result["execution_time"] = time.time() - item_start
            results.append(item_result)
        
        total_time = time.time() - start_time
        return BatchResponse(results=results, total_execution_time=total_time)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量处理失败: {str(e)}")

@app.get("/api/combined-data", response_model=CombinedDataResponse)
async def get_combined_data(user_id: str = None):
    """获取组合数据，减少多次API调用"""
    start_time = time.time()
    
    try:
        # 并行获取数据
        all_policies = agent.policies
        all_jobs = job_matcher.get_all_jobs()
        
        recommendations = {}
        if user_id:
            try:
                recommendations = user_profile_manager.get_personalized_recommendations(user_id)
            except Exception as e:
                logger.warning(f"获取个性化推荐失败: {str(e)}")
                # 回退到通用推荐
                recommendations = {
                    "policies": all_policies[:3],
                    "jobs": all_jobs[:3]
                }
        else:
            # 通用推荐
            recommendations = {
                "policies": all_policies[:3],
                "jobs": all_jobs[:3]
            }
        
        return CombinedDataResponse(
            policies=all_policies,
            jobs=all_jobs,
            recommendations=recommendations,
            execution_time=time.time() - start_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取组合数据失败: {str(e)}")

# 添加Mangum适配器，支持Vercel部署
from mangum import Mangum

# 创建Mangum处理程序
handler = Mangum(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
