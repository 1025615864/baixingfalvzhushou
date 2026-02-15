"""A/B 测试框架服务测试"""
from __future__ import annotations

import random

import pytest

from app.services.ab_testing import (
    ExperimentConfigurator,
    TrafficAllocator,
    ExperimentAnalyzer,
    ab_test_service,
    create_experiment,
    assign_variant,
    analyze_experiment,
)


class TestExperimentConfigurator:
    """实验配置器测试"""

    def test_create_experiment(self):
        """测试创建实验"""
        configurator = ExperimentConfigurator()
        variants = [
            {"id": "control", "name": "对照组"},
            {"id": "treatment", "name": "实验组"},
        ]
        result = configurator.create_experiment(
            experiment_id="test_exp",
            name="测试实验",
            variants=variants,
            traffic_percentage=50,
        )

        assert result["id"] == "test_exp"
        assert result["variants_count"] == 2
        assert result["traffic_percentage"] == 50
        assert result["configured"] is True

        # 验证实验已保存
        experiment = configurator.get_experiment("test_exp")
        assert experiment["id"] == "test_exp"
        assert experiment["name"] == "测试实验"
        assert experiment["status"] == "draft"

    def test_get_experiment_not_found(self):
        """测试获取不存在的实验"""
        configurator = ExperimentConfigurator()
        result = configurator.get_experiment("nonexistent")
        assert result == {}

    def test_list_experiments(self):
        """测试列出所有实验"""
        configurator = ExperimentConfigurator()
        configurator.create_experiment(
            experiment_id="exp1",
            name="实验1",
            variants=[{"id": "control"}],
        )
        configurator.create_experiment(
            experiment_id="exp2",
            name="实验2",
            variants=[{"id": "treatment"}],
        )

        experiments = configurator.list_experiments()
        assert len(experiments) == 2

    def test_update_experiment_status(self):
        """测试更新实验状态"""
        configurator = ExperimentConfigurator()
        configurator.create_experiment(
            experiment_id="test_exp",
            name="测试实验",
            variants=[{"id": "control"}],
        )

        result = configurator.update_experiment_status("test_exp", "running")
        assert result["id"] == "test_exp"
        assert result["status"] == "running"
        assert result["updated"] is True

        # 验证状态已更新
        experiment = configurator.get_experiment("test_exp")
        assert experiment["status"] == "running"

    def test_update_experiment_status_not_found(self):
        """测试更新不存在的实验状态"""
        configurator = ExperimentConfigurator()
        result = configurator.update_experiment_status("nonexistent", "running")
        assert result["id"] == "nonexistent"
        assert result["status"] is None
        assert result["updated"] is False


class TestTrafficAllocator:
    """流量分配器测试"""

    def test_assign_variant_first_time(self):
        """测试首次分配变体"""
        allocator = TrafficAllocator()
        variants = [
            {"id": "control", "weight": 1},
            {"id": "treatment", "weight": 1},
        ]

        result = allocator.assign_variant(
            user_id=1,
            experiment_id="test_exp",
            variants=variants,
            traffic_percentage=100,
        )

        assert result["user_id"] == 1
        assert result["experiment_id"] == "test_exp"
        assert result["variant_id"] in ["control", "treatment"]
        assert result["source"] == "random"

    def test_assign_variant_cached(self):
        """测试缓存的变体分配"""
        allocator = TrafficAllocator()
        variants = [{"id": "control", "weight": 1}]

        # 首次分配
        allocator.assign_variant(
            user_id=1,
            experiment_id="test_exp",
            variants=variants,
            traffic_percentage=100,
        )

        # 第二次分配应使用缓存
        result = allocator.assign_variant(
            user_id=1,
            experiment_id="test_exp",
            variants=variants,
            traffic_percentage=100,
        )

        assert result["source"] == "cache"

    def test_assign_variant_excluded_by_traffic(self):
        """测试流量百分比排除"""
        from unittest.mock import patch

        allocator = TrafficAllocator()
        variants = [{"id": "control", "weight": 1}]

        # 使用固定随机值确保被排除
        with patch("random.randint", return_value=101):
            result = allocator.assign_variant(
                user_id=1,
                experiment_id="test_exp",
                variants=variants,
                traffic_percentage=50,
            )

        assert result["variant_id"] == "control"
        assert result["source"] == "excluded"

    def test_get_user_variant(self):
        """测试获取用户变体"""
        allocator = TrafficAllocator()
        variants = [{"id": "treatment", "weight": 1}]

        allocator.assign_variant(
            user_id=1,
            experiment_id="test_exp",
            variants=variants,
            traffic_percentage=100,
        )

        variant = allocator.get_user_variant(1, "test_exp")
        assert variant == "treatment"

    def test_get_user_variant_not_assigned(self):
        """测试获取未分配用户的变体"""
        allocator = TrafficAllocator()
        variant = allocator.get_user_variant(999, "test_exp")
        assert variant == "control"


