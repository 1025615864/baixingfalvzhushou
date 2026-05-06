"""gRPC 客户端 - 支持 TLS 加密、服务发现、Fallback降级、Bulkhead隔离"""

import grpc
from typing import Optional, Any, Dict, Callable, Union
import logging
import asyncio
from dataclasses import dataclass, field
from enum import Enum
import time
import threading

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class GrpcConfig:
    host: str
    port: int
    timeout: int = 30
    max_retries: int = 3
    use_tls: bool = False
    tls_cert_path: Optional[str] = None
    service_name: Optional[str] = None


class CircuitBreaker:
    """熔断器 - 防止级联故障"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 3,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                if time.time() - self._last_failure_time >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
            return self._state

    def record_success(self):
        with self._lock:
            self._failure_count = 0
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_calls += 1
                if self._half_open_calls >= self.half_open_max_calls:
                    self._state = CircuitState.CLOSED
                    logger.info("Circuit breaker CLOSED after successful recovery")

    def record_failure(self):
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(f"Circuit breaker OPEN after {self._failure_count} failures")

    def can_execute(self) -> bool:
        return self.state != CircuitState.OPEN


class Bulkhead:
    """Bulkhead 隔离 - 限制并发连接数"""

    def __init__(self, max_concurrent_calls: int = 10, max_queue_size: int = 20):
        self.max_concurrent_calls = max_concurrent_calls
        self.max_queue_size = max_queue_size
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._lock = threading.Lock()

    def _get_semaphore(self) -> asyncio.Semaphore:
        if self._semaphore is None:
            with self._lock:
                if self._semaphore is None:
                    self._semaphore = asyncio.Semaphore(self.max_concurrent_calls)
        return self._semaphore

    async def acquire(self):
        return await self._get_semaphore().acquire()

    def release(self):
        self._get_semaphore().release()

    @property
    def available_capacity(self) -> int:
        return self.max_concurrent_calls


class GrpcClient:
    def __init__(
        self,
        config: GrpcConfig,
        stub_class: Any,
        enable_bulkhead: bool = True,
        max_concurrent_calls: int = 10,
        enable_circuit_breaker: bool = True,
        circuit_breaker_threshold: int = 5,
    ):
        self.config = config
        self.stub_class = stub_class
        self._channel: Optional[grpc.Channel] = None
        self._stub: Optional[Any] = None

        self._bulkhead = Bulkhead(max_concurrent_calls=max_concurrent_calls) if enable_bulkhead else None
        self._circuit_breaker = CircuitBreaker(failure_threshold=circuit_breaker_threshold) if enable_circuit_breaker else None

    def _create_channel_credentials(self) -> grpc.ChannelCredentials:
        if self.config.use_tls:
            if self.config.tls_cert_path:
                with open(self.config.tls_cert_path, "rb") as f:
                    trusted_certs = f.read()
                credentials = grpc.ssl_channel_credentials(root_certificates=trusted_certs)
            else:
                credentials = grpc.ssl_channel_credentials()
            return credentials
        return grpc.insecure_channel_credentials()

    def connect(self) -> Any:
        if self._channel is None:
            credentials = self._create_channel_credentials()
            target = f"{self.config.host}:{self.config.port}"

            options = [
                ("grpc.max_send_message_length", 50 * 1024 * 1024),
                ("grpc.max_receive_message_length", 50 * 1024 * 1024),
                ("grpc.keepalive_time_ms", 30000),
                ("grpc.keepalive_timeout_ms", 10000),
                ("grpc.max_concurrent_streams", 100),
            ]

            if self.config.use_tls:
                self._channel = grpc.secure_channel(target, credentials, options=options)
            else:
                self._channel = grpc.insecure_channel(target, options=options)

            self._stub = self.stub_class(self._channel)
        return self._stub

    async def call_with_fallback(
        self,
        func_name: str,
        request: Any,
        fallback_fn: Optional[Callable[[], Any]] = None,
        retry_count: Optional[int] = None,
    ) -> Any:
        """带降级的gRPC调用"""
        try:
            return await self.call_with_retry(func_name, request, retry_count)
        except Exception as e:
            if fallback_fn:
                logger.warning(f"gRPC call {func_name} failed, using fallback: {e}")
                try:
                    if asyncio.iscoroutinefunction(fallback_fn):
                        return await fallback_fn()
                    return fallback_fn()
                except Exception as fallback_error:
                    logger.error(f"Fallback function also failed: {fallback_error}")
                    raise e
            raise e

    async def call_with_resilience(
        self,
        func_name: str,
        request: Any,
        fallback_fn: Optional[Callable[[], Any]] = None,
        retry_count: Optional[int] = None,
        timeout: Optional[int] = None,
    ) -> Any:
        """带完整韧性的gRPC调用：Bulkhead + CircuitBreaker + Retry + Fallback"""
        if self._circuit_breaker and not self._circuit_breaker.can_execute():
            logger.warning(f"Circuit breaker is OPEN for {self.config.service_name or self.config.host}")
            if fallback_fn:
                return await self._execute_fallback(fallback_fn)
            raise Exception("Circuit breaker is OPEN")

        if self._bulkhead:
            await self._bulkhead.acquire()

        try:
            result = await self._execute_call_with_timeout(
                func_name, request, retry_count, timeout
            )

            if self._circuit_breaker:
                self._circuit_breaker.record_success()

            return result

        except Exception as e:
            if self._circuit_breaker:
                self._circuit_breaker.record_failure()
            raise e

        finally:
            if self._bulkhead:
                self._bulkhead.release()

    async def _execute_fallback(self, fallback_fn: Callable) -> Any:
        try:
            if asyncio.iscoroutinefunction(fallback_fn):
                return await fallback_fn()
            return fallback_fn()
        except Exception as fallback_error:
            logger.error(f"Fallback function failed: {fallback_error}")
            raise

    async def _execute_call_with_timeout(
        self,
        func_name: str,
        request: Any,
        retry_count: Optional[int],
        timeout: Optional[int],
    ) -> Any:
        call_timeout = timeout or self.config.timeout

        async def do_call():
            return await self.call_with_retry(func_name, request, retry_count)

        try:
            return await asyncio.wait_for(do_call(), timeout=call_timeout)
        except asyncio.TimeoutError:
            logger.error(f"gRPC call {func_name} timed out after {call_timeout}s")
            raise grpc.RpcError(f"Timeout after {call_timeout}s")

    async def call_with_retry(
        self,
        func_name: str,
        request: Any,
        retry_count: Optional[int] = None,
    ) -> Any:
        max_retries = retry_count if retry_count is not None else self.config.max_retries
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                stub = self.connect()
                func = getattr(stub, func_name)

                if asyncio.iscoroutinefunction(func):
                    result = await func(request, timeout=self.config.timeout)
                else:
                    result = func(request, timeout=self.config.timeout)

                return result

            except grpc.RpcError as e:
                last_error = e
                code = e.code()

                if code == grpc.StatusCode.UNAVAILABLE:
                    logger.warning(
                        f"gRPC call {func_name} failed (attempt {attempt + 1}): "
                        f"Service unavailable"
                    )
                    self._channel = None
                    await asyncio.sleep(2 ** attempt)
                elif code == grpc.StatusCode.DEADLINE_EXCEEDED:
                    logger.warning(f"gRPC call {func_name} failed: Deadline exceeded")
                    await asyncio.sleep(1)
                else:
                    logger.error(f"gRPC call {func_name} failed: {e}")
                    raise

            except Exception as e:
                logger.error(f"Unexpected error in gRPC call {func_name}: {e}")
                raise

        raise last_error

    def get_circuit_state(self) -> Optional[CircuitState]:
        return self._circuit_breaker.state if self._circuit_breaker else None

    def get_bulkhead_capacity(self) -> Optional[int]:
        return self._bulkhead.available_capacity if self._bulkhead else None

    def close(self):
        if self._channel:
            self._channel.close()
            self._channel = None
            self._stub = None


class GrpcClientPool:
    def __init__(self):
        self._clients: Dict[str, GrpcClient] = {}

    def register(
        self,
        name: str,
        config: GrpcConfig,
        stub_class: Any,
        enable_bulkhead: bool = True,
        max_concurrent_calls: int = 10,
        enable_circuit_breaker: bool = True,
        circuit_breaker_threshold: int = 5,
    ):
        self._clients[name] = GrpcClient(
            config,
            stub_class,
            enable_bulkhead=enable_bulkhead,
            max_concurrent_calls=max_concurrent_calls,
            enable_circuit_breaker=enable_circuit_breaker,
            circuit_breaker_threshold=circuit_breaker_threshold,
        )
        logger.info(
            f"Registered gRPC client: {name} -> {config.host}:{config.port} "
            f"(TLS: {config.use_tls}, Bulkhead: {enable_bulkhead}, CB: {enable_circuit_breaker})"
        )

    def register_with_discovery(
        self,
        name: str,
        service_name: str,
        stub_class: Any,
        use_tls: bool = False,
        timeout: int = 30,
        max_retries: int = 3,
        enable_bulkhead: bool = True,
        max_concurrent_calls: int = 10,
        enable_circuit_breaker: bool = True,
    ):
        config = GrpcConfig(
            host=service_name,
            port=50051,
            timeout=timeout,
            max_retries=max_retries,
            use_tls=use_tls,
            service_name=service_name,
        )
        self._clients[name] = GrpcClient(
            config,
            stub_class,
            enable_bulkhead=enable_bulkhead,
            max_concurrent_calls=max_concurrent_calls,
            enable_circuit_breaker=enable_circuit_breaker,
        )
        logger.info(
            f"Registered gRPC client with service discovery: {name} -> {service_name} "
            f"(TLS: {use_tls})"
        )

    def get(self, name: str) -> Optional[GrpcClient]:
        return self._clients.get(name)

    def get_config(self, name: str) -> Optional[GrpcConfig]:
        client = self._clients.get(name)
        return client.config if client else None

    def get_health_status(self) -> Dict[str, Any]:
        return {
            name: {
                "circuit_state": client.get_circuit_state().value if client.get_circuit_state() else None,
                "bulkhead_capacity": client.get_bulkhead_capacity(),
            }
            for name, client in self._clients.items()
        }

    def close_all(self):
        for name, client in self._clients.items():
            client.close()
            logger.info(f"Closed gRPC client: {name}")


grpc_pool = GrpcClientPool()
