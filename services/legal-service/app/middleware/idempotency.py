"""幂等性中间件 - 基于 Idempotency-Key 请求头保障接口幂等性"""
import json
import logging
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

logger = logging.getLogger(__name__)


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """基于 Idempotency-Key 请求头的幂等性保障

    适用于 POST/PUT/PATCH 等写操作，防止重复提交
    """

    CACHE_TTL = 86400
    LOCK_TTL = 10

    def __init__(self, app, redis_client):
        super().__init__(app)
        self.redis = redis_client

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method not in ("POST", "PUT", "PATCH"):
            return await call_next(request)

        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return await call_next(request)

        if not self.redis:
            return await call_next(request)

        cache_key = f"idempotency:{idempotency_key}"

        try:
            cached = await self.redis.get(cache_key)
            if cached:
                logger.info(f"Idempotency key replay: {idempotency_key}")
                return JSONResponse(
                    content=json.loads(cached),
                    headers={
                        "X-Idempotent-Replayed": "true",
                        "X-Idempotency-Key": idempotency_key,
                    }
                )

            lock_key = f"idempotency_lock:{idempotency_key}"
            acquired = await self.redis.set(
                lock_key, "1", nx=True, ex=self.LOCK_TTL
            )
            if not acquired:
                return JSONResponse(
                    status_code=409,
                    content={
                        "code": "L40901",
                        "message": "请求处理中，请稍后重试",
                    }
                )

            try:
                response = await call_next(request)

                if response.status_code < 500:
                    body = b""
                    async for chunk in response.body_iterator:
                        body += chunk

                    await self.redis.set(
                        cache_key,
                        body,
                        ex=self.CACHE_TTL
                    )

                    return Response(
                        content=body,
                        status_code=response.status_code,
                        headers={
                            **dict(response.headers),
                            "X-Idempotency-Key": idempotency_key,
                        }
                    )
                else:
                    return Response(
                        content=await response.body(),
                        status_code=response.status_code,
                        headers={
                            **dict(response.headers),
                            "X-Idempotency-Key": idempotency_key,
                        }
                    )
            finally:
                await self.redis.delete(lock_key)

        except Exception as e:
            logger.error(f"Idempotency middleware error: {e}")
            return await call_next(request)


async def get_idempotency_key(request: Request) -> Optional[str]:
    """从请求头获取幂等键"""
    return request.headers.get("Idempotency-Key")
