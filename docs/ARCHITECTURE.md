# 百姓助手技术架构文档

## 1. 系统架构概览

### 1.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              客户端层 (Clients)                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐│
│  │   Web浏览器      │  │   移动端 H5      │  │      小程序 (微信)          ││
│  │  (React + TS)   │  │   (React + TS)   │  │                            ││
│  └────────┬────────┘  └────────┬────────┘  └──────────────┬──────────────┘│
└───────────┼─────────────────────┼─────────────────────────┼───────────────┘
            │                     │                         │
            ▼                     ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              接入层 (API Gateway)                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  Nginx 反向代理 + 负载均衡                                               ││
│  │  • SSL/TLS 终端                                                          ││
│  │  • 静态资源服务 (前端构建产物)                                           ││
│  │  • 流量分发与健康检查                                                    ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└───────────┬─────────────────────┬─────────────────────────┬───────────────┘
            │                     │                         │
            ▼                     ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              应用层 (Application Layer)                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                    FastAPI + Uvicorn (ASGI Server)                       ││
│  │  ┌─────────────────────────────────────────────────────────────────────┐││
│  │  │                         中间件系统                                  │││
│  │  │  • 请求/响应日志  • 认证授权  • CSRF保护  • 速率限制               │││
│  │  │  • 指标采集      • 安全头    • 审计日志  • Sentry上下文            │││
│  │  │  • AI质量监控    • 请求追踪  • 响应封装  • CORS跨域               │││
│  │  └─────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────┘│
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐│
│  │   用户模块    │ │   律师模块    │ │   咨询模块    │ │    知识库模块        ││
│  │  • 注册/登录  │ │  • 律师认证   │ │  • AI咨询    │ │    • RAG检索        ││
│  │  • JWT认证    │ │  • 律所管理   │ │  • 预约咨询  │ │    • 向量存储       ││
│  │  • TOTP 2FA  │ │  • 推广管理   │ │  • 合同审查  │ │    • 知识管理       ││
│  │  • 积分系统   │ │  • 评价系统   │ │  • 语音转写 │ │    • 法规查询        ││
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────────────┘│
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐│
│  │   支付模块    │ │   论坛模块    │ │   资讯模块    │ │    通知模块          ││
│  │  • 支付宝    │ │  • 发帖/回帖  │ │  • AI新闻    │ │    • 站内信          ││
│  │  • 微信支付  │ │  • 点赞/收藏  │ │  • 订阅管理  │ │    • 邮件通知        ││
│  │  • IkunPay   │ │  • 版主管理   │ │  • 推荐系统  │ │    • 短信通知        ││
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────────────┘│
└───────────┬─────────────────────┬─────────────────────────┬───────────────┘
            │                     │                         │
            ▼                     ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              数据层 (Data Layer)                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐│
│  │  PostgreSQL   │ │    Redis     │ │  ChromaDB   │ │    对象存储          ││
│  │  • 主数据库   │ │  • 缓存层    │ │  • 向量存储 │ │    • S3/MinIO        ││
│  │  • 异步ORM    │ │  • 会话存储  │ │  • 知识向量 │ │    • 文件存储        ││
│  │  • Alembic迁移│ │  • 限流计数  │ │             │ │    • 图片/文档       ││
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
            │                     │                         │
            ▼                     ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              外部服务 (External Services)                    │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐│
│  │   OpenAI     │ │  支付宝/微信   │ │    SendGrid  │ │    阿里云OSS         ││
│  │  (LLM API)   │ │   支付网关     │ │   (邮件)      │ │    (对象存储)        ││
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 分层架构

| 层次 | 职责 | 技术栈 |
|------|------|--------|
| **接入层** | 请求路由、负载均衡、SSL终端、静态资源服务 | Nginx |
| **应用层** | 业务逻辑处理、API路由、中间件处理、认证授权 | FastAPI + Uvicorn |
| **数据层** | 数据持久化、缓存、向量存储、文件存储 | PostgreSQL + Redis + ChromaDB + S3 |
| **外部服务** | 第三方API调用、AI模型、支付网关、通知服务 | OpenAI + 支付宝/微信 + SendGrid |

