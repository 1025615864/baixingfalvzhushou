"""熔断器模式实现

提供对外部服务调用的熔断保护，防止级联故障扩散。

熔断器模式:
    当检测到外部服务连续失败时，熔断器会自动"打开"，拒绝所有请求。
    等待超时后，熔断器进入"半开"状态，允许部分请求通过以测试服务恢复情况。
    如果服务恢复正常，熔断器"关闭"，恢复正常工作；如果仍有问题，重新"打开"。

状态转换图:
    CLOSED (正常) --连续失败--> OPEN (打开)
    OPEN (打开) --超时--> HALF_OPEN (半开)
    HALF_OPEN (半开) --成功--> CLOSED (正常)
    HALF_OPEN (半开) --失败--> OPEN (打开)

使用示例:
    ```python
    from app.utils import get_circuit_breaker, CircuitBreakerOpen
    from app.core import ExternalServiceException

    # 获取熔断器
    cb = get_circuit_breaker("payment_service")

    # 基本使用
    try:
        result = await cb.call(payment_api.call, order_id=123)
    except CircuitBreakerOpen:
        # 熔断器打开，使用缓存或默认值
        return get_cached_result(order_id)

    # 使用降级策略
    result = await cb.call_with_fallback(
        payment_api.call,
        fallback=get_default_payment_response,
        order_id=123
    )
    ```

配置示例:
    ```python
    from app.utils import CircuitConfig, get_circuit_breaker

    config = CircuitConfig(
        failure_threshold=5,      # 连续5次失败后打开
        success_threshold=2,      # 半开状态下需要2次成功才能关闭
        timeout_seconds=30.0,     # 30秒后进入半开状态
        expected_exception=ExternalServiceException,  # 只对这类异常计数
    )
    cb = get_circuit_breaker("payment_service", config)
    ```
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger("circuit_breaker")


class CircuitState(Enum):
    """熔断器状态枚举

    Attributes:
        CLOSED: 正常状态，允许所有请求通过
        OPEN: 打开状态，拒绝所有请求
        HALF_OPEN: 半开状态，允许部分请求通过以测试恢复
    """

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitStats:
    """熔断器统计信息

    用于追踪熔断器的运行状态和调用统计。

    Attributes:
        total_calls: 总调用次数
        successful_calls: 成功调用次数
        failed_calls: 失败调用次数
        last_failure_time: 最后失败时间戳
        last_success_time: 最后成功时间戳
        consecutive_failures: 连续失败次数
        consecutive_successes: 连续成功次数
    """

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0


@dataclass
class CircuitConfig:
    """熔断器配置

    用于配置熔断器的行为参数。

    Attributes:
        failure_threshold: 连续失败次数阈值，达到后打开熔断器
        success_threshold: 半开状态下需要连续成功的次数
        timeout_seconds: 熔断器打开后的超时时间
        expected_exception: 需要捕获并计数的异常类型
    """

    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: float = 30.0
    expected_exception: type[Exception] = Exception


@dataclass
class CircuitBreaker:
    """熔断器实现

    用于保护对外部服务的调用，防止级联故障。

    熔断器通过追踪调用失败次数来工作：
        1. 正常情况下处于CLOSED状态
        2. 连续失败达到阈值后进入OPEN状态
        3. OPEN状态下经过超时时间后进入HALF_OPEN状态
        4. HALF_OPEN状态下允许测试请求通过
        5. 测试成功则回到CLOSED，失败则回到OPEN

    Attributes:
        name: 熔断器名称
        config: 熔断器配置
        state: 当前状态
        stats: 统计信息
        last_state_change: 最后状态变更时间戳
        _lock: 异步锁用于并发控制

    Examples:
        ```python
        cb = CircuitBreaker(
            name="payment_service",
            config=CircuitConfig(failure_threshold=3)
        )

        # 同步函数
        result = cb.call_sync(external_api.request)

        # 异步函数
        result = await cb.call(external_api.async_request)
        ```
    """

    name: str
    config: CircuitConfig = field(default_factory=CircuitConfig)
    state: CircuitState = CircuitState.CLOSED
    stats: CircuitStats = field(default_factory=CircuitStats)
    last_state_change: float = field(default_factory=time.time)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def __post_init__(self) -> None:
        self._lock = asyncio.Lock()

    def _update_last_failure(self) -> None:
        """更新失败统计"""
        self.stats.last_failure_time = time.time()
        self.stats.consecutive_failures += 1
        self.stats.consecutive_successes = 0

    def _update_last_success(self) -> None:
        """更新成功统计"""
        self.stats.last_success_time = time.time()
        self.stats.consecutive_successes += 1
        self.stats.consecutive_failures = 0

    def _should_open(self) -> bool:  # noqa: E501
        """检查是否应该打开熔断器"""
        return self.stats.consecutive_failures >= self.config.failure_threshold

    def _should_close(self) -> bool:  # noqa: E501
        """检查是否应该关闭熔断器"""
        return self.stats.consecutive_successes >= self.config.success_threshold

    def _should_transition_to_closed(self) -> bool:
        """检查是否应该转换到关闭状态"""
        if self.state == CircuitState.HALF_OPEN:
            return self._should_close()
        return False

    async def _try_open(self) -> None:
        """尝试打开熔断器"""
        if self._should_open():
            self.state = CircuitState.OPEN
            self.last_state_change = time.time()
            logger.warning(
                f"Circuit breaker '{self.name}' OPENED after "
                f"{self.stats.consecutive_failures} consecutive failures"
            )

    async def _try_close(self) -> None:
        """尝试关闭熔断器"""
        if self._should_transition_to_closed():
            self.state = CircuitState.CLOSED
            self.last_state_change = time.time()
            self.stats.consecutive_failures = 0
            self.stats.consecutive_successes = 0
            logger.info(
                f"Circuit breaker '{self.name}' CLOSED - service recovered"
            )

    async def _try_open_from_half_open(self, success: bool) -> None:
        """从半开状态尝试打开"""
        if self.state == CircuitState.HALF_OPEN:
            if not success:
                self.state = CircuitState.OPEN
                self.last_state_change = time.time()
                self.stats.consecutive_successes = 0
                logger.warning(
                    f"Circuit breaker '{self.name}' OPENED from "
                    "HALF_OPEN - test failed"
                )

    def _is_timeout_elapsed(self) -> bool:
        """检查超时时间是否已过"""
        return (
            time.time() - self.last_state_change
        ) >= self.config.timeout_seconds

    async def _try_transition_to_half_open(self) -> bool:
        """尝试转换到半开状态"""
        if self.state == CircuitState.OPEN and self._is_timeout_elapsed():
            self.state = CircuitState.HALF_OPEN
            self.last_state_change = time.time()
            self.stats.consecutive_successes = 0
            self.stats.consecutive_failures = 0
            logger.info(
                f"Circuit breaker '{self.name}' HALF_OPEN - "
                "testing service recovery"
            )
            return True
        return False

    async def call(
        self,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """执行受保护的函数调用

        Args:
            func: 要执行的函数（同步或异步）
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数执行结果

        Raises:
            CircuitBreakerOpen: 熔断器打开时抛出
            Exception: 函数执行失败时抛出
        """
        async with self._lock:
            self.stats.total_calls += 1

            if self.state == CircuitState.OPEN:
                if not await self._try_transition_to_half_open():
                    raise CircuitBreakerOpen(
                        f"Circuit breaker '{self.name}' is OPEN"
                    )

            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                self._update_last_success()
                self.stats.successful_calls += 1
                await self._try_close()

                return result

            except self.config.expected_exception as e:
                self._update_last_failure()
                self.stats.failed_calls += 1
                logger.error(
                    f"Circuit breaker '{self.name}' call failed: {e}"
                )
                await self._try_open()
                await self._try_open_from_half_open(success=False)
                raise

    async def call_with_fallback(
        self,
        func: Callable[..., Any],
        fallback: Optional[Callable[..., Any]] = None,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """执行受保护的函数调用，支持降级策略

        当熔断器打开或调用失败时，执行降级函数返回备用结果。

        Args:
            func: 要执行的函数
            fallback: 降级函数，接收错误或参数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数执行结果或降级结果

        Examples:
            ```python
            # 降级函数不接收参数
            result = await cb.call_with_fallback(
                external_api.call,
                fallback=get_default_response,
                param=value
            )

            # 降级函数接收错误信息
            result = await cb.call_with_fallback(
                external_api.call,
                fallback=lambda e: {"error": str(e)},
                param=value
            )
            ```
        """
        try:
            return await self.call(func, *args, **kwargs)
        except CircuitBreakerOpen:
            if fallback:
                if asyncio.iscoroutinefunction(fallback):
                    return await fallback(*args, **kwargs)
                return fallback(*args, **kwargs)
            raise
        except Exception as e:
            if fallback:
                if asyncio.iscoroutinefunction(fallback):
                    return await fallback(e)
                return fallback(e)
            raise

    def get_stats(self) -> dict[str, Any]:
        """获取熔断器统计信息

        Returns:
            包含熔断器状态的字典
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "total_calls": self.stats.total_calls,
            "successful_calls": self.stats.successful_calls,
            "failed_calls": self.stats.failed_calls,
            "consecutive_failures": self.stats.consecutive_failures,
            "consecutive_successes": self.stats.consecutive_successes,
            "last_failure_time": self.stats.last_failure_time,
            "last_success_time": self.stats.last_success_time,
            "last_state_change": self.last_state_change,
        }

    def reset(self) -> None:
        """重置熔断器

        将熔断器恢复到初始关闭状态，清除所有统计信息。
        """
        self.state = CircuitState.CLOSED
        self.stats = CircuitStats()
        self.last_state_change = time.time()
        logger.info(f"Circuit breaker '{self.name}' reset")


