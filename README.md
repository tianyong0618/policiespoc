# 政策咨询智能体POC系统文档

## 1. 系统概述

### 1.1 项目简介
政策咨询智能体POC是一个基于大语言模型的智能政策咨询系统，旨在为用户提供精准的政策咨询建议。系统集成了DeepSeek V3模型，通过LangChain框架实现智能对话和场景化政策推荐。

### 1.2 核心功能
- **智能对话**：基于LLM的自然语言交互
- **场景化咨询**：支持四种标准场景的精准咨询
- **政策匹配**：基于意图识别和实体提取的政策检索
- **结构化回答**：生成包含肯定、否定和建议的结构化回复
- **性能监控**：实时追踪LLM调用时间和系统响应时间
- **缓存机制**：提升重复查询的响应速度
- **会话管理**：支持多会话历史记录
- **岗位推荐**：基于用户画像和技能的个性化岗位推荐
- **课程推荐**：基于用户需求的培训课程智能匹配
- **用户画像**：支持用户画像创建和管理

### 1.3 应用场景
1. 创业扶持政策精准咨询
2. 技能培训岗位个性化推荐
3. 多重政策叠加咨询
4. 培训课程智能匹配

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
│  │  /api/chat   │  │/api/policies │  │/api/evaluate │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     表现层 (Presentation)                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                Orchestrator（协调器）                │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │  │
│  │  │请求处理  │  │结果整合  │  │响应格式化│          │  │
│  │  └──────────┘  └──────────┘  └──────────┘          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      业务逻辑层 (Business)                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐ │
│  │ PolicyMatcher   │  │   IntentAnalyzer│  │  ResponseGenerator││
│  │ （政策匹配器）   │  │ （意图分析器）   │  │  （回答生成器）   │ │
│  └─────────────────┘  └─────────────────┘  └────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐                  │ │
│  │   JobMatcher    │  │    UserMatcher  │                  │ │
│  │ （岗位匹配器）   │  │ （用户匹配器）   │                  │ │
│  └─────────────────┘  └─────────────────┘                  │ │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     数据访问层 (Data)                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐ │
│  │ PolicyRetriever │  │   JobRetriever  │  │   UserRetriever │ │
│  │ （政策检索器）   │  │ （岗位检索器）   │  │  （用户检索器）   │ │
│  └─────────────────┘  └─────────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  基础设施层 (Infrastructure)                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐ │
│  │    ChatBot      │  │ HistoryManager │  │  CacheManager   │ │
│  │ （对话机器人）   │  │ （历史管理器）   │  │  （缓存管理器）   │ │
│  └─────────────────┘  └─────────────────┘  └────────────────┘ │
│  ┌─────────────────┐                                        │ │
│  │ ConfigManager   │                                        │ │
│  │ （配置管理器）   │                                        │ │
│  └─────────────────┘                                        │ │
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
├── code/                        # 核心代码目录
│   ├── langchain/              # LangChain业务逻辑
│   │   ├── __init__.py
│   │   ├── business/           # 业务逻辑层
│   │   │   ├── intent_analyzer.py     # 意图分析器
│   │   │   ├── job_matcher.py          # 岗位匹配器
│   │   │   ├── policy_matcher.py       # 政策匹配器
│   │   │   ├── response_generator.py   # 回答生成器
│   │   │   └── user_matcher.py         # 用户匹配器
│   │   ├── data/                # 数据访问层
│   │   │   ├── data_files/      # 数据文件
│   │   │   │   ├── jobs.json           # 岗位数据
│   │   │   │   ├── policies.json       # 政策数据
│   │   │   │   └── user_profiles.json  # 用户画像数据
│   │   │   ├── models/           # 数据模型
│   │   │   │   ├── job.py               # 岗位模型
│   │   │   │   ├── policy.py            # 政策模型
│   │   │   │   └── user.py              # 用户模型
│   │   │   ├── job_retriever.py         # 岗位检索器
│   │   │   ├── policy_retriever.py      # 政策检索器
│   │   │   └── user_retriever.py        # 用户检索器
│   │   ├── infrastructure/      # 基础设施层
│   │   │   ├── chatbot.py               # LLM对话集成
│   │   │   ├── history_manager.py       # 会话历史管理
│   │   │   ├── cache_manager.py         # 缓存管理
│   │   │   └── config_manager.py         # 配置管理
│   │   └── presentation/         # 表现层
│   │       └── orchestrator.py          # 协调器
│   ├── serve_code/             # 后端API服务
│   │   ├── main.py             # FastAPI主程序
│   │   ├── requirements.txt    # Python依赖
│   ├── test/                   # 测试目录
│   │   ├── test_cases.md       # 测试用例文档
│   │   ├── test_report.md      # 测试报告
│   │   ├── test_scenario1_comprehensive.py # 场景1综合测试
│   │   ├── test_scenario1_results.json # 场景1测试结果
│   │   ├── test_scenario2_comprehensive.py # 场景2综合测试
│   │   └── test_scenario2_results.json # 场景2测试结果
│   └── web_code/               # 前端界面
│       ├── index.html          # 主页面
│       ├── app.js              # 前端逻辑
│       └── style.css           # 样式文件
├── doc/                        # 文档目录
├── .env                        # 环境变量配置（本地开发）
├── .gitignore                  # Git忽略文件
├── main.py                     # Vercel部署入口
├── package.json                # 项目配置
├── requirements.txt            # 根目录依赖（Vercel部署）
└── vercel.json                 # Vercel部署配置
```

## 3. 技术栈

### 3.1 后端技术
| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.12+ | 开发语言 |
| FastAPI | Latest | Web框架 |
| LangChain | Latest | LLM应用框架 |
| LangChain-OpenAI | Latest | OpenAI兼容API集成 |
| python-dotenv | Latest | 环境变量管理 |
| Pydantic | Latest | 数据验证 |
| Uvicorn | Latest | ASGI服务器 |
| Mangum | Latest | AWS Lambda适配器（Vercel部署） |

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
| 火山引擎 | DeepSeek V3 | 大语言模型 |

## 4. 核心模块详解

### 4.1 表现层 (Presentation)

#### Orchestrator模块 ([orchestrator.py](file:///Users/tianyong/Documents/works/workspace/hp/公司文档/AI调研/政策咨询POC/code/langchain/presentation/orchestrator.py))

##### 功能描述
协调器，负责处理用户请求，整合各模块功能，生成统一的响应格式。

##### 核心方法
```python
def process_query(self, user_input):
    """处理用户查询的完整流程"""
    # 1. 识别意图和实体
    # 2. 验证意图是否在服务范围内
    # 3. 检索相关政策和推荐
    # 4. 生成结构化回答
    # 5. 评估结果
    # 6. 构建思考过程
    # 7. 返回结果


