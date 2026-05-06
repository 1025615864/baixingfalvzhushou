# AI 服务 / 知识库 / 档案库 — 验收评审报告

---

## 🏆 总评

```
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│   验收结论：  ⚠️ 有条件通过（需修复 4 项必修）                  │
│                                                               │
│   ┌──────────────┬────────┬──────────────────────────┐        │
│   │ 服务         │ 成熟度  │ 评级                     │        │
│   ├──────────────┼────────┼──────────────────────────┤        │
│   │ AI 服务      │  88%   │ 生产可用(有条件)          │        │
│   │ 知识库服务   │  78%   │ 需要修复后上线            │        │
│   │ 档案库服务   │  78%   │ 需要修复后上线            │        │
│   │ Embedding    │  85%   │ 生产可用(有条件)          │        │
│   └──────────────┴────────┴──────────────────────────┘        │
│                                                               │
│   必须修复项：  4 项  （不修复不能上线）                         │
│   建议修复项：  5 项  （上线后 2 周内完成）                      │
│   可延后项：    3 项  （按迭代节奏推进）                         │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## 📊 P0 修复验证（前两轮提出的问题）

| 问题 | 状态 | 验证 |
|------|------|------|
| API Key 硬编码 | ✅ 已修复 | .env.example 中用占位符，BaseSettings 读环境变量 |
| SQLite 生产环境 | ✅ 已修复 | PostgreSQL + asyncpg 连接池 |
| ChromaDB 本地模式 | ✅ 已修复 | pgvector 迁移方案就绪 |
| CORS 全开放 | ✅ 已修复 | CORS_ORIGINS 按环境配置 |
| Embedding 重复加载 | ✅ 已修复 | 独立 Embedding 服务 (8006) |
| LLM 无容错 | ✅ 已修复 | 熔断器 + 重试 + 降级 + 备用 Provider |
| 对话上下文缺失 | ✅ 已修复 | Session 管理 + 上下文管理 |
| Token 用量无控制 | ✅ 已修复 | 用量追踪 + 计费 |
| RAG 质量无评估 | ✅ 已修复 | 检索质量日志 |
| 输入安全防护 | ✅ 已修复 | InputSanitizer + 15 种注入检测 |
| 三服务无鉴权 | ✅ 已修复 | 知识库/档案库写操作需登录 |

**改进率：11/11 全部解决 👏**

---

## 🔴 必须修复（不修复不能上线）— 预计 4 天

### 必修 1：AI 服务直接访问知识库/档案库数据库 — 共享数据库反模式

```
当前状态：
  AI 服务 .env 中同时配置了：
    DATABASE_URL              → AI 自己的库
    KNOWLEDGE_DATABASE_URL    → 直接连知识库的库 ❌
    ARCHIVE_DATABASE_URL      → 直接连档案库的库 ❌

  ┌──────────────┐
  │   AI 服务    │──────→ ai_service DB        ✅ 正常
  │   (8005)     │──────→ knowledge_service DB  ❌ 越权
  │              │──────→ archive_service DB    ❌ 越权
  └──────────────┘

  问题：
  1. 知识库改表结构 → AI 服务直接崩溃（耦合）
  2. 三个服务同时写同一张表 → 锁竞争/数据混乱
  3. 知识库做读写分离/分库 → AI 服务的连接串全部失效
  4. 违反微服务核心原则：每个服务独占自己的数据库
```

```python
# ✅ 改进：AI 服务通过 HTTP API 调用知识库和档案库

# app/clients/knowledge_client.py
class KnowledgeServiceClient:
    """通过 API 访问知识库，不直接连数据库"""

    def __init__(self, base_url: str = "http://knowledge-service:8081"):
        self._client = httpx.AsyncClient(base_url=base_url, timeout=10.0)

    async def search(
        self,
        query: str,
        top_k: int = 5,
        category: str = None,
    ) -> list[dict]:
        params = {"query": query, "top_k": top_k}
        if category:
            params["category"] = category
        response = await self._client.get("/api/v1/search", params=params)
        response.raise_for_status()
        return response.json()["results"]

    async def get_by_id(self, knowledge_id: str) -> dict:
        response = await self._client.get(f"/api/v1/knowledge/{knowledge_id}")
        response.raise_for_status()
        return response.json()

