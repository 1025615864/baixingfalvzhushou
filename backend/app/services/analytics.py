"""数据分析平台服务

提供业务数据看板、核心指标、趋势图表等功能。
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class MetricsCollector:
    """指标收集器"""

    def __init__(self):
        self._metrics: dict[str, dict[str, Any]] = {}
        self._events: list[dict[str, Any]] = []

    async def record_metric(
        self,
        metric_name: str,
        value: int | float,
        dimensions: dict[str, str] | None = None,
    ) -> None:
        """记录指标

        Args:
            metric_name: 指标名称
            value: 值
            dimensions: 维度
        """
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        hour = datetime.now(timezone.utc).strftime("%H")

        key = f"{metric_name}_{date}_{hour}"
        dim_key = str(sorted(dimensions.items())) if dimensions else "default"

        if key not in self._metrics:
            self._metrics[key] = {
                "metric_name": metric_name,
                "date": date,
                "hour": hour,
                "dimensions": dimensions,
                "values": {},
            }

        if dim_key not in self._metrics[key]["values"]:
            self._metrics[key]["values"][dim_key] = []

        self._metrics[key]["values"][dim_key].append(value)

        logger.info(f"Recorded metric {metric_name}: {value}")

    async def record_event(
        self,
        event_type: str,
        user_id: int | None = None,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """记录事件

        Args:
            event_type: 事件类型
            user_id: 用户ID
            properties: 属性
        """
        event = {
            "id": len(self._events) + 1,
            "event_type": event_type,
            "user_id": user_id,
            "properties": properties or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self._events.append(event)

    def get_metric_series(
        self,
        metric_name: str,
        days: int = 7,
    ) -> list[dict[str, Any]]:
        """获取指标时序数据

        Args:
            metric_name: 指标名称
            days: 天数

        Returns:
            时序数据
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        results = []
        current = start_date.date()

        while current <= end_date.date():
            date_str = current.strftime("%Y-%m-%d")
            total = 0

            for key, metric in self._metrics.items():
                if metric["metric_name"] == metric_name and metric["date"] == date_str:
                    for values in metric["values"].values():
                        total += sum(values)

            results.append({
                "date": date_str,
                "value": total,
            })

            current += timedelta(days=1)

        return results