---

## 2. 后端架构

### 2.1 Web框架

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| Web框架 | [FastAPI](backend/app/main.py:1) | 现代高性能异步Web框架 |
| ASGI服务器 | Uvicorn | ASGI实现，支持HTTP/WebSocket |
| RESTful API | Pydantic v2 | 数据验证和序列化 |
| API文档 | Swagger UI + ReDoc | 自动生成API文档 |

### 2.2 数据库

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| ORM | [SQLAlchemy 2.0](backend/requirements.txt:7) | 异步ORM，支持Core和ORM双模式 |
| 主数据库 | PostgreSQL 15+ | 关系型数据库，支持JSON类型 |
| 数据库驱动 | asyncpg | 异步PostgreSQL驱动 |
| 数据库迁移 | Alembic | 版本控制和迁移管理 |
| 开发数据库 | SQLite (aiosqlite) | 本地开发环境使用 |

**数据库配置示例：**
```python
# backend/app/database/engine.py
DATABASE_URL = "postgresql+asyncpg://user:pass@host:5432/baixing"
```

### 2.3 缓存系统

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 缓存 | Redis 7+ | 内存键值存储，支持集群模式 |
| 缓存策略 | 多级缓存 | 本地缓存(Cachetools) + Redis分布式缓存 |
| 会话存储 | Redis | JWT token + refresh token存储 |
| 限流计数 | Redis | 滑动窗口算法实现API限流 |

### 2.4 认证系统

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| JWT算法 | RS256 + HS256 双算法 | 支持RSA签名和HMAC签名 |
| Token管理 | [token_rotation.py](backend/app/core/token_rotation.py:1) | Access Token + Refresh Token轮换 |
| 双因素认证 | TOTP (pyotp) | 基于时间的一次性密码 |
| 密码哈希 | passlib | BCrypt加密 |
| CSRF保护 | [csrf_middleware.py](backend/app/middleware/csrf_middleware.py:1) | CSRF Token验证 |

### 2.5 中间件系统

| 中间件 | 文件位置 | 功能说明 |
|--------|----------|----------|
| ErrorLoggingMiddleware | [logging_middleware.py](backend/app/middleware/logging_middleware.py:1) | 统一错误日志记录 |
| RequestLoggingMiddleware | [logging_middleware.py](backend/app/middleware/logging_middleware.py:1) | 请求/响应日志 |
| CORSMiddleware | FastAPI内置 | 跨域资源共享 |
| RateLimitMiddleware | [rate_limit.py](backend/app/middleware/rate_limit.py:1) | API限流 (120req/min, 20req/sec) |
| MetricsMiddleware | [metrics_middleware.py](backend/app/middleware/metrics_middleware.py:1) | Prometheus指标采集 |
| EnvelopeMiddleware | [envelope_middleware.py](backend/app/middleware/envelope_middleware.py:1) | 统一响应封装 |
| SecurityHeadersMiddleware | [security_headers.py](backend/app/core/middleware/security_headers.py:1) | HTTP安全响应头 |
| CSRF Middleware | [csrf_middleware.py](backend/app/middleware/csrf_middleware.py:1) | CSRF攻击防护 |
| SentryContextMiddleware | [sentry_context_middleware.py](backend/app/middleware/sentry_context_middleware.py:1) | Sentry上下文注入 |
| AuthContextMiddleware | [auth_context_middleware.py](backend/app/middleware/auth_context_middleware.py:1) | 用户认证上下文 |
| AuditMiddleware | [audit_middleware.py](backend/app/middleware/audit_middleware.py:1) | 操作审计日志 |
| RequestIdMiddleware | [request_id_middleware.py](backend/app/middleware/request_id_middleware.py:1) | 请求追踪ID |
| TracingMiddleware | [request_id_middleware.py](backend/app/middleware/request_id_middleware.py:1) | 分布式追踪 |
| AIQualityMiddleware | [ai_quality_middleware.py](backend/app/middleware/ai_quality_middleware.py:1) | AI响应质量监控 |

