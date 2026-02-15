"""Redis 缓存和消息队列服务

提供 Redis 集成用于缓存和消息队列功能。
"""

import asyncio
import json
import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional, Callable, Union, cast
from contextlib import asynccontextmanager

import redis.asyncio as redis
from redis.asyncio import Redis

from ..config import get_settings

logger = logging.getLogger(__name__)

# 延迟初始化 settings，避免模块导入时出错
_settings = None


def _get_settings():
    """延迟获取 settings"""
    global _settings
    if _settings is None:
        _settings = get_settings()
    return _settings


class RedisService:
    """Redis 服务类"""

    def __init__(self):
        self._client: Optional[Redis] = None
        self._is_connected = False

    async def connect(self):
        """连接 Redis"""
        if self._client is not None:
            return

        settings = _get_settings()
        redis_url = settings.redis_url.strip() if settings.redis_url else None

        if not redis_url:
            logger.warning("Redis URL 未配置，缓存功能将不可用")
            return

        try:
            self._client = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )

            # 测试连接
            client = cast(Redis, self._client)
            ping_result: bool = await client.ping()  # type: ignore[assignment]
            if ping_result is True:
                self._is_connected = True
            logger.info("Redis 连接成功")

        except Exception as e:
            logger.error(f"Redis 连接失败: {e}")
            self._is_connected = False

    async def disconnect(self):
        """断开 Redis 连接"""
        if self._client:
            await self._client.close()
            self._client = None
            self._is_connected = False
            logger.info("Redis 连接已关闭")

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._is_connected

    # ========== 缓存操作 ==========

    async def get(self, key: str) -> Optional[str]:
        """获取缓存值"""
        if not self._is_connected or self._client is None:
            return None

        try:
            client = cast(Redis, self._client)
            return await client.get(key)
        except Exception as e:
            logger.error(f"Redis GET 错误: {e}")
            return None

    async def set(
        self,
        key: str,
        value: str,
        expire_seconds: Optional[int] = None,
    ) -> bool:
        """设置缓存值

        Args:
            key: 键
            value: 值
            expire_seconds: 过期时间（秒）
        """
        if not self._is_connected or self._client is None:
            return False

        try:
            client = cast(Redis, self._client)
            if expire_seconds:
                await client.setex(key, expire_seconds, value)
            else:
                await client.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Redis SET 错误: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self._is_connected or self._client is None:
            return False

        try:
            client = cast(Redis, self._client)
            await client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE 错误: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self._is_connected or self._client is None:
            return False

        try:
            client = cast(Redis, self._client)
            return await client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS 错误: {e}")
            return False

    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """获取 JSON 缓存"""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None

    async def set_json(
        self,
        key: str,
        value: Union[Dict[str, Any], List[Dict[str, Any]]],
        expire_seconds: Optional[int] = None,
    ) -> bool:
        """设置 JSON 缓存"""
        try:
            json_str = json.dumps(value, ensure_ascii=False)
            return await self.set(key, json_str, expire_seconds)
        except Exception as e:
            logger.error(f"Redis SET JSON 错误: {e}")
            return False

    async def incr(self, key: str) -> int:
        """自增"""
        if not self._is_connected or self._client is None:
            return 0

        try:
            client = cast(Redis, self._client)
            return await client.incr(key)
        except Exception as e:
            logger.error(f"Redis INCR 错误: {e}")
            return 0

    async def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        if not self._is_connected or self._client is None:
            return False

        try:
            client = cast(Redis, self._client)
            return await client.expire(key, seconds)
        except Exception as e:
            logger.error(f"Redis EXPIRE 错误: {e}")
            return False

    # ========== 缓存键生成 ==========

    @staticmethod
    def make_key(prefix: str, *parts) -> str:
        """生成缓存键"""
        return f"{prefix}:{':'.join(str(p) for p in parts)}"

    # 预定义的缓存键
    CACHE_KEYS = {
        "user_balance": "points:balance:{user_id}",
        "user_daily_stats": "points:daily:{user_id}:{date}",
        "user_history": "points:history:{user_id}",
        "leaderboard": "points:leaderboard",
        "product_list": "points:products",
        "recommendation": "rec:{user_id}",
        "news_list": "news:{category}:{page}",
    }

    def get_cache_key(self, key_type: str, **kwargs) -> str:
        """获取缓存键"""
        template = self.CACHE_KEYS.get(key_type, "{key_type}:{kwargs}")
        return template.format(**kwargs)

    # ========== 消息队列 ==========

    async def publish(self, channel: str, message: Dict) -> int:
        """发布消息

        Args:
            channel: 频道名
            message: 消息内容

        Returns:
            订阅者数量
        """
        if not self._is_connected or self._client is None:
            return 0

        try:
            client = cast(Redis, self._client)
            return await client.publish(
                channel,
                json.dumps(message, ensure_ascii=False),
            )
        except Exception as e:
            logger.error(f"Redis PUBLISH 错误: {e}")
            return 0

    @asynccontextmanager
    async def subscribe(self, channel: str):
        """订阅频道

        Usage:
            async with redis_service.subscribe("points:notifications") as pubsub:
                async for message in pubsub.listen():
                    print(message)
        """
        if not self._is_connected or self._client is None:
            raise RuntimeError("Redis 未连接")

        client = cast(Redis, self._client)
        pubsub = client.pubsub()
        await pubsub.subscribe(channel)

        try:
            yield pubsub
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()

    # ========== 分布式锁 ==========

    async def acquire_lock(
        self,
        lock_name: str,
        timeout: int = 10,
        expire_seconds: int = 30,
    ) -> Optional[str]:
        """获取分布式锁

        Args:
            lock_name: 锁名称
            timeout: 获取锁超时时间（秒）
            expire_seconds: 锁过期时间（秒）

        Returns:
            锁标识（获取失败返回 None）
        """
        if not self._is_connected or self._client is None:
            return None

        import uuid
        lock_id = str(uuid.uuid4())
        end_time = asyncio.get_event_loop().time() + timeout

        while asyncio.get_event_loop().time() < end_time:
            try:
                client = cast(Redis, self._client)
                # 使用 SET NX PX
                result = await client.set(
                    f"lock:{lock_name}",
                    lock_id,
                    nx=True,
                    px=expire_seconds * 1000,
                )
                if result:
                    return lock_id
            except Exception as e:
                logger.error(f"获取锁错误: {e}")

            await asyncio.sleep(0.1)

        return None

    async def release_lock(self, lock_name: str, lock_id: str) -> bool:
        """释放分布式锁"""
        if not self._is_connected or self._client is None:
            return False

        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """

        try:
            client = cast(Redis, self._client)
            result = await client.eval(  # type: ignore[arg-type]
                script,
                1,  # numkeys
                f"lock:{lock_name}",  # keys
                lock_id,  # args
            )
            return result == 1
        except Exception as e:
            logger.error(f"释放锁错误: {e}")
            return False


# 单例
_redis_service: Optional[RedisService] = None


def get_redis_service() -> RedisService:
    """获取 Redis 服务单例"""
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisService()
    return _redis_service


# ========== 缓存装饰器 ==========

def cached(expire_seconds: int = 300, key_prefix: str = ""):
    """缓存装饰器

    Usage:
        @cached(expire_seconds=600, key_prefix="user")
        async def get_user_info(user_id: int):
            return await fetch_user_from_db(user_id)
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            redis = get_redis_service()

            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{args}:{kwargs}"
            cache_key = cache_key.replace(" ", "").replace("'", '"')

            # 尝试从缓存获取
            cached_value = await redis.get_json(cache_key)
            if cached_value is not None:
                logger.debug(f"缓存命中: {cache_key}")
                return cached_value

            # 执行函数
            result = await func(*args, **kwargs)

            # 存入缓存
            if result is not None:
                await redis.set_json(cache_key, result, expire_seconds)

            return result

        return wrapper

    return decorator


