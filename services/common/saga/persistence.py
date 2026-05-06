"""Saga 状态持久化

与 orchestrator 中的 SagaExecutionLog 保持一致，支持：
- PostgreSQL 持久化
- Redis 缓存
- 状态查询与恢复
"""

import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SagaPersistence:
    """Saga 持久化基类"""

    async def save_state(self, saga_id: str, **kwargs) -> None:
        raise NotImplementedError

    async def get_state(self, saga_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    async def list_sagas(self, status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        raise NotImplementedError

    async def update_status(self, saga_id: str, status: str, **kwargs) -> bool:
        raise NotImplementedError


class PostgresSagaPersistence(SagaPersistence):
    """PostgreSQL Saga 持久化"""

    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def save_state(self, saga_id: str, **kwargs) -> None:
        """保存 Saga 状态"""
        from .orchestrator import SagaExecutionLog

        db: AsyncSession = self._session_factory()
        try:
            log = SagaExecutionLog(
                id=saga_id,
                saga_type=kwargs.get("saga_type", "unknown"),
                status=kwargs.get("status", "running"),
                correlation_id=kwargs.get("correlation_id"),
                current_step=kwargs.get("current_step", 0),
                total_steps=kwargs.get("total_steps", 0),
                steps_log=kwargs.get("steps_log"),
                error_message=kwargs.get("error_message"),
                metadata=kwargs.get("metadata"),
                started_at=kwargs.get("started_at"),
                completed_at=kwargs.get("completed_at"),
            )
            db.add(log)
            await db.commit()
            logger.info(f"Saga state saved: {saga_id}")
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to save saga state {saga_id}: {e}")
            raise
        finally:
            await db.close()

    async def get_state(self, saga_id: str) -> Optional[Dict[str, Any]]:
        """获取 Saga 状态"""
        from .orchestrator import SagaExecutionLog

        db: AsyncSession = self._session_factory()
        try:
            result = await db.execute(
                select(SagaExecutionLog).where(SagaExecutionLog.id == saga_id)
            )
            log = result.scalar_one_or_none()
            if not log:
                return None
            return {
                "id": log.id,
                "saga_type": log.saga_type,
                "status": log.status,
                "correlation_id": log.correlation_id,
                "current_step": log.current_step,
                "total_steps": log.total_steps,
                "steps_log": log.steps_log,
                "error_message": log.error_message,
                "metadata": log.metadata,
                "started_at": log.started_at.isoformat() if log.started_at else None,
                "completed_at": log.completed_at.isoformat() if log.completed_at else None,
            }
        finally:
            await db.close()

    async def list_sagas(
        self, status: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """列出 Saga 状态"""
        from .orchestrator import SagaExecutionLog

        db: AsyncSession = self._session_factory()
        try:
            query = select(SagaExecutionLog).order_by(SagaExecutionLog.created_at.desc()).limit(limit)
            if status:
                query = query.where(SagaExecutionLog.status == status)

            result = await db.execute(query)
            logs = result.scalars().all()

            return [
                {
                    "id": log.id,
                    "saga_type": log.saga_type,
                    "status": log.status,
                    "correlation_id": log.correlation_id,
                    "current_step": log.current_step,
                    "total_steps": log.total_steps,
                    "error_message": log.error_message,
                    "started_at": log.started_at.isoformat() if log.started_at else None,
                    "completed_at": log.completed_at.isoformat() if log.completed_at else None,
                }
                for log in logs
            ]
        finally:
            await db.close()

    async def update_status(self, saga_id: str, status: str, **kwargs) -> bool:
        """更新 Saga 状态"""
        from .orchestrator import SagaExecutionLog

        db: AsyncSession = self._session_factory()
        try:
            update_data = {"status": status}
            if "error_message" in kwargs:
                update_data["error_message"] = kwargs["error_message"]
            if "current_step" in kwargs:
                update_data["current_step"] = kwargs["current_step"]
            if "completed_at" in kwargs:
                update_data["completed_at"] = kwargs["completed_at"]

            stmt = update(SagaExecutionLog).where(SagaExecutionLog.id == saga_id).values(**update_data)
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount > 0
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update saga status {saga_id}: {e}")
            return False
        finally:
            await db.close()


class RedisSagaPersistence:
    """Redis Saga 缓存 - 用于快速访问"""

    def __init__(self, redis_client, key_prefix: str = "saga:"):
        self._redis = redis_client
        self.key_prefix = key_prefix

    async def save_state(self, saga_id: str, state: Dict[str, Any], ttl: int = 86400) -> None:
        """保存 Saga 状态到 Redis"""
        key = f"{self.key_prefix}{saga_id}"
        await self._redis.setex(key, ttl, json.dumps(state))

    async def get_state(self, saga_id: str) -> Optional[Dict[str, Any]]:
        """从 Redis 获取 Saga 状态"""
        key = f"{self.key_prefix}{saga_id}"
        data = await self._redis.get(key)
        if data:
            return json.loads(data)
        return None


class HybridSagaPersistence(SagaPersistence):
    """混合持久化 - Redis 缓存 + PostgreSQL 持久化"""

    def __init__(self, postgres_persistence: PostgresSagaPersistence, redis_persistence: RedisSagaPersistence):
        self.postgres = postgres_persistence
        self.redis = redis_persistence

    async def save_state(self, saga_id: str, **kwargs) -> None:
        await self.postgres.save_state(saga_id, **kwargs)
        state = await self.postgres.get_state(saga_id)
        if state:
            await self.redis.save_state(saga_id, state)

    async def get_state(self, saga_id: str) -> Optional[Dict[str, Any]]:
        cached = await self.redis.get_state(saga_id)
        if cached:
            return cached
        return await self.postgres.get_state(saga_id)

    async def list_sagas(self, status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        return await self.postgres.list_sagas(status, limit)

    async def update_status(self, saga_id: str, status: str, **kwargs) -> bool:
        result = await self.postgres.update_status(saga_id, status, **kwargs)
        if result:
            state = await self.postgres.get_state(saga_id)
            if state:
                await self.redis.save_state(saga_id, state)
        return result
