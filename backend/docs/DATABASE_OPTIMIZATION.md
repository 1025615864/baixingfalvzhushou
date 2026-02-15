# 数据库优化指南

## 连接池配置

```python
# app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)

async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
```

## 索引优化

### 常用索引

```sql
-- 用户表
CREATE INDEX idx_user_phone ON users(phone);
CREATE INDEX idx_user_created_at ON users(created_at DESC);

-- 论坛帖子
CREATE INDEX idx_post_user ON forum_posts(user_id);
CREATE INDEX idx_post_created ON forum_posts(created_at DESC);

-- 新闻表
CREATE INDEX idx_news_published ON news(published_at DESC);
CREATE INDEX idx_news_topic ON news(topic_id);
```

## 查询优化

### N+1 问题解决

```python
# 使用 joinedload 预加载
from sqlalchemy.orm import selectinload

result = await session.execute(
    select(Post).options(selectinload(Post.comments))
)
```

### 分页查询

```python
# 避免 OFFSET 过大
async def get_posts(page: int, page_size: int):
    # 使用游标分页
    result = await session.execute(
        select(Post)
        .where(Post.id > last_id)
        .limit(page_size)
    )
```

## 缓存策略

参考 `backend/docs/CACHE_STRATEGY_GUIDE.md`

## 监控慢查询

```python
# 启用 SQL 日志
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```
