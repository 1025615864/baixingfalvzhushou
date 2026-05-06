# AI 三件套必修项修复 — 验收复审报告

---

## 📊 修复验证总览

```
┌──┬─────────────────────────────────────┬──────────┬───────────┐
│  │ 必修项                              │ 修复状态  │ 验证结果   │
├──┼─────────────────────────────────────┼──────────┼───────────┤
│ 1│ AI 服务移除直连 DB → HTTP API       │ ✅ 已实施 │ ⚠️ 有遗留  │
│ 2│ AI + Embedding 鉴权                │ ✅ 已实施 │ ⚠️ 有遗留  │
│ 3│ 知识库/档案库搜索限流               │ ✅ 已实施 │ ⚠️ 有遗留  │
│ 4│ Embedding readiness 检查           │ ✅ 已实施 │ ✅ 通过    │
└──┴─────────────────────────────────────┴──────────┴───────────┘

总评：架构方向正确，但 3 项实施存在细节问题需要补齐。
     预计补齐工作量：1 天
```

---

## ✅ 必修 4：Embedding Readiness — 完全通过

实施质量优秀，无需额外修改。

```
✅ /health/ready 检查模型是否加载
✅ /health/live 基础存活检查
✅ 模型未加载时返回 503
✅ 在 lifespan 中正确设置 model_loaded 标志
```

---

## ⚠️ 必修 1：HTTP 客户端替代直连 — 需要补齐 3 处

### 问题 1-A：AI 服务 .env 中的直连配置未清理

```bash
# ❌ ai-service/.env.example 中可能仍然存在
KNOWLEDGE_DATABASE_URL=postgresql://...
ARCHIVE_DATABASE_URL=postgresql://...

# ✅ 应该替换为
KNOWLEDGE_SERVICE_URL=http://knowledge-service:8081
ARCHIVE_SERVICE_URL=http://archive-service:8082
# 并删除 KNOWLEDGE_DATABASE_URL 和 ARCHIVE_DATABASE_URL
```

```python
# ✅ ai-service/app/config/settings.py 中也需要同步更新
class Settings(BaseSettings):
    # ❌ 删除这两行
    # KNOWLEDGE_DATABASE_URL: str = "..."
    # ARCHIVE_DATABASE_URL: str = "..."

    # ✅ 替换为
    KNOWLEDGE_SERVICE_URL: str = "http://knowledge-service:8081"
    ARCHIVE_SERVICE_URL: str = "http://archive-service:8082"
```

---

### 问题 1-B：rag_retrieval.py 重写后需要确认旧的本地向量调用已完全移除

```python
# 检查项：确保以下旧代码已从 rag_retrieval.py 中移除
# ❌ 不应再有这些引用
# from app.vector_stores.knowledge_store import knowledge_vector_store
# from app.vector_stores.archive_store import archive_vector_store
# 任何直接操作 ChromaDB collection 的代码

# ✅ 新代码应该只通过 HTTP 客户端
# from app.services.knowledge_service_client import KnowledgeServiceClient
# from app.services.archive_service_client import ArchiveServiceClient
```

**动作**：全局搜索 AI 服务中是否还有其他文件直接引用 `KNOWLEDGE_DATABASE_URL` 或本地向量库，确保全部迁移。

---

### 问题 1-C：向量搜索 API 缺少错误处理和超时保护

```python
# 当前 knowledge-service/app/routers/vector_search.py
# 需要确认是否处理了以下场景：

# ✅ 补充：对向量搜索端点添加超时和错误处理

# knowledge-service/app/routers/vector_search.py
@router.post("/vector/search")
async def vector_search(
    request: VectorSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        results = await asyncio.wait_for(
            vector_service.search(
                db=db,
                query=request.query,
                top_k=request.top_k,
                category=request.category,
            ),
            timeout=15.0,  # 向量搜索最多 15 秒
        )
        return {"results": results, "total": len(results)}
    except asyncio.TimeoutError:
        raise HTTPException(504, "向量搜索超时，请缩小检索范围")
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        raise HTTPException(500, "搜索服务暂时不可用")

# ✅ 同时确认 AI 服务客户端也有超时和降级
# ai-service/app/services/knowledge_service_client.py
class KnowledgeServiceClient:
    async def search(self, query: str, top_k: int = 5) -> list[dict]:
        try:
            response = await self._client.post(
                "/api/v1/vector/search",
                json={"query": query, "top_k": top_k},
                timeout=15.0,
            )
            response.raise_for_status()
            return response.json()["results"]
        except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
            logger.warning(f"Knowledge service search failed: {e}")
            return []  # 降级：返回空结果，AI 仍可以基于自身知识回答
```

---

## ⚠️ 必修 2：鉴权实施 — 需要补齐 2 处

### 问题 2-A：AI 服务只做了内部 API Key 鉴权，缺少用户 JWT 鉴权

