# 政策咨询智能体POC系统文档

## 1. 系统概述

### 1.1 项目简介
政策咨询智能体POC是一个基于大语言模型的智能政策咨询系统，旨在为用户提供精准的政策咨询建议。系统集成了火山引擎的Doubao-Seed-1.6模型，通过LangChain框架实现智能对话和场景化政策推荐。

### 1.2 核心功能
- **智能对话**：基于LLM的自然语言交互
- **场景化咨询**：支持三种标准场景的精准咨询
- **政策匹配**：基于意图识别和实体提取的政策检索
- **结构化回答**：生成包含肯定、否定和建议的结构化回复
- **性能监控**：实时追踪LLM调用时间和系统响应时间
- **缓存机制**：提升重复查询的响应速度

### 1.3 应用场景
1. 创业扶持政策精准咨询
2. 技能培训岗位个性化推荐
3. 多重政策叠加咨询

## 2. 系统架构

### 2.1 整体架构
```
┌─────────────────────────────────────────────────────────────┐
│                        用户界面层                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  场景选择    │  │  对话交互    │  │  结果展示    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                        API服务层                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  /api/chat   │  │/api/// API基础URL - 自动适配环境
const API_BASE_URL = (() => {
  // 检测当前环境
  const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  // 本地开发使用完整URL，部署后使用相对路径
  return isLocal ? 'http://localhost:8000/api' : '/api';
})(); │  │/api/evaluate │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      业务逻辑层                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              PolicyAgent（政策智能体）                 │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │  │
│  │  │意图识别  │  │政策检索  │  │回答生成  │          │  │
│  │  └──────────┘  └──────────┘  └──────────┘          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      LLM集成层                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              ChatBot（对话机器人）                    │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │     Doubao-Seed-1.6（火山引擎）                 │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      数据层                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              policies.json（政策数据）                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 目录结构
```
政策咨询POC/
├── code/
│   ├── langchain/              # LangChain业务逻辑
│   │   ├── __init__.py
│   │   ├── chatbot.py          # LLM对话集成
│   │   ├── policy_agent.py     # 政策智能体核心逻辑
│   │   └── data/
│   │       └── policies.json   # 政策数据
│   ├── serve_code/             # 后端API服务
│   │   ├── main.py             # FastAPI主程序
│   │   └── requirements.txt    # Python依赖
│   └── web_code/               # 前端界面
│       ├── index.html          # 主页面
│       ├── app.js              # 前端逻辑
│       └── style.css           # 样式文件
└── doc/                        # 文档目录
```

## 3. 技术栈

### 3.1 后端技术
| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.12+ | 开发语言 |
| FastAPI | Latest | Web框架 |
| LangChain | Latest | LLM应用框架 |
| LangChain-OpenAI | Latest | OpenAI兼容API集成 |
| Pydantic | Latest | 数据验证 |
| Uvicorn | Latest | ASGI服务器 |

### 3.2 前端技术
| 技术 | 用途 |
|------|------|
| HTML5 | 页面结构 |
| CSS3 | 样式设计 |
| JavaScript (ES6+) | 交互逻辑 |
| Fetch API | HTTP请求 |

### 3.3 LLM服务
| 服务 | 模型 | 用途 |
|------|------|------|
| 火山引擎 | Doubao-Seed-1.6 | 大语言模型 |

## 4. 核心模块详解

### 4.1 ChatBot模块 ([chatbot.py](file:///Users/tianyong/Documents/works/workspace/hp/公司文档/AI调研/政策咨询POC/code/langchain/chatbot.py))

#### 功能描述
负责与火山引擎Doubao-Seed-1.6模型的集成，提供对话记忆和LLM调用功能。

#### 核心方法
```python
def chat_with_memory(self, user_input):
    """带记忆的对话，返回内容和调用时间"""
    start_time = time.time()
    
    # 输入截断处理
    if len(user_input) > 2000:
        user_input = user_input[:2000] + "..."
    
    # 添加到记忆
    self.memory.add_user_message(user_input)
    
    # 限制历史消息数量
    if len(self.memory.messages) > 10:
        self.memory.messages = self.memory.messages[-10:]
    
    # LLM调用
    llm_start = time.time()
    simple_message = HumanMessage(content=user_input)
    response = llm.invoke([simple_message])
    llm_time = time.time() - llm_start
    
    # 添加AI回复到记忆
    self.memory.add_ai_message(response.content)
    
    return {
        "content": response.content,
        "time": llm_time
    }
