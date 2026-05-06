# AI 服务 / 知识库服务 / 档案库服务 — 深度架构审查

---

## 📊 三服务总览

```
┌──────────────────┐  ┌───────────────────┐  ┌──────────────────┐
│  知识库 (8081)   │  │   档案库 (8082)   │  │   AI服务 (8005)  │
│                  │  │                   │  │                  │
│ PostgreSQL       │  │ PostgreSQL        │  │ SQLite ⚠️        │
│ ChromaDB(本地)   │  │ ChromaDB(本地)    │  │ Redis + Kafka    │
│ text2vec-base    │  │ text2vec-base     │  │ DeepSeek LLM     │
│ Consul+OTEL      │  │ Consul+OTEL       │  │ OTEL             │
│                  │  │                   │  │                  │
│ ~15 端点         │  │ ~15 端点          │  │ ~20 端点         │
└──────────────────┘  └───────────────────┘  └──────────────────┘
```

---

## 🔴 严重问题（建议立即修复）

### 1. 🚨 API Key 硬编码在配置中 — 最高级安全事故

```python
# ❌ 当前 ai-service/app/config/settings.py
OPENAI_API_KEY = "sk-8661a3e7cb08429a88b1f70fdb1ae580"

# 这意味着：
# 1. 推送到 Git 仓库后，所有有仓库访问权限的人都能看到
# 2. 如果仓库公开，任何人都能盗用你的 DeepSeek 额度
# 3. Git 历史中永远保留，即使后续删除也能通过 git log 找回
# 4. 违反几乎所有安全合规标准（ISO 27001 / SOC2 / 等保）
```

```python
# ✅ 第一步：立即轮换密钥（当前密钥视为已泄露）
# 登录 DeepSeek 控制台 → 重新生成 API Key → 废弃旧密钥

# ✅ 第二步：使用环境变量 + 密钥管理
# ai-service/app/config/settings.py
class Settings(BaseSettings):
    OPENAI_API_KEY: str = Field(
        ...,                          # 必填，无默认值
        description="DeepSeek API Key",
    )
    OPENAI_BASE_URL: str = "https://api.deepseek.com/v1"

    model_config = SettingsConfigDict(
        env_file=".env",              # 从 .env 文件读取
        env_file_encoding="utf-8",
    )

# ✅ 第三步：确保 .env 不被提交
# .gitignore 中添加
.env
*.env
.env.*

# ✅ 第四步：清除 Git 历史中的密钥
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch services/ai-service/app/config/settings.py" \
  --prune-empty --tag-name-filter cat -- --all

# ✅ 第五步（生产环境）：使用密钥管理服务
# 方案 A: HashiCorp Vault
# 方案 B: 云厂商 KMS（阿里云 KMS / AWS Secrets Manager）
# 方案 C: Kubernetes Secrets（最低要求）
```

---

### 2. AI 服务使用 SQLite — 生产环境致命

```python
# ❌ 当前
DATABASE_URL = "sqlite+aiosqlite:///./ai_service.db"

# 致命问题：
# 1. SQLite 不支持并发写入 — 多用户同时对话会锁死
# 2. 单文件存储 — 容器重启数据全丢（除非挂载 volume）
# 3. 无法多实例部署 — 每个容器有自己的 .db 文件
# 4. 无连接池管理 — 高并发下性能断崖式下降
# 5. 不支持 JSONB/Array 等高级类型 — 限制数据建模
```

```python
# ✅ 改进：统一使用 PostgreSQL

# ai-service/app/config/settings.py
class Settings(BaseSettings):
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://ai_user:password@localhost:5432/ai_service",
        description="AI服务数据库连接"
    )
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 3600

# ai-service/app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,                    # 自动检测断连
    echo=settings.DEBUG,
)

async_session = async_sessionmaker(engine, expire_on_commit=False)

# requirements.txt 中替换
# ❌ aiosqlite
# ✅ asyncpg>=0.29.0
```

---

### 3. ChromaDB 本地嵌入式运行 — 无法水平扩展

