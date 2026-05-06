"""Saga 持久化集成

为 Order Service 提供带持久化的 Saga 执行器
"""

import asyncio
import logging
import os
from typing import Optional, Dict, Any

from services.common.saga import (
    SagaOrchestrator,
    SagaState,
    SagaStatus,
    HybridSagaPersistence,
    PostgresSagaPersistence,
)

logger = logging.getLogger(__name__)

_postgres_url: Optional[str] = None
_redis_url: Optional[str] = None
_persistence: Optional[HybridSagaPersistence] = None


async def init_saga_persistence(
    postgres_url: Optional[str] = None,
    redis_url: Optional[str] = None,
) -> HybridSagaPersistence:
    """初始化 Saga 持久化"""
    global _persistence, _postgres_url, _redis_url

    _postgres_url = postgres_url or os.getenv(
        "SAGA_POSTGRES_URL",
        f"postgresql+asyncpg://{os.getenv('DB_USER', 'postgres')}:"
        f"{os.getenv('DB_PASSWORD', 'postgres')}@"
        f"{os.getenv('DB_HOST', 'localhost')}:"
        f"{os.getenv('DB_PORT', '5432')}/"
        f"{os.getenv('DB_NAME', 'baixing')}"
    )

    _redis_url = redis_url or os.getenv(
        "SAGA_REDIS_URL",
        f"redis://:{os.getenv('REDIS_PASSWORD', '')}@"
        f"{os.getenv('REDIS_HOST', 'localhost')}:"
        f"{os.getenv('REDIS_PORT', '6379')}"
    )

    _persistence = HybridSagaPersistence(
        postgres_url=_postgres_url,
        redis_url=_redis_url,
        redis_ttl=3600,
    )

    await _persistence.initialize()
    logger.info("Saga persistence initialized (Hybrid mode)")

    return _persistence


async def close_saga_persistence():
    """关闭 Saga 持久化"""
    global _persistence
    if _persistence:
        await _persistence.close()
        _persistence = None
        logger.info("Saga persistence closed")


async def get_persistence() -> Optional[HybridSagaPersistence]:
    """获取持久化实例"""
    return _persistence


class PersistentSagaOrchestrator(SagaOrchestrator):
    """带持久化的 Saga 编排器"""

    def __init__(
        self,
        saga_id: str,
        steps: list,
        description: str = "",
        persistence: Optional[HybridSagaPersistence] = None,
    ):
        super().__init__(
            saga_id=saga_id,
            steps=steps,
            description=description,
        )
        self._persistence = persistence or _persistence

    async def _save_state(self, state: SagaState):
        """保存状态到持久化存储"""
        if self._persistence:
            try:
                await self._persistence.save_state(state)
                logger.debug(f"Saga state saved: {self.saga_id}")
            except Exception as e:
                logger.error(f"Failed to save saga state: {e}")

    async def execute(self) -> SagaState:
        """执行 Saga 并持久化状态"""
        if self._persistence:
            existing_state = await self._persistence.get_state(self.saga_id)
            if existing_state:
                logger.info(f"Resuming saga: {self.saga_id}")
                self.state = existing_state

        try:
            result = await super().execute()

            if self._persistence:
                await self._save_state(result)

            return result

        except Exception as e:
            logger.error(f"Saga execution failed: {self.saga_id}, error: {e}")
            if self._persistence:
                self.state.status = SagaStatus.FAILED
                self.state.error = str(e)
                await self._save_state(self.state)
            raise


async def get_saga_state(saga_id: str) -> Optional[SagaState]:
    """获取 Saga 状态"""
    if not _persistence:
        return None
    return await _persistence.get_state(saga_id)


async def list_pending_sagas(limit: int = 100) -> list:
    """列出待处理的 Saga"""
    if not _persistence:
        return []
    return await _persistence.list_sagas(status="in_progress", limit=limit)
