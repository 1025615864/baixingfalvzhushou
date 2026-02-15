"""移动端适配服务

提供响应式布局和触屏交互功能。
"""
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class DeviceDetector:
    """设备检测器"""

    def __init__(self):
        self._devices: dict[str, dict[str, Any]] = {}

    def detect_device(self, user_agent: str) -> dict[str, Any]:
        """检测设备类型

        Args:
            user_agent: User-Agent 字符串

        Returns:
            设备信息
        """
        ua_lower = user_agent.lower()

        if "mobile" in ua_lower or "android" in ua_lower or "iphone" in ua_lower or "ipad" in ua_lower:
            device_type = "mobile"
            if "tablet" in ua_lower or "ipad" in ua_lower:
                device_type = "tablet"
        else:
            device_type = "desktop"

        self._devices[user_agent] = {
            "user_agent": user_agent,
            "device_type": device_type,
            "detected_at": datetime.now(timezone.utc).isoformat(),
        }

        return {
            "device_type": device_type,
            "is_mobile": device_type in ["mobile", "tablet"],
        }

    def get_screen_sizes(self, device_type: str) -> dict[str, int]:
        """获取屏幕尺寸

        Args:
            device_type: 设备类型

        Returns:
            屏幕尺寸
        """
        sizes = {
            "mobile": {"width": 375, "height": 667},
            "tablet": {"width": 768, "height": 1024},
            "desktop": {"width": 1920, "height": 1080},
        }

        return sizes.get(device_type, sizes["desktop"])


class ResponsiveLayout:
    """响应式布局"""

    def __init__(self):
        self._breakpoints: dict[str, dict[str, int]] = {
            "xs": {"min": 0, "max": 575},
            "sm": {"min": 576, "max": 767},
            "md": {"min": 768, "max": 991},
            "lg": {"min": 992, "max": 1199},
            "xl": {"min": 1200, "max": 1399},
            "xxl": {"min": 1400, "max": 99999},
        }

    def get_breakpoint(self, screen_width: int) -> str:
        """获取断点

        Args:
            screen_width: 屏幕宽度

        Returns:
            断点名称
        """
        for name, range_ in self._breakpoints.items():
            if range_["min"] <= screen_width <= range_["max"]:
                return name

        return "xxl"

    def get_layout_config(self, breakpoint: str) -> dict[str, Any]:
        """获取布局配置

        Args:
            breakpoint: 断点名称

        Returns:
            布局配置
        """
        configs = {
            "xs": {
                "columns": 1,
                "gutter": 8,
                "margin": 16,
                "font_size": 14,
                "icon_size": 24,
                "button_height": 44,
            },
            "sm": {
                "columns": 2,
                "gutter": 12,
                "margin": 16,
                "font_size": 14,
                "icon_size": 24,
                "button_height": 44,
            },
            "md": {
                "columns": 3,
                "gutter": 16,
                "margin": 24,
                "font_size": 15,
                "icon_size": 28,
                "button_height": 48,
            },
            "lg": {
                "columns": 4,
                "gutter": 20,
                "margin": 32,
                "font_size": 15,
                "icon_size": 32,
                "button_height": 48,
            },
            "xl": {
                "columns": 5,
                "gutter": 24,
                "margin": 40,
                "font_size": 16,
                "icon_size": 32,
                "button_height": 52,
            },
            "xxl": {
                "columns": 6,
                "gutter": 24,
                "margin": 48,
                "font_size": 16,
                "icon_size": 32,
                "button_height": 52,
            },
        }

        return configs.get(breakpoint, configs["md"])


