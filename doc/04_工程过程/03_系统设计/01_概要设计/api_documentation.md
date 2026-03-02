# 政策咨询智能体API文档

## 1. 概述

政策咨询智能体API是一个基于FastAPI框架开发的RESTful API服务，旨在提供政策咨询、岗位匹配和用户画像管理等功能。本文档详细描述了所有API端点、请求参数、响应格式和使用示例。

### 1.1 基础URL

```
http://localhost:8000
```

### 1.2 响应格式

所有API响应均采用统一的JSON格式，包含以下字段：

```json
{
  "success": true,        // 操作是否成功
  "data": {},            // 响应数据
  "error": null,         // 错误信息（仅当success为false时存在）
  "execution_time": 0.5  // 执行时间（秒）
}
```

## 2. API端点

### 2.1 对话相关

#### 2.1.1 流式对话

**接口**：`POST /api/chat/stream`

**描述**：处理用户对话，返回流式响应

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 | 示例 |
|-------|------|------|------|------|
| message | string | 是 | 用户消息 | "我想了解大学生就业政策" |
| scenario | string | 否 | 对话场景 | "general" |
| session_id | string | 否 | 会话ID，若不提供则创建新会话 | "session_123456" |

**请求示例**：

```json
{
  "message": "我想了解大学生就业政策",
  "scenario": "general",
  "session_id": "session_123456"
}
```

**响应格式**：

流式响应（Server-Sent Events），包含以下事件类型：

| 事件类型 | 描述 | 数据格式 |
|---------|------|---------|
| session | 会话信息 | `{"session_id": "session_123456"}` |
| follow_up | 追问 | `{"type": "follow_up", "content": "请问您是应届毕业生吗？"}` |
| analysis_start | 分析开始 | `{"type": "analysis_start", "message": "正在分析您的问题..."}` |
| thinking | 思考过程 | `{"type": "thinking", "content": "需要查找相关政策..."}` |
| analysis_result | 分析结果 | `{"type": "analysis_result", "data": {...}}` |
| analysis_complete | 分析完成 | `{"type": "analysis_complete", "message": "分析完成"}` |
| message | 普通消息 | `{"content": "这是一条普通消息"}` |
| error | 错误信息 | `{"error": "处理失败的原因"}` |
| done | 完成信号 | `{}` |

#### 2.1.2 普通对话

**接口**：`POST /api/chat`

**描述**：处理用户对话，返回完整响应

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 | 示例 |
|-------|------|------|------|------|
| message | string | 是 | 用户消息 | "我想了解大学生就业政策" |
| scenario | string | 否 | 对话场景 | "general" |
| session_id | string | 否 | 会话ID | "session_123456" |

**请求示例**：

```json
{
  "message": "我想了解大学生就业政策",
  "scenario": "general"
}
```

**响应示例**：

```json
{
  "success": true,
  "data": {
    "intent": {
      "type": "policy_inquiry",
      "keywords": ["大学生", "就业", "政策"]
    },
    "relevant_policies": [
      {
        "id": "policy_001",
        "title": "大学生就业创业扶持政策",
        "category": "就业政策",
        "summary": "为大学生提供就业创业扶持..."
      }
    ],
    "response": {
      "content": "根据您的问题，以下是相关的大学生就业政策...",
      "confidence": 0.95
    },
    "recommended_jobs": [
      {
        "id": "job_001",
        "title": "软件工程师",
        "company": "科技公司",
        "salary": "10000-15000",
        "location": "北京"
      }
    ]
  },
  "error": null,
  "execution_time": 1.2
}
```

### 2.2 会话历史

#### 2.2.1 获取会话历史列表

**接口**：`GET /api/history`

**描述**：获取所有会话历史的列表

**请求参数**：无

**响应示例**：