# ========== 积分系统专用缓存 ==========

class PointsCache:
    """积分系统缓存"""

    def __init__(self, redis: RedisService):
        self.redis = redis

    # 用户积分缓存
    USER_BALANCE_TTL = 60  # 1分钟
    USER_DAILY_STATS_TTL = 3600  # 1小时

    async def get_user_balance(self, user_id: int) -> Optional[int]:
        """获取用户积分缓存"""
        key = self.redis.get_cache_key("user_balance", user_id=user_id)
        value = await self.redis.get(key)
        return int(value) if value else None

    async def set_user_balance(self, user_id: int, balance: int):
        """设置用户积分缓存"""
        key = self.redis.get_cache_key("user_balance", user_id=user_id)
        await self.redis.set(key, str(balance), self.USER_BALANCE_TTL)

    async def invalidate_user_balance(self, user_id: int):
        """清除用户积分缓存"""
        key = self.redis.get_cache_key("user_balance", user_id=user_id)
        await self.redis.delete(key)

    # 排行榜缓存
    LEADERBOARD_TTL = 300  # 5分钟

    async def get_leaderboard(self) -> Optional[List[Dict]]:
        """获取排行榜缓存"""
        key = self.redis.get_cache_key("leaderboard")
        result = await self.redis.get_json(key)
        return result  # type: ignore[return-value]

    async def set_leaderboard(self, leaderboard: List[Dict]):
        """设置排行榜缓存"""
        key = self.redis.get_cache_key("leaderboard")
        await self.redis.set_json(key, leaderboard, self.LEADERBOARD_TTL)

    async def invalidate_leaderboard(self):
        """清除排行榜缓存"""
        key = self.redis.get_cache_key("leaderboard")
        await self.redis.delete(key)

    # 商品列表缓存
    PRODUCTS_TTL = 600  # 10分钟

    async def get_products(
            self, product_type: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """获取商品列表缓存"""
        key = self.redis.get_cache_key(
            "product_list", type=product_type or "all")
        result = await self.redis.get_json(key)
        return result  # type: ignore[return-value]

    async def set_products(
            self, products: List[Dict[str, Any]], product_type: Optional[str] = None):
        """设置商品列表缓存"""
        key = self.redis.get_cache_key(
            "product_list", type=product_type or "all")
        await self.redis.set_json(key, products, self.PRODUCTS_TTL)

    async def invalidate_products(self):
        """清除商品列表缓存"""
        for product_type in ["all", "voucher", "vip", "package"]:
            key = self.redis.get_cache_key("product_list", type=product_type)
            await self.redis.delete(key)


def get_points_cache() -> PointsCache:
    """获取积分缓存单例"""
    return PointsCache(get_redis_service())
