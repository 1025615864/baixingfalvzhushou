"""A/B 测试框架服务

提供流量分配和效果统计功能。
"""
import logging
import random
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class ExperimentConfigurator:
    """实验配置器"""

    def __init__(self):
        self._experiments: dict[str, dict[str, Any]] = {}

    def create_experiment(
        self,
        experiment_id: str,
        name: str,
        variants: list[dict[str, str]],
        traffic_percentage: int = 100,
    ) -> dict[str, Any]:
        """创建实验

        Args:
            experiment_id: 实验ID
            name: 名称
            variants: 变体列表
            traffic_percentage: 流量百分比

        Returns:
            配置结果
        """
        self._experiments[experiment_id] = {
            "id": experiment_id,
            "name": name,
            "variants": variants,
            "traffic_percentage": traffic_percentage,
            "status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        return {
            "id": experiment_id,
            "name": name,
            "variants_count": len(variants),
            "traffic_percentage": traffic_percentage,
            "configured": True,
        }

    def get_experiment(self, experiment_id: str) -> dict[str, Any]:
        """获取实验配置

        Args:
            experiment_id: 实验ID

        Returns:
            实验配置
        """
        return self._experiments.get(experiment_id, {})

    def list_experiments(self) -> list[dict[str, Any]]:
        """列出所有实验

        Returns:
            实验列表
        """
        return list(self._experiments.values())

    def update_experiment_status(
        self,
        experiment_id: str,
        status: str,
    ) -> dict[str, Any]:
        """更新实验状态

        Args:
            experiment_id: 实验ID
            status: 状态

        Returns:
            更新结果
        """
        if experiment_id in self._experiments:
            self._experiments[experiment_id]["status"] = status
            return {"id": experiment_id, "status": status, "updated": True}

        return {"id": experiment_id, "status": None, "updated": False}


class TrafficAllocator:
    """流量分配器"""

    def __init__(self):
        self._allocations: dict[int, dict[str, str]] = {}

    def assign_variant(
        self,
        user_id: int,
        experiment_id: str,
        variants: list[dict[str, str]],
        traffic_percentage: int = 100,
    ) -> dict[str, Any]:
        """分配变体

        Args:
            user_id: 用户ID
            experiment_id: 实验ID
            variants: 变体列表
            traffic_percentage: 流量百分比

        Returns:
            分配结果
        """
        key = f"{experiment_id}_{user_id}"

        if key in self._allocations:
            return {
                "user_id": user_id,
                "experiment_id": experiment_id,
                "variant_id": self._allocations[key],
                "source": "cache",
            }

        if random.randint(1, 100) > traffic_percentage:
            self._allocations[key] = "control"
            return {
                "user_id": user_id,
                "experiment_id": experiment_id,
                "variant_id": "control",
                "source": "excluded",
            }

        variant_weights = {}
        for i, variant in enumerate(variants):
            variant_id = variant.get("id", f"variant_{i}")
            weight = variant.get("weight", 1)
            variant_weights[variant_id] = weight

        total_weight = sum(variant_weights.values())
        random_value = random.randint(1, total_weight)
        cumulative = 0

        for variant_id, weight in variant_weights.items():
            cumulative += weight
            if random_value <= cumulative:
                self._allocations[key] = variant_id
                return {
                    "user_id": user_id,
                    "experiment_id": experiment_id,
                    "variant_id": variant_id,
                    "source": "random",
                }

        self._allocations[key] = "control"
        return {
            "user_id": user_id,
            "experiment_id": experiment_id,
            "variant_id": "control",
            "source": "default",
        }

    def get_user_variant(self, user_id: int, experiment_id: str) -> str:
        """获取用户变体

        Args:
            user_id: 用户ID
            experiment_id: 实验ID

        Returns:
            变体ID
        """
        key = f"{experiment_id}_{user_id}"
        return self._allocations.get(key, "control")