```json
{
  "sessions": [
    {
      "session_id": "session_123456",
      "created_at": "2024-01-01T12:00:00",
      "last_message": "我想了解大学生就业政策"
    },
    {
      "session_id": "session_789012",
      "created_at": "2024-01-01T13:00:00",
      "last_message": "有哪些适合我的岗位？"
    }
  ]
}
```

#### 2.2.2 获取特定会话的历史消息

**接口**：`GET /api/history/{session_id}`

**描述**：获取指定会话的详细历史消息

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 | 示例 |
|-------|------|------|------|------|
| session_id | string | 是 | 会话ID | "session_123456" |

**响应示例**：

```json
{
  "session_id": "session_123456",
  "created_at": "2024-01-01T12:00:00",
  "messages": [
    {
      "role": "user",
      "content": "我想了解大学生就业政策",
      "timestamp": "2024-01-01T12:00:00"
    },
    {
      "role": "ai",
      "content": "根据您的问题，以下是相关的大学生就业政策...",
      "timestamp": "2024-01-01T12:00:01"
    }
  ]
}
```

#### 2.2.3 删除会话

**接口**：`DELETE /api/history/{session_id}`

**描述**：删除指定的会话

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 | 示例 |
|-------|------|------|------|------|
| session_id | string | 是 | 会话ID | "session_123456" |

**响应示例**：

```json
{
  "status": "success"
}
```

### 2.3 政策相关

#### 2.3.1 获取政策列表

**接口**：`GET /api/policies`

**描述**：获取所有政策的列表

**请求参数**：无

**响应示例**：

```json
{
  "success": true,
  "data": {
    "policies": [
      {
        "id": "policy_001",
        "title": "大学生就业创业扶持政策",
        "category": "就业政策",
        "summary": "为大学生提供就业创业扶持..."
      },
      {
        "id": "policy_002",
        "title": "人才引进补贴政策",
        "category": "人才政策",
        "summary": "为引进人才提供补贴..."
      }
    ]
  },
  "error": null,
  "execution_time": 0.1
}
```

### 2.4 评估相关

#### 2.4.1 评估演示结果

**接口**：`POST /api/evaluate`

**描述**：评估智能体的响应结果

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 | 示例 |
|-------|------|------|------|------|
| user_input | string | 是 | 用户输入 | "我想了解大学生就业政策" |
| response | object | 是 | 智能体响应 | `{"content": "相关政策有..."}` |

**请求示例**：

```json
{
  "user_input": "我想了解大学生就业政策",
  "response": {
    "content": "根据您的问题，以下是相关的大学生就业政策..."
  }
}
```

**响应示例**：

```json
{
  "success": true,
  "data": {
    "score": 85,
    "max_score": 100,
    "policy_recall_accuracy": "高",
    "condition_accuracy": "高",
    "user_satisfaction": "满意"
  },
  "error": null,
  "execution_time": 0.5
}
```

### 2.5 健康检查

#### 2.5.1 健康检查

**接口**：`GET /api/health`

**描述**：检查API服务是否正常运行

**请求参数**：无

**响应示例**：

```json
{
  "success": true,
  "data": {
    "status": "healthy"
  },
  "error": null,
  "execution_time": 0.01
}
```

### 2.6 性能监控

#### 2.6.1 获取性能指标

**接口**：`GET /api/performance/metrics`

**描述**：获取系统性能指标

**请求参数**：无

**响应示例**：

```json
{
  "success": true,
  "data": {
    "response_times": {
      "avg": 0.5,
      "min": 0.1,
      "max": 2.0
    },
    "throughput": 10,
    "error_rate": 0.01
  },
  "error": null,
  "execution_time": 0.05
}
```

#### 2.6.2 获取性能报告

**接口**：`GET /api/performance/report`

**描述**：获取性能报告

**请求参数**：无

**响应示例**：