```
❌ 当前架构：

  知识库实例1          知识库实例2
  ┌─────────────┐    ┌─────────────┐
  │ FastAPI      │    │ FastAPI      │
  │ ChromaDB     │    │ ChromaDB     │
  │ /data/chroma │    │ /data/chroma │  ← 两份独立数据！
  │ text2vec模型 │    │ text2vec模型 │  ← 两份模型内存！
  └─────────────┘    └─────────────┘

  问题：
  1. 每个实例加载独立的向量库 → 数据不一致
  2. 每个实例加载 text2vec 模型 → 内存翻倍（约 400MB/实例）
  3. 实例 1 写入的向量，实例 2 看不到
  4. 容器重启向量全丢（除非持久化 volume）
  5. 知识库和档案库各自独立的 ChromaDB → 重复基础设施
```

```
✅ 改进方案（按复杂度递增）：

方案 A：PostgreSQL pgvector（推荐 — 最小改动）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  所有实例 ────────→ PostgreSQL + pgvector 扩展
                     ┌──────────────────────┐
                     │ legal_knowledge      │
                     │ ├── content TEXT      │
                     │ ├── embedding vector  │ ← pgvector
                     │ └── metadata JSONB   │
                     │                      │
                     │ legal_cases          │
                     │ ├── content TEXT      │
                     │ ├── embedding vector  │
                     │ └── metadata JSONB   │
                     └──────────────────────┘

  优势：复用现有 PostgreSQL，无新依赖
  劣势：超大规模（>1000万向量）时性能不如专用向量库
```

```python
# ✅ pgvector 实现示例

# 安装扩展（PostgreSQL 中执行一次）
# CREATE EXTENSION vector;

# models/knowledge.py
from pgvector.sqlalchemy import Vector

class LegalKnowledge(Base):
    __tablename__ = "legal_knowledge"

    id = Column(UUID, primary_key=True, default=uuid4)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    category_id = Column(UUID, ForeignKey("knowledge_categories.id"))
    embedding = Column(Vector(768), nullable=True)   # text2vec-base 输出 768 维
    metadata_ = Column(JSONB, default={})
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # 创建 IVFFlat 索引加速检索
    __table_args__ = (
        Index(
            "ix_knowledge_embedding",
            embedding,
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"}
        ),
    )

# services/vector_service.py
class VectorService:
    def __init__(self, embedding_model):
        self._model = embedding_model

    async def search(
        self,
        db: AsyncSession,
        query: str,
        top_k: int = 5,
        category_id: str = None,
    ) -> list[dict]:
        # 生成查询向量
        query_embedding = self._model.encode(query)

        # 向量相似度搜索 + 元数据过滤
        stmt = (
            select(
                LegalKnowledge,
                LegalKnowledge.embedding.cosine_distance(query_embedding).label("distance")
            )
            .order_by("distance")
            .limit(top_k)
        )
        if category_id:
            stmt = stmt.where(LegalKnowledge.category_id == category_id)

        results = (await db.execute(stmt)).all()
        return [
            {
                "id": str(row.LegalKnowledge.id),
                "title": row.LegalKnowledge.title,
                "content": row.LegalKnowledge.content,
                "score": 1 - row.distance,  # 转换为相似度
            }
            for row in results
        ]

# requirements.txt
# ❌ chromadb>=0.4.0         (移除)
# ✅ pgvector>=0.2.4         (新增)
```

```
方案 B：ChromaDB Server 模式（中等改动）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  知识库/档案库 ────→ ChromaDB Server（独立部署）
                      ┌──────────────────┐
                      │  ChromaDB Server │
                      │  :8000           │
                      │  持久化存储       │
                      └──────────────────┘

  docker-compose.yml:
    chroma:
      image: chromadb/chroma:latest
      ports: ["8000:8000"]
      volumes: ["chroma_data:/chroma/chroma"]
```

```
方案 C：Milvus / Qdrant（大规模推荐）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  适合 >100万向量的场景，暂不需要
```

---

### 4. Embedding 模型每个服务各加载一份 — 内存浪费

```
❌ 当前：

  知识库服务 → 加载 text2vec-base-chinese (~400MB 内存)
  档案库服务 → 加载 text2vec-base-chinese (~400MB 内存)
  AI服务     → 可能也需要加载
  
  总计：~1.2GB 内存仅用于重复的 embedding 模型
```