class ExperimentAnalyzer:
    """实验分析器"""

    def __init__(self):
        self._configurator = ExperimentConfigurator()
        self._allocator = TrafficAllocator()
        self._metrics: dict[str, dict[str, Any]] = {}

    def record_metric(
        self,
        user_id: int,
        experiment_id: str,
        metric_name: str,
        value: float,
    ) -> dict[str, Any]:
        """记录指标

        Args:
            user_id: 用户ID
            experiment_id: 实验ID
            metric_name: 指标名称
            value: 值

        Returns:
            记录结果
        """
        variant = self._allocator.get_user_variant(user_id, experiment_id)

        if experiment_id not in self._metrics:
            self._metrics[experiment_id] = {}

        if variant not in self._metrics[experiment_id]:
            self._metrics[experiment_id][variant] = {
                "values": [],
                "count": 0,
                "sum": 0,
            }

        self._metrics[experiment_id][variant]["values"].append(value)
        self._metrics[experiment_id][variant]["count"] += 1
        self._metrics[experiment_id][variant]["sum"] += value

        return {
            "user_id": user_id,
            "experiment_id": experiment_id,
            "variant": variant,
            "metric_name": metric_name,
            "recorded": True,
        }

    def analyze_experiment(self, experiment_id: str) -> dict[str, Any]:
        """分析实验

        Args:
            experiment_id: 实验ID

        Returns:
            分析结果
        """
        experiment = self._configurator.get_experiment(experiment_id)
        if not experiment:
            return {"error": "Experiment not found"}

        metrics = self._metrics.get(experiment_id, {})
        results = {}

        for variant, data in metrics.items():
            avg_value = data["sum"] / max(data["count"], 1)
            results[variant] = {
                "count": data["count"],
                "sum": data["sum"],
                "average": round(avg_value, 4),
            }

        control_data = results.get("control", {})
        treatment_data = {k: v for k, v in results.items() if k != "control"}

        comparison = {}
        for variant_id, variant_data in treatment_data.items():
            if control_data:
                lift = ((variant_data["average"] - control_data["average"]
                         ) / max(control_data["average"], 0.001)) * 100
                comparison[variant_id] = {
                    "lift": round(lift, 2),
                    "is_significant": abs(lift) > 5,
                }

        return {
            "experiment_id": experiment_id,
            "experiment_name": experiment.get("name", ""),
            "status": experiment.get("status", ""),
            "results": results,
            "comparison": comparison,
        }

    def get_experiment_stats(self) -> dict[str, Any]:
        """获取实验统计

        Returns:
            统计数据
        """
        experiments = self._configurator.list_experiments()
        total_users = len(self._allocator._allocations)

        return {
            "total_experiments": len(experiments),
            "active_experiments": sum(
                1 for e in experiments if e.get("status") == "running"),
            "total_users_assigned": total_users,
        }


# 单例实例
ab_test_service = ExperimentAnalyzer()


async def create_experiment(
    experiment_id: str,
    name: str,
    variants: list[dict[str, str]],
    traffic_percentage: int = 100,
) -> dict[str, Any]:
    """便捷函数：创建实验

    Args:
        experiment_id: 实验ID
        name: 名称
        variants: 变体列表
        traffic_percentage: 流量百分比

    Returns:
        配置结果
    """
    return ab_test_service._configurator.create_experiment(
        experiment_id=experiment_id,
        name=name,
        variants=variants,
        traffic_percentage=traffic_percentage,
    )


async def assign_variant(
    user_id: int,
    experiment_id: str,
    variants: list[dict[str, str]],
    traffic_percentage: int = 100,
) -> dict[str, Any]:
    """便捷函数：分配变体

    Args:
        user_id: 用户ID
        experiment_id: 实验ID
        variants: 变体列表
        traffic_percentage: 流量百分比

    Returns:
        分配结果
    """
    return ab_test_service._allocator.assign_variant(
        user_id=user_id,
        experiment_id=experiment_id,
        variants=variants,
        traffic_percentage=traffic_percentage,
    )


async def analyze_experiment(experiment_id: str) -> dict[str, Any]:
    """便捷函数：分析实验

    Args:
        experiment_id: 实验ID

    Returns:
        分析结果
    """
    return ab_test_service.analyze_experiment(experiment_id)