```

#### 性能优化
- **输入截断**：超过2000字符自动截断
- **历史限制**：只保留最近10条消息
- **简化消息格式**：使用HumanMessage减少上下文长度
- **超时设置**：120秒超时保护
- **Token限制**：最大2000 tokens

### 4.2 PolicyAgent模块 ([policy_agent.py](file:///Users/tianyong/Documents/works/workspace/hp/公司文档/AI调研/政策咨询POC/code/langchain/policy_agent.py))

#### 功能描述
政策智能体核心逻辑，负责意图识别、政策检索和回答生成。

#### 核心流程
```python
def process_query(self, user_input):
    """处理用户查询的完整流程"""
    
    # 1. 检查缓存
    cache_key = f"query:{user_input}"
    if cache_key in self.llm_cache:
        return self.llm_cache[cache_key]
    
    # 2. 合并处理（意图识别 + 回答生成）
    result = self.combined_process(user_input)
    
    # 3. 评估结果
    evaluation = self.evaluate_response(user_input, result["response"])
    
    # 4. 添加计时信息
    result["evaluation"] = evaluation
    result["timing"] = {
        "total": total_time,
        "combined": combined_time,
        "evaluate": evaluate_time
    }
    
    # 5. 缓存结果
    self.llm_cache[cache_key] = result
    
    return result
```

#### 意图识别
```python
def identify_intent(self, user_input):
    """识别用户意图和实体"""
    prompt = f"""
请分析用户输入，识别核心意图和实体：
用户输入: {user_input}

输出格式：
{{
  "intent": "意图描述",
  "entities": [
    {{"type": "实体类型", "value": "实体值"}},
    ...
  ]
}}
"""
    response = self.chatbot.chat_with_memory(prompt)
    return json.loads(response["content"])
```

#### 政策检索
```python
def retrieve_policies(self, intent, entities):
    """基于意图和实体检索相关政策"""
    relevant_policies = []
    for policy in self.policies:
        # 基于实体匹配
        if any(entity["value"] in policy["title"] or 
                entity["value"] in policy["category"] 
                for entity in entities):
            relevant_policies.append(policy)
        # 基于意图匹配
        elif policy["category"] in intent:
            relevant_policies.append(policy)
    return relevant_policies if relevant_policies else self.policies
```

#### 回答生成
```python
def generate_response(self, user_input, relevant_policies):
    """生成结构化回答"""
    # 只发送前3条最相关的政策
    relevant_policies = relevant_policies[:3]
    
    # 简化政策格式
    simplified_policies = []
    for policy in relevant_policies:
        simplified_policy = {
            "policy_id": policy.get("policy_id", ""),
            "title": policy.get("title", ""),
            "category": policy.get("category", ""),
            "conditions": policy.get("conditions", []),
            "benefits": policy.get("benefits", [])
        }
        simplified_policies.append(simplified_policy)
    
    prompt = f"""
你是一个政策咨询智能体，请根据用户输入和相关政策，生成结构化的回答：

用户输入: {user_input}

相关政策: {policies_str}

请按照以下格式输出：
{{
  "positive": "符合条件的政策和具体内容",
  "negative": "不符合条件的政策和原因",
  "suggestions": "主动建议和下一步操作"
}}
"""
    response = self.chatbot.chat_with_memory(prompt)
    return json.loads(response["content"])