```python
# ✅ 方案一：提取为独立的 Embedding Service（推荐）

# embedding-service/app/main.py
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI

app = FastAPI(title="Embedding Service")
model = None

@app.on_event("startup")
async def load_model():
    global model
    model = SentenceTransformer("shibing624/text2vec-base-chinese")

@app.post("/api/v1/embeddings")
async def create_embeddings(request: EmbeddingRequest):
    """统一的向量化接口"""
    vectors = model.encode(
        request.texts,
        batch_size=32,
        normalize_embeddings=True,
    )
    return {
        "embeddings": vectors.tolist(),
        "model": "text2vec-base-chinese",
        "dimensions": 768,
    }

@app.post("/api/v1/embeddings/search")
async def semantic_search(request: SearchRequest):
    """语义搜索"""
    query_vec = model.encode([request.query], normalize_embeddings=True)
    return {"embedding": query_vec[0].tolist()}

# docker-compose.yml
embedding-service:
    build: ./services/embedding-service
    ports: ["8090:8090"]
    deploy:
      resources:
        limits:
          memory: 1G       # 集中分配内存
        reservations:
          memory: 512M
```

```python
# ✅ 知识库/档案库改为调用 Embedding Service

# knowledge-service/app/clients/embedding_client.py
class EmbeddingClient:
    def __init__(self, base_url: str = "http://embedding-service:8090"):
        self._client = httpx.AsyncClient(base_url=base_url, timeout=10.0)

    async def encode(self, texts: list[str]) -> list[list[float]]:
        response = await self._client.post(
            "/api/v1/embeddings",
            json={"texts": texts}
        )
        response.raise_for_status()
        return response.json()["embeddings"]

    async def encode_single(self, text: str) -> list[float]:
        results = await self.encode([text])
        return results[0]
```

```python
# ✅ 方案二（更简单）：如果用 pgvector，在写入时计算一次 embedding 存库
# 查询时只计算查询文本的 embedding（单次计算，开销很小）
# 可以在每个服务中保留轻量的模型加载，但只用于查询
```

---

### 5. CORS 全开放 — 安全漏洞

```python
# ❌ 当前：三个服务都是
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # 任何域名都能调用！
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 风险：
# 1. 任何网站都能通过浏览器直接调用你的 API
# 2. allow_credentials=True + allow_origins=["*"] 是浏览器安全模型的大忌
# 3. 恶意网站可以利用用户的登录态调用你的 API（CSRF 变种）
```

```python
# ✅ 改进：按环境配置 CORS

# config/settings.py
class Settings(BaseSettings):
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000"],  # 开发环境只允许前端
        description="允许的跨域来源"
    )
    ENVIRONMENT: str = "development"

# main.py
if settings.ENVIRONMENT == "development":
    origins = settings.CORS_ORIGINS
else:
    origins = [
        "https://www.baixingfalv.com",
        "https://app.baixingfalv.com",
        "https://admin.baixingfalv.com",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "Idempotency-Key"],
)

# ✅ 更好的方案：微服务不直接对外暴露
# 通过 API Gateway（Kong/APISIX）统一管理 CORS
# 内部微服务间通信不需要 CORS
```

---

## 🟡 重要改进（建议近期完成）

### 6. 知识库与档案库高度同构 — 应考虑合并或抽象

```
当前对比：
┌────────────────┬──────────────────┬──────────────────┐
│     维度       │    知识库(8081)   │    档案库(8082)  │
├────────────────┼──────────────────┼──────────────────┤
│ 框架           │ FastAPI           │ FastAPI          │
│ 数据库         │ PostgreSQL        │ PostgreSQL       │
│ 向量库         │ ChromaDB          │ ChromaDB         │
│ Embedding      │ text2vec-base     │ text2vec-base    │
│ CRUD操作       │ 几乎相同          │ 几乎相同         │
│ 搜索           │ 全文+向量         │ 全文+向量        │
│ 分类           │ 有               │ 有               │
│ 批量导入       │ 有               │ 有               │
│ 批量导出       │ 有               │ 有               │
│ 向量重建       │ 有               │ 有               │
│ Consul         │ 有               │ 有               │
│ OTEL           │ 有               │ 有               │
│ Kafka          │ 有               │ 有               │
│ 不同点         │ 法律条文/解释     │ 案例/判决书      │
└────────────────┴──────────────────┴──────────────────┘

结论：两个服务 90% 代码逻辑重复
```

