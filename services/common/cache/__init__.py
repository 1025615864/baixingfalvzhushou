import hashlib
import json
import logging
import os
import functools
from typing import Optional, Callable

logger = logging.getLogger(__name__)

_redis_client = None


def init_cache(redis_client):
    global _redis_client
    _redis_client = redis_client


def _get_cache_key(prefix: str, *args, **kwargs) -> str:
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    key_hash = hashlib.md5(key_data.encode()).hexdigest()
    return f"cache:{prefix}:{key_hash}"


def cached(
    prefix: str,
    ttl: int = 300,
    key_builder: Optional[Callable] = None,
):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if _redis_client is None:
                return await func(*args, **kwargs)

            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = _get_cache_key(prefix, *args[1:], **kwargs)

            try:
                cached_value = await _redis_client.get(cache_key)
                if cached_value is not None:
                    return json.loads(cached_value)
            except Exception as e:
                logger.warning(f"Cache read error for {cache_key}: {e}")

            result = await func(*args, **kwargs)

            try:
                await _redis_client.setex(
                    cache_key,
                    ttl,
                    json.dumps(result, default=str),
                )
            except Exception as e:
                logger.warning(f"Cache write error for {cache_key}: {e}")

            return result

        wrapper.cache_prefix = prefix
        wrapper.cache_ttl = ttl
        return wrapper

    return decorator


async def invalidate_cache(prefix: str, *args, **kwargs):
    if _redis_client is None:
        return

    if args or kwargs:
        cache_key = _get_cache_key(prefix, *args, **kwargs)
        try:
            await _redis_client.delete(cache_key)
        except Exception as e:
            logger.warning(f"Cache invalidation error for {cache_key}: {e}")
    else:
        pattern = f"cache:{prefix}:*"
        try:
            keys = []
            async for key in _redis_client.scan_iter(match=pattern, count=100):
                keys.append(key)
            if keys:
                await _redis_client.delete(*keys)
        except Exception as e:
            logger.warning(f"Cache pattern invalidation error for {pattern}: {e}")