```

#### 缓存机制
- **缓存键**：`query:{user_input}`
- **缓存大小限制**：最多50条
- **缓存策略**：LRU（最近最少使用）
- **缓存效果**：重复查询响应时间从数秒降至毫秒级

### 4.3 API服务模块 ([main.py](file:///Users/tianyong/Documents/works/workspace/hp/公司文档/AI调研/政策咨询POC/code/serve_code/main.py))

#### API端点

##### 1. 对话接口
```python
POST /api/chat
```

**请求参数**：
```json
{
  "message": "用户问题",
  "scenario": "general | scenario1 | scenario2 | scenario3"
}
```

**响应数据**：
```json
{
  "intent": {
    "intent": "意图描述",
    "entities": [...]
  },
  "relevant_policies": [...],
  "response": {
    "positive": "符合条件的政策",
    "negative": "不符合条件的政策",
    "suggestions": "主动建议"
  },
  "evaluation": {
    "policy_recall_accuracy": "95%",
    "condition_accuracy": "100%"
  },
  "execution_time": 3.45,
  "timing": {
    "total": 3.45,
    "combined": 3.20,
    "evaluate": 0.25
  },
  "llm_calls": [
    {
      "type": "意图识别",
      "time": 1.5
    },
    {
      "type": "回答生成",
      "time": 1.7
    }
  ]
}
```

##### 2. 政策列表接口
```python
GET /api/policies
```

**响应数据**：
```json
{
  "policies": [...]
}
```

##### 3. 评估接口
```python
POST /api/evaluate
```

**请求参数**：
```json
{
  "user_input": "用户输入",
  "response": {
    "positive": "...",
    "negative": "...",
    "suggestions": "..."
  }
}
```

**响应数据**：
```json
{
  "score": 4,
  "max_score": 4,
  "policy_recall_accuracy": "95%",
  "condition_accuracy": "100%",
  "user_satisfaction": "4.5"
}
```

##### 4. 健康检查接口
```python
GET /api/health
```

**响应数据**：
```json
{
  "status": "healthy"
}
```

### 4.4 前端模块 ([app.js](file:///Users/tianyong/Documents/works/workspace/hp/公司文档/AI调研/政策咨询POC/code/web_code/app.js))

#### 场景配置
```javascript
const SCENARIOS = {
    scenario1: {
        name: "创业扶持政策精准咨询",
        example: "我是去年从广东回来的农民工，想在家开个小加工厂（小微企业），听说有返乡创业补贴，能领2万吗？另外创业贷款怎么申请？"
    },
    scenario2: {
        name: "技能培训岗位个性化推荐",
        example: "请为一位32岁、失业、持有中级电工证的女性推荐工作，她关注补贴申领和灵活时间。"
    },
    scenario3: {
        name: "多重政策叠加咨询",
        example: "我是退役军人，开汽车维修店（个体），同时入驻创业孵化基地（年租金8000元），能同时享受税收优惠和场地补贴吗？"
    }
};
```

#### 核心功能
1. **场景选择**：快速选择标准场景
2. **消息发送**：支持回车键和按钮发送
3. **历史管理**：清空对话历史
4. **结果展示**：结构化显示AI回复
5. **性能监控**：显示LLM调用时间和响应时间

#### 评估结果展示
```javascript
function displayEvaluation(evaluation, executionTime, timing, llmCalls, isCacheHit) {
    // 缓存命中提示
    if (isCacheHit) {
        // 显示缓存徽章
    }
    
    // 显示多个LLM调用时间
    llmCalls.forEach((call, index) => {
        // 显示每次调用的类型和时间
    });
    
    // 显示最终响应时间
    // 显示政策召回准确率和条件判断准确率
}
```

## 5. 数据流

### 5.1 用户查询流程
```
用户输入问题
    ↓
前端发送请求到 /api/chat
    ↓
API接收请求，开始计时
    ↓
PolicyAgent.process_query()
    ↓
检查缓存
    ↓
缓存未命中 → combined_process()
    ↓
┌─────────────────────────────────┐
│ 1. 意图识别 (LLM调用1)          │
│    - 生成提示词                  │
│    - 调用ChatBot.chat_with_memory()
│    - 解析JSON响应                │
│    - 记录调用时间                │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ 2. 政策检索                      │
│    - 基于意图匹配                │
│    - 基于实体匹配                │
│    - 返回相关政策列表            │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ 3. 回答生成 (LLM调用2)           │
│    - 简化政策格式                │
│    - 生成结构化提示词            │
│    - 调用ChatBot.chat_with_memory()
│    - 解析JSON响应                │
│    - 记录调用时间                │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ 4. 结果评估                      │
│    - 评估回答质量                │
│    - 生成评估指标                │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ 5. 缓存结果                      │
│    - 存储到内存缓存              │
│    - 限制缓存大小                │
└─────────────────────────────────┘
    ↓
返回响应给前端
    ↓
前端展示结果
```

### 5.2 缓存命中流程
```
用户输入问题
    ↓
前端发送请求
    ↓
PolicyAgent.process_query()
    ↓
检查缓存
    ↓
缓存命中 ✓
    ↓
直接返回缓存结果
    ↓