```
✅ 方案一：合并为统一的知识检索服务（推荐）

  ┌─────────────────────────────────────────────┐
  │         knowledge-service (8081)             │
  │                                              │
  │  /api/v1/knowledge/                          │
  │  ├── /collections                            │
  │  │   ├── POST   创建集合(法律知识/案例档案)   │
  │  │   ├── GET    列出集合                      │
  │  │   └── DELETE 删除集合                      │
  │  │                                           │
  │  ├── /documents                              │
  │  │   ├── POST   添加文档                      │
  │  │   ├── GET    搜索文档（全文+向量+混合）      │
  │  │   ├── PUT    更新文档                      │
  │  │   └── DELETE 删除文档                      │
  │  │                                           │
  │  ├── /categories                             │
  │  │   └── CRUD                                │
  │  │                                           │
  │  ├── /batch                                  │
  │  │   ├── POST /import                        │
  │  │   └── GET  /export                        │
  │  │                                           │
  │  └── /admin                                  │
  │      ├── POST /vector/rebuild                │
  │      └── POST /seed                          │
  │                                              │
  │  数据隔离通过 collection_type 字段区分：       │
  │  - "legal_knowledge" (法律知识)               │
  │  - "case_archive" (案例档案)                  │
  │  - "regulation" (法规)                        │
  │  - 未来可扩展...                              │
  └─────────────────────────────────────────────┘
```

```python
# ✅ 统一文档模型

class Document(Base):
    """统一文档表 — 支持多种知识类型"""
    __tablename__ = "documents"

    id = Column(UUID, primary_key=True, default=uuid4)
    collection_type = Column(
        String(50), nullable=False, index=True,
        comment="文档类型: legal_knowledge / case_archive / regulation"
    )
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    category_id = Column(UUID, ForeignKey("categories.id"), nullable=True)

    # 元数据（不同类型有不同字段）
    metadata_ = Column(JSONB, default={}, comment="""
        legal_knowledge: {"law_name": "民法典", "article": "第1032条", ...}
        case_archive: {"court": "最高人民法院", "case_number": "(2024)最高法民终123号", ...}
    """)

    # 向量（pgvector）
    embedding = Column(Vector(768), nullable=True)

    # 通用字段
    source = Column(String(500), nullable=True)
    status = Column(String(20), default="published", index=True)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, onupdate=func.now())

    __table_args__ = (
        Index("ix_doc_type_category", "collection_type", "category_id"),
        Index("ix_doc_embedding", embedding,
              postgresql_using="ivfflat",
              postgresql_ops={"embedding": "vector_cosine_ops"}),
    )

class Category(Base):
    """统一分类表"""
    __tablename__ = "categories"

    id = Column(UUID, primary_key=True, default=uuid4)
    collection_type = Column(String(50), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    parent_id = Column(UUID, ForeignKey("categories.id"), nullable=True)
    sort_order = Column(Integer, default=0)
```

```python
# ✅ 统一搜索接口（支持多种检索模式）

class SearchMode(str, Enum):
    KEYWORD = "keyword"      # 传统全文搜索
    SEMANTIC = "semantic"    # 纯向量语义搜索
    HYBRID = "hybrid"        # 混合搜索（推荐）

@router.get("/documents/search")
async def search_documents(
    query: str = Query(..., min_length=1, max_length=500),
    collection_type: Optional[str] = Query(None),
    category_id: Optional[UUID] = Query(None),
    mode: SearchMode = Query(SearchMode.HYBRID),
    top_k: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    embedding_client: EmbeddingClient = Depends(),
):
    if mode == SearchMode.KEYWORD:
        results = await search_service.keyword_search(db, query, collection_type, top_k)
    elif mode == SearchMode.SEMANTIC:
        query_vec = await embedding_client.encode_single(query)
        results = await search_service.vector_search(db, query_vec, collection_type, top_k)
    else:
        # 混合搜索：关键词 + 语义，加权融合
        query_vec = await embedding_client.encode_single(query)
        results = await search_service.hybrid_search(
            db, query, query_vec, collection_type, top_k,
            keyword_weight=0.3, semantic_weight=0.7,
        )

    return {"results": results, "mode": mode, "total": len(results)}
```