class TouchInteraction:
    """触屏交互"""

    def __init__(self):
        self._gestures: dict[int, list[dict[str, Any]]] = {}

    def register_touch(
        self,
        user_id: int,
        touch_type: str,
        x: float,
        y: float,
    ) -> dict[str, Any]:
        """注册触摸事件

        Args:
            user_id: 用户ID
            touch_type: 触摸类型
            x: X坐标
            y: Y坐标

        Returns:
            注册结果
        """
        if user_id not in self._gestures:
            self._gestures[user_id] = []

        self._gestures[user_id].append({
            "type": touch_type,
            "x": x,
            "y": y,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        if len(self._gestures[user_id]) > 100:
            self._gestures[user_id] = self._gestures[user_id][-100:]

        return {
            "success": True,
            "touch_type": touch_type,
        }

    def detect_gesture(self, user_id: int) -> dict[str, Any]:
        """检测手势

        Args:
            user_id: 用户ID

        Returns:
            手势信息
        """
        if user_id not in self._gestures or len(self._gestures[user_id]) < 2:
            return {"gesture": "unknown"}

        gestures = self._gestures[user_id]

        start = gestures[0]
        end = gestures[-1]

        delta_x = end["x"] - start["x"]
        delta_y = end["y"] - start["y"]

        if abs(delta_x) > abs(delta_y):
            if delta_x > 50:
                gesture = "swipe_right"
            elif delta_x < -50:
                gesture = "swipe_left"
            else:
                gesture = "tap"
        else:
            if delta_y > 50:
                gesture = "swipe_down"
            elif delta_y < -50:
                gesture = "swipe_up"
            else:
                gesture = "tap"

        return {
            "gesture": gesture,
            "delta_x": delta_x,
            "delta_y": delta_y,
        }

    def get_touch_stats(self, user_id: int) -> dict[str, Any]:
        """获取触摸统计

        Args:
            user_id: 用户ID

        Returns:
            统计信息
        """
        if user_id not in self._gestures:
            return {"total_touches": 0}

        touches = self._gestures[user_id]

        touch_types: dict[str, int] = {}
        for t in touches:
            t_type = t["type"]
            touch_types[t_type] = touch_types.get(t_type, 0) + 1

        return {
            "total_touches": len(touches),
            "touch_types": touch_types,
        }


class MobileOptimizationService:
    """移动端优化服务"""

    def __init__(self):
        self.device_detector = DeviceDetector()
        self.responsive_layout = ResponsiveLayout()
        self.touch_interaction = TouchInteraction()

    async def optimize_for_device(
        self,
        user_agent: str,
        screen_width: int,
    ) -> dict[str, Any]:
        """优化设备适配

        Args:
            user_agent: User-Agent 字符串
            screen_width: 屏幕宽度

        Returns:
            优化配置
        """
        device_info = self.device_detector.detect_device(user_agent)
        breakpoint = self.responsive_layout.get_breakpoint(screen_width)
        layout_config = self.responsive_layout.get_layout_config(breakpoint)

        return {
            "device_type": device_info["device_type"],
            "is_mobile": device_info["is_mobile"],
            "breakpoint": breakpoint,
            "layout_config": layout_config,
            "screen_size": self.device_detector.get_screen_sizes(
                device_info["device_type"]),
        }

    async def register_touch(
        self,
        user_id: int,
        touch_type: str,
        x: float,
        y: float,
    ) -> dict[str, Any]:
        """注册触摸事件

        Args:
            user_id: 用户ID
            touch_type: 触摸类型
            x: X坐标
            y: Y坐标

        Returns:
            注册结果
        """
        result = self.touch_interaction.register_touch(
            user_id, touch_type, x, y)
        gesture = self.touch_interaction.detect_gesture(user_id)

        return {
            **result,
            "detected_gesture": gesture["gesture"],
        }

    async def get_mobile_stats(self) -> dict[str, Any]:
        """获取移动端统计

        Returns:
            统计数据
        """
        total_touches = sum(
            len(g) for g in self.touch_interaction._gestures.values()
        )

        return {
            "total_touches": total_touches,
            "total_users": len(self.touch_interaction._gestures),
        }


# 单例实例
mobile_optimization_service = MobileOptimizationService()


async def optimize_for_device(
    user_agent: str,
    screen_width: int,
) -> dict[str, Any]:
    """便捷函数：优化设备适配

    Args:
        user_agent: User-Agent 字符串
        screen_width: 屏幕宽度

    Returns:
        优化配置
    """
    return await mobile_optimization_service.optimize_for_device(
        user_agent=user_agent,
        screen_width=screen_width,
    )


async def register_touch(
    user_id: int,
    touch_type: str,
    x: float,
    y: float,
) -> dict[str, Any]:
    """便捷函数：注册触摸事件

    Args:
        user_id: 用户ID
        touch_type: 触摸类型
        x: X坐标
        y: Y坐标

    Returns:
        注册结果
    """
    return await mobile_optimization_service.register_touch(
        user_id=user_id,
        touch_type=touch_type,
        x=x,
        y=y,
    )