class DashboardManager:
    """看板管理器"""

    def __init__(self):
        self._dashboards: dict[str, dict[str, Any]] = {}
        self._widgets: list[dict[str, Any]] = []

    def create_dashboard(
        self,
        name: str,
        description: str = "",
    ) -> dict[str, Any]:
        """创建看板

        Args:
            name: 名称
            description: 描述

        Returns:
            看板信息
        """
        dashboard_id = f"DB-{len(self._dashboards) + 1:04d}"
        now = datetime.now(timezone.utc).isoformat()

        dashboard = {
            "id": dashboard_id,
            "name": name,
            "description": description,
            "created_at": now,
            "updated_at": now,
            "widgets": [],
        }

        self._dashboards[dashboard_id] = dashboard

        logger.info(f"Created dashboard {dashboard_id}: {name}")

        return {
            "dashboard_id": dashboard_id,
            "name": name,
        }

    def add_widget(
        self,
        dashboard_id: str,
        widget_type: str,
        title: str,
        metric_name: str,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """添加组件

        Args:
            dashboard_id: 看板ID
            widget_type: 组件类型
            title: 标题
            metric_name: 指标名称
            config: 配置

        Returns:
            组件信息
        """
        dashboard = self._dashboards.get(dashboard_id)

        if not dashboard:
            return {
                "success": False,
                "error": "看板不存在",
            }

        widget = {
            "id": len(self._widgets) + 1,
            "dashboard_id": dashboard_id,
            "widget_type": widget_type,
            "title": title,
            "metric_name": metric_name,
            "config": config or {},
        }

        self._widgets.append(widget)
        dashboard["widgets"].append(widget["id"])

        dashboard["updated_at"] = datetime.now(timezone.utc).isoformat()

        logger.info(f"Added widget to dashboard {dashboard_id}")

        return {
            "widget_id": widget["id"],
            "title": title,
            "type": widget_type,
        }

    def get_dashboard(self, dashboard_id: str) -> dict[str, Any]:
        """获取看板

        Args:
            dashboard_id: 看板ID

        Returns:
            看板信息
        """
        dashboard = self._dashboards.get(dashboard_id)

        if not dashboard:
            return {}

        widgets = [
            w for w in self._widgets if w["dashboard_id"] == dashboard_id]

        return {
            "id": dashboard["id"],
            "name": dashboard["name"],
            "description": dashboard["description"],
            "widgets": widgets,
            "created_at": dashboard["created_at"],
            "updated_at": dashboard["updated_at"],
        }


class AnalyticsService:
    """分析服务"""

    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.dashboard_manager = DashboardManager()

    async def get_business_metrics(
        self,
        days: int = 7,
    ) -> dict[str, Any]:
        """获取业务指标

        Args:
            days: 天数

        Returns:
            指标数据
        """
        registration_series = self.metrics_collector.get_metric_series(
            metric_name="registration",
            days=days,
        )

        consultation_series = self.metrics_collector.get_metric_series(
            metric_name="consultation",
            days=days,
        )

        active_users_series = self.metrics_collector.get_metric_series(
            metric_name="active_users",
            days=days,
        )

        return {
            "period_days": days,
            "registrations": {
                "series": registration_series,
                "total": sum(d["value"] for d in registration_series),
                "trend": self._calculate_trend(registration_series),
            },
            "consultations": {
                "series": consultation_series,
                "total": sum(d["value"] for d in consultation_series),
                "trend": self._calculate_trend(consultation_series),
            },
            "active_users": {
                "series": active_users_series,
                "total": sum(d["value"] for d in active_users_series),
                "trend": self._calculate_trend(active_users_series),
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _calculate_trend(self, series: list[dict[str, Any]]) -> str:
        """计算趋势

        Args:
            series: 时序数据

        Returns:
            趋势描述
        """
        if len(series) < 2:
            return "stable"

        values = [d["value"] for d in series]
        first_half = sum(values[: len(values) // 2])
        second_half = sum(values[len(values) // 2:])

        if second_half > first_half * 1.1:
            return "up"
        elif second_half < first_half * 0.9:
            return "down"
        else:
            return "stable"

    async def export_metrics(
        self,
        metrics: list[str],
        days: int = 7,
        format: str = "json",
    ) -> dict[str, Any]:
        """导出指标

        Args:
            metrics: 指标列表
            days: 天数
            format: 格式

        Returns:
            导出数据
        """
        data = {}

        for metric_name in metrics:
            series = self.metrics_collector.get_metric_series(
                metric_name=metric_name,
                days=days,
            )
            data[metric_name] = {
                "series": series,
                "total": sum(d["value"] for d in series),
            }

        return {
            "metrics": list(metrics),
            "period_days": days,
            "format": format,
            "data": data,
            "exported_at": datetime.now(timezone.utc).isoformat(),
        }


class FunnelAnalyzer:
    """漏斗分析器"""

    def __init__(self):
        self._funnels: dict[str, dict[str, Any]] = {}

    def create_funnel(
        self,
        name: str,
        steps: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """创建漏斗

        Args:
            name: 名称
            steps: 步骤

        Returns:
            漏斗信息
        """
        funnel_id = f"FNL-{len(self._funnels) + 1:04d}"
        now = datetime.now(timezone.utc).isoformat()

        funnel = {
            "id": funnel_id,
            "name": name,
            "steps": steps,
            "created_at": now,
        }

        self._funnels[funnel_id] = funnel

        logger.info(f"Created funnel {funnel_id}: {name}")

        return {
            "funnel_id": funnel_id,
            "name": name,
            "steps_count": len(steps),
        }

    def analyze_funnel(
        self,
        funnel_id: str,
        data: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """分析漏斗

        Args:
            funnel_id: 漏斗ID
            data: 数据

        Returns:
            分析结果
        """
        funnel = self._funnels.get(funnel_id)

        if not funnel:
            return {
                "success": False,
                "error": "漏斗不存在",
            }

        step_counts = {}
        for step in funnel["steps"]:
            step_name = step.get("name", step.get("event", ""))
            count = sum(1 for d in data if step_name in str(d))
            step_counts[step_name] = count

        conversion_rates = {}
        step_names = list(step_counts.keys())
        for i, step_name in enumerate(step_names):
            if i == 0:
                conversion_rates[step_name] = 100.0
            else:
                prev_count = step_counts.get(step_names[i - 1], 1)
                curr_count = step_counts.get(step_name, 0)
                rate = (curr_count / prev_count * 100) if prev_count > 0 else 0
                conversion_rates[step_name] = round(rate, 2)

        overall_rate = 100.0
        for rate in list(conversion_rates.values())[1:]:
            overall_rate *= rate / 100

        return {
            "funnel_id": funnel_id,
            "funnel_name": funnel["name"],
            "step_counts": step_counts,
            "conversion_rates": conversion_rates,
            "overall_conversion_rate": round(overall_rate, 2),
            "drop_off_points": [
                name for name, rate in conversion_rates.items()
                if rate < 50 and name != list(conversion_rates.keys())[0]
            ],
        }


# 单例实例
analytics_service = AnalyticsService()
funnel_analyzer = FunnelAnalyzer()


async def get_business_metrics(
    days: int = 7,
) -> dict[str, Any]:
    """便捷函数：获取业务指标

    Args:
        days: 天数

    Returns:
        指标数据
    """
    return await analytics_service.get_business_metrics(days=days)


async def export_metrics(
    metrics: list[str],
    days: int = 7,
    format: str = "json",
) -> dict[str, Any]:
    """便捷函数：导出指标

    Args:
        metrics: 指标列表
        days: 天数
        format: 格式

    Returns:
        导出数据
    """
    return await analytics_service.export_metrics(
        metrics=metrics,
        days=days,
        format=format,
    )


def analyze_funnel(
    funnel_id: str,
    data: list[dict[str, Any]],
) -> dict[str, Any]:
    """便捷函数：分析漏斗

    Args:
        funnel_id: 漏斗ID
        data: 数据

    Returns:
        分析结果
    """
    return funnel_analyzer.analyze_funnel(funnel_id=funnel_id, data=data)


def create_funnel(
    name: str,
    steps: list[dict[str, Any]],
) -> dict[str, Any]:
    """便捷函数：创建漏斗

    Args:
        name: 名称
        steps: 步骤

    Returns:
        漏斗信息
    """
    return funnel_analyzer.create_funnel(name=name, steps=steps)