---

## 3. 前端架构

### 3.1 框架与构建

| 组件 | 技术选型 | 版本 |
|------|----------|------|
| 框架 | React | 18.2.0 |
| 语言 | TypeScript | 5.3.3 |
| 构建工具 | Vite | 5.0.8 |
| 包管理 | npm | 9.0.0+ |

### 3.2 状态管理

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 全局状态 | [Zustand](frontend-v2/package.json:40) | 轻量级状态管理 |
| 服务端状态 | TanStack React Query | 异步数据获取和缓存 |
| 表单状态 | React Hook Form | 表单验证和管理 |
| 不可变更新 | Immer | 简化不可变数据操作 |

### 3.3 UI组件库

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 组件库 | Ant Design | 5.21.3，企业级UI组件库 |
| 样式框架 | Tailwind CSS | 3.4.0，原子化CSS |
| 动画 | Framer Motion | 12.34.0，声明式动画 |
| 图表 | Recharts | 3.7.0，数据可视化 |
| 图标 | Lucide React | 460.0，SVG图标库 |

### 3.4 路由

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 路由 | React Router DOM | 6.20.0 |
| 路由策略 | 懒加载 | React.lazy() + Suspense |
| 路由守卫 | 自定义Hook | 认证状态检查 |

**前端目录结构：**
```
frontend-v2/src/
├── app/                    # 应用入口
│   ├── App.tsx            # 根组件
│   └── styles/            # 全局样式
├── components/            # 通用UI组件
│   └── ui/                # 基础UI组件 (Badge, Card, Form...)
├── features/              # 功能模块 (按领域组织)
│   ├── faq/              # 常见问题
│   ├── news/             # 新闻资讯
│   ├── notification/     # 通知中心
│   ├── search/           # 搜索
│   ├── security/         # 安全设置
│   ├── points/           # 积分系统
│   ├── promotion/        # 推广中心
│   ├── enterprise/       # 企业服务
│   ├── settlement/       # 结算
│   ├── payment/          # 支付
│   ├── post/             # 帖子
│   ├── forum/            # 论坛
│   ├── legal-document-mall/ # 法律文书商城
│   ├── video-consultation/ # 视频咨询
│   ├── vertical-channel/ # 垂直频道
│   ├── static-pages/     # 静态页面
│   └── membership/       # 会员中心
├── pages/                # 页面组件
│   ├── Chat/            # AI咨询
│   ├── Home/            # 首页
│   ├── Lawyer/          # 律师服务
│   ├── News/            # 新闻
│   ├── Payment/         # 支付
│   ├── Profile/         # 个人中心
│   ├── Knowledge/       # 知识库
│   ├── ContractReviewPage/ # 合同审查
│   └── auth/            # 登录注册
├── shared/               # 共享资源
│   ├── hooks/           # 自定义Hooks
│   ├── lib/             # 工具库 (API, logger, prefetch)
│   ├── store/           # 状态管理
│   ├── components/      # 共享组件 (VirtualList, Loading)
│   └── utils/           # 通用工具
├── test/                 # 测试配置与工具
└── types/                # TypeScript 类型定义
```

---

## 4. AI 架构

### 4.1 大语言模型集成

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| LLM框架 | LangChain | 0.2.0+，模块化LLM编排 |
| OpenAI客户端 | langchain-openai | OpenAI API封装 |
| Embeddings | OpenAI Text Embedding | 文本向量化 |
| AI客户端 | openai | 1.30.0+ |

### 4.2 向量知识库

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 向量数据库 | ChromaDB | 0.5.0+，轻量级向量数据库 |
| 文本分割 | langchain-text-splitters | 文档分块 |
| Tokenizer | tiktoken | OpenAI tokenizer |