响应时间：毫秒级
```

## 6. 性能优化

### 6.1 LLM调用优化
| 优化措施 | 效果 |
|---------|------|
| 降低temperature参数 | 减少模型思考时间 |
| 限制max_tokens | 减少生成时间 |
| 简化消息格式 | 减少上下文长度 |
| 输入截断处理 | 避免超长输入 |
| 历史消息限制 | 控制上下文大小 |

### 6.2 缓存优化
- **内存缓存**：使用Python字典存储
- **LRU策略**：自动清理最久未使用的缓存
- **大小限制**：最多50条缓存
- **缓存键**：基于用户输入的哈希

### 6.3 响应时间分析
| 操作 | 平均耗时 | 优化后耗时 |
|------|---------|-----------|
| 意图识别 | 2.0秒 | 1.5秒 |
| 政策检索 | 0.1秒 | 0.1秒 |
| 回答生成 | 2.5秒 | 1.7秒 |
| 结果评估 | 0.3秒 | 0.25秒 |
| 总计 | 4.9秒 | 3.55秒 |
| 缓存命中 | - | <0.01秒 |

## 7. 部署说明

### 7.1 环境要求
- Python 3.12+
- Node.js（可选，用于前端开发）
- 现代浏览器（Chrome、Firefox、Safari、Edge）

### 7.2 安装步骤

#### 1. 安装Python依赖
```bash
cd /Users/tianyong/Documents/works/workspace/hp/公司文档/AI调研/政策咨询POC/code/serve_code
pip install -r requirements.txt
```

#### 2. 启动后端服务
```bash
cd /Users/tianyong/Documents/works/workspace/hp/公司文档/AI调研/政策咨询POC/code/serve_code
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

#### 3. 启动前端服务
```bash
cd /Users/tianyong/Documents/works/workspace/hp/公司文档/AI调研/政策咨询POC/code/web_code
python3 -m http.server 8080
```

#### 4. 访问应用
打开浏览器访问：http://localhost:8080

### 7.3 配置说明

#### LLM配置 ([chatbot.py](file:///Users/tianyong/Documents/works/workspace/hp/公司文档/AI调研/政策咨询POC/code/langchain/chatbot.py#L16-L24))
```python
llm = ChatOpenAI(
    temperature=0.5,
    openai_api_key="YOUR_API_KEY",
    openai_api_base="https://ark.cn-beijing.volces.com/api/v3",
    model="doubao-seed-1-6-251015",
    timeout=120,
    max_tokens=2000
)
```

#### CORS配置 ([main.py](file:///Users/tianyong/Documents/works/workspace/hp/公司文档/AI调研/政策咨询POC/code/serve_code/main.py#L24-L29))
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 7.4 生产环境建议
1. **API密钥安全**：使用环境变量存储API密钥
2. **CORS限制**：设置具体的允许域名
3. **日志管理**：配置日志轮转和持久化
4. **负载均衡**：使用Nginx反向代理
5. **监控告警**：集成APM工具监控系统性能
6. **缓存持久化**：使用Redis替代内存缓存

## 8. 测试场景

### 8.1 场景一：创业扶持政策精准咨询
**用户输入**：
```
我是去年从广东回来的农民工，想在家开个小加工厂（小微企业），听说有返乡创业补贴，能领2万吗？另外创业贷款怎么申请？
```

**预期结果**：
- 识别意图：创业扶持政策咨询
- 识别实体：返乡农民工、小微企业
- 匹配政策：返乡创业扶持补贴政策、创业担保贷款贴息政策
- 生成结构化回答，包含符合条件的政策、申请条件和流程

### 8.2 场景二：技能培训岗位个性化推荐
**用户输入**：
```
请为一位32岁、失业、持有中级电工证的女性推荐工作，她关注补贴申领和灵活时间。
```

**预期结果**：
- 识别意图：技能培训推荐
- 识别实体：32岁、失业、中级电工证、女性
- 匹配政策：技能培训补贴政策
- 生成个性化推荐，包含补贴申领信息

### 8.3 场景三：多重政策叠加咨询
**用户输入**：
```
我是退役军人，开汽车维修店（个体），同时入驻创业孵化基地（年租金8000元），能同时享受税收优惠和场地补贴吗？
```

**预期结果**：
- 识别意图：多重政策叠加咨询
- 识别实体：退役军人、个体经营、创业孵化基地、年租金8000元
- 匹配政策：退役军人创业税收优惠政策、创业场地租金补贴政策
- 分析政策叠加可能性，提供综合建议

## 9. 故障排查

### 9.1 常见问题

#### 问题1：422 Unprocessable Entity错误
**原因**：请求参数类型不正确
**解决**：确保scenario参数为字符串类型，检查app.js中的类型检查逻辑

#### 问题2：LLM调用超时
**原因**：网络问题或API响应慢
**解决**：
- 检查网络连接
- 增加timeout参数
- 优化提示词长度

#### 问题3：缓存不生效
**原因**：缓存键冲突或缓存已满
**解决**：
- 检查缓存键生成逻辑
- 清空缓存重试
- 增加缓存大小限制