---

### 7. AI 服务缺少 LLM 调用容错

```python
# ❌ 当前：直接调用 DeepSeek API，无容错
# 问题：
# 1. DeepSeek 宕机 → 整个 AI 功能不可用
# 2. 限流/超时 → 用户体验极差
# 3. 无 fallback → 单点故障

# ✅ 改进：多层容错 + 降级策略

class LLMService:
    def __init__(self, settings: Settings):
        # 主模型
        self._primary = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            timeout=30.0,
            max_retries=2,
        )
        # 备用模型（可选：通义千问/文心一言/本地模型）
        self._fallback = AsyncOpenAI(
            api_key=settings.FALLBACK_API_KEY,
            base_url=settings.FALLBACK_BASE_URL,
            timeout=30.0,
        ) if settings.FALLBACK_API_KEY else None

    async def chat(
        self,
        messages: list[dict],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        model = model or self._settings.LLM_MODEL

        # 第一层：主模型 + 重试
        try:
            response = await self._call_with_timeout(
                self._primary, messages, model, temperature, max_tokens
            )
            return LLMResponse(content=response, model=model, fallback=False)
        except Exception as e:
            logger.warning(f"Primary LLM failed: {e}")

        # 第二层：备用模型
        if self._fallback:
            try:
                response = await self._call_with_timeout(
                    self._fallback, messages,
                    self._settings.FALLBACK_MODEL,
                    temperature, max_tokens
                )
                return LLMResponse(
                    content=response,
                    model=self._settings.FALLBACK_MODEL,
                    fallback=True
                )
            except Exception as e:
                logger.error(f"Fallback LLM failed: {e}")

        # 第三层：降级响应
        return LLMResponse(
            content="抱歉，AI 服务暂时不可用，请稍后再试。您也可以直接搜索知识库或联系在线律师。",
            model="fallback_static",
            fallback=True,
            degraded=True,
        )

    async def _call_with_timeout(self, client, messages, model, temp, max_tokens):
        """带超时和 Token 限制的 LLM 调用"""
        try:
            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temp,
                    max_tokens=max_tokens,
                ),
                timeout=45.0  # 硬超时
            )
            return response.choices[0].message.content
        except asyncio.TimeoutError:
            raise LLMTimeoutError("LLM 响应超时")
```

---

### 8. AI 服务缺少对话上下文管理

```python
# ✅ 完整的对话上下文管理

class ConversationManager:
    """管理多轮对话上下文，控制 Token 用量"""

    MAX_HISTORY_TURNS = 10        # 最多保留 10 轮
    MAX_CONTEXT_TOKENS = 4000     # 上下文最大 Token 数

    def __init__(self, redis: Redis):
        self._redis = redis

    async def get_context(self, conversation_id: str) -> list[dict]:
        """获取对话上下文"""
        key = f"conv:{conversation_id}:messages"
        messages = await self._redis.lrange(key, 0, -1)
        return [json.loads(m) for m in messages]

    async def add_message(self, conversation_id: str, role: str, content: str):
        """添加消息并修剪上下文"""
        key = f"conv:{conversation_id}:messages"

        message = {"role": role, "content": content, "timestamp": datetime.utcnow().isoformat()}
        await self._redis.rpush(key, json.dumps(message, ensure_ascii=False))

        # 修剪：保留最近 N 轮
        await self._redis.ltrim(key, -(self.MAX_HISTORY_TURNS * 2), -1)

        # 设置 TTL：对话 24 小时后自动过期
        await self._redis.expire(key, 86400)

    async def build_prompt(
        self,
        conversation_id: str,
        user_message: str,
        system_prompt: str,
        rag_context: str = "",
    ) -> list[dict]:
        """构建完整的 Prompt"""
        messages = [{"role": "system", "content": system_prompt}]

        # RAG 检索结果注入
        if rag_context:
            messages.append({
                "role": "system",
                "content": f"以下是相关法律知识，请据此回答：\n\n{rag_context}"
            })

        # 历史上下文
        history = await self.get_context(conversation_id)
        messages.extend([
            {"role": m["role"], "content": m["content"]}
            for m in history
        ])

        # 当前消息
        messages.append({"role": "user", "content": user_message})

        # Token 控制：如果超限，压缩早期历史
        messages = self._trim_to_token_limit(messages)

        return messages

    def _trim_to_token_limit(self, messages: list[dict]) -> list[dict]:
        """从中间删除最早的历史消息，保留 system prompt 和最近消息"""
        total_tokens = sum(len(m["content"]) // 2 for m in messages)  # 粗估
        while total_tokens > self.MAX_CONTEXT_TOKENS and len(messages) > 3:
            removed = messages.pop(2)  # 删除 system 之后最早的消息
            total_tokens -= len(removed["content"]) // 2
        return messages
```