### 4.3 RAG知识库系统

```
用户查询 → 向量化 → ChromaDB检索 → 上下文增强 → LLM生成 → 响应返回
```

| 服务 | 文件位置 | 功能 |
|------|----------|------|
| 知识服务 | [knowledge_service.py](backend/app/services/knowledge_service.py:1) | 知识管理 |
| RAG检索 | [rag_knowledge.py](backend/app/services/rag_knowledge.py:1) | RAG流程实现 |
| AI配置 | [config_manager.py](backend/app/services/ai/config_manager.py:1) | 模型配置管理 |
| Prompt管理 | [prompts.py](backend/app/services/ai/prompts.py:1) | Prompt模板 |

---

## 5. 支付架构

### 5.1 支付通道

| 通道 | 文件位置 | 说明 |
|------|----------|------|
| 支付宝 | [alipay.py](backend/app/services/payment/alipay.py:1) | 支付宝开放平台 |
| 微信支付 | [wechatpay.py](backend/app/services/payment/wechatpay.py:1) | 微信支付V3 |
| IkunPay | 内部支付通道 | 平台自有支付 |

### 5.2 支付回调处理

| 组件 | 文件位置 | 功能 |
|------|----------|------|
| 回调路由 | [callbacks.py](backend/app/routers/payment/callbacks.py:1) | 支付回调处理 |
| 支付服务 | [payment_service.py](backend/app/services/payment_service.py:1) | 支付核心逻辑 |
| 幂等中间件 | [payment_idempotency.py](backend/app/core/middleware/payment_idempotency.py:1) | 防止重复扣款 |

### 5.3 支付安全保障

| 机制 | 文件位置 | 说明 |
|------|----------|------|
| 支付锁 | [payment_lock.py](backend/app/utils/payment_lock.py:1) | 分布式支付锁 |
| 支付安全 | [payment_security.py](backend/app/utils/payment_security.py:1) | 签名验证 |
| 加密工具 | [crypto_utils.py](backend/app/routers/payment/crypto_utils.py:1) | 加密解密 |

---

## 6. 监控与运维

### 6.1 指标采集

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 指标库 | Prometheus Client | 0.19.0+ |
| 指标配置 | [metrics_config.py](backend/app/core/metrics_config.py:1) | 自定义指标定义 |
| 数据库监控 | [db_pool.py](backend/app/core/monitoring/db_pool.py:1) | 连接池监控 |
| 查询监控 | [query_monitor.py](backend/app/core/monitoring/query_monitor.py:1) | 慢查询追踪 |

**Prometheus指标类型：**
- Counter：请求计数
- Histogram：请求延迟分布
- Gauge：当前连接数
- Summary：自定义摘要

### 6.2 告警系统

| 组件 | 配置文件 | 说明 |
|------|----------|------|
| Alertmanager | [alertmanager.yml](alertmanager/alertmanager.yml:1) | 告警聚合与路由 |
| 告警规则 | [prometheus-rules.yaml](helm/baixing-assistant/templates/prometheus-rules.yaml:1) | K8s部署配置 |

**告警项：**
- 服务不可用 (5xx错误)
- 响应延迟 > 2s
- 数据库连接池耗尽
- 支付失败率 > 5%
- CPU/Memory使用率 > 80%

### 6.3 错误追踪

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 错误追踪 | Sentry SDK | 2.0.0+ |
| Sentry配置 | [sentry_config.py](backend/app/core/sentry_config.py:1) | Sentry初始化 |
| 上下文注入 | [sentry_context_middleware.py](backend/app/middleware/sentry_context_middleware.py:1) | 用户/请求上下文 |

### 6.4 日志系统

| 组件 | 文件位置 | 说明 |
|------|----------|------|
| 日志配置 | [logging_config.py](backend/app/utils/logging_config.py:1) | 结构化日志 |
| 日志分析 | [log_analyzer.py](backend/app/utils/log_analyzer.py:1) | 日志分析工具 |
| 敏感信息过滤 | [log_sanitizer.py](backend/app/middleware/log_sanitizer.py:1) | PII脱敏 |