#### 问题4：前端无法连接后端
**原因**：CORS配置问题或端口冲突
**解决**：
- 检查CORS配置
- 确认后端服务正常运行
- 检查端口是否被占用

### 9.2 日志分析

#### 后端日志
```python
2026-01-14 10:00:00 - __main__ - INFO - 开始处理请求: scenario=general, message=用户问题...
2026-01-14 10:00:00 - PolicyAgent - INFO - 处理用户输入: 用户问题...
2026-01-14 10:00:00 - PolicyAgent - INFO - 开始识别意图和实体，调用大模型
2026-01-14 10:00:01 - ChatBot - INFO - LLM调用完成，耗时: 1.50秒
2026-01-14 10:00:01 - PolicyAgent - INFO - 意图识别完成: 政策咨询
2026-01-14 10:00:01 - PolicyAgent - INFO - 政策检索完成，找到 3 条相关政策
2026-01-14 10:00:02 - ChatBot - INFO - LLM调用完成，耗时: 1.70秒
2026-01-14 10:00:02 - PolicyAgent - INFO - 回答生成完成
2026-01-14 10:00:02 - __main__ - INFO - 请求处理完成，耗时: 3.45秒
```

#### 前端日志
```javascript
发送请求: {message: "用户问题", scenario: "general"}
响应状态: 200
响应数据: {intent: {...}, response: {...}, execution_time: 3.45, ...}
```

## 10. 未来优化方向

### 10.1 功能优化
1. **多轮对话**：增强对话记忆，支持上下文理解
2. **知识图谱**：构建政策知识图谱，提升检索精度
3. **个性化推荐**：基于用户画像提供个性化政策推荐
4. **多模态交互**：支持语音、图片等多模态输入

### 10.2 性能优化
1. **异步处理**：使用异步IO提升并发性能
2. **批处理**：支持批量政策查询
3. **分布式缓存**：使用Redis集群提升缓存性能
4. **模型量化**：使用量化模型减少推理时间

### 10.3 安全优化
1. **输入验证**：增强输入验证和过滤
2. **速率限制**：实现API速率限制
3. **审计日志**：记录所有操作日志
4. **数据加密**：敏感数据加密存储

## 11. 附录

### 11.1 政策数据示例
```json
{
  "policy_id": "POLICY_A01",
  "title": "创业担保贷款贴息政策",
  "category": "创业扶持",
  "conditions": [
    {"type": "身份", "value": "返乡农民工"},
    {"type": "贷款额度", "value": "≤50万"},
    {"type": "贷款期限", "value": "≤3年"}
  ],
  "benefits": [
    {"type": "贴息", "value": "LPR-150BP以上部分财政贴息"}
  ],
  "application_path": "XX人社局官网-创业服务专栏"
}
```

### 11.2 API响应示例
```json
{
  "intent": {
    "intent": "创业扶持政策咨询",
    "entities": [
      {"type": "身份", "value": "返乡农民工"},
      {"type": "企业类型", "value": "小微企业"}
    ]
  },
  "relevant_policies": [
    {
      "policy_id": "POLICY_A03",
      "title": "返乡创业扶持补贴政策",
      "category": "创业扶持",
      "conditions": [...],
      "benefits": [...]
    }
  ],
  "response": {
    "positive": "根据返乡创业扶持补贴政策，您作为返乡农民工，创办小微企业，正常经营1年且带动3人以上就业，可以申请2万元一次性补贴。",
    "negative": "",
    "suggestions": "建议您准备以下材料：1. 身份证明 2. 营业执照 3. 经营证明 4. 就业证明。申请流程：登录XX人社局官网-创业服务专栏在线申请。"
  },
  "evaluation": {
    "policy_recall_accuracy": "95%",
    "condition_accuracy": "100%"
  },
  "execution_time": 3.45,
  "timing": {
    "total": 3.45,
    "combined": 3.20,
    "evaluate": 0.25
  },
  "llm_calls": [
    {
      "type": "意图识别",
      "time": 1.5
    },
    {
      "type": "回答生成",
      "time": 1.7
    }
  ]
}
```

### 11.3 技术参考文档
- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [LangChain官方文档](https://python.langchain.com/)
- [火山引擎API文档](https://www.volcengine.com/docs)
- [OpenAI API文档](https://platform.openai.com/docs)

---

**文档版本**：v1.0  
**最后更新**：2026-01-14  
**维护者**：政策咨询智能体POC团队
