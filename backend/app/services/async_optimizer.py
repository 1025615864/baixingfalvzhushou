"""异步处理优化工具

实现异步任务队列和重试机制。
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable, Optional
from functools import wraps

from app.services.cache_service import cache_service


logger = logging.getLogger(__name__)


class AsyncTaskQueue:
    """异步任务队列"""

    def __init__(self, max_workers: int = 10) -> None:
        self.max_workers = max_workers
        self.queue: asyncio.Queue = asyncio.Queue()
        self.workers: list[asyncio.Task] = []
        self.running = False

    async def start(self) -> None:
        """启动工作线程"""
        self.running = True
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)

    async def stop(self) -> None:
        """停止工作线程"""
        self.running = False
        for _ in range(self.max_workers):
            await self.queue.put(None)  # 发送停止信号

        # 等待所有工作线程结束
        await asyncio.gather(*self.workers)

    async def _worker(self, name: str) -> None:
        """工作线程

        Args:
            name: 工作线程名称
        """
        while self.running:
            task = await self.queue.get()
            if task is None:
                break

            try:
                func, args, kwargs = task
                await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Worker {name} error: {e}")

    async def submit(
        self,
        func: Callable,
        *args: Any,
        **kwargs: Any
    ) -> None:
        """提交任务

        Args:
            func: 任务函数
            *args: 函数参数
            **kwargs: 函数关键字参数
        """
        await self.queue.put((func, args, kwargs))

    async def submit_batch(
        self,
        tasks: list[tuple[Callable, tuple, dict]]
    ) -> None:
        """批量提交任务

        Args:
            tasks: 任务列表
        """
        for func, args, kwargs in tasks:
            await self.submit(func, *args, **kwargs)


class RetryPolicy:
    """重试策略"""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential: bool = True
    ) -> None:
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential = exponential

    def get_delay(self, attempt: int) -> float:
        """获取延迟时间

        Args:
            attempt: 尝试次数

        Returns:
            延迟时间（秒）
        """
        if self.exponential:
            delay = self.base_delay * (2 ** (attempt - 1))
        else:
            delay = self.base_delay

        return min(delay, self.max_delay)


async def retry_with_backoff(
    func: Callable,
    *args: Any,
    policy: Optional[RetryPolicy] = None,
    **kwargs: Any
) -> Any:
    """带退避的重试

    Args:
        func: 要重试的函数
        *args: 函数参数
        policy: 重试策略
        **kwargs: 函数关键字参数

    Returns:
        函数结果
    """
    if policy is None:
        policy = RetryPolicy()

    last_error = None

    for attempt in range(1, policy.max_attempts + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_error = e

            if attempt >= policy.max_attempts:
                raise

            # 计算延迟时间
            delay = policy.get_delay(attempt)
            logger.warning(
                f"Attempt {attempt}/{policy.max_attempts} failed, "
                f"retrying in {delay:.1f}s: {e}"
            )

            await asyncio.sleep(delay)

    raise last_error


def async_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential: bool = True
):
    """异步重试装饰器

    Args:
        max_attempts: 最大尝试次数
        base_delay: 基础延迟
        max_delay: 最大延迟
        exponential: 是否使用指数退避

    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            policy = RetryPolicy(max_attempts, base_delay, max_delay, exponential)
            return await retry_with_backoff(func, *args, policy=policy, **kwargs)
        return wrapper
    return decorator


# 全局任务队列
task_queue = AsyncTaskQueue(max_workers=10)


async def initialize_async_queue() -> None:
    """初始化异步任务队列"""
    await task_queue.start()


async def shutdown_async_queue() -> None:
    """关闭异步任务队列"""
    await task_queue.stop()


# 异步处理优化最佳实践
ASYNC_PROCESSING_BEST_PRACTICES = {
    "task_queue": {
        "description": "任务队列",
        "when": "处理耗时操作",
        "how": "使用异步任务队列",
        "benefit": "提高响应速度",
    },
    "retry_mechanism": {
        "description": "重试机制",
        "when": "处理可能失败的操作",
        "how": "使用指数退避重试",
        "benefit": "提高成功率",
    },
    "circuit_breaker": {
        "description": "熔断器",
        "when": "服务不可用时",
        "how": "使用熔断器模式",
        "benefit": "防止级联失败",
    },
    "timeout": {
        "description": "超时控制",
        "when": "所有异步操作",
        "how": "设置合理的超时时间",
        "benefit": "避免长时间等待",
    },
}
