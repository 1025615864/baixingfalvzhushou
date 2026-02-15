# 技术规范

> **版本: v5.1** | **最后更新**: 2026-01-29

## 🎉 项目状态（2026-01-28）

> 项目持续迭代中，已完成安全审计修复和前后端对齐审计，新增漏斗分析管理后台。
> - [TASKS_NEXT.md](../TASKS_NEXT.md) - 当前迭代任务
> - [WORK_STATUS.md](../WORK_STATUS.md) - 项目工作状态

### 完成统计

| 阶段 | 状态 | 进度 |
|------|------|------|
| Phase 0（稳定性） | ✅ 已完成 | 100% |
| Phase 1（体验+可观测） | ✅ 已完成 | 100% |
| Phase 2（垂直场景） | ✅ 已完成 | 100% |
| 业务扩展池 | ✅ 已完成 | 100% |
| 安全审计修复 | ✅ 已完成 | 100% |
| 前后端对齐审计 | 🔄 进行中 | 60% |

### 新增服务模块

| 模块 | 功能 |
|------|------|
| `action_cards.py` | AI 行动卡服务 |
| `list_performance.py` | 列表性能优化服务 |
| `data_security.py` | 数据安全服务 |
| `points.py` | 积分体系服务 |
| `wechat.py` | 微信生态服务 |
| `content_quality.py` | 内容质量评分服务 |
| `funnel_analysis.py` | 用户行为漏斗分析服务 |
| `ab_testing.py` | A/B 测试框架服务 |

---

## 一、技术栈

### 前端

- **框架**：React 19.2.3 + TypeScript 5.6.0
- **构建**：Vite 5.4.0
- **路由**：React Router DOM 7.12.0
- **状态/数据请求**：React Query 5.90.12
- **HTTP 请求**：Axios 1.13.2
- **样式**：TailwindCSS 4.1.18
- **Markdown 渲染**：react-markdown 10.1.0 + remark-gfm 4.0.1
- **E2E 测试**：Playwright 1.57.0
- **错误监控**：Sentry 10.32.1

### 后端

- **框架**：FastAPI 0.109.0+
- **运行**：Uvicorn 0.24.0+
- **数据库**：SQLite（默认，本地开箱即用）/ PostgreSQL（生产推荐）
- **ORM**：SQLAlchemy 2.0.36（async）
- **迁移**：Alembic 1.13.0+
- **认证**：JWT（python-jose 3.3.0）
- **缓存/限流/锁**：Redis 5.0+（生产强依赖；当 `DEBUG=false` 时必须配置且可用，否则启动失败）
- **AI**：OpenAI 1.30.0+（`OPENAI_API_KEY` + `OPENAI_BASE_URL`）
- **RAG/向量库**：LangChain 0.2.0+ + ChromaDB 0.5.0+
- **文档处理**：pypdf 3.17.1、docx2txt 0.8、reportlab 4.0.0+

### 部署

- **本地/演示**：Docker Compose（`docker-compose.yml`）
- **生产示例**：`docker-compose.prod.yml`（含 Redis）
- **K8s**：Helm Chart（`helm/baixing-assistant`）

---

## 二、项目结构

### 仓库根目录

```
.
├── backend/                 # FastAPI 后端
├── frontend/                # React 前端
├── docs/                    # 文档
├── scripts/                 # 冒烟/运维脚本
├── docker-compose.yml
├── docker-compose.prod.yml
└── helm/                    # Helm Chart
```

### 后端结构（backend/app）

```
backend/app/
├── main.py                  # FastAPI 入口；挂载 /api；周期任务
├── config.py                # Pydantic Settings；env 解析与生产校验
├── database.py              # Async SQLAlchemy engine/session；init_db
├── models/                  # SQLAlchemy ORM 模型
├── schemas/                 # Pydantic schema（请求/响应）
├── routers/                 # API 路由（按业务拆分）
├── services/                # 业务服务层
├── middleware/              # 中间件（日志/限流等）
└── utils/                   # 通用工具（鉴权、限流、权限等）
```

### 前端结构（frontend/src）

```
frontend/src/
├── App.tsx                  # 路由表（前台 + /admin）
├── components/              # 组件（含 AdminLayout/Layout 等）
├── pages/                   # 页面
├── contexts/                # Auth/Theme/Language 等
├── hooks/                   # useApi/useToast 等
├── api/                     # axios client
└── tests/e2e/               # Playwright 用例
```