```
当前实施：
  X-Internal-API-Key → 保护服务间调用 ✅

缺失：
  用户直接调用 AI 对话接口时的 JWT 验证 ❌

  POST /api/v1/ai/chat          ← 用户调用，需要 JWT
  POST /api/v1/ai/chat/stream   ← 用户调用，需要 JWT
  /api/v1/ai/admin/*            ← 管理员调用，需要 JWT + role=admin
  /api/v1/ai-ops/*              ← 运营调用，需要 JWT + role=admin

这两层是不同的：
  ┌─────────┐  JWT Token    ┌──────────┐  X-Internal-API-Key  ┌────────────┐
  │  用户    │─────────────→│  AI 服务  │────────────────────→│ Embedding  │
  │ (浏览器) │              │  (8005)   │                     │  (8006)    │
  └─────────┘              └──────────┘                     └────────────┘
        ↑                       ↑
     需要 JWT               需要两者都有
```

```python
# ✅ 补充：AI 服务的用户鉴权（与 legal-service 模式一致）

# ai-service/app/middleware/jwt_auth.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer(auto_error=False)

class JWTAuth:
    """面向终端用户的 JWT 鉴权"""

    def __init__(self, settings):
        self._secret = settings.JWT_SECRET_KEY
        self._algorithm = settings.JWT_ALGORITHM

    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> dict:
        if not credentials:
            raise HTTPException(401, "未提供认证信息")
        try:
            payload = jwt.decode(
                credentials.credentials,
                self._secret,
                algorithms=[self._algorithm],
            )
            return {
                "user_id": payload["sub"],
                "role": payload.get("role", "user"),
            }
        except jwt.ExpiredSignatureError:
            raise HTTPException(401, "Token 已过期")
        except jwt.InvalidTokenError:
            raise HTTPException(401, "无效 Token")

    async def require_admin(
        self,
        user: dict = Depends(get_current_user),
    ) -> dict:
        if user["role"] not in ("admin", "super_admin"):
            raise HTTPException(403, "需要管理员权限")
        return user

jwt_auth = JWTAuth(settings)

# ✅ 路由中应用
# chat.py
@router.post("/chat")
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(jwt_auth.get_current_user),  # ← 用户必须登录
):
    # Token 用量控制可以正确关联 user_id
    ...

# agent.py
@router.post("/admin/agents/")
async def create_agent(
    data: AgentCreate,
    current_user: dict = Depends(jwt_auth.require_admin),  # ← 需要管理员
):
    ...

# health.py — 不需要鉴权
@router.get("/health")
async def health():  # 无 Depends
    ...
```

```bash
# ✅ ai-service/.env.example 中添加
JWT_SECRET_KEY=your-jwt-secret-key-same-as-user-service
JWT_ALGORITHM=HS256
```

---

### 问题 2-B：Internal API Key 的值需要在所有服务间统一配置

```
当前：每个服务独立配置 INTERNAL_API_KEY
问题：如果 AI 服务的 key 和 Embedding 服务的 key 不一致，调用会 401

✅ 确保 docker-compose.yml 或部署配置中统一
```

```yaml
# docker-compose.yml 示例
x-internal-key: &internal-key
  INTERNAL_API_KEY: ${INTERNAL_API_KEY}  # 从 .env 统一读取

services:
  ai-service:
    environment:
      <<: *internal-key
      KNOWLEDGE_SERVICE_URL: http://knowledge-service:8081
      ARCHIVE_SERVICE_URL: http://archive-service:8082
      EMBEDDING_SERVICE_URL: http://embedding-service:8006

  embedding-service:
    environment:
      <<: *internal-key

  knowledge-service:
    environment:
      <<: *internal-key
      EMBEDDING_SERVICE_URL: http://embedding-service:8006

  archive-service:
    environment:
      <<: *internal-key
      EMBEDDING_SERVICE_URL: http://embedding-service:8006
```

---

## ⚠️ 必修 3：限流实施 — 需要补齐 2 处

### 问题 3-A：限流只加在了 search 路由，重操作未覆盖

```
上轮评审明确要求限流的接口：

  ✅ GET  /api/v1/search              30次/分钟  已添加
  ❌ POST /api/v1/vector/rebuild      1次/小时   未添加 ← 全量重建，非常昂贵
  ❌ POST /api/v1/batch/import        2次/小时   未添加 ← 批量写入
  ❌ GET  /api/v1/batch/export        5次/小时   未添加
  ❌ POST /api/v1/seed                1次/天     未添加
  ❌ POST /api/v1/vector/search       30次/分钟  未添加 ← 新增的向量搜索端点
```

```python
# ✅ 补充：在重操作路由中添加限流

# knowledge-service/app/routers/vector_ops.py
from shared.middleware.rate_limit import SlidingWindowRateLimiter

rate_limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=3600)

@router.post("/vector/rebuild")
async def rebuild_vectors(
    request: Request,
    current_user: dict = Depends(require_admin),  # 需要管理员
):
    client_ip = request.client.host
    user_key = current_user.get("user_id", client_ip)

    if not await rate_limiter.is_allowed(f"vector_rebuild:{user_key}"):
        raise HTTPException(429, "向量重建操作每小时仅允许 1 次")

    # ... 重建逻辑

# knowledge-service/app/routers/batch.py
import_limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=3600)

@router.post("/batch/import")
async def batch_import(
    request: Request,
    current_user: dict = Depends(require_admin),
):
    if not await import_limiter.is_allowed(f"batch_import:{current_user['user_id']}"):
        raise HTTPException(429, "批量导入每小时仅允许 2 次")
    ...

# ✅ 新增的 vector_search.py 也需要限流
vector_search_limiter = SlidingWindowRateLimiter(max_requests=60, window_seconds=60)

@router.post("/vector/search")
async def vector_search(request: Request, ...):
    client_ip = request.client.host
    if not await vector_search_limiter.is_allowed(f"vector_search:{client_ip}"):
        raise HTTPException(429, "搜索请求过于频繁")
    ...
```