```json
{
  "success": true,
  "data": {
    "report_id": "report_123456",
    "generated_at": "2024-01-01T12:00:00",
    "metrics": {
      "response_times": {
        "avg": 0.5,
        "min": 0.1,
        "max": 2.0
      },
      "throughput": 10,
      "error_rate": 0.01
    }
  },
  "error": null,
  "execution_time": 0.1
}
```

#### 2.6.3 保存性能报告到文件

**接口**：`POST /api/performance/save-report`

**描述**：保存性能报告到文件

**请求参数**：无

**响应示例**：

```json
{
  "success": true,
  "data": {
    "filename": "performance_report_20240101_120000.json"
  },
  "error": null,
  "execution_time": 0.2
}
```

#### 2.6.4 获取综合性能报告

**接口**：`GET /api/performance/comprehensive-report`

**描述**：获取综合性能报告

**请求参数**：无

**响应示例**：

```json
{
  "success": true,
  "data": {
    "report_id": "comprehensive_report_123456",
    "generated_at": "2024-01-01T12:00:00",
    "metrics": {
      "response_times": {
        "avg": 0.5,
        "min": 0.1,
        "max": 2.0
      },
      "throughput": 10,
      "error_rate": 0.01
    },
    "optimization_suggestions": [
      "建议优化数据库查询",
      "建议增加缓存机制"
    ]
  },
  "error": null,
  "execution_time": 0.3
}
```

#### 2.6.5 获取当前应用的优化策略

**接口**：`GET /api/performance/optimization/strategies`

**描述**：获取当前应用的性能优化策略

**请求参数**：无

**响应示例**：

```json
{
  "success": true,
  "data": {
    "strategies": [
      {
        "type": "cache_optimization",
        "enabled": true,
        "parameters": {
          "cache_size": 1000,
          "expiry_time": 3600
        }
      },
      {
        "type": "batch_processing",
        "enabled": true,
        "parameters": {
          "batch_size": 10
        }
      }
    ]
  },
  "error": null,
  "execution_time": 0.1
}
```

#### 2.6.6 获取优化历史

**接口**：`GET /api/performance/optimization/history`

**描述**：获取性能优化历史记录

**请求参数**：无

**响应示例**：

```json
{
  "success": true,
  "data": {
    "history": [
      {
        "timestamp": "2024-01-01T10:00:00",
        "strategy": "cache_optimization",
        "metrics_before": {
          "response_time": 1.0
        },
        "metrics_after": {
          "response_time": 0.5
        }
      },
      {
        "timestamp": "2024-01-01T11:00:00",
        "strategy": "batch_processing",
        "metrics_before": {
          "throughput": 5
        },
        "metrics_after": {
          "throughput": 10
        }
      }
    ]
  },
  "error": null,
  "execution_time": 0.2
}
```

#### 2.6.7 评估优化效果

**接口**：`GET /api/performance/optimization/effectiveness`

**描述**：评估性能优化的效果

**请求参数**：无

**响应示例**：

```json
{
  "success": true,
  "data": {
    "overall_improvement": 50,
    "metrics": {
      "response_time": {
        "before": 1.0,
        "after": 0.5,
        "improvement": 50
      },
      "throughput": {
        "before": 5,
        "after": 10,
        "improvement": 100
      }
    }
  },
  "error": null,
  "execution_time": 0.3
}
```

#### 2.6.8 设置性能优化阈值

**接口**：`POST /api/performance/optimization/thresholds`

**描述**：设置性能优化的阈值

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 | 示例 |
|-------|------|------|------|------|
| response_time | number | 否 | 响应时间阈值（秒） | 1.0 |
| error_rate | number | 否 | 错误率阈值 | 0.05 |
| throughput | number | 否 | 吞吐量阈值（请求/秒） | 10 |

**请求示例**：

```json
{
  "response_time": 1.0,
  "error_rate": 0.05,
  "throughput": 10
}
```

**响应示例**：

```json
{
  "success": true,
  "data": {
    "thresholds": {
      "response_time": 1.0,
      "error_rate": 0.05,
      "throughput": 10
    }
  },
  "error": null,
  "execution_time": 0.1
}
```