class CircuitBreakerOpen(Exception):
    """熔断器打开异常

    当熔断器处于OPEN状态时调用被拒绝会抛出此异常。
    """

    pass


class CircuitBreakerRegistry:
    """熔断器注册表

    用于集中管理和获取熔断器实例。

    Features:
        - 单例模式管理熔断器
        - 支持按名称获取和创建
        - 批量获取统计信息

    Examples:
        ```python
        registry = CircuitBreakerRegistry()

        # 获取或创建
        cb1 = await registry.get_or_create("payment_service")
        cb2 = await registry.get_or_create("payment_service")  # 返回同一个实例

        # 获取统计
        all_stats = registry.get_all_stats()
        ```
    """

    def __init__(self) -> None:
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()

    async def get_or_create(
        self,
        name: str,
        config: Optional[CircuitConfig] = None,
    ) -> CircuitBreaker:
        """获取或创建熔断器

        Args:
            name: 熔断器名称
            config: 可选的熔断器配置

        Returns:
            熔断器实例
        """
        async with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(
                    name=name,
                    config=config or CircuitConfig(),
                )
            return self._breakers[name]

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """获取熔断器

        Args:
            name: 熔断器名称

        Returns:
            熔断器实例，如果不存在则返回None
        """
        return self._breakers.get(name)

    def remove(self, name: str) -> None:
        """移除熔断器

        Args:
            name: 熔断器名称
        """
        if name in self._breakers:
            del self._breakers[name]

    def get_all_stats(self) -> list[dict[str, Any]]:
        """获取所有熔断器统计信息

        Returns:
            包含所有熔断器状态的列表
        """
        return [cb.get_stats() for cb in self._breakers.values()]  # noqa: E741


circuit_breaker_registry = CircuitBreakerRegistry()


def get_circuit_breaker(
    name: str, config: Optional[CircuitConfig] = None
) -> CircuitBreaker:
    """获取熔断器实例

    这是一个便捷函数，用于从全局注册表获取熔断器。
    支持同步和异步调用环境。

    Args:
        name: 熔断器名称
        config: 可选的熔断器配置

    Returns:
        熔断器实例

    Examples:
        ```python
        from app.utils import get_circuit_breaker, CircuitConfig

        # 使用默认配置
        cb = get_circuit_breaker("payment_service")

        # 使用自定义配置
        cb = get_circuit_breaker(
            "payment_service",
            CircuitConfig(failure_threshold=3, timeout_seconds=60.0)
        )

        # 异步调用
        async def example():
            cb = await circuit_breaker_registry.get_or_create("service_name")
        ```
    """
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        # 在运行中的事件循环中，必须使用异步方式获取
        # 返回协程，调用者需要使用 await
        return circuit_breaker_registry.get_or_create(name, config)
    else:
        return loop.run_until_complete(
            circuit_breaker_registry.get_or_create(name, config)
        )