---

### 9. AI 服务缺少用量控制与计费

```python
# ❌ 当前：无 Token 用量限制
# DeepSeek 按 Token 计费，不限制会导致：
# 1. 单用户疯狂调用 → 账单爆炸
# 2. 恶意用户发送超长文本 → 高额 Token 消耗

# ✅ 改进：结合会员体系的用量控制

class UsageService:
    """Token 用量管理"""

    DAILY_LIMITS = {
        "free":  {"messages": 20,  "tokens": 50_000},
        "vip":   {"messages": 200, "tokens": 500_000},
        "svip":  {"messages": -1,  "tokens": 5_000_000},   # -1=无限
        "admin": {"messages": -1,  "tokens": -1},
    }

    async def check_and_consume(
        self,
        user_id: str,
        user_role: str,
        estimated_tokens: int,
        redis: Redis,
    ) -> bool:
        limits = self.DAILY_LIMITS.get(user_role, self.DAILY_LIMITS["free"])
        today = datetime.utcnow().strftime("%Y-%m-%d")

        # 消息次数检查
        msg_key = f"usage:{user_id}:{today}:messages"
        msg_count = int(await redis.get(msg_key) or 0)
        if limits["messages"] != -1 and msg_count >= limits["messages"]:
            raise QuotaExceededError(
                "今日对话次数已达上限",
                current=msg_count,
                limit=limits["messages"],
                reset_at=f"{today}T23:59:59Z",
            )

        # Token 用量检查
        token_key = f"usage:{user_id}:{today}:tokens"
        token_count = int(await redis.get(token_key) or 0)
        if limits["tokens"] != -1 and (token_count + estimated_tokens) > limits["tokens"]:
            raise QuotaExceededError(
                "今日 Token 用量已达上限",
                current=token_count,
                limit=limits["tokens"],
            )

        # 消费
        pipe = redis.pipeline()
        pipe.incr(msg_key)
        pipe.incrby(token_key, estimated_tokens)
        pipe.expire(msg_key, 86400)
        pipe.expire(token_key, 86400)
        await pipe.execute()

        return True

    async def record_actual_usage(
        self, user_id: str, prompt_tokens: int, completion_tokens: int, db: AsyncSession
    ):
        """记录实际用量（用于分析和计费）"""
        record = TokenUsageRecord(
            user_id=user_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            model=self._settings.LLM_MODEL,
            # DeepSeek 价格：输入 ¥1/百万token，输出 ¥2/百万token
            estimated_cost=(prompt_tokens * 0.001 + completion_tokens * 0.002) / 1000,
        )
        db.add(record)
        await db.commit()
```

---

### 10. RAG 检索质量缺少评估机制