---

## 三、命名规范

| 类型            | 规范                          | 示例                      |
| --------------- | ----------------------------- | ------------------------- |
| React 组件文件  | PascalCase                    | `NewsTopicsPage.tsx`      |
| hooks           | camelCase                     | `useApi.ts`               |
| 后端路由文件    | snake_case / 模块名           | `routers/news.py`         |
| SQLAlchemy 表名 | snake_case（复数）/按模型定义 | `users`、`payment_orders` |
| API 路径        | kebab-case/分层路径           | `/api/news/topics`        |

---

## 三点五、分层开发范式（强制）

### 3.5.1 后端分层职责

- **routers**：仅做参数校验、权限鉴权、调用 services、组装响应。
  - 禁止在路由内定义 BaseModel；统一放在 `backend/app/schemas/`。
  - 禁止在路由内直接写 ORM/SQL 或直连外部 API。
- **services**：业务逻辑与事务编排入口，跨模块协作必须走 services。
  - 统一使用 `AsyncSession`，在服务层控制事务边界。
  - 外部依赖封装为 client/adapter（建议放在 `services/<domain>/clients.py` 或 `services/<domain>/clients/`）。
- **schemas**：请求/响应契约（Pydantic），仅承载结构与校验。
- **models**：ORM 定义与关系，不承载业务逻辑。
- **middleware/utils**：横切能力（日志/限流/RequestId/Envelope）。

### 3.5.2 后端目录规范

- `services/<domain>/` 为业务落点，建议 `core.py` 承载核心流程，其余按职责拆分。
- 单文件建议 < 500 行，超出需拆分并通过 `__init__.py` 聚合导出，保持旧导入路径兼容。
- 新增路由需在 `backend/app/routers/__init__.py` 注册，避免遗漏。
- 新增模型需同步 `backend/app/database.py:init_db()` 的导入列表。

### 3.5.3 前端代码范式

- API 调用统一走 `frontend/src/api/client.ts` 或 `frontend/src/hooks/useApi.ts`。
- 页面与组件层禁止直接 `axios`/`fetch`，统一通过 hooks 或 domains 访问。
- WebSocket 统一走 `frontend/src/hooks/useWebSocket.ts`。
- 组件命名与文件结构保持单一职责，避免“巨型组件”。

## 四、环境变量

> 后端配置定义见 `backend/app/config.py`；示例见 `backend/env.example`。