### 2.7 岗位相关

#### 2.7.1 获取岗位列表

**接口**：`GET /api/jobs`

**描述**：获取所有岗位的列表

**请求参数**：无

**响应示例**：

```json
{
  "success": true,
  "data": {
    "jobs": [
      {
        "id": "job_001",
        "title": "软件工程师",
        "company": "科技公司",
        "salary": "10000-15000",
        "location": "北京"
      },
      {
        "id": "job_002",
        "title": "数据分析师",
        "company": "互联网公司",
        "salary": "12000-18000",
        "location": "上海"
      }
    ]
  },
  "error": null,
  "execution_time": 0.1
}
```

#### 2.7.2 获取单个岗位详情

**接口**：`GET /api/jobs/{job_id}`

**描述**：获取指定岗位的详细信息

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 | 示例 |
|-------|------|------|------|------|
| job_id | string | 是 | 岗位ID | "job_001" |

**响应示例**：

```json
{
  "success": true,
  "data": {
    "id": "job_001",
    "title": "软件工程师",
    "company": "科技公司",
    "salary": "10000-15000",
    "location": "北京",
    "description": "负责公司软件系统的开发和维护...",
    "requirements": "本科及以上学历，计算机相关专业...",
    "benefits": "五险一金，带薪年假..."
  },
  "error": null,
  "execution_time": 0.05
}
```

### 2.8 用户画像相关

#### 2.8.1 获取用户画像

**接口**：`GET /api/users/{user_id}/profile`

**描述**：获取指定用户的画像信息

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 | 示例 |
|-------|------|------|------|------|
| user_id | string | 是 | 用户ID | "user_123456" |

**响应示例**：

```json
{
  "success": true,
  "data": {
    "user_id": "user_123456",
    "description": "计算机专业应届毕业生，对软件开发感兴趣",
    "core_needs": ["就业指导", "技能提升", "职业规划"],
    "associated_relations": ["大学生", "计算机专业", "应届毕业生"]
  },
  "error": null,
  "execution_time": 0.1
}
```

#### 2.8.2 创建或更新用户画像

**接口**：`POST /api/users/{user_id}/profile`

**描述**：创建或更新用户画像

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 | 示例 |
|-------|------|------|------|------|
| user_id | string | 是 | 用户ID | "user_123456" |
| basic_info | object | 否 | 基本信息 | `{"age": 22, "education": "本科"}` |
| skills | array | 否 | 技能列表 | `["Python", "Java"]` |
| preferences | object | 否 | 偏好设置 | `{"industry": "IT", "location": "北京"}` |
| policy_interest | array | 否 | 政策兴趣 | `["就业政策", "创业政策"]` |
| job_interest | array | 否 | 岗位兴趣 | `["软件工程师", "数据分析师"]` |

**请求示例**：

```json
{
  "basic_info": {
    "age": 22,
    "education": "本科"
  },
  "skills": ["Python", "Java"],
  "preferences": {
    "industry": "IT",
    "location": "北京"
  },
  "policy_interest": ["就业政策", "创业政策"],
  "job_interest": ["软件工程师", "数据分析师"]
}
```

**响应示例**：

```json
{
  "success": true,
  "data": {
    "user_id": "user_123456",
    "description": "计算机专业应届毕业生，对软件开发感兴趣",
    "core_needs": ["就业指导", "技能提升", "职业规划"],
    "associated_relations": ["大学生", "计算机专业", "应届毕业生"]
  },
  "error": null,
  "execution_time": 0.2
}
```

#### 2.8.3 获取个性化推荐

**接口**：`GET /api/users/{user_id}/recommendations`

**描述**：获取针对指定用户的个性化推荐

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 | 示例 |
|-------|------|------|------|------|
| user_id | string | 是 | 用户ID | "user_123456" |