```python
# ✅ 检索质量评估与自动优化

class RetrievalQualityService:
    """评估 RAG 检索质量，持续优化"""

    async def evaluate_and_log(
        self,
        query: str,
        retrieved_docs: list[dict],
        llm_response: str,
        user_feedback: Optional[str],  # 用户反馈：helpful / not_helpful
        db: AsyncSession,
    ):
        # 自动评估指标
        evaluation = {
            "relevance_score": self._calculate_relevance(query, retrieved_docs),
            "coverage_score": self._calculate_coverage(query, retrieved_docs),
            "doc_count": len(retrieved_docs),
            "avg_similarity": sum(d.get("score", 0) for d in retrieved_docs) / max(len(retrieved_docs), 1),
        }

        log = RetrievalLog(
            query=query,
            doc_ids=[d["id"] for d in retrieved_docs],
            evaluation=evaluation,
            user_feedback=user_feedback,
            llm_response_length=len(llm_response),
        )
        db.add(log)
        await db.commit()

        # 如果检索质量持续低下，触发告警
        if evaluation["relevance_score"] < 0.3:
            logger.warning(
                "low_retrieval_quality",
                query=query,
                score=evaluation["relevance_score"],
            )

    def _calculate_relevance(self, query, docs) -> float:
        """基于关键词重叠率的简单相关性评估"""
        if not docs:
            return 0.0
        query_terms = set(jieba.cut(query))
        scores = []
        for doc in docs:
            doc_terms = set(jieba.cut(doc.get("title", "") + doc.get("content", "")))
            overlap = len(query_terms & doc_terms) / max(len(query_terms), 1)
            scores.append(overlap)
        return sum(scores) / len(scores)
```

---

## 🔵 架构优化（中期规划）

### 11. 三服务缺少统一鉴权

```python
# ❌ 当前：知识库和档案库可能没有鉴权（报告中未提及 auth middleware）
# AI 服务的管理接口（agent 管理/质量运营）需要管理员权限

# ✅ 统一鉴权方案

# shared/auth_dependency.py（三个服务共享）
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx

security = HTTPBearer()

class AuthDependency:
    """
    通过 user-service 的公钥验证 JWT
    或通过 gRPC 调用 ValidateToken
    """

    def __init__(self):
        self._public_key = None

    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Security(security),
    ) -> dict:
        token = credentials.credentials
        try:
            payload = jwt.decode(token, self._public_key, algorithms=["RS256"])
            return {
                "user_id": payload["sub"],
                "role": payload.get("role", "user"),
            }
        except jwt.ExpiredSignatureError:
            raise HTTPException(401, "Token 已过期")
        except jwt.InvalidTokenError:
            raise HTTPException(401, "无效 Token")

    async def require_admin(self, user: dict = Depends(get_current_user)):
        if user["role"] not in ("admin", "super_admin"):
            raise HTTPException(403, "需要管理员权限")
        return user

# ✅ AI 服务路由使用
@router.post("/admin/agents/", dependencies=[Depends(auth.require_admin)])
async def create_agent(data: AgentCreate):
    ...

# ✅ 知识库写操作需要鉴权，读操作可公开
@router.post("/knowledge/", dependencies=[Depends(auth.get_current_user)])
async def create_knowledge(data: KnowledgeCreate):
    ...

@router.get("/knowledge/search")  # 搜索不需要登录
async def search_knowledge(query: str):
    ...
```

---

### 12. 缺少请求输入安全防护

```python
# ❌ AI 对话接口可能遭受：
# 1. Prompt 注入攻击
# 2. 超长文本攻击（消耗 Token）
# 3. 敏感信息泄露引导

# ✅ 输入安全层

class InputSanitizer:
    MAX_MESSAGE_LENGTH = 2000       # 单条消息最大字符数
    MAX_SYSTEM_OVERRIDE_PATTERNS = [
        r"忽略.*指令",
        r"ignore.*instructions",
        r"你现在是.*",
        r"假装你是.*",
        r"forget.*previous",
        r"system\s*prompt",
    ]

    def sanitize(self, user_input: str) -> str:
        # 1. 长度限制
        if len(user_input) > self.MAX_MESSAGE_LENGTH:
            raise InputError("消息长度超过限制")

        # 2. Prompt 注入检测
        for pattern in self.MAX_SYSTEM_OVERRIDE_PATTERNS:
            if re.search(pattern, user_input, re.IGNORECASE):
                logger.warning("prompt_injection_detected", input_preview=user_input[:50])
                raise InputError("检测到不安全的输入内容")

        # 3. 清理特殊字符
        cleaned = user_input.strip()
        cleaned = re.sub(r'<[^>]+>', '', cleaned)  # 去除 HTML 标签

        return cleaned

# ✅ 在 chat 路由中使用
@router.post("/chat")
async def chat(
    request: ChatRequest,
    sanitizer: InputSanitizer = Depends(),
):
    clean_message = sanitizer.sanitize(request.message)
    ...
```

---

## 📋 完整改进优先级

