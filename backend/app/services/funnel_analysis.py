"""用户行为漏斗分析服务

提供转化率追踪和流失节点分析功能。
"""
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class FunnelConfigurator:
    """漏斗配置器"""

    def __init__(self):
        self._funnels: dict[str, dict[str, Any]] = {}

    def create_funnel(
        self,
        funnel_id: str,
        name: str,
        steps: list[dict[str, str]],
    ) -> dict[str, Any]:
        """创建漏斗

        Args:
            funnel_id: 漏斗ID
            name: 名称
            steps: 步骤列表

        Returns:
            配置结果
        """
        self._funnels[funnel_id] = {
            "id": funnel_id,
            "name": name,
            "steps": steps,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        return {
            "id": funnel_id,
            "name": name,
            "steps_count": len(steps),
            "configured": True,
        }

    def get_funnel(self, funnel_id: str) -> dict[str, Any]:
        """获取漏斗配置

        Args:
            funnel_id: 漏斗ID

        Returns:
            漏斗配置
        """
        return self._funnels.get(funnel_id, {})

    def list_funnels(self) -> list[dict[str, Any]]:
        """列出所有漏斗

        Returns:
            漏斗列表
        """
        return list(self._funnels.values())


class FunnelTracker:
    """漏斗追踪器"""

    def __init__(self):
        self._events: list[dict[str, Any]] = []
        self._user_progress: dict[int, dict[str, Any]] = {}

    def track_event(
        self,
        user_id: int,
        funnel_id: str,
        step_id: str,
    ) -> dict[str, Any]:
        """追踪事件

        Args:
            user_id: 用户ID
            funnel_id: 漏斗ID
            step_id: 步骤ID

        Returns:
            追踪结果
        """
        event = {
            "user_id": user_id,
            "funnel_id": funnel_id,
            "step_id": step_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self._events.append(event)

        if user_id not in self._user_progress:
            self._user_progress[user_id] = {"funnels": {}}

        if funnel_id not in self._user_progress[user_id]["funnels"]:
            self._user_progress[user_id]["funnels"][funnel_id] = {
                "current_step": None,
                "completed_steps": [],
                "entered_at": None,
                "completed_at": None,
            }

        funnel_progress = self._user_progress[user_id]["funnels"][funnel_id]

        if funnel_progress["entered_at"] is None:
            funnel_progress["entered_at"] = event["timestamp"]

        if step_id not in funnel_progress["completed_steps"]:
            funnel_progress["completed_steps"].append(step_id)
            funnel_progress["current_step"] = step_id

        logger.info(
            f"Tracked funnel event: user {user_id}, funnel {funnel_id}, step {step_id}")

        return {
            "user_id": user_id,
            "funnel_id": funnel_id,
            "step_id": step_id,
            "tracked": True,
        }

    def get_user_progress(self, user_id: int,
                          funnel_id: str) -> dict[str, Any]:
        """获取用户进度

        Args:
            user_id: 用户ID
            funnel_id: 漏斗ID

        Returns:
            进度数据
        """
        if user_id not in self._user_progress:
            return {"user_id": user_id, "funnel_id": funnel_id,
                    "progress": 0, "completed_steps": []}

        funnel_progress = self._user_progress[user_id]["funnels"].get(
            funnel_id, {})

        return {
            "user_id": user_id,
            "funnel_id": funnel_id,
            "progress": len(funnel_progress.get("completed_steps", [])),
            "completed_steps": funnel_progress.get("completed_steps", []),
            "entered_at": funnel_progress.get("entered_at"),
            "completed_at": funnel_progress.get("completed_at"),
        }


class FunnelAnalyzer:
    """漏斗分析器"""

    def __init__(self):
        self._tracker = FunnelTracker()
        self._configurator = FunnelConfigurator()

    def analyze_funnel(
        self,
        funnel_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """分析漏斗

        Args:
            funnel_id: 漏斗ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            分析结果
        """
        funnel = self._configurator.get_funnel(funnel_id)
        if not funnel:
            return {"error": "Funnel not found"}

        steps = funnel.get("steps", [])
        step_counts: dict[str, int] = {}

        for step in steps:
            step_id = step.get("id", "")
            step_counts[step_id] = 0

        for event in self._tracker._events:
            if event.get("funnel_id") == funnel_id:
                step_id = event.get("step_id", "")
                if step_id in step_counts:
                    step_counts[step_id] += 1

        step_data = []
        prev_count = 0

        for step in steps:
            step_id = step.get("id", "")
            current_count = step_counts.get(step_id, 0)
            conversion_rate = round(current_count /
                                    max(prev_count, 1) *
                                    100, 2) if prev_count > 0 else 100.0

            step_data.append({
                "step_id": step_id,
                "name": step.get("name", ""),
                "users": current_count,
                "conversion_rate": conversion_rate,
                "drop_off": round((prev_count - current_count) / max(prev_count, 1) * 100, 2) if prev_count > 0 else 0,
            })

            prev_count = current_count

        total_users = step_data[0]["users"] if step_data else 0
        final_users = step_data[-1]["users"] if step_data else 0
        overall_conversion = round(final_users /
                                   max(total_users, 1) *
                                   100, 2) if total_users > 0 else 0

        return {
            "funnel_id": funnel_id,
            "funnel_name": funnel.get("name", ""),
            "total_users": total_users,
            "overall_conversion": overall_conversion,
            "steps": step_data,
        }

    def identify_drop_off_points(self, funnel_id: str) -> list[dict[str, Any]]:
        """识别流失节点

        Args:
            funnel_id: 漏斗ID

        Returns:
            流失节点列表
        """
        analysis = self.analyze_funnel(funnel_id)

        if "error" in analysis:
            return []

        drop_off_points = []

        for i, step in enumerate(analysis.get("steps", [])):
            if step.get("drop_off", 0) > 20:
                drop_off_points.append({
                    "step_id": step["step_id"],
                    "step_name": step["name"],
                    "drop_off_rate": step["drop_off"],
                    "severity": "high" if step["drop_off"] > 50 else "medium",
                    "recommendation": self._get_recommendation(step["step_id"], step["drop_off"]),
                })

        return drop_off_points

    def _get_recommendation(self, step_id: str, drop_off_rate: float) -> str:
        """获取建议

        Args:
            step_id: 步骤ID
            drop_off_rate: 流失率

        Returns:
            建议
        """
        recommendations = {
            "signup": "简化注册流程，减少必填字段",
            "login": "提供第三方登录选项",
            "browse": "优化搜索和推荐算法",
            "consult": "降低咨询入口门槛",
            "payment": "简化支付流程，提供更多支付方式",
        }

        default_rec = "分析用户反馈，优化该步骤体验"
        return recommendations.get(step_id, default_rec)

    async def get_funnel_stats(self) -> dict[str, Any]:
        """获取漏斗统计

        Returns:
            统计数据
        """
        funnels = self._configurator.list_funnels()
        total_events = len(self._tracker._events)
        total_users = len(self._tracker._user_progress)

        return {
            "total_funnels": len(funnels),
            "total_events": total_events,
            "total_users_tracked": total_users,
        }


# 单例实例
funnel_service = FunnelAnalyzer()


async def create_funnel(
    funnel_id: str,
    name: str,
    steps: list[dict[str, str]],
) -> dict[str, Any]:
    """便捷函数：创建漏斗

    Args:
        funnel_id: 漏斗ID
        name: 名称
        steps: 步骤列表

    Returns:
        配置结果
    """
    return funnel_service._configurator.create_funnel(funnel_id, name, steps)


async def track_funnel_event(
    user_id: int,
    funnel_id: str,
    step_id: str,
) -> dict[str, Any]:
    """便捷函数：追踪漏斗事件

    Args:
        user_id: 用户ID
        funnel_id: 漏斗ID
        step_id: 步骤ID

    Returns:
        追踪结果
    """
    return funnel_service._tracker.track_event(user_id, funnel_id, step_id)


async def analyze_funnel(
    funnel_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """便捷函数：分析漏斗

    Args:
        funnel_id: 漏斗ID
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        分析结果
    """
    return funnel_service.analyze_funnel(funnel_id, start_date, end_date)


async def get_funnel_config(
    funnel_id: str,
) -> dict[str, Any]:
    """便捷函数：获取漏斗配置

    Args:
        funnel_id: 漏斗ID

    Returns:
        漏斗配置
    """
    return funnel_service._configurator.get_funnel(funnel_id)


async def list_funnels() -> list[dict[str, Any]]:
    """便捷函数：列出所有漏斗

    Returns:
        漏斗列表
    """
    return funnel_service._configurator.list_funnels()


async def get_drop_off_points(
    funnel_id: str,
) -> list[dict[str, Any]]:
    """便捷函数：获取流失节点

    Args:
        funnel_id: 漏斗ID

    Returns:
        流失节点列表
    """
    return funnel_service.identify_drop_off_points(funnel_id)


async def get_user_funnel_progress(
    user_id: int,
    funnel_id: str,
) -> dict[str, Any]:
    """便捷函数：获取用户漏斗进度

    Args:
        user_id: 用户ID
        funnel_id: 漏斗ID

    Returns:
        用户进度
    """
    return funnel_service._tracker.get_user_progress(user_id, funnel_id)


async def get_funnel_stats() -> dict[str, Any]:
    """便捷函数：获取漏斗统计

    Returns:
        统计数据
    """
    return await funnel_service.get_funnel_stats()