---

### 问题 3-B：限流器的 Redis 连接未确认

```python
# 当前 SlidingWindowRateLimiter 是否使用 Redis？
# 如果是内存字典实现 → 多实例部署时限流失效
# 如果是 Redis 实现 → 知识库/档案库服务需要确认 Redis 连接

# ✅ 检查项：
# 1. knowledge-service 和 archive-service 是否已配置 Redis？
# 2. .env.example 中是否有 REDIS_URL？
# 3. 如果没有 Redis，可以先用内存限流（单实例足够），但需要标注

# 如果暂无 Redis，用内存实现 + TODO 标注
class InMemoryRateLimiter:
    """单实例内存限流器 — 多实例部署时需替换为 Redis 实现"""
    # TODO: 多实例部署时需要改为 Redis 后端

    def __init__(self, max_requests: int, window_seconds: int):
        self._max = max_requests
        self._window = window_seconds
        self._requests: dict[str, list[float]] = {}

    async def is_allowed(self, key: str) -> bool:
        now = time.time()
        if key not in self._requests:
            self._requests[key] = []
        # 清除过期记录
        self._requests[key] = [
            t for t in self._requests[key] if now - t < self._window
        ]
        if len(self._requests[key]) >= self._max:
            return False
        self._requests[key].append(now)
        return True
```

---

## 📋 补齐清单

```
┌──┬──────────────────────────────────────────────────┬───────┬───────┐
│  │ 补齐项                                           │ 工作量 │ 状态  │
├──┼──────────────────────────────────────────────────┼───────┼───────┤
│  │ 必修 1 遗留                                      │       │       │
│1A│ 清理 AI 服务 settings 中的 *_DATABASE_URL         │ 10分钟│  ☐   │
│1B│ 全局搜索确认无残留的本地向量库引用                  │ 15分钟│  ☐   │
│1C│ vector_search 端点添加超时 + 客户端添加降级         │ 30分钟│  ☐   │
├──┼──────────────────────────────────────────────────┼───────┼───────┤
│  │ 必修 2 遗留                                      │       │       │
│2A│ AI 服务添加 JWT 鉴权 (chat 需登录, admin 需管理员) │ 2小时 │  ☐   │
│2B│ 确认 docker-compose 中 INTERNAL_API_KEY 统一      │ 10分钟│  ☐   │
├──┼──────────────────────────────────────────────────┼───────┼───────┤
│  │ 必修 3 遗留                                      │       │       │
│3A│ vector/rebuild, batch/import, seed 添加限流       │ 1小时 │  ☐   │
│3B│ 确认限流器 Redis 连接或标注单实例限制               │ 15分钟│  ☐   │
├──┼──────────────────────────────────────────────────┼───────┼───────┤
│  │ 合计                                             │ ~5小时│       │
└──┴──────────────────────────────────────────────────┴───────┴───────┘
```

---

## 🎯 验收结论

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│   当前状态：架构方向 ✅ 正确 / 实施完成度 ~75%                     │
│                                                                  │
│   必修 4 (Embedding readiness)    → ✅ 完全通过，无需修改         │
│   必修 1 (HTTP 替代直连)           → ⚠️ 核心已完成，需补 3 处细节  │
│   必修 2 (鉴权)                    → ⚠️ 内部鉴权已完成，缺用户JWT  │
│   必修 3 (限流)                    → ⚠️ 搜索已限流，重操作未覆盖   │
│                                                                  │
│   ┌───────────────────────────────────────────────────────┐      │
│   │                                                       │      │
│   │   补齐 7 项细节（约 5 小时）后即可正式通过验收          │      │
│   │                                                       │      │
│   │   其中 2A (JWT 鉴权) 是最关键的一项：                  │      │
│   │   没有它，Token 用量控制无法关联到具体用户，             │      │
│   │   且任何人可以不登录直接调用 LLM 接口                   │      │
│   │                                                       │      │
│   └───────────────────────────────────────────────────────┘      │
│                                                                  │
│   完成补齐后，全平台 6 个服务验收状态：                            │
│                                                                  │
│   User Service      ✅ 已验收通过                                 │
│   Legal Service     ✅ 有条件通过（领域隔离+缓存失效+预约超时）      │
│   AI Service        ✅ 补齐后通过                                  │
│   Knowledge Service ✅ 补齐后通过                                  │
│   Archive Service   ✅ 补齐后通过                                  │
│   Embedding Service ✅ 已验收通过                                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```