```
 优先级    │ 问题                              │ 影响             │ 工作量
──────────┼──────────────────────────────────┼─────────────────┼────────
 🔴 P0    │ API Key 硬编码在代码中             │ 密钥泄露/资金损失 │ 1小时
 🔴 P0    │ AI 服务使用 SQLite                │ 并发锁死/数据丢失 │ 0.5天
 🔴 P0    │ ChromaDB 本地模式无法扩展          │ 数据不一致/内存爆 │ 3天
 🔴 P0    │ CORS allow_origins=["*"]          │ 安全漏洞         │ 10分钟
 🔴 P0    │ Embedding 模型重复加载(×3)         │ 1.2GB 内存浪费   │ 2天
 🟡 P1    │ 知识库/档案库高度重复              │ 维护成本翻倍     │ 5天
 🟡 P1    │ LLM 调用无容错/降级               │ 单点故障         │ 2天
 🟡 P1    │ 对话上下文管理缺失                 │ 多轮对话混乱     │ 2天
 🟡 P1    │ Token 用量无控制                  │ 账单爆炸         │ 1天
 🟡 P1    │ RAG 检索质量无评估                │ 回答质量无法优化  │ 2天
 🔵 P2    │ 三服务缺少统一鉴权                │ 越权访问         │ 2天
 🔵 P2    │ AI 输入安全防护                   │ Prompt注入       │ 1天
```

---

## 🆚 五服务横向对比

| 维度 | User | Legal | Knowledge | Archive | AI |
|------|------|-------|-----------|---------|-----|
| **数据库** | ✅ PG | ✅ PG | ✅ PG | ✅ PG | ❌ SQLite |
| **安全性** | ✅ 强 | ✅ 中 | ⚠️ 弱 | ⚠️ 弱 | ❌ Key泄露 |
| **可扩展性** | ✅ 好 | ✅ 好 | ❌ ChromaDB本地 | ❌ ChromaDB本地 | ⚠️ SQLite限制 |
| **事件驱动** | ⚠️ 可选 | ✅ Outbox | ✅ Kafka | ✅ Kafka | ✅ Kafka |
| **可观测性** | ⚠️ 基础 | ✅ 完整 | ✅ OTEL | ✅ OTEL | ✅ OTEL |
| **测试** | ✅ 6文件 | ✅ 8文件 | ⚠️ 未知 | ⚠️ 未知 | ⚠️ 未知 |
| **鉴权** | ✅ JWT | ✅ JWT | ❌ 缺失 | ❌ 缺失 | ⚠️ 部分 |
| **容错** | ✅ | ✅ | ⚠️ | ⚠️ | ❌ 无LLM降级 |
| **文档** | ⚠️ | ✅ 完整 | ⚠️ | ⚠️ | ⚠️ |

---

## 🎯 建议实施路线图

```
第 1 天（紧急）
├── ✅ 轮换 DeepSeek API Key + 环境变量化        (1小时)
├── ✅ 修复 CORS 配置                            (10分钟)
└── ✅ AI 服务切换 PostgreSQL                     (半天)

第 2-4 天
├── ✅ ChromaDB → pgvector 迁移                   (3天)
└── ✅ 提取 Embedding Service 或精简模型加载       (1天)

第 5-8 天
├── ✅ 知识库/档案库合并为统一知识检索服务          (4天)
└── ✅ LLM 容错 + 降级策略                        (1天)

第 9-12 天
├── ✅ 对话上下文管理                              (2天)
├── ✅ Token 用量控制                              (1天)
└── ✅ 统一鉴权                                   (1天)

第 13-15 天
├── ✅ RAG 质量评估                                (2天)
├── ✅ 输入安全防护                                (1天)
└── ✅ 补充测试                                   (2天)
```

> **核心结论**：三个 AI 相关服务的 **基础设施安全性** 是全平台最薄弱的环节（API Key 泄露、SQLite、CORS 全开、无鉴权）。User Service 和 Legal Service 已经具备企业级水准，但 AI/知识库/档案库还停留在 **原型阶段**。建议优先用 **1 天修复 4 个 P0 安全问题**，再用 **2 周** 完成架构升级（pgvector + 服务合并 + LLM 容错），整个平台才能达到一致的生产就绪水位。