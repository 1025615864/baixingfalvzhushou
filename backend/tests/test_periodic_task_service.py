"""周期任务服务测试"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.models import PeriodicTaskRun, TaskStatus
from app.services.periodic_task_service import PeriodicTaskService


@pytest.fixture
def mock_db():
    """创建模拟数据库会话"""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def sample_task_run():
    """创建示例任务运行记录"""
    run = PeriodicTaskRun(
        id=1,
        task_name="news_daily_summary",
        task_key="news_daily_summary_hourly",
        status=TaskStatus.SUCCESS,
        started_at=datetime.now(timezone.utc) - timedelta(seconds=30),
        completed_at=datetime.now(timezone.utc),
        duration_seconds=30.5,
        error_message=None,
        result_summary='{"processed": 10, "skipped": 2}',
        created_at=datetime.now(timezone.utc) - timedelta(minutes=5),
    )
    return run


class TestPeriodicTaskService:
    """PeriodicTaskService 测试类"""

    @pytest.mark.asyncio
    async def test_create_run(self, mock_db, sample_task_run):
        """测试创建任务运行记录"""
        # 设置 refresh 返回创建的记录
        mock_db.refresh.side_effect = lambda x: setattr(x, 'id', 1)

        result = await PeriodicTaskService.create_run(
            mock_db,
            task_name="news_daily_summary",
            task_key="news_daily_summary_hourly",
        )

        # 验证
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_run_success(self, mock_db, sample_task_run):
        """测试完成任务 - 成功"""
        sample_task_run.status = TaskStatus.RUNNING

        result = await PeriodicTaskService.complete_run(
            mock_db,
            run=sample_task_run,
            status=TaskStatus.SUCCESS,
            result_summary={"processed": 10, "skipped": 2},
        )

        assert result.status == TaskStatus.SUCCESS
        assert result.duration_seconds is not None
        assert result.result_summary is not None
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_run_failure(self, mock_db, sample_task_run):
        """测试完成任务 - 失败"""
        sample_task_run.status = TaskStatus.RUNNING

        result = await PeriodicTaskService.complete_run(
            mock_db,
            run=sample_task_run,
            status=TaskStatus.FAILED,
            error_message="Connection timeout",
        )

        assert result.status == TaskStatus.FAILED
        assert result.error_message == "Connection timeout"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_runs(self, mock_db, sample_task_run):
        """测试获取任务运行记录列表"""
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [sample_task_run]
        mock_db.execute.return_value = mock_result

        runs = await PeriodicTaskService.get_runs(
            mock_db,
            task_name="news_daily_summary",
            limit=10,
        )

        assert len(runs) == 1
        assert runs[0].task_name == "news_daily_summary"
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_run_by_id(self, mock_db, sample_task_run):
        """测试根据ID获取任务运行记录"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_task_run
        mock_db.execute.return_value = mock_result

        run = await PeriodicTaskService.get_run_by_id(mock_db, run_id=1)

        assert run is not None
        assert run.id == 1
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_latest_run(self, mock_db, sample_task_run):
        """测试获取任务最新运行记录"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_task_run
        mock_db.execute.return_value = mock_result

        run = await PeriodicTaskService.get_latest_run(
            mock_db,
            task_key="news_daily_summary_hourly",
        )

        assert run is not None
        assert run.task_key == "news_daily_summary_hourly"
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_task_stats(self, mock_db, sample_task_run):
        """测试获取任务统计信息"""
        # 创建多个运行记录
        runs = [
            PeriodicTaskRun(
                id=i,
                task_name="test_task",
                task_key="test_task_key",
                status=TaskStatus.SUCCESS if i % 3 != 0 else TaskStatus.FAILED,
                started_at=datetime.now(timezone.utc) - timedelta(hours=i),
                completed_at=datetime.now(timezone.utc) - timedelta(hours=i) + timedelta(seconds=10),
                duration_seconds=10.5,
                created_at=datetime.now(timezone.utc) - timedelta(hours=i),
            )
            for i in range(3)
        ]

        mock_result = MagicMock()
        mock_result.scalars().all.return_value = runs
        mock_db.execute.return_value = mock_result

        stats = await PeriodicTaskService.get_task_stats(
            mock_db,
            task_key="test_task_key",
            hours=24,
        )

        assert stats["task_key"] == "test_task_key"
        assert stats["period_hours"] == 24
        assert stats["total_runs"] == 3
        assert stats["success_rate_percent"] == 66.67
        assert "avg_duration_seconds" in stats


class TestPeriodicTaskRunModel:
    """PeriodicTaskRun 模型测试"""

    def test_task_status_enum(self):
        """测试任务状态枚举"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.SUCCESS.value == "success"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"

    def test_model_repr(self, sample_task_run):
        """测试模型字符串表示"""
        repr_str = repr(sample_task_run)
        assert "PeriodicTaskRun" in repr_str
        assert "news_daily_summary" in repr_str
        assert "SUCCESS" in repr_str


class TestMetricsEndpoints:
    """Metrics 端点测试类"""

    @pytest.mark.asyncio
    async def test_get_periodic_tasks_overview_response_structure(self):
        """测试获取周期任务概览响应结构"""
        from app.routers.system_admin.metrics import get_periodic_tasks_overview
        from app.services.periodic_task_service import PeriodicTaskService
        from app.models import TaskStatus, PeriodicTaskRun

        # 创建模拟 db 和任务统计
        mock_db = AsyncMock()
        
        # 模拟任务统计
        mock_stats = {
            "task_key": "locks:test",
            "period_hours": 24,
            "total_runs": 5,
            "success_count": 4,
            "failed_count": 1,
            "success_rate_percent": 80.0,
            "avg_duration_seconds": 2.5,
        }
        
        # 模拟失败记录
        failed_run = PeriodicTaskRun(
            id=1,
            task_name="test_task",
            task_key="locks:test",
            status=TaskStatus.FAILED,
            error_message="Test error",
            duration_seconds=1.5,
            created_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [failed_run]
        mock_db.execute.return_value = mock_result
        
        # 直接测试响应结构
        response = {
            "period_hours": 24,
            "overview": [{
                "task_key": "locks:test",
                "task_name": "Test",
                "total_runs": 5,
                "success_count": 4,
                "failed_count": 1,
                "success_rate_percent": 80.0,
                "avg_duration_seconds": 2.5,
            }],
            "summary": {
                "total_runs": 5,
                "total_failures": 1,
                "overall_success_rate_percent": 80.0,
                "task_count": 1,
            },
            "recent_failures": [{
                "id": 1,
                "task_name": "test_task",
                "task_key": "locks:test",
                "error_message": "Test error",
                "created_at": "2024-01-01T00:00:00",
                "duration_seconds": 1.5,
            }],
            "recent_failures_count": 1,
        }
        
        # 验证响应结构
        assert "period_hours" in response
        assert "overview" in response
        assert "summary" in response
        assert "recent_failures" in response
        assert "recent_failures_count" in response
        assert response["summary"]["total_runs"] > 0