def process_stream_query(self, user_input, session_id=None, conversation_history=None):
    """处理流式查询，支持实时响应"""
    # 1. 识别意图
    # 2. 验证意图是否在服务范围内
    # 3. 分析用户输入
    # 4. 检索政策和推荐
    # 5. 生成回答
    # 6. 流式返回结果
```

### 4.2 业务逻辑层 (Business)

#### IntentAnalyzer模块 ([intent_analyzer.py](file:///Users/tianyong/Documents/works/workspace/hp/公司文档/AI调研/政策咨询POC/code/langchain/business/intent_analyzer.py))

##### 功能描述
意图分析器，负责识别用户意图和提取实体信息。

##### 核心方法
```python
def ir_identify_intent(self, user_input):
    """识别用户意图和实体"""
    # 1. 生成意图识别提示
    # 2. 调用大模型
    # 3. 处理LLM响应
    # 4. 解析JSON结果
    # 5. 返回意图信息
```

#### PolicyMatcher模块 ([policy_matcher.py](file:///Users/tianyong/Documents/works/workspace/hp/公司文档/AI调研/政策咨询POC/code/langchain/business/policy_matcher.py))

##### 功能描述
政策匹配器，负责基于用户意图和实体匹配相关政策。

##### 核心方法
```python
def match_policies(self, intent, entities, original_input=None):
    """基于意图和实体匹配政策"""
    # 1. 提取实体值和用户需求关键词
    # 2. 检查用户具体条件
    # 3. 逐个检查政策是否符合用户条件
    # 4. 限制返回的政策数量
    # 5. 返回符合条件的政策