---

## 7. CI/CD 流程

### 7.1 GitHub Actions 工作流

| 工作流 | 触发条件 | 说明 |
|--------|----------|------|
| [CI](../.github/workflows/ci.yml) | push/pr | 主流水线 (CI + 测试 + 类型检查) |
| [Code Quality](../.github/workflows/code-quality.yml) | push/pr | 代码质量 + 安全扫描 |
| [Release](../.github/workflows/release.yml) | tag | 版本发布 |
| [Pact](../.github/workflows/pact.yml) | push | 契约测试 |

**CI/CD流程阶段：**
```
1. 前端代码检查 (Lint + Type Check)
2. 前端构建测试
3. 后端代码检查 (Black + isort + Ruff)
4. 后端测试 (pytest + coverage)
5. 安全扫描 (Trivy)
6. Docker构建测试
7. 部署到测试环境 (develop分支)
8. 部署到生产环境 (main分支)
```

### 7.2 容器化部署

| 镜像 | Dockerfile | 说明 |
|------|------------|------|
| 后端镜像 | [backend/Dockerfile](backend/Dockerfile:1) | Python 3.11 + 安全加固 |
| 前端镜像 | frontend-v2/Dockerfile | Node 20 + Nginx |

**Docker特性：**
- 非root用户运行 (appuser:appgroup)
- 多阶段构建优化体积
- 镜像安全扫描 (Trivy)
- 健康检查配置

### 7.3 K8s部署

| 组件 | 配置位置 | 说明 |
|------|----------|------|
| Helm Chart | [helm/baixing-assistant](helm/baixing-assistant:1) | K8s部署配置 |
| 后端Deployment | [backend-deployment.yaml](helm/baixing-assistant/templates/backend-deployment.yaml:1) | 后端Pod配置 |
| 前端Deployment | [frontend-deployment.yaml](helm/baixing-assistant/templates/frontend-deployment.yaml:1) | 前端Pod配置 |
| Ingress | [ingress.yaml](helm/baixing-assistant/templates/ingress.yaml:1) | 路由配置 |
| 配置管理 | External Secrets | 敏感信息管理 |

---

## 8. 目录结构说明

### 8.1 后端目录结构

```
backend/
├── app/                        # 应用主目录
│   ├── main.py                 # FastAPI应用入口
│   ├── config/                 # 配置管理
│   │   ├── settings.py         # 应用配置
│   │   └── tasks.py            # 异步任务配置
│   ├── core/                   # 核心模块
│   │   ├── error_handler.py    # 错误处理
│   │   ├── exceptions.py       # 自定义异常
│   │   ├── metrics.py          # 指标定义
│   │   ├── middleware_config.py# 中间件配置
│   │   └── health.py           # 健康检查
│   ├── database/               # 数据库层
│   │   ├── engine.py           # 数据库引擎
│   │   ├── session.py          # 会话管理
│   │   ├── migrations.py        # 迁移管理
│   │   └── seeding.py          # 数据初始化
│   ├── models/                 # SQLAlchemy模型
│   │   ├── user.py             # 用户模型
│   │   ├── payment.py          # 支付模型
│   │   └── ...                 # 其他领域模型
│   ├── routers/                # API路由
│   │   ├── user.py             # 用户API
│   │   ├── payment/            # 支付模块API
│   │   ├── ai/                 # AI模块API
│   │   └── ...                 # 其他业务API
│   ├── schemas/                # Pydantic模型
│   │   ├── user.py             # 用户Schema
│   │   └── ...                 # 其他Schema
│   ├── services/               # 业务服务层
│   │   ├── user_service.py     # 用户服务
│   │   ├── payment_service.py  # 支付服务
│   │   ├── ai/                 # AI服务
│   │   └── ...                 # 其他服务
│   ├── middleware/             # 自定义中间件
│   │   ├── auth_context.py     # 认证上下文
│   │   ├── rate_limit.py       # 限流
│   │   └── ...                 # 其他中间件
│   └── utils/                  # 工具函数
│       ├── security.py         # 安全工具
│       ├── validators.py       # 验证器
│       └── ...                  # 其他工具
├── alembic/                     # 数据库迁移
│   └── versions/               # 迁移脚本
├── tests/                       # 测试目录
│   ├── conftest.py              # pytest配置
│   ├── test_*.py               # 单元测试
│   └── e2e/                    # 端到端测试
├── scripts/                     # 运维脚本
├── requirements.txt             # 生产依赖
├── requirements-dev.txt        # 开发依赖
├── Dockerfile                   # 生产镜像
├── Dockerfile.dev              # 开发镜像
└── Makefile                    # 构建命令
```

