# AI 服务 (AI Service)

## 服务概览

| 属性 | 值 |
|------|-----|
| 服务名称 | ai-service |
| 端口 | 8005 |
| 基础路径 | /api/v1/ai |
| 技术栈 | FastAPI + SQLAlchemy 2.0 + PostgreSQL + ChromaDB + DeepSeek LLM |
| 数据库 | ai_service |
| 健康检查 | GET /health |
| 就绪检查 | GET /health/ready |

## 服务描述

AI 服务是法律助手的核心智能引擎，提供基于 RAG 的法律对话、Agent 编排、模型路由和流式响应。集成知识库和档案库的向量检索，支持多级 RAG 降级策略（本地向量库 → 远程知识服务 → LLM 兜底）。提供 WebSocket 实时通信、质量运营监控和审计日志等企业级能力。

## API 端点

### AI对话 (chat.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/v1/ai/chat | AI对话（非流式），支持匿名用户 | JWT |
| POST | /api/v1/ai/chat/stream | AI对话（流式SSE），支持匿名用户 | JWT |
| GET | /api/v1/ai/debug/rag | 调试RAG检索结果 | 否 |
| GET | /api/v1/ai/sessions/{user_id} | 获取用户会话列表 | 否 |
| GET | /api/v1/ai/sessions/{session_id}/history | 获取会话历史 | JWT |

### Agent管理 (agent.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /api/v1/ai/admin/agents/ | 获取Agent配置列表 | 否 |
| POST | /api/v1/ai/admin/agents/ | 创建Agent配置（支持版本管理） | 否 |
| PATCH | /api/v1/ai/admin/agents/{agent_id} | 更新Agent配置 | 否 |

### 配置管理 (config.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /api/v1/ai/admin/config/models | 获取LLM模型配置（主模型/降级模型/温度/最大Token） | 否 |
| GET | /api/v1/ai/admin/config/rag | 获取RAG配置（top_k/相似度阈值） | 否 |

### 监控指标 (metrics.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /api/v1/ai/metrics | 获取所有监控指标（LLM/RAG/Agent/Session） | 否 |
| GET | /api/v1/ai/metrics/cache | 获取缓存统计（命中率/大小/淘汰数） | 否 |
| POST | /api/v1/ai/metrics/cache/invalidate | 使缓存失效（可选pattern） | 否 |
| POST | /api/v1/ai/metrics/reset | 重置所有指标 | 否 |
| GET | /api/v1/ai/metrics/config | 获取LLM配置（熔断阈值/超时/Token限制） | 否 |

### 健康检查 (health.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /api/v1/health/ | 获取完整健康状态（向量库/LLM/用户服务/Backend） | 否 |
| GET | /api/v1/health/live | 存活检查 | 否 |
| GET | /api/v1/health/ready | 就绪检查（检查所有依赖） | 否 |
| GET | /api/v1/health/dependencies | 获取依赖服务状态（延迟/健康/消息） | 否 |

### WebSocket (websocket.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| WS | /ws/chat | WebSocket聊天端点，支持实时Agent状态推送 | JWT（Query参数token） |
| WS | /ws/status | WebSocket状态订阅端点 | JWT（Query参数token） |

### AI质量运营 (ai_ops.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/v1/ai-ops/quality/feedback | 提交质量反馈（评分/点赞点踩/问题标签） | 管理员 |
| GET | /api/v1/ai-ops/quality/stats | 获取质量统计（1d/7d/30d） | 否 |
| GET | /api/v1/ai-ops/token/stats | 获取Token消耗统计 | 管理员 |
| GET | /api/v1/ai-ops/cost/stats | 获取成本统计 | 管理员 |
| GET | /api/v1/ai-ops/ai/conversations | 获取对话统计 | 管理员 |
| GET | /api/v1/ai-ops/ai/quality/report | 获取质量报告 | 否 |
| GET | /api/v1/ai-ops/knowledge/gaps | 获取知识缺口分析 | 管理员 |
| GET | /api/v1/ai-ops/vector/status | 获取向量库状态 | 否 |
| GET | /api/v1/ai-ops/analytics/overview | 获取分析概览 | 否 |
| GET | /api/v1/ai-ops/retrieval/hit-rate | 获取检索命中率统计（按小时/天分组） | 管理员 |
| GET | /api/v1/ai-ops/retrieval/distribution | 获取检索级别分布 | 否 |
| GET | /api/v1/ai-ops/retrieval/unmatched | 获取未匹配查询列表 | 管理员 |