```

#### JobMatcher模块 ([job_matcher.py](file:///Users/tianyong/Documents/works/workspace/hp/公司文档/AI调研/政策咨询POC/code/langchain/business/job_matcher.py))

##### 功能描述
岗位匹配器，负责基于用户画像和技能匹配相关岗位。

##### 核心方法
```python
def match_jobs_by_entities(self, entities, user_input=""):
    """基于实体信息匹配岗位"""
    # 1. 从实体中提取信息和关键词
    # 2. 从用户输入中提取额外信息
    # 3. 计算岗位与用户的匹配度
    # 4. 按匹配度排序
    # 5. 返回匹配度最高的岗位
```

#### UserMatcher模块 ([user_matcher.py](file:///Users/tianyong/Documents/works/workspace/hp/公司文档/AI调研/政策咨询POC/code/langchain/business/user_matcher.py))

##### 功能描述
用户匹配器，负责创建和管理用户画像，提供个性化推荐。

##### 核心方法
```python
def create_or_update_user_profile(self, user_id, user_data):
    """创建或更新用户画像"""
    # 1. 构建用户描述
    # 2. 计算核心需求
    # 3. 生成关联关系
    # 4. 保存用户画像
    # 5. 返回用户画像
```

#### ResponseGenerator模块 ([response_generator.py](file:///Users/tianyong/Documents/works/workspace/hp/公司文档/AI调研/政策咨询POC/code/langchain/business/response_generator.py))

##### 功能描述
回答生成器，负责基于政策和推荐生成结构化回答。

##### 核心方法
```python
def rg_generate_response(self, user_input, relevant_policies, scenario, recommended_jobs=None):
    """生成结构化回答"""
    # 1. 构建回答提示
    # 2. 调用大模型
    # 3. 处理LLM响应
    # 4. 解析JSON结果
    # 5. 返回结构化回答
```

### 4.3 数据访问层 (Data)

#### PolicyRetriever模块 ([policy_retriever.py](file:///Users/tianyong/Documents/works/workspace/hp/公司文档/AI调研/政策咨询POC/code/langchain/data/policy_retriever.py))

##### 功能描述
政策检索器，负责加载和管理政策数据，提供政策检索功能。

##### 核心方法
```python
def pr_retrieve_policies(self, intent, entities, original_input=None):
    """检索相关政策"""
    # 1. 提取实体值和用户需求关键词
    # 2. 检查用户具体条件
    # 3. 逐个检查政策是否符合用户条件
    # 4. 限制返回的政策数量
    # 5. 返回符合条件的政策


def pr_load_policies(self):
    """加载政策数据（带缓存）"""
    # 1. 检查缓存
    # 2. 从配置中获取政策文件路径
    # 3. 加载政策数据
    # 4. 缓存数据
    # 5. 返回政策数据
```

#### JobRetriever模块 ([job_retriever.py](file:///Users/tianyong/Documents/works/workspace/hp/公司文档/AI调研/政策咨询POC/code/langchain/data/job_retriever.py))

##### 功能描述
岗位检索器，负责加载和管理岗位数据。

##### 核心方法
```python
def load_jobs(self):
    """加载岗位数据"""
    # 1. 从配置中获取岗位文件路径
    # 2. 加载岗位数据
    # 3. 返回岗位数据
```

#### UserRetriever模块 ([user_retriever.py](file:///Users/tianyong/Documents/works/workspace/hp/公司文档/AI调研/政策咨询POC/code/langchain/data/user_retriever.py))

##### 功能描述
用户检索器，负责加载和管理用户画像数据。

##### 核心方法
```python
def load_user_profiles(self):
    """加载用户画像数据"""
    # 1. 从配置中获取用户画像文件路径
    # 2. 加载用户画像数据
    # 3. 返回用户画像数据
```

### 4.4 基础设施层 (Infrastructure)

#### ChatBot模块 ([chatbot.py](file:///Users/tianyong/Documents/works/workspace/hp/公司文档/AI调研/政策咨询POC/code/langchain/infrastructure/chatbot.py))

##### 功能描述
对话机器人，负责与DeepSeek V3模型的集成，提供对话记忆和LLM调用功能。

##### 核心方法
```python
def chat_with_memory(self, user_input):
    """带记忆的对话，返回内容和调用时间"""
    # 1. 输入截断处理
    # 2. 添加到对话记忆
    # 3. 限制历史消息数量
    # 4. LLM调用
    # 5. 记录调用时间
    # 6. 返回结果
