"""Redis分布式锁"""
import uuid
from typing import Optional
import redis.asyncio as redis


class RedisLockManager:
    """Redis分布式锁管理器"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self._client: Optional[redis.Redis] = None

    async def _get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client

    async def acquire_lock(
        self,
        key: str,
        timeout: int = 10,
        lock_timeout: int = 30,
    ) -> Optional[str]:
        """尝试获取分布式锁

        Args:
            key: 锁的键名
            timeout: 获取锁的超时时间（秒）
            lock_timeout: 锁的自动过期时间（秒）

        Returns:
            锁的值（用于释放锁），获取失败返回None
        """
        lock_key = f"lock:{key}"
        lock_value = str(uuid.uuid4())
        client = await self._get_client()

        import time
        start_time = time.time()
        while time.time() - start_time < timeout:
            result = await client.set(lock_key, lock_value, nx=True, ex=lock_timeout)
            if result:
                return lock_value
            import asyncio
            await asyncio.sleep(0.1)

        return None

    async def release_lock(self, key: str, lock_value: str) -> bool:
        """释放分布式锁（原子操作）"""
        lock_key = f"lock:{key}"
        client = await self._get_client()

        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        result = await client.eval(script, 1, lock_key, lock_value)
        return result == 1

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None


lock_manager = RedisLockManager()