```env
# backend/.env 示例（开发）
DATABASE_URL=sqlite+aiosqlite:///./data/app.db

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production

# 支付回调密钥（生产 DEBUG=false 必填）
PAYMENT_WEBHOOK_SECRET=your-payment-webhook-secret

# CORS
CORS_ALLOW_ORIGINS=http://localhost:5173,http://localhost:3000
FRONTEND_BASE_URL=http://localhost:5173
TRUSTED_PROXIES=[]

# OpenAI配置（可选，用于AI功能）
OPENAI_API_KEY=your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_TRANSCRIBE_API_KEY=
OPENAI_TRANSCRIBE_BASE_URL=

# AI模型（可选）
AI_MODEL=gpt-4o-mini
AI_FALLBACK_MODELS=gpt-3.5-turbo

# 语音转写配置
VOICE_TRANSCRIBE_PROVIDER=auto
VOICE_TRANSCRIBE_FORCE_ENABLED=false

# Sherpa ASR配置
SHERPA_ASR_ENABLED=false
SHERPA_ASR_MODE=off
SHERPA_ASR_REMOTE_URL=

# Sherpa ONNX本地模型配置
SHERPA_ONNX_TOKENS=/app/data/sherpa_models/tokens.txt
SHERPA_ONNX_WENET_CTC_MODEL=/app/data/sherpa_models/wenet_ctc.zip
SHERPA_ONNX_WHISPER_ENCODER=/app/data/sherpa_models/whisper-encoder.int8.onnx
SHERPA_ONNX_WHISPER_DECODER=/app/data/sherpa_models/whisper-decoder.int8.onnx
SHERPA_ONNX_WHISPER_LANGUAGE=zh
SHERPA_ONNX_WHISPER_TASK=transcribe
SHERPA_ONNX_WHISPER_TAIL_PADDINGS=-1
SHERPA_ONNX_NUM_THREADS=2
SHERPA_ONNX_DECODING_METHOD=greedy_search
SHERPA_ONNX_DEBUG=false
SHERPA_ONNX_SAMPLE_RATE=16000
SHERPA_ONNX_FEATURE_DIM=80

# 商业化/权益（可选）
VIP_DEFAULT_DAYS=30
VIP_DEFAULT_PRICE=29
GUEST_AI_LIMIT=3
GUEST_AI_WINDOW_SECONDS=86400
FREE_AI_CHAT_DAILY_LIMIT=5
VIP_AI_CHAT_DAILY_LIMIT=1000000000
FREE_DOCUMENT_GENERATE_DAILY_LIMIT=10
VIP_DOCUMENT_GENERATE_DAILY_LIMIT=50
GUEST_DOCUMENT_GENERATE_LIMIT=0
GUEST_DOCUMENT_GENERATE_WINDOW_SECONDS=86400

# 律师结算（可选）
SETTLEMENT_WITHDRAW_MAX_AMOUNT=50000

# Redis（生产必需；DEBUG=false 且 Redis 不可用会导致启动失败）
REDIS_URL=

# 上传存储（可选；默认 local）
STORAGE_PROVIDER=local
STORAGE_PUBLIC_BASE_URL=
STORAGE_S3_BUCKET=
STORAGE_S3_ENDPOINT_URL=
STORAGE_S3_REGION=
STORAGE_S3_ACCESS_KEY_ID=
STORAGE_S3_SECRET_ACCESS_KEY=
STORAGE_S3_PREFIX=uploads

# Sentry（可选）
SENTRY_DSN=
SENTRY_ENVIRONMENT=
SENTRY_RELEASE=
SENTRY_TRACES_SAMPLE_RATE=0
SENTRY_PROFILES_SAMPLE_RATE=0

# 调试
DEBUG=true
SQL_ECHO=
```

### 配置约束（生产）

- 当 `DEBUG=false`：
  - `JWT_SECRET_KEY/SECRET_KEY` 必须为安全值（且长度足够）
  - `PAYMENT_WEBHOOK_SECRET` 必须配置
  - `REDIS_URL` 必须配置且 Redis 必须可用（用于限流/分布式锁/周期任务；不可用则启动失败）
  - DB 默认启用 Alembic head 门禁：当 DB schema 未升级到 `head`，启动失败并提示迁移命令；如需临时允许运行时 DDL，可设置 `DB_ALLOW_RUNTIME_DDL=1`（不建议长期使用）
  - 当 `STORAGE_PROVIDER=s3`：
    - `STORAGE_S3_BUCKET` 必须配置
    - `STORAGE_PUBLIC_BASE_URL` 必须配置（用于生成/重定向可访问的文件 URL）

## 四点五、运行模式与门禁矩阵（非常重要）

> 目标：用一张表讲清楚 `DEBUG` / Redis / `DB_ALLOW_RUNTIME_DDL` 对启动、迁移、限流、周期任务的影响，避免误配。

| 场景                                   | Redis 连接       | DB 迁移门禁（Alembic head） | 是否允许运行时 DDL（create_all/补列补索引） | 周期任务/分布式锁                        | 备注               |
| -------------------------------------- | ---------------- | --------------------------- | ------------------------------------------- | ---------------------------------------- | ------------------ |
| `DEBUG=true`（开发/测试口径）          | 可选（不要求）   | 默认不强制（允许绕过）      | 允许（用于本地开箱即用）                    | 允许跑；锁可能退化为进程内（仅适合开发） | 开发体验优先       |
| `DEBUG=false`（生产口径）且 Redis 可用 | 必须可用         | 强制：不在 head 启动失败    | 默认不允许（除非 `DB_ALLOW_RUNTIME_DDL=1`） | 生产正确：Redis 分布式锁避免多副本重复跑 | 生产推荐           |
| `DEBUG=false` 且 Redis 不可用          | 不可用           | 无意义（启动直接失败）      | 无意义                                      | 无意义                                   | 启动失败是设计行为 |
| `DB_ALLOW_RUNTIME_DDL=1`（应急）       | 建议仍提供 Redis | 可绕过 head 门禁            | 允许（应急/兼容）                           | 取决于 Redis                             | 不建议长期使用     |

补充说明：