```

##### 性能优化
- **输入截断**：超过2000字符自动截断
- **历史限制**：只保留最近10条消息
- **简化消息格式**：使用HumanMessage减少上下文长度
- **超时设置**：1800秒超时保护
- **Token限制**：最大8192 tokens

#### HistoryManager模块 ([history_manager.py](file:///Users/tianyong/Documents/works/workspace/hp/公司文档/AI调研/政策咨询POC/code/langchain/infrastructure/history_manager.py))

##### 功能描述
历史管理器，负责管理用户会话历史。

##### 核心方法
```python
def create_session(self):
    """创建新会话"""
    # 1. 生成会话ID
    # 2. 初始化会话数据
    # 3. 保存会话
    # 4. 返回会话ID


def add_message(self, session_id, role, content):
    """添加消息到会话历史"""
    # 1. 检查会话是否存在
    # 2. 创建消息对象
    # 3. 添加消息到会话
    # 4. 限制消息数量
    # 5. 保存会话


def get_session(self, session_id):
    """获取会话历史"""
    # 1. 检查会话是否存在
    # 2. 返回会话数据
```

#### CacheManager模块 ([cache_manager.py](file:///Users/tianyong/Documents/works/workspace/hp/公司文档/AI调研/政策咨询POC/code/langchain/infrastructure/cache_manager.py))

##### 功能描述
缓存管理器，负责缓存LLM响应和计算结果，提升系统性能。

##### 核心方法
```python
def get(self, key):
    """获取缓存数据"""
    # 1. 检查缓存是否存在
    # 2. 检查缓存是否过期
    # 3. 返回缓存数据


def set(self, key, value, ttl=3600):
    """设置缓存数据"""
    # 1. 检查缓存大小
    # 2. 如果缓存已满，清理最久未使用的缓存
    # 3. 设置缓存数据
    # 4. 设置过期时间
```

#### ConfigManager模块 ([config_manager.py](file:///Users/tianyong/Documents/works/workspace/hp/公司文档/AI调研/政策咨询POC/code/langchain/infrastructure/config_manager.py))

##### 功能描述
配置管理器，负责加载和管理系统配置。

##### 核心方法
```python
def get(self, key, default=None):
    """获取配置值"""
    # 1. 按层级查找配置
    # 2. 如果不存在，返回默认值
    # 3. 返回配置值


def load_config(self):
    """加载配置"""
    # 1. 加载环境变量
    # 2. 加载默认配置
    # 3. 合并配置
    # 4. 返回配置
```

### 4.5 API服务模块 ([main.py](file:///Users/tianyong/Documents/works/workspace/hp/公司文档/AI调研/政策咨询POC/code/serve_code/main.py))

#### API端点

##### 1. 对话接口（流式）
```
POST /api/chat/stream
```

**请求参数**：
```json
{
  "message": "用户问题",
  "scenario": "general | scenario1 | scenario2 | scenario3",
  "session_id": "可选，会话ID"
}
```

**响应数据**：
- SSE流式响应，包含会话信息、上下文数据和消息内容

##### 2. 对话接口（非流式）
```
POST /api/chat
```

**响应数据**：
```json
{
  "intent": {"intent": "意图描述", "entities": [...]},
  "relevant_policies": [...],
  "response": {"positive": "...", "negative": "...", "suggestions": "..."},
  "evaluation": {...},
  "execution_time": 3.45,
  "thinking_process": [...],
  "recommended_jobs": [...]
}
```

##### 3. 政策列表接口
```
GET /api/policies
```

##### 4. 健康检查接口
```
GET /api/health
```

##### 5. 会话管理接口
```
GET /api/history
GET /api/history/{session_id}
DELETE /api/history/{session_id}
```

##### 6. 岗位管理接口
```
GET /api/jobs
GET /api/jobs/{job_id}
```

##### 7. 用户画像接口
```
GET /api/users/{user_id}/profile
POST /api/users/{user_id}/profile
```

##### 8. 推荐接口
```
GET /api/users/{user_id}/recommendations
GET /api/recommendations
```

### 4.6 前端模块 ([app.js](file:///Users/tianyong/Documents/works/workspace/hp/公司文档/AI调研/政策咨询POC/code/web_code/app.js))

#### 核心功能
1. **场景选择**：快速选择标准场景
2. **消息发送**：支持回车键和按钮发送
3. **历史管理**：管理对话历史记录
4. **结果展示**：结构化显示AI回复
5. **性能监控**：显示LLM调用时间和响应时间
6. **会话管理**：支持多会话切换和删除

#### API地址配置
```javascript
// API基础URL - 自动适配环境
const API_BASE_URL = (() => {
  // 检测当前环境
  const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  // 本地开发使用完整URL，部署后使用相对路径
  return isLocal ? 'http://localhost:8000/api' : '/api';
})();
```

## 5. 数据流

### 5.1 用户查询流程
```
用户输入问题
    ↓