**响应示例**：

```json
{
  "success": true,
  "data": {
    "policies": [
      {
        "id": "policy_001",
        "title": "大学生就业创业扶持政策",
        "category": "就业政策",
        "summary": "为大学生提供就业创业扶持..."
      }
    ],
    "jobs": [
      {
        "id": "job_001",
        "title": "软件工程师",
        "company": "科技公司",
        "salary": "10000-15000",
        "location": "北京"
      }
    ]
  },
  "error": null,
  "execution_time": 0.3
}
```

#### 2.8.4 获取通用推荐

**接口**：`GET /api/recommendations`

**描述**：获取通用的政策和岗位推荐

**请求参数**：无

**响应示例**：

```json
{
  "success": true,
  "data": {
    "policies": [
      {
        "id": "policy_001",
        "title": "大学生就业创业扶持政策",
        "category": "就业政策"
      },
      {
        "id": "policy_002",
        "title": "人才引进补贴政策",
        "category": "人才政策"
      },
      {
        "id": "policy_003",
        "title": "创业贷款贴息政策",
        "category": "创业政策"
      }
    ],
    "jobs": [
      {
        "id": "job_001",
        "title": "软件工程师",
        "company": "科技公司",
        "salary": "10000-15000"
      },
      {
        "id": "job_002",
        "title": "数据分析师",
        "company": "互联网公司",
        "salary": "12000-18000"
      },
      {
        "id": "job_003",
        "title": "产品经理",
        "company": "科技公司",
        "salary": "15000-20000"
      }
    ]
  },
  "error": null,
  "execution_time": 0.2
}
```

### 2.9 批量处理

#### 2.9.1 批量处理API请求

**接口**：`POST /api/batch`

**描述**：批量处理多个API请求，减少网络往返时间

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 | 示例 |
|-------|------|------|------|------|
| requests | array | 是 | 请求列表 | 见下方示例 |

**请求示例**：

```json
{
  "requests": [
    {
      "type": "chat",
      "params": {
        "message": "我想了解大学生就业政策",
        "scenario": "general"
      }
    },
    {
      "type": "policies",
      "params": {}
    },
    {
      "type": "jobs",
      "params": {}
    }
  ]
}
```

**响应示例**：

```json
{
  "results": [
    {
      "intent": {
        "type": "policy_inquiry",
        "keywords": ["大学生", "就业", "政策"]
      },
      "relevant_policies": [...],
      "response": {...},
      "success": true,
      "execution_time": 1.2
    },
    {
      "policies": [...],
      "success": true,
      "execution_time": 0.1
    },
    {
      "jobs": [...],
      "success": true,
      "execution_time": 0.1
    }
  ],
  "total_execution_time": 1.4
}
```

### 2.10 组合数据

#### 2.10.1 获取组合数据

**接口**：`GET /api/combined-data`

**描述**：获取组合数据，减少多次API调用

**请求参数**：

| 参数名 | 类型 | 必填 | 描述 | 示例 |
|-------|------|------|------|------|
| user_id | string | 否 | 用户ID，用于获取个性化推荐 | "user_123456" |

**响应示例**：

```json
{
  "policies": [
    {
      "id": "policy_001",
      "title": "大学生就业创业扶持政策",
      "category": "就业政策",
      "summary": "为大学生提供就业创业扶持..."
    }
  ],
  "jobs": [
    {
      "id": "job_001",
      "title": "软件工程师",
      "company": "科技公司",
      "salary": "10000-15000",
      "location": "北京"
    }
  ],
  "recommendations": {
    "policies": [
      {
        "id": "policy_001",
        "title": "大学生就业创业扶持政策",
        "category": "就业政策"
      }
    ],
    "jobs": [
      {
        "id": "job_001",
        "title": "软件工程师",
        "company": "科技公司",
        "salary": "10000-15000"
      }
    ]
  },
  "execution_time": 0.3
}
```