### 8.2 配置文件说明

| 文件 | 说明 |
|------|------|
| `.env.example` | 环境变量模板 |
| `.env.prod` | 生产环境配置 |
| `.env.docker` | Docker环境配置 |
| `.env.jwt.example` | JWT配置示例 |
| `alembic.ini` | 数据库迁移配置 |
| `pyrightconfig.json` | Python类型检查配置 |
| `pytest.ini` | 测试配置 |
| `.pre-commit-config.yaml` | Git钩子配置 |
| `.bandit` | 安全扫描配置 |
| `.trivyignore` | 漏洞扫描忽略列表 |

### 8.3 监控配置

| 目录/文件 | 说明 |
|-----------|------|
| `prometheus/` | Prometheus配置 |
| `grafana/` | Grafana仪表板配置 |
| `alertmanager/` | Alertmanager配置 |

---

## 附录

### A. 技术栈总览

| 层级 | 技术 |
|------|------|
| **前端** | React 18 + TypeScript + Vite + Zustand + TanStack Query + Ant Design + Tailwind CSS |
| **后端** | FastAPI + Uvicorn + SQLAlchemy 2.0 + PostgreSQL + Redis + Alembic |
| **AI** | LangChain + OpenAI + ChromaDB |
| **支付** | 支付宝 + 微信支付 + IkunPay |
| **监控** | Prometheus + Alertmanager + Sentry + Grafana |
| **部署** | Docker + Docker Compose + Kubernetes (Helm) |
| **CI/CD** | GitHub Actions |

### B. API版本策略

- 当前版本：`/api/v1/`
- 版本控制：URL路径方式
- 向后兼容：渐进式废弃旧版本

### C. 安全措施

- JWT双算法支持 (RS256/HS256)
- TOTP双因素认证
- CSRF保护
- API限流
- 请求签名验证
- 敏感数据加密存储
- SQL注入防护
- XSS防护
- 安全响应头

---

## 12. 微服务架构

### 12.1 架构概览