class TestExperimentAnalyzer:
    """实验分析器测试"""

    def test_record_metric(self):
        """测试记录指标"""
        analyzer = ExperimentAnalyzer()
        analyzer._allocator._allocations["test_exp_1"] = "treatment"

        result = analyzer.record_metric(
            user_id=1,
            experiment_id="test_exp",
            metric_name="conversion",
            value=1.0,
        )

        assert result["user_id"] == 1
        assert result["experiment_id"] == "test_exp"
        assert result["variant"] == "treatment"
        assert result["metric_name"] == "conversion"
        assert result["recorded"] is True

    def test_analyze_experiment_not_found(self):
        """测试分析不存在的实验"""
        analyzer = ExperimentAnalyzer()
        result = analyzer.analyze_experiment("nonexistent")
        assert result["error"] == "Experiment not found"

    def test_analyze_experiment_success(self):
        """测试成功分析实验"""
        analyzer = ExperimentAnalyzer()
        analyzer._configurator.create_experiment(
            experiment_id="test_exp",
            name="测试实验",
            variants=[{"id": "control"}, {"id": "treatment"}],
        )
        analyzer._allocator._allocations["test_exp_1"] = "control"
        analyzer._allocator._allocations["test_exp_2"] = "treatment"

        analyzer.record_metric(user_id=1, experiment_id="test_exp", metric_name="conversion", value=1.0)
        analyzer.record_metric(user_id=2, experiment_id="test_exp", metric_name="conversion", value=2.0)

        result = analyzer.analyze_experiment("test_exp")
        assert result["experiment_id"] == "test_exp"
        assert result["experiment_name"] == "测试实验"
        assert "results" in result
        assert "comparison" in result

    def test_get_experiment_stats(self):
        """测试获取实验统计"""
        analyzer = ExperimentAnalyzer()
        analyzer._configurator.create_experiment(
            experiment_id="exp1",
            name="实验1",
            variants=[{"id": "control"}],
        )
        analyzer._configurator.update_experiment_status("exp1", "running")
        analyzer._allocator._allocations["exp1_1"] = "control"
        analyzer._allocator._allocations["exp1_2"] = "treatment"

        stats = analyzer.get_experiment_stats()
        assert stats["total_experiments"] == 1
        assert stats["active_experiments"] == 1
        assert stats["total_users_assigned"] == 2


class TestConvenienceFunctions:
    """便捷函数测试"""

    @pytest.mark.asyncio
    async def test_create_experiment_convenience(self):
        """测试创建实验便捷函数"""
        variants = [{"id": "control"}]
        result = await create_experiment(
            experiment_id="test_exp",
            name="测试实验",
            variants=variants,
        )
        assert result["configured"] is True

    @pytest.mark.asyncio
    async def test_assign_variant_convenience(self):
        """测试分配变体便捷函数"""
        variants = [{"id": "treatment", "weight": 1}]
        result = await assign_variant(
            user_id=1,
            experiment_id="test_exp",
            variants=variants,
        )
        assert result["user_id"] == 1

    @pytest.mark.asyncio
    async def test_analyze_experiment_convenience(self):
        """测试分析实验便捷函数"""
        # 先创建实验
        await create_experiment(
            experiment_id="test_exp",
            name="测试实验",
            variants=[{"id": "control"}],
        )
        result = await analyze_experiment("test_exp")
        assert result["experiment_id"] == "test_exp"


class TestSingletonService:
    """单例服务测试"""

    def test_ab_test_service_singleton(self):
        """测试A/B测试服务单例"""
        assert ab_test_service is not None
        assert isinstance(ab_test_service, ExperimentAnalyzer)