- `init_db()` 的行为：
  - 当 `DEBUG=false` 且未设置 `DB_ALLOW_RUNTIME_DDL=1`：只做 Alembic head 检查（`backend/app/database.py::_assert_alembic_head`）。
  - 当 `DEBUG=true` 或 `DB_ALLOW_RUNTIME_DDL=1`：会执行 `Base.metadata.create_all()`，并可能做少量 SQLite/PG 兜底 DDL。
- 生产最佳实践：Alembic only + Redis 锁 + PostgreSQL。

进一步阅读：

- `docs/ARCHITECTURE.md`：架构总览与关键不变量。
- `docs/DATABASE.md`：迁移规范与 DB 运维 Runbook（备份/恢复/演练/回滚）。

### 生产环境变量清单（建议）

> 完整字段以 `backend/app/config.py` 为准；以下为生产部署建议最小集/常用集。

- 必填（生产）
  - `DATABASE_URL`（推荐 PostgreSQL）
  - `JWT_SECRET_KEY`（强随机；长度足够）
  - `PAYMENT_WEBHOOK_SECRET`（支付回调签名/鉴权）
  - `FRONTEND_BASE_URL`（用于生成支付回跳/链接）
  - `CORS_ALLOW_ORIGINS`（前端域名白名单）
- AI（如启用 AI 能力）
  - `OPENAI_API_KEY`
  - `OPENAI_BASE_URL`
  - `AI_MODEL`
- Redis（生产必需，`DEBUG=false` 时必须配置且可用）
  - `REDIS_URL`
- 支付渠道（按启用的渠道配置）
  - IKUNPAY：`IKUNPAY_PID` / `IKUNPAY_KEY` / `IKUNPAY_NOTIFY_URL`（可选 `IKUNPAY_RETURN_URL` / `IKUNPAY_GATEWAY_URL`）
  - ALIPAY：`ALIPAY_APP_ID` / `ALIPAY_PUBLIC_KEY` / `ALIPAY_PRIVATE_KEY` / `ALIPAY_NOTIFY_URL`（可选 `ALIPAY_RETURN_URL` / `ALIPAY_GATEWAY_URL`）
  - WECHATPAY：按后端配置项要求（如 `WECHATPAY_*` 系列；若仅保留回调链路也需确保 notify 可达）

### CI / E2E secrets 与生产 secrets 分离

- CI（GitHub Actions）中用于跑回归的密钥应使用 **测试专用 dummy 值**（例如 `JWT_SECRET_KEY=test-secret-key`），不得复用生产密钥。
- 需要访问线上环境的 smoke（例如 `.github/workflows/post-deploy-smoke.yml`）应通过 **GitHub Environments** 的 secrets 管理（如 `production` 环境），并做到：
  - 最小权限 token（只读或仅限 smoke 所需接口）
  - 与生产业务密钥（支付/AI/JWT）严格隔离

---

## 五、API 与鉴权约定

- **Base URL**：后端统一挂载在 `/api`（见 `backend/app/main.py`）。
- **认证方式**：JWT Bearer。

请求头示例：

```http
Authorization: Bearer <token>
```

- **游客与限流**：
  - AI/文书生成等接口对游客按 IP 做限制（并返回 429）。

---

## 六、开发与质量门禁

### 本地启动

- 后端（建议在 `backend/` 目录执行）：
  - `py -m uvicorn app.main:app --reload --port 8000`
- 前端：
  - `npm install`
  - `npm run dev`

### 测试

- 后端：
  - 安装（含测试依赖）：`py -m pip install -r backend/requirements-dev.txt`
  - 运行：`py -m pytest -q`
- 前端：
  - 安装：`npm --prefix frontend ci`
  - 构建：`npm --prefix frontend run build`
- E2E（Playwright，最小文书闭环）：
  - 安装浏览器：`npm --prefix frontend run test:e2e:install`
  - 运行（仅文书用例）：`npm --prefix frontend run test:e2e -- --grep "documents:"`
- CI：GitHub Actions workflow：`.github/workflows/ci.yml`

---

## 七、重要工程约束（必须遵守）

- **Secrets 不入库**：`OPENAI_API_KEY`、`JWT_SECRET_KEY/SECRET_KEY`、`PAYMENT_WEBHOOK_SECRET` 等必须通过环境变量/Secret Manager 注入；系统配置（SystemConfig）禁止写入敏感信息（后端会返回 400）。
- **生产周期任务**：生产多副本部署时使用 Redis 分布式锁，避免任务重复跑。

