"""Saga 状态持久化

支持：
- PostgreSQL 存储
- Redis 缓存
- 自动恢复
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, asdict
import json

from sqlalchemy import Column, String, Text, Integer, DateTime, JSON, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

logger = logging.getLogger(__name__)

Base = declarative_base()


class SagaStateModel(Base):
    """Saga 状态数据库模型"""

    __tablename__ = "saga_states"

    id = Column(String(64), primary_key=True)
    saga_id = Column(String(64), unique=True, nullable=False, index=True)
    saga_name = Column(String(128), nullable=False)
    status = Column(String(32), nullable=False)
    current_step = Column(String(64), nullable=True)
    steps = Column(JSON, nullable=False, default=list)
    completed_steps = Column(JSON, nullable=False, default=list)
    skipped_steps = Column(JSON, nullable=False, default=list)
    step_results = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)


class SagaPersistence:
    """Saga 持久化基类"""

    async def save_state(self, state: "SagaState") -> None:
        raise NotImplementedError

    async def get_state(self, saga_id: str) -> Optional["SagaState"]:
        raise NotImplementedError

    async def list_sagas(
        self, status: Optional[str] = None, limit: int = 100
    ) -> List["SagaState"]:
        raise NotImplementedError


class PostgresSagaPersistence(SagaPersistence):
    """PostgreSQL Saga 持久化"""

    def __init__(
        self,
        database_url: str,
        pool_size: int = 10,
        max_overflow: int = 20,
    ):
        self.database_url = database_url
        self._engine = create_async_engine(
            database_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            echo=False,
        )
        self._session_factory = sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )

    async def initialize(self):
        """初始化数据库表"""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Saga persistence database initialized")

    async def close(self):
        """关闭数据库连接"""
        await self._engine.dispose()

    async def save_state(self, state: "SagaState") -> None:
        """保存 Saga 状态"""
        async with self._session_factory() as session:
            import uuid

            saga = SagaStateModel(
                id=str(uuid.uuid4()),
                saga_id=state.saga_id,
                saga_name=getattr(state, "saga_name", "unknown"),
                status=state.status.value if hasattr(state.status, "value") else state.status,
                current_step=state.current_step,
                steps=state.steps,
                completed_steps=state.completed_steps,
                skipped_steps=getattr(state, "skipped_steps", []),
                step_results=json.dumps(state.to_dict()) if hasattr(state, "to_dict") else None,
                error=state.error,
                started_at=datetime.fromisoformat(state.started_at) if isinstance(state.started_at, str) else state.started_at,
                completed_at=datetime.fromisoformat(state.completed_at) if state.completed_at and isinstance(state.completed_at, str) else state.completed_at,
            )

            session.add(saga)
            try:
                await session.commit()
                logger.info(f"Saga state saved: {state.saga_id}")
            except Exception as e:
                await session.rollback()
                await self._update_state(session, state)
                logger.warning(f"Saga state updated: {state.saga_id}")

    async def _update_state(self, session: AsyncSession, state: "SagaState") -> None:
        """更新已存在的 Saga 状态"""
        from sqlalchemy import update

        stmt = (
            update(SagaStateModel)
            .where(SagaStateModel.saga_id == state.saga_id)
            .values(
                status=state.status.value if hasattr(state.status, "value") else state.status,
                current_step=state.current_step,
                steps=state.steps,
                completed_steps=state.completed_steps,
                skipped_steps=getattr(state, "skipped_steps", []),
                step_results=json.dumps(state.to_dict()) if hasattr(state, "to_dict") else None,
                error=state.error,
                completed_at=datetime.fromisoformat(state.completed_at) if state.completed_at and isinstance(state.completed_at, str) else state.completed_at,
                updated_at=datetime.utcnow(),
            )
        )
        await session.execute(stmt)
        await session.commit()

    async def get_state(self, saga_id: str) -> Optional["SagaState"]:
        """获取 Saga 状态"""
        from ..saga.orchestrator import SagaState, SagaStatus

        async with self._session_factory() as session:
            result = await session.get(SagaStateModel, saga_id)
            if not result:
                for col in [SagaStateModel.id, SagaStateModel.saga_id]:
                    query = f"SELECT * FROM saga_states WHERE {col.name} = :saga_id"
                    row = await session.execute(query, {"saga_id": saga_id})
                    result = row.fetchone()
                    if result:
                        break

            if not result:
                return None

            return SagaState(
                saga_id=result.saga_id,
                status=SagaStatus(result.status),
                steps=result.steps or [],
                completed_steps=result.completed_steps or [],
                skipped_steps=result.skipped_steps or [],
                current_step=result.current_step,
                error=result.error,
                started_at=result.started_at.isoformat() if result.started_at else None,
                completed_at=result.completed_at.isoformat() if result.completed_at else None,
            )

    async def list_sagas(
        self, status: Optional[str] = None, limit: int = 100
    ) -> List[SagaState]:
        """列出 Saga 状态"""
        from ..saga.orchestrator import SagaState, SagaStatus

        async with self._session_factory() as session:
            query = "SELECT * FROM saga_states"
            params = {}

            if status:
                query += " WHERE status = :status"
                params["status"] = status

            query += " ORDER BY created_at DESC LIMIT :limit"
            params["limit"] = limit

            result = await session.execute(query, params)
            rows = result.fetchall()

            states = []
            for row in rows:
                states.append(
                    SagaState(
                        saga_id=row.saga_id,
                        status=SagaStatus(row.status),
                        steps=row.steps or [],
                        completed_steps=row.completed_steps or [],
                        skipped_steps=row.skipped_steps or [],
                        current_step=row.current_step,
                        error=row.error,
                        started_at=row.started_at.isoformat() if row.started_at else None,
                        completed_at=row.completed_at.isoformat() if row.completed_at else None,
                    )
                )

            return states

    async def get_active_sagas(self) -> List[SagaState]:
        """获取活跃的 Sagas"""
        return await self.list_sagas(status="running")

    async def get_failed_sagas(self) -> List[SagaState]:
        """获取失败的 Sagas (用于补偿)"""
        return await self.list_sagas(status="failed")


class RedisSagaPersistence:
    """Redis Saga 缓存 - 用于快速访问"""

    def __init__(self, redis_url: str, key_prefix: str = "saga:"):
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self._redis = None

    async def connect(self):
        """连接 Redis"""
        import redis.asyncio as redis

        self._redis = redis.from_url(self.redis_url)
        logger.info("Saga Redis cache connected")

    async def close(self):
        """关闭 Redis 连接"""
        if self._redis:
            await self._redis.close()

    async def save_state(self, state: "SagaState", ttl: int = 86400) -> None:
        """保存 Saga 状态到 Redis"""
        if not self._redis:
            await self.connect()

        key = f"{self.key_prefix}{state.saga_id}"
        data = json.dumps(state.to_dict())

        await self._redis.setex(key, ttl, data)
        logger.debug(f"Saga state cached: {state.saga_id}")

    async def get_state(self, saga_id: str) -> Optional["SagaState"]:
        """从 Redis 获取 Saga 状态"""
        if not self._redis:
            await self.connect()

        from ..saga.orchestrator import SagaState

        key = f"{self.key_prefix}{saga_id}"
        data = await self._redis.get(key)

        if not data:
            return None

        return SagaState(**json.loads(data))


class HybridSagaPersistence(SagaPersistence):
    """混合持久化 - Redis 缓存 + PostgreSQL 持久化"""

    def __init__(
        self,
        postgres_url: str,
        redis_url: str,
        redis_ttl: int = 3600,
    ):
        self.postgres = PostgresSagaPersistence(postgres_url)
        self.redis = RedisSagaPersistence(redis_url)
        self.redis_ttl = redis_ttl

    async def initialize(self):
        await self.postgres.initialize()
        await self.redis.connect()

    async def close(self):
        await self.postgres.close()
        await self.redis.close()

    async def save_state(self, state: "SagaState") -> None:
        await self.postgres.save_state(state)
        await self.redis.save_state(state, ttl=self.redis_ttl)

    async def get_state(self, saga_id: str) -> Optional["SagaState"]:
        cached = await self.redis.get_state(saga_id)
        if cached:
            return cached

        return await self.postgres.get_state(saga_id)

    async def list_sagas(
        self, status: Optional[str] = None, limit: int = 100
    ) -> List["SagaState"]:
        return await self.postgres.list_sagas(status, limit)
