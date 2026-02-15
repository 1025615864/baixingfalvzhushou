"""测试 A/B 测试路由"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException


class TestABTestingRouter:
    """测试 A/B 测试路由"""

    @pytest.mark.asyncio
    async def test_create_ab_experiment_success(self):
        """测试创建实验成功"""
        from app.routers.ab_testing import create_ab_experiment
        
        with patch('app.routers.ab_testing.create_experiment') as mock_create:
            mock_create.return_value = {"experiment_id": "test_exp", "name": "Test"}
            
            result = await create_ab_experiment(
                experiment_id="test_exp",
                name="Test Experiment",
                variants='["A", "B"]',
                traffic_percentage=50
            )
            
            assert result["experiment_id"] == "test_exp"

    @pytest.mark.asyncio
    async def test_create_ab_experiment_invalid_json(self):
        """测试创建实验时 JSON 格式无效"""
        from app.routers.ab_testing import create_ab_experiment
        
        with pytest.raises(HTTPException) as exc_info:
            await create_ab_experiment(
                experiment_id="test_exp",
                name="Test Experiment",
                variants='invalid json',
                traffic_percentage=50
            )
        
        assert exc_info.value.status_code == 400
        assert "variants 格式无效" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_list_ab_experiments(self):
        """测试列出所有实验"""
        from app.routers.ab_testing import list_ab_experiments
        
        with patch('app.routers.ab_testing.ab_test_service') as mock_service:
            mock_service._configurator.list_experiments.return_value = [
                {"id": "exp1", "name": "Experiment 1"}
            ]
            
            result = await list_ab_experiments()
            
            assert "experiments" in result
            assert len(result["experiments"]) == 1

    @pytest.mark.asyncio
    async def test_get_ab_experiment_found(self):
        """测试获取实验详情（实验存在）"""
        from app.routers.ab_testing import get_ab_experiment
        
        with patch('app.routers.ab_testing.ab_test_service') as mock_service:
            mock_service._configurator.get_experiment.return_value = {
                "id": "exp1",
                "name": "Experiment 1"
            }
            
            result = await get_ab_experiment("exp1")
            
            assert result["id"] == "exp1"

    @pytest.mark.asyncio
    async def test_get_ab_experiment_not_found(self):
        """测试获取实验详情（实验不存在）"""
        from app.routers.ab_testing import get_ab_experiment
        
        with patch('app.routers.ab_testing.ab_test_service') as mock_service:
            mock_service._configurator.get_experiment.return_value = None
            
            with pytest.raises(HTTPException) as exc_info:
                await get_ab_experiment("nonexistent")
            
            assert exc_info.value.status_code == 404
            assert "实验不存在" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_update_ab_experiment_status(self):
        """测试更新实验状态"""
        from app.routers.ab_testing import update_ab_experiment_status
        
        with patch('app.routers.ab_testing.ab_test_service') as mock_service:
            mock_service._configurator.update_experiment_status.return_value = {
                "id": "exp1",
                "status": "running"
            }
            
            result = await update_ab_experiment_status("exp1", "running")
            
            assert result["status"] == "running"

    @pytest.mark.asyncio
    async def test_assign_ab_variant_success(self):
        """测试分配变体成功"""
        from app.routers.ab_testing import assign_ab_variant
        from app.models.user import User
        
        mock_user = User(id=123, username="test_user")
        
        with patch('app.routers.ab_testing.assign_variant') as mock_assign:
            mock_assign.return_value = {"variant": "A"}
            
            result = await assign_ab_variant(
                experiment_id="test_exp",
                variants='["A", "B"]',
                traffic_percentage=50,
                current_user=mock_user
            )
            
            assert result["variant"] == "A"

    @pytest.mark.asyncio
    async def test_assign_ab_variant_no_user(self):
        """测试分配变体（无用户）"""
        from app.routers.ab_testing import assign_ab_variant
        
        with patch('app.routers.ab_testing.assign_variant') as mock_assign:
            mock_assign.return_value = {"variant": "A"}
            
            result = await assign_ab_variant(
                experiment_id="test_exp",
                variants='["A", "B"]',
                traffic_percentage=50,
                current_user=None
            )
            
            assert result["variant"] == "A"

    @pytest.mark.asyncio
    async def test_assign_ab_variant_invalid_json(self):
        """测试分配变体时 JSON 格式无效"""
        from app.routers.ab_testing import assign_ab_variant
        
        with pytest.raises(HTTPException) as exc_info:
            await assign_ab_variant(
                experiment_id="test_exp",
                variants='invalid json',
                traffic_percentage=50,
                current_user=None
            )
        
        assert exc_info.value.status_code == 400
        assert "variants 格式无效" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_ab_experiment_analysis(self):
        """测试获取实验分析结果"""
        from app.routers.ab_testing import get_ab_experiment_analysis
        
        with patch('app.routers.ab_testing.analyze_experiment') as mock_analyze:
            mock_analyze.return_value = {
                "experiment_id": "test_exp",
                "results": {"A": 100, "B": 150}
            }
            
            result = await get_ab_experiment_analysis("test_exp")
            
            assert result["experiment_id"] == "test_exp"

    @pytest.mark.asyncio
    async def test_record_ab_metric(self):
        """测试记录实验指标"""
        from app.routers.ab_testing import record_ab_metric
        from app.models.user import User
        
        mock_user = User(id=123, username="test_user")
        
        with patch('app.routers.ab_testing.ab_test_service') as mock_service:
            mock_service.record_metric.return_value = {"success": True}
            
            result = await record_ab_metric(
                current_user=mock_user,
                experiment_id="test_exp",
                metric_name="clicks",
                value=10.0
            )
            
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_get_ab_stats(self):
        """测试获取实验统计信息"""
        from app.routers.ab_testing import get_ab_stats
        
        with patch('app.routers.ab_testing.ab_test_service') as mock_service:
            mock_service.get_experiment_stats.return_value = {
                "total_experiments": 10,
                "active_experiments": 5
            }
            
            result = await get_ab_stats()
            
            assert result["total_experiments"] == 10