---

## 八、可观测性与排障（Stage 9）

### 8.1 request_id（端到端追踪）

- 前端会为**每个 API 请求**生成 `X-Request-Id`，并在所有 API 请求中携带。
- 后端会优先使用请求头中的 `X-Request-Id`，并保证响应也带 `X-Request-Id`。
- 后端请求日志/错误日志会以 **JSON 结构化日志**形式输出 `request_id`，用于从前端报错快速定位到具体请求。

常用排查路径：

- 浏览器 DevTools -> Network -> 任意失败请求：
  - 看 Response Headers 中的 `X-Request-Id`
  - 若为 AI 接口错误，响应体也可能包含 `request_id`
- 后端日志中按 `request_id=<id>` 搜索：
  - K8s：`kubectl -n <ns> logs deploy/<release>-baixing-assistant-backend | findstr "\"request_id\":\"<id>\""`
  - Docker：`docker logs <container> | grep '"request_id":"<id>"'`

### 8.2 Prometheus 指标（/metrics）

后端暴露 Prometheus 指标：

- `GET /metrics`

关键指标（用于告警与 Grafana Dashboard）：

- HTTP：
  - `baixing_http_requests_total{method,route,status}`
  - `baixing_http_request_duration_seconds_bucket{method,route,status,le}`（用于 P95 等分位数）
- 周期任务：
  - `baixing_job_runs_total{job}` / `baixing_job_failure_total{job}`
  - `baixing_job_last_run_timestamp_seconds{job}` / `baixing_job_last_success{job}`

常用 PromQL：

- 5xx 比例：
  - `sum(rate(baixing_http_requests_total{status=~"5.."}[5m])) / clamp_min(sum(rate(baixing_http_requests_total[5m])), 1)`
- P95 延迟（全局）：
  - `histogram_quantile(0.95, sum by (le) (rate(baixing_http_request_duration_seconds_bucket[5m])))`
- P95 延迟（按 route 拆分）：
  - `histogram_quantile(0.95, sum by (route, le) (rate(baixing_http_request_duration_seconds_bucket[5m])))`

### 8.3 关键异常上报（可选 webhook）

后端支持将关键异常以 webhook 方式异步上报（默认关闭；上报失败不影响主流程）。

环境变量：

```env
CRITICAL_EVENTS_ENABLED=false
CRITICAL_EVENTS_WEBHOOK_URL=
CRITICAL_EVENTS_WEBHOOK_BEARER=
CRITICAL_EVENTS_WEBHOOK_HEADER_NAME=
CRITICAL_EVENTS_WEBHOOK_HEADER_VALUE=
CRITICAL_EVENTS_MIN_INTERVAL_SECONDS=30
CRITICAL_EVENTS_TIMEOUT_SECONDS=3
```

说明：

- `CRITICAL_EVENTS_ENABLED=true` 且设置 `CRITICAL_EVENTS_WEBHOOK_URL` 后启用。
- 支持两种鉴权方式（二选一即可）：
  - `CRITICAL_EVENTS_WEBHOOK_BEARER`：发送 `Authorization: Bearer ...`
  - `CRITICAL_EVENTS_WEBHOOK_HEADER_NAME/CRITICAL_EVENTS_WEBHOOK_HEADER_VALUE`：自定义 header
- 内置简单去重/限频（`CRITICAL_EVENTS_MIN_INTERVAL_SECONDS`），避免异常风暴刷屏。
- 上报 payload 会包含：`event`、`severity`、`request_id`（如有）、`env`、`data` 等字段。

### 8.4 AI 质量监控（可选）

AI 质量监控系统用于监控 AI 咨询服务的质量指标，包括响应时间、用户评分、错误率等。

#### 8.4.1 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI Quality Monitoring System                 │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Middleware   │    │  API Routes  │    │   Services   │      │
│  ├──────────────┤    ├──────────────┤    ├──────────────┤      │
│  │ AIQuality    │    │ GET /stats   │    │ AIQuality    │      │
│  │ Middleware   │    │ GET /logs    │    │ Metrics      │      │
│  │              │    │ GET /metrics │    │ AILogger     │      │
│  │              │    │ GET /health  │    │ Service      │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

#### 8.4.2 文件结构