前端发送请求到 /api/chat/stream
    ↓
API接收请求，开始计时
    ↓
Orchestrator.process_stream_query()
    ↓
┌─────────────────────────────────┐
│ 1. 意图识别 (LLM调用1)          │
│    - 调用IntentAnalyzer        │
│    - 生成提示词                  │
│    - 调用ChatBot.chat_with_memory()
│    - 解析JSON响应                │
│    - 记录调用时间                │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ 2. 验证意图                      │
│    - 检查意图是否在服务范围内    │
│    - 确定需要的服务类型          │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ 3. 检索政策和推荐                │
│    - 调用PolicyRetriever        │
│    - 基于意图匹配政策            │
│    - 基于实体匹配政策            │
│    - 返回相关政策列表            │
│    - 调用JobMatcher生成岗位推荐  │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ 4. 生成回答 (LLM调用2)           │
│    - 调用ResponseGenerator      │
│    - 构建回答提示                │
│    - 调用ChatBot.chat_with_memory()
│    - 解析JSON响应                │
│    - 记录调用时间                │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ 5. 构建思考过程                  │
│    - 组织意图识别结果            │
│    - 组织政策检索结果            │
│    - 组织岗位推荐结果            │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ 6. 结果评估                      │
│    - 评估回答质量                │
│    - 生成评估指标                │
└─────────────────────────────────┘
    ↓
通过SSE流式返回响应
    ↓
前端展示结果
```

## 6. 部署说明

### 6.1 环境要求
- Python 3.12+
- 现代浏览器（Chrome、Firefox、Safari、Edge）

### 6.2 本地开发部署

#### 1. 安装Python依赖
```bash
# 安装后端依赖
cd code/serve_code
pip install -r requirements.txt
```

#### 2. 配置环境变量
在项目根目录创建`.env`文件：
```
# LLM API配置
OPENAI_API_KEY=YOUR_API_KEY
OPENAI_API_BASE=https://ark.cn-beijing.volces.com/api/v3
LLM_MODEL=deepseek-v3-2-251201
LLM_TIMEOUT=1800
LLM_MAX_TOKENS=8192
```

#### 3. 启动后端服务
```bash
# 从根目录运行（推荐，与Vercel部署方式一致）
python3 -m uvicorn main:app --reload --port 8000

# 或从serve_code目录运行
cd code/serve_code
python3 -m uvicorn main:app --reload --port 8000
```

#### 4. 启动前端服务
```bash
cd code/web_code
# 使用端口3001（避免与其他服务冲突）
python3 -m http.server 3001

