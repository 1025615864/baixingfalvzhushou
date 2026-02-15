# 缓存策略指南

## 缓存层级

```
浏览器缓存 → CDN 缓存 → Redis 缓存 → 数据库
```

## Redis 缓存

### 配置

```python
# app/services/cache_service.py
from redis import asyncio as aioredis

class CacheService:
    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url)

    async def get(self, key: str):
        return await self.redis.get(key)

    async def set(self, key: str, value: str, ttl: int = 3600):
        await self.redis.setex(key, ttl, value)

    async def delete(self, key: str):
        await self.redis.delete(key)
```

### 使用

```python
@cache_service.cache(key="user:{user_id}", ttl=3600)
async def get_user(user_id: int) -> User:
    return await db.get(User, user_id)
```

## 缓存策略

### 缓存模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| Cache-Aside | 应用管理缓存 | 大多数场景 |
| Read-Through | 缓存自动加载 | 简单读场景 |
| Write-Through | 同步写入 | 强一致性 |
| Write-Behind | 异步写入 | 高写入场景 |

### TTL 配置

```python
CACHE_TTL = {
    "user_profile": 3600,      # 1小时
    "post_list": 300,         # 5分钟
    "news_detail": 1800,      # 30分钟
    "config": 86400,           # 1天
    "session": 604800,         # 7天
}
```

## 缓存失效

```python
async def invalidate_user_cache(user_id: int):
    """清除用户相关缓存"""
    patterns = [
        f"user:{user_id}",
        f"user:{user_id}:posts",
        f"user:{user_id}:profile",
    ]
    for pattern in patterns:
        await cache_service.delete_pattern(pattern)
```

## 缓存击穿处理

```python
from asyncio import Lock

user_cache_lock = Lock()

async def get_user_cached(user_id: int) -> User:
    # 1. 尝试从缓存获取
    cached = await cache_service.get(f"user:{user_id}")
    if cached:
        return User.parse_raw(cached)

    # 2. 获取锁
    async with user_cache_lock:
        # 3. 双重检查
        cached = await cache_service.get(f"user:{user_id}")
        if cached:
            return User.parse_raw(cached)

        # 4. 从数据库获取
        user = await db.get(User, user_id)
        await cache_service.set(f"user:{user_id}", user.json(), ttl=3600)
        return user
```

## 缓存监控

```python
# 记录缓存命中率
async def track_cache_metrics(key: str, hit: bool):
    metric = f"cache_hit{{key='{key}'}}" if hit else f"cache_miss{{key='{key}'}}"
    prometheus_metrics.increment(metric)
```
