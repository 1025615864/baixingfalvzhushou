"""Saga 分布式事务编排器

提供分布式事务的 Saga 模式实现，支持：
- 正向流程执行
- 补偿回滚机制
- 事务状态持久化
- 重试和手动干预
"""
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Optional
from enum import Enum
from dataclasses import dataclass, field
from sqlalchemy import Column, Integer, String, DateTime, JSON, Index
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)

Base = DeclarativeBase()


class SagaStatus(str, Enum):
    """Saga 事务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"
    FAILED = "failed"


class StepStatus(str, Enum):
    """步骤状态"""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"
    SKIPPED = "skipped"


class SagaExecutionLog(Base):
    """Saga 执行日志表"""
    __tablename__ = "saga_execution_logs"

    id = Column(String(36), primary_key=True)
    saga_type = Column(String(50), index=True)
    status = Column(String(20), index=True)
    correlation_id = Column(String(50), nullable=True, index=True)
    current_step = Column(Integer, default=0)
    total_steps = Column(Integer, default=0)
    steps_log = Column(JSON, nullable=True)
    error_message = Column(String(500), nullable=True)
    metadata = Column(JSON, nullable=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_saga_type_status", "saga_type", "status"),
        Index("ix_saga_correlation", "correlation_id"),
    )


@dataclass
class SagaStep:
    """Saga 步骤定义"""
    name: str
    action: Callable[..., Coroutine[Any, Any, Any]]
    compensate: Callable[..., Coroutine[Any, Any, Any]]
    description: str = ""
    max_retries: int = 3


@dataclass
class StepExecutionResult:
    """步骤执行结果"""
    step_name: str
    status: StepStatus
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class SagaOrchestrator:
    """Saga 编排器"""

    def __init__(self, db_session_factory, max_retries: int = 3):
        self.db_session_factory = db_session_factory
        self.max_retries = max_retries
        self.steps: list[SagaStep] = []
        self.execution_results: list[StepExecutionResult] = []

    def add_step(
        self,
        name: str,
        action: Callable[..., Coroutine[Any, Any, Any]],
        compensate: Callable[..., Coroutine[Any, Any, Any]],
        description: str = "",
        max_retries: int = None,
    ) -> "SagaOrchestrator":
        """添加 Saga 步骤"""
        self.steps.append(SagaStep(
            name=name,
            action=action,
            compensate=compensate,
            description=description,
            max_retries=max_retries or self.max_retries,
        ))
        return self

    async def execute(self, saga_type: str, correlation_id: str = None, **kwargs) -> dict:
        """执行 Saga 事务"""
        saga_id = str(uuid.uuid4())
        correlation_id = correlation_id or saga_id

        log = SagaExecutionLog(
            id=saga_id,
            saga_type=saga_type,
            status=SagaStatus.RUNNING.value,
            correlation_id=correlation_id,
            total_steps=len(self.steps),
            metadata=kwargs,
        )

        db = self.db_session_factory()
        db.add(log)
        db.commit()

        try:
            for idx, step in enumerate(self.steps):
                logger.info(f"Saga {saga_id}: Executing step {idx + 1}/{len(self.steps)}: {step.name}")
                log.current_step = idx + 1
                log.steps_log = self._serialize_results()
                db.commit()

                result = await self._execute_with_retry(step, idx, **kwargs)
                self.execution_results.append(result)

                if result.status == StepStatus.FAILED:
                    logger.error(f"Saga {saga_id}: Step {step.name} failed: {result.error}")
                    await self._compensate(db, log, **kwargs)
                    return self._build_result(SagaStatus.FAILED, log)

            log.status = SagaStatus.COMPLETED.value
            log.completed_at = datetime.now(timezone.utc)
            log.steps_log = self._serialize_results()
            db.commit()

            logger.info(f"Saga {saga_id}: Completed successfully")
            return self._build_result(SagaStatus.COMPLETED, log)

        except Exception as e:
            logger.error(f"Saga {saga_id}: Unexpected error: {e}")
            log.status = SagaStatus.FAILED.value
            log.error_message = str(e)
            log.completed_at = datetime.now(timezone.utc)
            db.commit()
            await self._compensate(db, log, **kwargs)
            return self._build_result(SagaStatus.FAILED, log)

        finally:
            db.close()

    async def _execute_with_retry(self, step: SagaStep, idx: int, **kwargs) -> StepExecutionResult:
        """带重试的步骤执行"""
        result = StepExecutionResult(
            step_name=step.name,
            status=StepStatus.PENDING,
            started_at=datetime.now(timezone.utc),
        )

        for attempt in range(step.max_retries):
            try:
                result.result = await step.action(**kwargs)
                result.status = StepStatus.SUCCESS
                result.completed_at = datetime.now(timezone.utc)
                logger.info(f"Step {step.name} succeeded on attempt {attempt + 1}")
                return result
            except Exception as e:
                result.error = str(e)
                logger.warning(f"Step {step.name} attempt {attempt + 1} failed: {e}")
                if attempt < step.max_retries - 1:
                    await self._wait_before_retry(attempt)

        result.status = StepStatus.FAILED
        result.completed_at = datetime.now(timezone.utc)
        return result

    async def _compensate(self, db, log: SagaExecutionLog, **kwargs):
        """执行补偿回滚"""
        log.status = SagaStatus.COMPENSATING.value
        db.commit()

        completed_steps = [r for r in self.execution_results if r.status == StepStatus.SUCCESS]
        for step_result in reversed(completed_steps):
            step = next((s for s in self.steps if s.name == step_result.step_name), None)
            if step:
                try:
                    logger.info(f"Compensating step: {step.name}")
                    await step.compensate(**kwargs, previous_result=step_result.result)
                    step_result.status = StepStatus.COMPENSATED
                except Exception as e:
                    logger.error(f"Compensation failed for {step.name}: {e}")
                    step_result.error = f"Compensation failed: {e}"

        log.status = SagaStatus.COMPENSATED.value
        log.completed_at = datetime.now(timezone.utc)
        log.steps_log = self._serialize_results()
        db.commit()

    async def _wait_before_retry(self, attempt: int):
        """重试前的等待"""
        import asyncio
        delay = min(2 ** attempt, 30)
        await asyncio.sleep(delay)

    def _serialize_results(self) -> list[dict]:
        """序列化执行结果"""
        return [
            {
                "step_name": r.step_name,
                "status": r.status.value,
                "error": r.error,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in self.execution_results
        ]

    def _build_result(self, status: SagaStatus, log: SagaExecutionLog) -> dict:
        """构建执行结果"""
        return {
            "saga_id": log.id,
            "status": status.value,
            "saga_type": log.saga_type,
            "correlation_id": log.correlation_id,
            "total_steps": log.total_steps,
            "completed_steps": len(self.execution_results),
            "steps": self._serialize_results(),
            "error_message": log.error_message,
            "started_at": log.started_at.isoformat() if log.started_at else None,
            "completed_at": log.completed_at.isoformat() if log.completed_at else None,
        }


def create_saga(db_session_factory, saga_type: str) -> SagaOrchestrator:
    """创建 Saga 编排器"""
    return SagaOrchestrator(db_session_factory)
