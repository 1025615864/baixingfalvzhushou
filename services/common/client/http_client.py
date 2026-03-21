"""服务间HTTP调用客户端

提供微服务间HTTP通信的统一接口，支持：
- 服务发现
- 负载均衡（轮询）
- 超时控制
- 重试机制
- 熔断器
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional
from urllib.parse import urljoin

import httpx

logger = logging.getLogger(__name__)


class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceEndpoint:
    """服务端点"""
    name: str
    host: str
    port: int
    base_url: str
    status: ServiceStatus = ServiceStatus.UNKNOWN
    consecutive_failures: int = 0
    last_failure_time: float = 0

    def url(self, path: str = "") -> str:
        return urljoin(self.base_url, path)


class CircuitState(str, Enum):
    CLOSED = "closed"      # 正常
    OPEN = "open"          # 熔断
    HALF_OPEN = "half_open"  # 半开


class CircuitBreaker:
    """熔断器

    防止级联故障，当服务失败率过高时自动熔断。
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: float = 30.0,
    ):
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0

    def record_success(self) -> None:
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info("Circuit breaker closed")
        else:
            self.failure_count = 0

    def record_failure(self) -> None:
        import time
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.success_count = 0

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.warning("Circuit breaker reopened")
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

    @property
    def is_open(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return False
        if self.state == CircuitState.HALF_OPEN:
            return False
        return True

    def should_try(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.HALF_OPEN:
            return True
        # 检查超时
        import time
        if time.time() - self.last_failure_time > self.timeout:
            self.state = CircuitState.HALF_OPEN
            self.success_count = 0
            return True
        return False


class ServiceClient:
    """服务HTTP客户端

    支持：
    - 多实例负载均衡
    - 熔断器
    - 超时控制
    - 重试机制
    """

    def __init__(
        self,
        service_name: str,
        endpoints: list[dict[str, Any]],
        timeout: float = 10.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.service_name = service_name
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._current_index = 0
        self._lock = asyncio.Lock()

        # 初始化服务端点
        self.endpoints: list[ServiceEndpoint] = []
        for ep in endpoints:
            self.endpoints.append(
                ServiceEndpoint(
                    name=service_name,
                    host=ep["host"],
                    port=ep["port"],
                    base_url=f"http://{ep['host']}:{ep['port']}",
                )
            )

        # 熔断器
        self.circuit_breaker = CircuitBreaker()

        # HTTP 客户端
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _get_next_endpoint(self) -> Optional[ServiceEndpoint]:
        """获取下一个可用的服务端点（轮询）"""
        if not self.endpoints:
            return None

        async with self._lock:
            # 尝试找到健康的端点
            for _ in range(len(self.endpoints)):
                self._current_index = (self._current_index + 1) % len(self.endpoints)
                ep = self.endpoints[self._current_index]
                if ep.status == ServiceStatus.HEALTHY:
                    return ep

            # 如果都不可用，返回第一个
            return self.endpoints[self._current_index]

    async def request(
        self,
        method: str,
        path: str,
        **kwargs,
    ) -> httpx.Response:
        """发送HTTP请求（带重试和熔断）"""

        if not self.circuit_breaker.should_try():
            raise ServiceUnavailableError(
                f"Service {self.service_name} is unavailable (circuit open)"
            )

        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries):
            endpoint = await self._get_next_endpoint()
            if not endpoint:
                raise ServiceUnavailableError(f"No endpoints available for {self.service_name}")

            try:
                client = await self._get_client()
                url = endpoint.url(path)

                response = await client.request(
                    method=method,
                    url=url,
                    **kwargs,
                )

                # 检查响应状态
                if response.status_code < 500:
                    self.circuit_breaker.record_success()
                    endpoint.consecutive_failures = 0
                    return response

                # 服务端错误，重试
                last_error = ServiceError(
                    f"Service {self.service_name} returned {response.status_code}",
                    status_code=response.status_code,
                )

            except httpx.TimeoutException as e:
                endpoint.consecutive_failures += 1
                last_error = e
                logger.warning(
                    f"Request timeout for {self.service_name} (attempt {attempt + 1})"
                )

            except httpx.ConnectError as e:
                endpoint.consecutive_failures += 1
                last_error = e
                logger.warning(
                    f"Connection error for {self.service_name} (attempt {attempt + 1})"
                )

            except Exception as e:
                endpoint.consecutive_failures += 1
                last_error = e
                logger.error(f"Unexpected error for {self.service_name}: {e}")

            # 记录失败
            if endpoint.consecutive_failures >= 3:
                endpoint.status = ServiceStatus.UNHEALTHY
                self.circuit_breaker.record_failure()

            # 重试等待
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay * (attempt + 1))

        # 所有重试都失败
        self.circuit_breaker.record_failure()
        raise ServiceError(
            f"Service {self.service_name} failed after {self.max_retries} attempts",
            previous=last_error,
        )

    async def get(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("PUT", path, **kwargs)

    async def patch(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("PATCH", path, **kwargs)

    async def delete(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("DELETE", path, **kwargs)


class ServiceUnavailableError(Exception):
    """服务不可用异常"""
    pass


class ServiceError(Exception):
    """服务调用异常"""

    def __init__(self, message: str, status_code: int = 0, previous: Exception = None):
        super().__init__(message)
        self.status_code = status_code
        self.previous = previous