# app/clients/archive_client.py
class ArchiveServiceClient:
    """通过 API 访问档案库"""

    def __init__(self, base_url: str = "http://archive-service:8082"):
        self._client = httpx.AsyncClient(base_url=base_url, timeout=10.0)

    async def search(self, query: str, top_k: int = 5) -> list[dict]:
        response = await self._client.get(
            "/api/v1/search",
            params={"query": query, "top_k": top_k}
        )
        response.raise_for_status()
        return response.json()["results"]

    async def get_recommendations(self, case_id: str) -> list[dict]:
        response = await self._client.get(f"/api/v1/recommendations/{case_id}")
        response.raise_for_status()
        return response.json()

# ✅ RAG 服务改为通过客户端检索
class RAGService:
    def __init__(
        self,
        knowledge_client: KnowledgeServiceClient,
        archive_client: ArchiveServiceClient,
    ):
        self._knowledge = knowledge_client
        self._archive = archive_client

    async def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        """并行检索知识库 + 档案库"""
        knowledge_task = self._knowledge.search(query, top_k)
        archive_task = self._archive.search(query, top_k)

        knowledge_results, archive_results = await asyncio.gather(
            knowledge_task, archive_task,
            return_exceptions=True,
        )

        results = []
        if not isinstance(knowledge_results, Exception):
            results.extend([
                {**r, "source": "knowledge"} for r in knowledge_results
            ])
        else:
            logger.warning(f"Knowledge search failed: {knowledge_results}")

        if not isinstance(archive_results, Exception):
            results.extend([
                {**r, "source": "archive"} for r in archive_results
            ])
        else:
            logger.warning(f"Archive search failed: {archive_results}")

        # 按相似度混合排序
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return results[:top_k]

# ✅ .env 中移除
# ❌ KNOWLEDGE_DATABASE_URL=...  删除
# ❌ ARCHIVE_DATABASE_URL=...    删除
# ✅ KNOWLEDGE_SERVICE_URL=http://knowledge-service:8081  新增
# ✅ ARCHIVE_SERVICE_URL=http://archive-service:8082      新增