### 审计日志运营 (audit_ops.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /api/v1/ai-ops/audit/logs | 查询审计日志（支持多维筛选） | 管理员 |
| GET | /api/v1/ai-ops/audit/export | 导出审计日志（CSV格式） | 否 |
| GET | /api/v1/ai-ops/audit/history/{resource_type}/{resource_id} | 获取资源变更历史 | 管理员 |

## 数据模型

| 模型 | 表名 | 说明 |
|------|------|------|
| AgentConfig | agent_configs | Agent配置，含名称/版本/提示模板/规则/RAG配置 |
| RetrievalLog | retrieval_logs | RAG检索日志，含查询/意图/检索级别/延迟/缓存命中 |
| TokenUsageRecord | token_usage_records | Token消耗记录，含模型/Token数/成本/延迟 |
| ConversationQualityRecord | conversation_quality_records | 对话质量记录，含评分/反馈/问题标签 |

## 关联服务

| 关联服务 | 通信方式 | 说明 |
|----------|----------|------|
| knowledge-service | HTTP | 知识库RAG检索（Level 2降级） |
| archive-service | HTTP | 档案库RAG检索 |
| user-service | HTTP | 用户认证与信息查询 |
| embedding-service | HTTP | 文本向量化服务 |
| backend | HTTP | 前端网关、RAG检索降级 |
| DeepSeek LLM | HTTP | 大语言模型推理（主模型+降级模型） |

## 配置项

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| DATABASE_URL | postgresql+asyncpg://ai_user:password@localhost:5432/ai_service | 数据库连接 |
| OPENAI_API_KEY | (空) | DeepSeek API Key（生产环境必填） |
| OPENAI_BASE_URL | https://api.deepseek.com/v1 | LLM API基础URL |
| LLM_MODEL | deepseek-chat | 主LLM模型 |
| SECONDARY_LLM_MODEL | deepseek-reasoner | 降级LLM模型 |
| SECONDARY_LLM_URL | (空) | 降级LLM地址 |
| SECONDARY_LLM_KEY | (空) | 降级LLM密钥 |
| CIRCUIT_BREAKER_THRESHOLD | 5 | 熔断器失败次数阈值 |
| CIRCUIT_BREAKER_TIMEOUT | 30 | 熔断器超时时间（秒） |
| MAX_TOKENS | 2000 | 最大生成Token数 |
| TEMPERATURE | 0.7 | 生成温度 |
| USER_SERVICE_URL | http://localhost:8001 | 用户服务地址 |
| BACKEND_URL | http://localhost:8000 | Backend地址 |
| LEGAL_SERVICE_URL | http://localhost:8008 | 法律服务地址 |
| KNOWLEDGE_SERVICE_URL | http://localhost:8081 | 知识库服务地址 |
| ARCHIVE_SERVICE_URL | http://localhost:8013 | 档案服务地址 |
| EMBEDDING_SERVICE_URL | http://localhost:8003 | 向量嵌入服务地址 |
| INTERNAL_API_KEY | internal-api-key-change-in-production | 内部API密钥 |
| RAG_LEVEL1_TIMEOUT_MS | 500 | RAG Level 1超时（毫秒） |
| RAG_LEVEL2_TIMEOUT_MS | 2000 | RAG Level 2超时（毫秒） |
| RAG_MIN_SIMILARITY | 0.75 | RAG最低相似度阈值 |
| RAG_TOP_K | 5 | RAG检索返回数量 |
| USE_REMOTE_SESSION | true | 是否使用远程会话存储 |
| ENABLE_KAFKA_PRODUCER | false | 是否启用Kafka生产者 |
| ENABLE_KAFKA_CONSUMER | false | 是否启用Kafka消费者 |
| CONSUL_ENABLED | false | 是否启用Consul服务注册 |
| ENVIRONMENT | development | 运行环境 |

## 部署信息

- Dockerfile: services/ai-service/Dockerfile
- 健康检查: /health
- 资源限制: CPU 1核 / 内存 1GB