项目采用渐进式微服务拆分策略，11个微服务已从单体应用中拆分为独立服务。

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端 (3000)                              │
│  vite.config.ts 配置了 15 个服务的代理                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway / Nginx                           │
│                      /api/v1/*                                   │
└─────────────────────────────────────────────────────────────────┘
    │           │           │           │           │
    ▼           ▼           ▼           ▼           ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ Backend│ │ User   │ │Payment │ │Embed-  │ │ Order  │
│  BFF   │ │Service │ │Channel │ │ding    │ │Service │
│ 8000   │ │ 8001   │ │ 8002   │ │ 8003   │ │ 8004   │
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘
    │           │           │           │
    ▼           ▼           ▼           ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│  AI    │ │ News   │ │Community│ │ Legal  │ │Search  │
│Service │ │Service │ │Service │ │Service │ │Service │
│ 8005   │ │ 8006   │ │ 8007   │ │ 8008   │ │ 8009   │
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘
    │           │           │           │
    ▼           ▼           ▼           ▼
┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
│Recommen-   │ │Notification│ │  Points    │ │  Archive   │
│dation Svc  │ │  Service   │ │  Service   │ │  Service   │
│   8010     │ │   8011     │ │   8012     │ │   8013     │
└────────────┘ └────────────┘ └────────────┘ └────────────┘
                                │
                                ▼
                          ┌────────────┐
                          │ Knowledge  │
                          │  Service   │
                          │   8081     │
                          └────────────┘
```

### 12.2 服务列表

| 服务 | 端口 | 前缀 | 说明 | 详细文档 |
|------|------|------|------|----------|
| Backend (BFF) | 8000 | /api/v1 | BFF 聚合层 | [backend-bff.md](services/backend-bff.md) |
| User Service | 8001 | /api/v1/users | 用户、认证、会员 | [user-service.md](services/user-service.md) |
| Payment Channel | 8002 | /api/v1/payment | 支付渠道 | [payment-channel-service.md](services/payment-channel-service.md) |
| Embedding Service | 8003 | /api/v1/embeddings | 向量嵌入 | [embedding-service.md](services/embedding-service.md) |
| Order Service | 8004 | /api/v1/orders | 订单管理 | [order-service.md](services/order-service.md) |
| AI Service | 8005 | /api/v1/ai | AI 对话 | [ai-service.md](services/ai-service.md) |
| News Service | 8006 | /api/v1/news | 新闻资讯 | [news-service.md](services/news-service.md) |
| Community Service | 8007 | /api/v1/community | 社区论坛 | [community-service.md](services/community-service.md) |
| Legal Service | 8008 | /api/v1/legal | 律师、法律知识 | [legal-service.md](services/legal-service.md) |
| Search Service | 8009 | /api/v1/search | 搜索服务 | [search-service.md](services/search-service.md) |
| Recommendation Service | 8010 | /api/v1/recommendations | 推荐服务 | [recommendation-service.md](services/recommendation-service.md) |
| Notification Service | 8011 | /api/v1/notifications | 通知服务 | [notification-service.md](services/notification-service.md) |
| Points Service | 8012 | /api/v1/points | 积分系统 | [points-service.md](services/points-service.md) |
| Archive Service | 8013 | /api/v1/archives | 档案服务 | [archive-service.md](services/archive-service.md) |
| Knowledge Service | 8081 | /api/v1/knowledge | 知识库 | [knowledge-service.md](services/knowledge-service.md) |
| Frontend | 3000 | / | 前端应用 | [frontend.md](services/frontend.md) |

### 12.3 前端代理配置

前端通过 `vite.config.ts` 配置开发环境代理:

```typescript
proxy: {
  '/api/v1/auth': { target: 'http://127.0.0.1:8001' },
  '/api/v1/users': { target: 'http://127.0.0.1:8001' },
  '/api/v1/payment': { target: 'http://127.0.0.1:8002' },
  '/api/v1/embeddings': { target: 'http://127.0.0.1:8003' },
  '/api/v1/orders': { target: 'http://127.0.0.1:8004' },
  '/api/v1/ai': { target: 'http://127.0.0.1:8005' },
  '/api/v1/news': { target: 'http://127.0.0.1:8006' },
  '/api/v1/community': { target: 'http://127.0.0.1:8007' },
  '/api/v1/legal': { target: 'http://127.0.0.1:8008' },
  '/api/v1/search': { target: 'http://127.0.0.1:8009' },
  '/api/v1/recommendations': { target: 'http://127.0.0.1:8010' },
  '/api/v1/notifications': { target: 'http://127.0.0.1:8011' },
  '/api/v1/points': { target: 'http://127.0.0.1:8012' },
  '/api/v1/archives': { target: 'http://127.0.0.1:8013' },
  '/api/v1/knowledge': { target: 'http://127.0.0.1:8081' },
}
```

### 12.4 启动服务

```bash
# Docker Compose 启动所有服务
docker compose up -d

# 单独启动某个服务
docker compose up -d --build user-service

# 启动后端
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000

# 启动所有微服务 (每个终端一个)
cd services/user-service && uvicorn app.main:app --port 8001
cd services/payment-channel-service && uvicorn app.main:app --port 8002
cd services/embedding-service && uvicorn app.main:app --port 8003
cd services/order-service && uvicorn app.main:app --port 8004
cd services/ai-service && uvicorn app.main:app --port 8005
cd services/news-service && uvicorn app.main:app --port 8006
cd services/community-service && uvicorn app.main:app --port 8007
cd services/legal-service && uvicorn app.main:app --port 8008
cd services/search-service && uvicorn app.main:app --port 8009
cd services/recommendation-service && uvicorn app.main:app --port 8010
cd services/notification-service && uvicorn app.main:app --port 8011
cd services/points-service && uvicorn app.main:app --port 8012
cd services/archive-service && uvicorn app.main:app --port 8013
cd services/knowledge-service && uvicorn app.main:app --port 8081

# 运行联调测试
bash scripts/test-microservices.sh
```

### 12.5 数据迁移

使用迁移脚本将数据从主数据库同步到微服务数据库:

```bash
python -m scripts.migrations.migrate_to_microservices --service user
python -m scripts.migrations.migrate_to_microservices --service news
python -m scripts.migrations.migrate_to_microservices --service community
python -m scripts.migrations.migrate_to_microservices --service notification
```

---

## 13. API Gateway (APISIX)

### 13.1 架构概览

```
客户端 → APISIX Gateway → 各微服务
         │
         ├── JWT 认证
         ├── 限流熔断
         ├── 日志审计
         └── 监控指标
```

### 13.2 APISIX 配置

| 功能 | 插件 | 说明 |
|------|------|------|
| 认证 | jwt-auth | JWT Token 验证 |
| 限流 | limit-req, limit-count | 滑动窗口限流 |
| 熔断 | api-breaker, circuit-breaker | 故障自动熔断 |
| 日志 | log-rotate | 日志滚动 |
| 监控 | prometheus | 指标导出 |

详细配置见: [APISIX 配置](../apisix/config.yaml)

---

## 14. 服务间通信 (gRPC + Kafka)

### 14.1 通信模式

| 模式 | 协议 | 场景 |
|------|------|------|
| 同步调用 | gRPC (HTTP/2) | 实时查询、低延迟场景 |
| 异步事件 | Kafka | 解耦、事件驱动场景 |

### 14.2 gRPC 服务

| 服务 | 端口 | 用途 |
|------|------|------|
| gRPC Gateway | 50051 | gRPC HTTP 网关 |

### 14.3 Kafka Topic

| Topic | 说明 | 消费者 |
|-------|------|--------|
| baixing.user.events | 用户事件 | Notification, Points |
| baixing.payment.events | 支付事件 | Order, Points |
| baixing.legal.events | 法律事件 | Notification |

详细设计见: [服务通信规范](./service-communication-spec.md)

---

## 15. 分布式事务 (SAGA)

### 15.1 SAGA 模式

适用于跨多个服务的业务操作，确保最终一致性。

**典型场景**: 下单 → 支付 → 积分 → 库存

### 15.2 可靠消息

适用于异步通知场景，确保消息可靠投递。

详细设计见: [DISTRIBUTED_TRANSACTION_DESIGN.md](DISTRIBUTED_TRANSACTION_DESIGN.md)

---

## 16. 契约测试 (Pact)

### 16.1 消费者驱动契约测试

```
UserService (Consumer) → Pact Broker ← LegalService (Provider)
```

### 16.2 集成 CI/CD

| 环境 | 触发条件 | 验证 |
|------|----------|------|
| 开发 | PR | 本地 Pact |
| 测试 | Merge | Broker 验证 |
| 生产 | 部署前 | can-i-deploy |

详细设计见: [CONTRACT_TESTING_DESIGN.md](CONTRACT_TESTING_DESIGN.md)

---

*文档最后更新：2026-05-11*