# 或使用其他可用端口
# python3 -m http.server 8080
```

#### 5. 访问应用
打开浏览器访问：http://localhost:3001（或使用你设置的前端端口）

### 6.3 Vercel部署

#### 1. 配置Vercel环境变量
在Vercel控制台添加以下环境变量：
- OPENAI_API_KEY
- OPENAI_API_BASE
- LLM_MODEL
- LLM_TIMEOUT
- LLM_MAX_TOKENS

#### 2. 部署方式
- 通过GitHub仓库自动部署
- 使用Vercel CLI手动部署

#### 3. 部署配置
- vercel.json：配置构建规则和路由
- main.py：FastAPI入口点
- requirements.txt：根目录依赖

## 7. 配置说明

### 7.1 LLM配置
通过环境变量配置LLM参数：

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| OPENAI_API_KEY | API密钥 | 必填 |
| OPENAI_API_BASE | API端点 | https://ark.cn-beijing.volces.com/api/v3 |
| LLM_MODEL | 模型名称 | deepseek-v3-2-251201 |
| LLM_TIMEOUT | 超时时间（秒） | 1800 |
| LLM_MAX_TOKENS | 最大令牌数 | 8192 |

### 7.2 应用配置
- **前端API地址**：自动适配环境，本地使用http://localhost:8000/api，部署后使用相对路径
- **CORS配置**：允许所有来源（生产环境建议限制）
- **缓存配置**：内存缓存，最多50条记录

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

### 8.4 场景四：培训课程智能匹配
**用户输入**：
```
我今年38岁，之前在工厂做机械操作工，现在失业了，只有初中毕业证，想转行做电商运营，不知道该报什么培训课程？另外，失业人员参加培训有补贴吗？
```

**预期结果**：
- 识别意图：培训课程智能匹配
- 识别实体：38岁、失业、初中毕业证、电商运营
- 匹配政策：职业技能提升补贴政策
- 匹配课程：电商运营基础课程、电商平台操作实务
- 生成课程+补贴打包方案和成长路径

## 9. 故障排查

### 9.1 常见问题

#### 问题1：前端无法连接后端
**原因**：
- 后端服务未启动
- 端口冲突
- CORS配置问题

**解决**：
- 检查后端服务是否正常运行
- 检查端口是否被占用
- 确认CORS配置是否允许前端域名

#### 问题2：LLM调用超时
**原因**：
- 网络问题
- API响应慢
- 提示词过长

**解决**：
- 检查网络连接
- 增加timeout参数
- 优化提示词长度
- 减少历史消息数量

#### 问题3：缓存不生效
**原因**：
- 缓存键冲突
- 缓存已满
- 缓存未正确实现

**解决**：
- 检查缓存键生成逻辑
- 清空缓存重试
- 增加缓存大小限制

#### 问题4：422 Unprocessable Entity错误
**原因**：
- 请求参数类型不正确
- 缺少必填参数

**解决**：
- 确保请求参数类型正确
- 检查是否缺少必填参数
- 查看API文档确认参数格式

## 10. 性能优化

### 10.1 LLM调用优化
| 优化措施 | 效果 |
|---------|------|
| 降低temperature参数 | 减少模型思考时间 |
| 限制max_tokens | 减少生成时间 |
| 简化消息格式 | 减少上下文长度 |
| 输入截断处理 | 避免超长输入 |
| 历史消息限制 | 控制上下文大小 |

### 10.2 缓存优化
- **内存缓存**：使用Python字典存储
- **LRU策略**：自动清理最久未使用的缓存
- **大小限制**：最多50条缓存
- **缓存键**：基于用户输入的哈希

### 10.3 响应时间分析
| 操作 | 平均耗时 | 优化后耗时 |
|------|---------|-----------|
| 意图识别 | 2.0秒 | 1.5秒 |
| 政策检索 | 0.1秒 | 0.1秒 |
| 回答生成 | 2.5秒 | 1.7秒 |
| 结果评估 | 0.3秒 | 0.25秒 |
| 总计 | 4.9秒 | 3.55秒 |
| 缓存命中 | - | <0.01秒 |

## 11. 未来优化方向

### 11.1 功能优化
1. **多轮对话**：增强对话记忆，支持上下文理解
2. **知识图谱**：构建政策知识图谱，提升检索精度
3. **个性化推荐**：基于用户画像提供个性化政策推荐
4. **多模态交互**：支持语音、图片等多模态输入
5. **政策时效性管理**：自动更新政策数据

### 11.2 性能优化
1. **异步处理**：使用异步IO提升并发性能
2. **批处理**：支持批量政策查询
3. **分布式缓存**：使用Redis集群提升缓存性能
4. **模型量化**：使用量化模型减少推理时间
5. **负载均衡**：支持多实例部署

### 11.3 安全优化
1. **输入验证**：增强输入验证和过滤
2. **速率限制**：实现API速率限制
3. **审计日志**：记录所有操作日志
4. **数据加密**：敏感数据加密存储
5. **API密钥管理**：使用密钥管理服务

## 12. 附录

### 12.1 政策数据示例
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

### 12.2 Vercel部署入口示例
```python
# Vercel FastAPI 入口点
# 导入现有FastAPI应用
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath('.'))

# 从现有位置导入app实例
from code.serve_code.main import app

# 暴露app实例，供Vercel使用
__all__ = ['app']
```

### 12.3 技术参考文档
- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [LangChain官方文档](https://python.langchain.com/)
- [火山引擎API文档](https://www.volcengine.com/docs)
- [OpenAI API文档](https://platform.openai.com/docs)

---

**文档版本**：v1.3  
**最后更新**：2026-02-12  
**维护者**：政策咨询智能体POC团队