```
backend/app/
├── middleware/
│   └── ai_quality_middleware.py    # ⭐ 核心中间件
├── routers/
│   └── ai_quality.py               # ⭐ API接口
└── services/
    └── ai_quality_metrics.py       # (可选)独立指标服务

backend/tests/
└── test_ai_quality_middleware.py   # ⭐ 测试用例
```

#### 8.4.3 核心指标

| 指标 | 说明 | 目标值 |
|------|------|--------|
| `baixing_ai_quality_conversations_total` | 总对话数 | - |
| `baixing_ai_quality_successful_conversations` | 成功对话数 | - |
| `baixing_ai_quality_errors_total` | 错误次数 | - |
| `baixing_ai_quality_response_time_seconds` | 响应时间 | P95 < 3s |
| `baixing_ai_quality_score_avg` | 平均评分 | >= 4.0 |
| `baixing_ai_quality_score_satisfaction_rate` | 满意度(4-5星) | >= 75% |

#### 8.4.4 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/system/ai-quality/stats` | 获取整体统计信息 |
| GET | `/api/system/ai-quality/logs` | 获取最近日志 |
| GET | `/api/system/ai-quality/prometheus` | Prometheus格式指标 |
| GET | `/api/system/ai-quality/dashboard` | 仪表板数据 |
| GET | `/api/system/ai-quality/health` | 健康检查 |
| POST | `/api/system/ai-quality/reset` | 重置统计数据(仅开发) |

#### 8.4.5 使用方式

**注册中间件** (`main.py`)：

```python
from .middleware.ai_quality_middleware import AIQualityMiddleware

app.add_middleware(AIQualityMiddleware)
```

**记录对话** (`routers/ai/chat.py`)：

```python
from ...middleware.ai_quality_middleware import get_ai_logger

ai_logger = get_ai_logger()
ai_logger.log_conversation(
    request_id=request_id,
    session_id=session_id,
    user_id=current_user.id if current_user else None,
    message_length=len(payload.message),
    response_length=len(answer),
    response_time_ms=response_time_ms,
    quality_score=None,  # 稍后通过用户反馈获取
    topics=["劳动法"],
    tools_used=["calculator"],
)
```

**记录反馈** (`routers/ai/analysis.py`)：

```python
ai_logger.log_feedback(
    request_id=request_id,
    is_positive=request.rating >= 2,
    feedback_text=request.feedback,
)
```

#### 8.4.6 生产环境配置

**Redis 持久化**（生产推荐）：

```python
from app.middleware.ai_quality_middleware import get_redis_ai_metrics

async def startup():
    redis = await get_redis_client()
    metrics = await get_redis_ai_metrics(redis)

async def periodic_persist():
    await metrics.persist_all()
```

**Grafana 仪表板**：

导入 `docs/grafana/ai-quality-dashboard.json` 或手动创建面板：

```
- Total Conversations: baixing_ai_quality_conversations_total
- Success Rate: (successful / total) * 100
- P95 Response Time: histogram_quantile(0.95, rate(baixing_ai_quality_response_time_seconds_bucket[5m]))
- Avg Quality Score: baixing_ai_quality_score_avg
- Satisfaction Rate: baixing_ai_quality_score_satisfaction_rate
```

#### 8.4.7 告警规则（建议）

```yaml
groups:
- name: ai-quality-alerts
  rules:
  - alert: AISatisfactionLow
    expr: baixing_ai_quality_score_satisfaction_rate < 75
    for: 1d
    annotations:
      summary: "AI满意度低于75%"

  - alert: AISlowResponse
    expr: histogram_quantile(0.95, rate(baixing_ai_quality_response_time_seconds_bucket[5m])) > 3
    for: 30m
    annotations:
      summary: "AI响应时间P95超过3秒"

  - alert: AIHighErrorRate
    expr: (baixing_ai_quality_errors_total / baixing_ai_quality_conversations_total) > 0.1
    for: 1h
    annotations:
      summary: "AI错误率超过10%"
```

#### 8.4.8 测试

```bash
# 单元测试
py -m pytest tests/test_ai_quality_middleware.py -v

# 负载测试
py -m pytest tests/test_ai_quality_load.py -v
```

相关文档：

- `docs/AI_QUALITY_MONITORING.md` - 详细设计文档
- `docs/API_DESIGN.md` - API接口文档