## 3. 数据模型

### 3.1 请求模型

#### 3.1.1 ChatRequest

```json
{
  "message": "用户消息",
  "scenario": "对话场景",
  "session_id": "会话ID"
}
```

#### 3.1.2 EvaluateRequest

```json
{
  "user_input": "用户输入",
  "response": {"content": "智能体响应"}
}
```

#### 3.1.3 UserProfileRequest

```json
{
  "basic_info": {"age": 22, "education": "本科"},
  "skills": ["Python", "Java"],
  "preferences": {"industry": "IT", "location": "北京"},
  "policy_interest": ["就业政策", "创业政策"],
  "job_interest": ["软件工程师", "数据分析师"]
}
```

#### 3.1.4 BatchRequest

```json
{
  "requests": [
    {
      "type": "chat",
      "params": {"message": "用户消息"}
    }
  ]
}
```

### 3.2 响应模型

#### 3.2.1 OptimizedResponse

```json
{
  "success": true,
  "data": {},
  "error": null,
  "execution_time": 0.5
}
```

#### 3.2.2 BatchResponse

```json
{
  "results": [],
  "total_execution_time": 1.0
}
```

#### 3.2.3 CombinedDataResponse

```json
{
  "policies": [],
  "jobs": [],
  "recommendations": {},
  "execution_time": 0.3
}
```

## 4. 错误处理

| 错误码 | 描述 | 示例 |
|-------|------|------|
| 404 | 资源不存在 | `{"success": false, "error": "Session not found", "execution_time": 0.01}` |
| 500 | 服务器内部错误 | `{"success": false, "error": "处理请求失败", "execution_time": 0.05}` |

## 5. 最佳实践

1. **使用流式API**：对于需要实时反馈的对话场景，推荐使用`/api/chat/stream`端点
2. **批量请求**：对于需要获取多种数据的场景，推荐使用`/api/batch`端点减少网络往返
3. **组合数据**：对于需要同时获取政策、岗位和推荐的场景，推荐使用`/api/combined-data`端点
4. **会话管理**：使用`session_id`保持对话上下文，提高用户体验
5. **性能监控**：定期使用性能监控相关API检查系统状态

## 6. 版本控制

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| 1.0 | 2024-01-01 | 初始版本 |
| 1.1 | 2024-01-15 | 添加性能监控相关API |
| 1.2 | 2024-01-30 | 添加批量处理和组合数据API |

## 7. 示例代码

### 7.1 Python示例

```python
import requests

# 发送聊天请求
response = requests.post('http://localhost:8000/api/chat', json={
    'message': '我想了解大学生就业政策',
    'scenario': 'general'
})
print(response.json())

# 获取政策列表
response = requests.get('http://localhost:8000/api/policies')
print(response.json())

# 获取岗位列表
response = requests.get('http://localhost:8000/api/jobs')
print(response.json())
```

### 7.2 JavaScript示例

```javascript
// 发送聊天请求
fetch('http://localhost:8000/api/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: '我想了解大学生就业政策',
    scenario: 'general'
  })
})
.then(response => response.json())
.then(data => console.log(data));

// 获取政策列表
fetch('http://localhost:8000/api/policies')
.then(response => response.json())
.then(data => console.log(data));

// 获取岗位列表
fetch('http://localhost:8000/api/jobs')
.then(response => response.json())
.then(data => console.log(data));
```

## 8. 总结

政策咨询智能体API提供了丰富的功能，包括对话处理、政策查询、岗位匹配、用户画像管理和性能监控等。通过本文档，开发者可以了解如何使用这些API端点，以及它们的请求参数和响应格式。

API设计遵循RESTful原则，使用统一的响应格式，便于客户端处理。同时，提供了流式响应、批量处理和组合数据等高级功能，以提高API的使用效率和用户体验。

如需进一步了解API的实现细节或有任何问题，请参考项目的源代码或联系开发团队。