# 工作量：1.5天
```

---

### 必修 2：AI 服务缺少 JWT 鉴权 — 任何人可调用 LLM

```
当前状态：
              AI服务   知识库   档案库   Embedding
  JWT验证       -       ✅      ✅        -

  AI 服务的 chat 接口没有鉴权：
    POST /api/v1/ai/chat          ← 任何人可调用
    POST /api/v1/ai/chat/stream   ← 任何人可调用
    /api/v1/ai/admin/*            ← 管理接口也无鉴权？

  后果：
  1. 攻击者直接调用 chat 接口 → 你的 DeepSeek 额度被盗刷
  2. Token 用量控制形同虚设 → 不知道是谁在调用
  3. 管理接口裸奔 → Agent 配置可被随意修改
```

```python
# ✅ 改进：AI 服务添加鉴权

# app/middleware/auth.py（复用其他服务的鉴权模式）
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

class AuthService:
    """JWT Token 验证（通过 user-service 公钥）"""

    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> dict:
        token = credentials.credentials
        try:
            # 方案 A：本地验证（RS256 公钥）
            payload = jwt.decode(token, self._public_key, algorithms=["RS256"])
            return {
                "user_id": payload["sub"],
                "role": payload.get("role", "user"),
            }
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="无效 Token")

    async def require_admin(
        self, user: dict = Depends(get_current_user)
    ) -> dict:
        if user["role"] not in ("admin", "super_admin"):
            raise HTTPException(status_code=403, detail="需要管理员权限")
        return user

auth = AuthService()

# ✅ 路由应用鉴权
# chat.py — 普通用户需登录
@router.post("/chat")
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(auth.get_current_user),  # ← 必须登录
):
    # Token 用量控制现在能正确识别 user_id 了
    await usage_service.check_and_consume(
        user_id=current_user["user_id"],
        user_role=current_user["role"],
        ...
    )

# agent.py — 管理接口需要 admin
@router.post("/admin/agents/")
async def create_agent(
    data: AgentCreate,
    current_user: dict = Depends(auth.require_admin),  # ← 需要管理员
):
    ...

# config.py — 配置管理需要 admin
@router.put("/admin/config/{key}")
async def update_config(
    current_user: dict = Depends(auth.require_admin),
):
    ...

# health.py — 健康检查不需要鉴权
@router.get("/health")  # 无 Depends，公开访问
async def health_check():
    ...

# ✅ Embedding 服务也需要保护（至少内部 Token）
# embedding-service 应该只允许内部服务调用
# 方案：API Key 验证
@app.middleware("http")
async def verify_internal_token(request: Request, call_next):
    if request.url.path in ("/health", "/docs", "/openapi.json"):
        return await call_next(request)
    token = request.headers.get("X-Internal-Token")
    if token != settings.INTERNAL_API_TOKEN:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    return await call_next(request)

# 工作量：1天
```

---

### 必修 3：知识库和档案库搜索接口缺少限流 — 向量搜索很昂贵

```
当前状态：
  知识库 GET /api/v1/search       ← 无限流
  档案库 GET /api/v1/search       ← 无限流
  知识库 POST /api/v1/vector/rebuild  ← 无限流

  问题：
  1. 每次向量搜索需要 embedding 计算 → 占用 Embedding 服务资源
  2. vector/rebuild 是全量重建 → 分钟级重操作，被频繁调用会拖垮服务
  3. 批量导入接口无限流 → 可以一次导入百万条数据
```

```python
# ✅ 改进：为知识库和档案库添加限流

# 两个服务都需要添加（以知识库为例）

# app/middleware/rate_limit.py
from fastapi import Request, HTTPException
from redis import asyncio as aioredis

class RateLimiter:
    LIMITS = {
        # (路径前缀, 方法): (次数, 时间窗口秒)
        ("/api/v1/search", "GET"):           (30, 60),    # 搜索：每分钟30次
        ("/api/v1/knowledge", "POST"):       (20, 60),    # 创建：每分钟20次
        ("/api/v1/batch/import", "POST"):    (2, 3600),   # 批量导入：每小时2次
        ("/api/v1/batch/export", "GET"):     (5, 3600),   # 批量导出：每小时5次
        ("/api/v1/vector/rebuild", "POST"):  (1, 3600),   # 向量重建：每小时1次 ⚠️
        ("/api/v1/seed", "POST"):            (1, 86400),  # 种子数据：每天1次
    }

    def __init__(self, redis: aioredis.Redis):
        self._redis = redis

    async def check(self, request: Request, user_id: str) -> bool:
        path = request.url.path
        method = request.method

        for (prefix, m), (limit, window) in self.LIMITS.items():
            if path.startswith(prefix) and method == m:
                key = f"rate:{prefix}:{user_id}"
                count = await self._redis.incr(key)
                if count == 1:
                    await self._redis.expire(key, window)
                if count > limit:
                    raise HTTPException(
                        status_code=429,
                        detail=f"请求过于频繁，请 {window}秒 后再试"
                    )
                return True
        return True

# 工作量：0.5天（两个服务各做一份）
```

---

### 必修 4：Embedding 服务无健康检查依赖 — 模型未加载也报健康

```
当前状态：
  Embedding 服务 (8006) 启动时加载 text2vec-base-chinese 模型
  模型加载需要 10-30 秒（取决于是否首次下载）

  如果 /health 在模型加载完成前就返回 healthy：
  → Consul 认为服务可用 → 其他服务开始调用 → 返回 500 错误
  → 知识库搜索全部失败 → 档案库搜索全部失败 → AI RAG 全部失败
```

```python
# ✅ 改进：区分 liveness 和 readiness

# embedding-service/app/main.py
model_loaded = False
model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, model_loaded
    logger.info("Loading embedding model...")
    model = SentenceTransformer("shibing624/text2vec-base-chinese")
    model_loaded = True
    logger.info("Embedding model loaded ✅")
    yield
    logger.info("Embedding service shutting down")

# 存活检查 — 进程活着就返回 OK
@app.get("/health/live")
async def liveness():
    return {"status": "alive"}

# 就绪检查 — 模型加载完才返回 OK
@app.get("/health/ready")
async def readiness():
    if not model_loaded:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded yet"
        )
    # 验证模型确实能工作
    try:
        test_result = model.encode(["测试"])
        if len(test_result[0]) != 768:
            raise ValueError("Unexpected embedding dimension")
    except Exception as e:
        raise HTTPException(503, detail=f"Model unhealthy: {e}")
    return {"status": "ready", "model": "text2vec-base-chinese", "dimensions": 768}

# ✅ Consul 注册时使用 readiness 检查
# consul_config:
#   health_check_url: "http://embedding-service:8006/health/ready"
#   health_check_interval: "10s"

# ✅ 其他服务调用 Embedding 时也需要处理未就绪情况
class EmbeddingClient:
    async def encode(self, texts: list[str]) -> list[list[float]]:
        try:
            response = await self._client.post("/api/v1/embeddings", json={"texts": texts})
            response.raise_for_status()
            return response.json()["embeddings"]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 503:
                logger.warning("Embedding service not ready, using fallback")
                return self._fallback_encode(texts)  # 降级方案
            raise

    def _fallback_encode(self, texts: list[str]) -> list[list[float]]:
        """降级：返回零向量，搜索退化为关键词搜索"""
        return [[0.0] * 768 for _ in texts]

# 工作量：0.5天
```

---

## 🟡 建议修复（上线后 2 周内完成）

### 建议 1：知识库和档案库仍未合并 — 维护成本翻倍

```
上轮审查已指出两个服务 90% 重复：

  知识库 (8081)                   档案库 (8082)
  ├── knowledge.py (CRUD)         ├── archive.py (CRUD)        ← 相同模式
  ├── categories.py               ├── case_categories.py       ← 相同模式
  ├── search.py                   ├── search.py                ← 几乎相同
  ├── batch.py                    ├── batch.py                 ← 几乎相同
  ├── vector_ops.py               ├── vector_ops.py            ← 完全相同
  ├── stats.py                    ├── stats.py                 ← 相同模式
  └── seed.py                     └── recommendations.py       ← 唯一差异

  不阻塞上线，但维护时：
  - 修一个 bug 需要改两个服务
  - 加一个功能需要实现两遍
  - 升级依赖需要改两个 requirements.txt

建议：上线后 1 个月内合并为统一的 knowledge-service，
     通过 collection_type 字段区分法律知识和案例档案。

工作量：5天
```

---

### 建议 2：AI 服务 requirements.txt 依赖过重

```
当前依赖链（部分）：

  langgraph      → 引入整个 LangChain 生态
  langchain      → 引入大量传递依赖
  chromadb       → 是否还需要？已经有 pgvector 了
  sentence-transformers → 如果用了 Embedding 服务，本地还需要吗？

  问题：
  1. Docker 镜像体积膨胀（可能 2-3GB）
  2. 构建时间长
  3. 依赖冲突风险高
  4. 安全漏洞扫描告警多
```

```python
# ✅ 建议清理

# 确认是否可移除：
# chromadb           → 如果已全面切换到 pgvector，可移除
# sentence-transformers → 如果已使用 Embedding 服务(8006)，本地不需要
# langchain          → 评估是否只用了少量功能，可替换为直接 openai 调用

# 最小化 requirements.txt：
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
sqlalchemy[asyncio]>=2.0.25
asyncpg>=0.29.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
aiokafka>=0.10.0
httpx>=0.26.0
openai>=1.10.0           # 直接调用 LLM，不需要 langchain 封装
redis>=5.0.0
pgvector>=0.2.4          # 替代 chromadb
langgraph>=0.1.0         # 如果 Agent 流程确实需要，保留
# ❌ chromadb           # 移除
# ❌ sentence-transformers  # 移除（已有 Embedding 服务）
# ❌ langchain          # 评估后决定

# 工作量：1天（需要逐个验证哪些依赖可安全移除）
```

---

### 建议 3：三服务缺少优雅关闭

```
当前状态：
  AI 服务     → lifespan 中是否有完整的关闭流程？未确认
  知识库     → 未见 lifespan 关闭逻辑
  档案库     → 未见 lifespan 关闭逻辑

  知识库/档案库需要关闭的资源：
  1. 数据库连接池
  2. Kafka Producer
  3. Consul 注销
  4. OTEL Provider flush
```

```python
# ✅ 以知识库为例（档案库同理）

# app/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动
    logger.info("Knowledge service starting...")
    await init_db()
    await init_kafka_producer()
    await register_consul()
    logger.info("Knowledge service started ✅")

    yield

    # 关闭（按依赖逆序）
    logger.info("Knowledge service shutting down...")
    await deregister_consul()           # 1. 停止接收流量
    await kafka_producer.flush()        # 2. 发送剩余事件
    await kafka_producer.stop()
    await engine.dispose()              # 3. 关闭数据库
    logger.info("Knowledge service stopped ✅")

# 工作量：0.5天（三个服务）
```

---

### 建议 4：知识库/档案库搜索缺少分页

```
当前：
  GET /api/v1/search?query=劳动合同

  返回全部结果？还是固定 top_k？
  如果用户需要翻页查看更多结果呢？
```

```python
# ✅ 搜索接口添加分页（与 legal-service 统一格式）

@router.get("/search")
async def search(
    query: str = Query(..., min_length=1, max_length=500),
    page: int = Query(1, ge=1, le=100),
    page_size: int = Query(10, ge=1, le=50),
    category: Optional[str] = Query(None),
    search_mode: str = Query("hybrid", pattern="^(keyword|semantic|hybrid)$"),
):
    results, total = await search_service.search(
        query=query,
        offset=(page - 1) * page_size,
        limit=page_size,
        category=category,
        mode=search_mode,
    )
    return {
        "items": results,
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": page * page_size < total,
    }

# 工作量：1天（两个服务）
```

---

### 建议 5：AI 服务 WebSocket 缺少鉴权和心跳

```
当前：
  /ws  → WebSocket 连接

  问题：
  1. WebSocket 连接时是否验证 Token？
  2. 客户端断线后连接是否超时释放？
  3. 是否有并发连接数限制？
```

```python
# ✅ WebSocket 安全加固

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),          # Token 通过 query 参数传递
):
    # 1. 鉴权
    try:
        user = await auth.validate_token(token)
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    # 2. 并发连接限制
    user_id = user["user_id"]
    conn_key = f"ws_conn:{user_id}"
    current_conns = int(await redis.get(conn_key) or 0)
    max_conns = 3  # 每用户最多 3 个 WebSocket 连接
    if current_conns >= max_conns:
        await websocket.close(code=4002, reason="Too many connections")
        return

    await redis.incr(conn_key)
    await redis.expire(conn_key, 3600)
    await websocket.accept()

    try:
        while True:
            # 3. 心跳超时（60 秒无消息自动断开）
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=60.0,
                )
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})
                try:
                    pong = await asyncio.wait_for(
                        websocket.receive_text(), timeout=10.0
                    )
                except asyncio.TimeoutError:
                    break  # 客户端无响应，断开

            # 处理消息...
            if data:
                await handle_message(websocket, user, data)

    except WebSocketDisconnect:
        pass
    finally:
        await redis.decr(conn_key)

# 工作量：1天
```

---

## 🔵 可延后项（按迭代推进）

| 项 | 说明 | 建议时间 |
|---|------|---------|
| 知识库/档案库合并 | 两服务 90% 重复 | 上线后 1 个月 |
| AI 服务 gRPC 接口 | 其他服务目前通过 Kafka/HTTP 调用 | 第二季度 |
| 知识库/档案库 Outbox | 当前 Kafka 直发，无可靠性保障 | 按需 |

---

## 📋 验收前必做清单

```
┌──┬──────────────────────────────────────────────┬───────┬──────┐
│  │ 事项                                         │ 工作量 │ 状态 │
├──┼──────────────────────────────────────────────┼───────┼──────┤
│ 1│ AI 服务移除直连知识库/档案库 DB，改用 HTTP API  │ 1.5天 │  ☐  │
│ 2│ AI 服务 + Embedding 服务添加鉴权               │ 1天   │  ☐  │
│ 3│ 知识库/档案库搜索+重操作添加限流               │ 0.5天 │  ☐  │
│ 4│ Embedding 服务 readiness 检查（模型就绪判断）   │ 0.5天 │  ☐  │
├──┼──────────────────────────────────────────────┼───────┼──────┤
│  │ 合计                                         │ 3.5天 │      │
└──┴──────────────────────────────────────────────┴───────┴──────┘
```

---

## 🆚 全平台 5+1 服务对比（最终版）

| 维度 | User | Legal | AI | Knowledge | Archive | Embedding |
|------|------|-------|-----|-----------|---------|-----------|
| **成熟度** | 90% | 95% | 88% | 78% | 78% | 85% |
| **鉴权** | ✅ 强 | ✅ 强 | ❌ 缺失 | ✅ 写操作 | ✅ 写操作 | ❌ 缺失 |
| **限流** | ✅ | ✅ 分级 | ✅ | ❌ 缺失 | ❌ 缺失 | — |
| **事务管理** | ✅ | ✅ TxMgr | ✅ | ⚠️ 基础 | ⚠️ 基础 | — |
| **事件驱动** | ⚠️ 可选 | ✅ Outbox | ✅ 消费 | ✅ 生产 | ✅ 生产 | — |
| **容错** | ✅ | ✅ 锁+重试 | ✅ 熔断 | ⚠️ 基础 | ⚠️ 基础 | ⚠️ |
| **可观测性** | ⚠️ | ✅ 完整 | ✅ 完整 | ✅ OTEL | ✅ OTEL | ⚠️ |
| **优雅关闭** | ✅ | ✅ 完整 | ⚠️ | ❌ | ❌ | ⚠️ |
| **测试** | ✅ 6文件 | ✅ 8文件 | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| **文档** | ⚠️ | ✅ 完整 | ⚠️ | ⚠️ | ⚠️ | ⚠️ |

---

## 🎯 最终结论

```
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│  修复 4 项必修内容（3.5 天）后，AI 三件套可以正式验收上线。     │
│                                                               │
│  核心风险排序：                                                │
│                                                               │
│  1. 🔴 AI 服务直连其他服务数据库（架构耦合）    ← 最危险       │
│  2. 🔴 AI 服务/Embedding 无鉴权（安全漏洞）    ← 必须修       │
│  3. 🔴 搜索/重建接口无限流（可被打垮）         ← 必须修       │
│  4. 🔴 Embedding 就绪检查（启动阶段故障）      ← 必须修       │
│                                                               │
│  完成后全平台 6 个服务均达到生产就绪标准。                      │
│                                                               │
│  全平台总工作量：                                              │
│  Legal Service 必修：2.5天  （已提出）                          │
│  AI 三件套必修：    3.5天  （本轮提出）                         │
│  合计：            6 天 → 可在 1 周内全部完成上线               │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```