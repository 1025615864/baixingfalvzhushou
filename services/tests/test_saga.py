"""Saga 分布式事务编排器单元测试"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch

from services.common.saga.orchestrator import (
    SagaOrchestrator,
    SagaStep,
    StepExecutionResult,
    SagaExecutionLog,
    SagaStatus,
    StepStatus,
    create_saga,
)


class MockDBSession:
    """模拟数据库会话"""

    def __init__(self):
        self.records = []
        self.committed = False
        self.closed = False

    def add(self, obj):
        self.records.append(obj)

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True


def mock_db_session_factory():
    """创建模拟数据库会话工厂"""
    return MockDBSession


class TestSagaOrchestrator:
    """Saga 编排器测试"""

    @pytest.fixture
    def orchestrator(self):
        """创建测试编排器"""
        return SagaOrchestrator(
            db_session_factory=mock_db_session_factory(),
            max_retries=2,
        )

    def test_add_step(self, orchestrator):
        """测试添加步骤"""
        async def action(**kwargs):
            return {"result": "ok"}

        async def compensate(**kwargs):
            pass

        result = orchestrator.add_step(
            name="create_order",
            action=action,
            compensate=compensate,
            description="创建订单",
        )

        assert result is orchestrator
        assert len(orchestrator.steps) == 1
        assert orchestrator.steps[0].name == "create_order"

    def test_add_step_with_custom_retries(self, orchestrator):
        """测试添加带自定义重试次数的步骤"""
        async def action(**kwargs):
            return {}

        async def compensate(**kwargs):
            pass

        orchestrator.add_step(
            name="retry_step",
            action=action,
            compensate=compensate,
            max_retries=5,
        )

        assert orchestrator.steps[0].max_retries == 5

    @pytest.mark.asyncio
    async def test_execute_success(self, orchestrator):
        """测试成功执行 Saga"""
        call_order = []

        async def step1(**kwargs):
            call_order.append("step1")
            return {"order_id": "123"}

        async def compensate1(**kwargs):
            call_order.append("compensate1")

        async def step2(**kwargs):
            call_order.append("step2")
            return {"payment_id": "456"}

        async def compensate2(**kwargs):
            call_order.append("compensate2")

        orchestrator.add_step("create_order", step1, compensate1)
        orchestrator.add_step("process_payment", step2, compensate2)

        result = await orchestrator.execute(
            saga_type="order_creation",
            correlation_id="test-001",
            user_id=123,
        )

        assert result["status"] == "completed"
        assert result["saga_type"] == "order_creation"
        assert result["total_steps"] == 2
        assert len(result["steps"]) == 2
        assert call_order == ["step1", "step2"]

    @pytest.mark.asyncio
    async def test_execute_with_compensation(self, orchestrator):
        """测试失败时执行补偿"""
        call_order = []

        async def step1(**kwargs):
            call_order.append("step1")
            return {"order_id": "123"}

        async def compensate1(**kwargs):
            call_order.append("compensate1")

        async def step2(**kwargs):
            call_order.append("step2")
            raise ValueError("Payment failed")

        async def compensate2(**kwargs):
            call_order.append("compensate2")

        orchestrator.add_step("create_order", step1, compensate1)
        orchestrator.add_step("process_payment", step2, compensate2)

        result = await orchestrator.execute(
            saga_type="order_creation",
            correlation_id="test-002",
        )

        assert result["status"] == "failed"
        assert "step1" in call_order
        assert "step2" in call_order
        assert "compensate1" in call_order

    @pytest.mark.asyncio
    async def test_execute_with_retry(self, orchestrator):
        """测试步骤重试机制"""
        attempt_count = 0

        async def flaky_step(**kwargs):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise ValueError("Temporary failure")
            return {"result": "ok"}

        async def compensate(**kwargs):
            pass

        orchestrator.add_step(
            "flaky_operation",
            flaky_step,
            compensate,
            max_retries=3,
        )

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await orchestrator.execute(
                saga_type="retry_test",
                correlation_id="test-003",
            )

        assert result["status"] == "completed"
        assert attempt_count == 2

    @pytest.mark.asyncio
    async def test_create_saga_helper(self):
        """测试 create_saga 辅助函数"""
        saga = create_saga(
            db_session_factory=mock_db_session_factory(),
            saga_type="test_saga",
        )

        assert isinstance(saga, SagaOrchestrator)

    def test_saga_execution_log_model(self):
        """测试 SagaExecutionLog 模型"""
        log = SagaExecutionLog(
            id="test-id",
            saga_type="order_creation",
            status=SagaStatus.RUNNING.value,
            correlation_id="corr-123",
            total_steps=3,
        )

        assert log.id == "test-id"
        assert log.saga_type == "order_creation"
        assert log.status == "running"
        assert log.total_steps == 3

    def test_step_execution_result(self):
        """测试 StepExecutionResult 数据类"""
        result = StepExecutionResult(
            step_name="create_order",
            status=StepStatus.SUCCESS,
            result={"order_id": "123"},
            started_at=datetime(2024, 1, 1, 10, 0, 0),
            completed_at=datetime(2024, 1, 1, 10, 0, 1),
        )

        assert result.step_name == "create_order"
        assert result.status == StepStatus.SUCCESS
        assert result.result == {"order_id": "123"}

    def test_saga_status_enum(self):
        """测试 SagaStatus 枚举"""
        assert SagaStatus.PENDING.value == "pending"
        assert SagaStatus.RUNNING.value == "running"
        assert SagaStatus.COMPLETED.value == "completed"
        assert SagaStatus.COMPENSATING.value == "compensating"
        assert SagaStatus.COMPENSATED.value == "compensated"
        assert SagaStatus.FAILED.value == "failed"

    def test_step_status_enum(self):
        """测试 StepStatus 枚举"""
        assert StepStatus.PENDING.value == "pending"
        assert StepStatus.SUCCESS.value == "success"
        assert StepStatus.FAILED.value == "failed"
        assert StepStatus.COMPENSATING.value == "compensating"
        assert StepStatus.COMPENSATED.value == "compensated"
        assert StepStatus.SKIPPED.value == "skipped"


class TestSagaExecutionLog:
    """Saga 执行日志测试"""

    def test_log_serialization(self):
        """测试日志序列化"""
        log = SagaExecutionLog(
            id="test-123",
            saga_type="payment",
            status=SagaStatus.COMPLETED.value,
            correlation_id="corr-456",
            current_step=3,
            total_steps=3,
            steps_log=[
                {"step_name": "step1", "status": "success"},
            ],
            error_message=None,
            metadata={"user_id": 123},
        )

        assert log.id == "test-123"
        assert log.steps_log is not None
        assert log.metadata["user_id"] == 123
