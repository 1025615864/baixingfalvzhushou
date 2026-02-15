"""无障碍访问优化服务

提供 ARIA 标签和键盘导航功能。
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ARIAHelper:
    """ARIA 属性助手"""

    @staticmethod
    def generate_label(
        component_type: str,
        label: str,
        description: str | None = None,
    ) -> dict[str, str]:
        """生成 ARIA 标签

        Args:
            component_type: 组件类型
            label: 标签
            description: 描述

        Returns:
            ARIA 属性字典
        """
        result = {
            "role": component_type,
            "aria-label": label,
        }

        if description:
            result["aria-description"] = description

        return result

    @staticmethod
    def generate_button_label(
        label: str,
        disabled: bool = False,
        expanded: bool | None = None,
    ) -> dict[str, Any]:
        """生成按钮 ARIA 标签

        Args:
            label: 标签
            disabled: 是否禁用
            expanded: 是否展开

        Returns:
            ARIA 属性字典
        """
        result = {
            "role": "button",
            "aria-label": label,
        }

        if disabled:
            result["aria-disabled"] = "true"

        if expanded is not None:
            result["aria-expanded"] = str(expanded).lower()

        return result

    @staticmethod
    def generate_input_label(
        label: str,
        required: bool = False,
        invalid: bool = False,
        error_message: str | None = None,
    ) -> dict[str, Any]:
        """生成输入框 ARIA 标签

        Args:
            label: 标签
            required: 是否必填
            invalid: 是否无效
            error_message: 错误信息

        Returns:
            ARIA 属性字典
        """
        result = {
            "aria-label": label,
        }

        if required:
            result["aria-required"] = "true"

        if invalid:
            result["aria-invalid"] = "true"
            if error_message:
                result["aria-errormessage"] = error_message

        return result

    @staticmethod
    def generate_dialog_label(
        label: str,
        modal: bool = True,
    ) -> dict[str, str]:
        """生成对话框 ARIA 标签

        Args:
            label: 标签
            modal: 是否模态

        Returns:
            ARIA 属性字典
        """
        result = {
            "role": "dialog",
            "aria-label": label,
        }

        if modal:
            result["aria-modal"] = "true"

        return result

    @staticmethod
    def generate_list_label(
        label: str,
        item_count: int,
    ) -> dict[str, Any]:
        """生成列表 ARIA 标签

        Args:
            label: 标签
            item_count: 项数量

        Returns:
            ARIA 属性字典
        """
        return {
            "role": "list",
            "aria-label": label,
            "aria-setsize": str(item_count),
        }

    @staticmethod
    def generate_live_region(
        content: str,
        atomic: bool = True,
        politeness: str = "polite",
    ) -> dict[str, str]:
        """生成实时区域 ARIA 标签

        Args:
            content: 内容
            atomic: 是否原子
            politeness: 礼貌级别

        Returns:
            ARIA 属性字典
        """
        return {
            "role": "status",
            "aria-live": politeness,
            "aria-atomic": str(atomic).lower(),
        }


class KeyboardNavigation:
    """键盘导航管理器"""

    def __init__(self):
        self._focus_order: dict[str, int] = {}
        self._shortcuts: dict[str, dict[str, str]] = {}

    def register_focus_order(self, element_id: str, order: int) -> None:
        """注册焦点顺序

        Args:
            element_id: 元素ID
            order: 顺序
        """
        self._focus_order[element_id] = order

    def get_focus_order(self, element_id: str) -> int:
        """获取焦点顺序

        Args:
            element_id: 元素ID

        Returns:
            顺序
        """
        return self._focus_order.get(element_id, 0)

    def register_shortcut(
        self,
        key: str,
        target_id: str,
        description: str,
    ) -> dict[str, str]:
        """注册快捷键

        Args:
            key: 键
            target_id: 目标元素ID
            description: 描述

        Returns:
            注册结果
        """
        self._shortcuts[key] = {
            "target": target_id,
            "description": description,
        }

        return {
            "key": key,
            "target": target_id,
            "registered": True,
        }

    def get_shortcuts(self) -> dict[str, dict[str, str]]:
        """获取所有快捷键

        Returns:
            快捷键列表
        """
        return self._shortcuts

    def generate_keyboard_guide(self) -> list[dict[str, str]]:
        """生成键盘导航指南

        Returns:
            指南列表
        """
        return [
            {"key": "Tab", "action": "移动到下一个可聚焦元素"},
            {"key": "Shift + Tab", "action": "移动到上一个可聚焦元素"},
            {"key": "Enter", "action": "激活按钮或链接"},
            {"key": "Space", "action": "选中复选框或触发按钮"},
            {"key": "Escape", "action": "关闭对话框或弹出层"},
            {"key": "Arrow keys", "action": "在菜单或列表中导航"},
            {"key": "Home", "action": "移动到第一个元素"},
            {"key": "End", "action": "移动到最后一个元素"},
        ]


class AccessibilityChecker:
    """无障碍检查器"""

    def __init__(self):
        self._issues: list[dict[str, Any]] = []

    def check_image_alt(self, has_alt: bool, alt_text: str |
                        None = None) -> dict[str, Any]:
        """检查图片 alt 属性

        Args:
            has_alt: 是否有 alt 属性
            alt_text: alt 文本

        Returns:
            检查结果
        """
        if not has_alt:
            return {
                "check": "image_alt",
                "passed": False,
                "issue": "图片缺少 alt 属性",
                "suggestion": "为装饰性图片添加空的 alt=''，为内容图片添加描述性 alt 文本",
            }

        if alt_text and len(alt_text) > 125:
            return {
                "check": "image_alt",
                "passed": False,
                "issue": "alt 文本过长",
                "suggestion": "将 alt 文本控制在 125 字符以内",
            }

        return {
            "check": "image_alt",
            "passed": True,
            "message": "图片 alt 属性检查通过",
        }

    def check_heading_structure(
            self, headings: list[dict[str, str]]) -> dict[str, Any]:
        """检查标题结构

        Args:
            headings: 标题列表

        Returns:
            检查结果
        """
        issues = []
        prev_level = 0

        for i, heading in enumerate(headings):
            level = heading.get("level", 0)

            if level > prev_level + 1 and prev_level != 0:
                issues.append(f"标题级别从 h{prev_level} 跳转到 h{level}")

            prev_level = level

        if issues:
            return {
                "check": "heading_structure",
                "passed": False,
                "issues": issues,
                "suggestion": "确保标题级别依次递增，不要跳过级别",
            }

        return {
            "check": "heading_structure",
            "passed": True,
            "message": "标题结构检查通过",
        }

    def check_color_contrast(self, foreground: str,
                             background: str) -> dict[str, Any]:
        """检查颜色对比度

        Args:
            foreground: 前景色
            background: 背景色

        Returns:
            检查结果
        """
        contrast_ratio = self._calculate_contrast_ratio(foreground, background)

        if contrast_ratio < 4.5:
            return {
                "check": "color_contrast",
                "passed": False,
                "contrast_ratio": round(contrast_ratio, 2),
                "issue": "对比度不足（需要 >= 4.5:1）",
                "suggestion": "加深前景色或减淡背景色",
            }

        return {
            "check": "color_contrast",
            "passed": True,
            "contrast_ratio": round(contrast_ratio, 2),
            "message": "颜色对比度检查通过",
        }

    def _calculate_contrast_ratio(self, fg: str, bg: str) -> float:
        """计算对比度

        Args:
            fg: 前景色
            bg: 背景色

        Returns:
            对比度
        """
        fg_luminance = self._get_luminance(fg)
        bg_luminance = self._get_luminance(bg)

        lighter = max(fg_luminance, bg_luminance)
        darker = min(fg_luminance, bg_luminance)

        return (lighter + 0.05) / (darker + 0.05)

    def _get_luminance(self, color: str) -> float:
        """获取颜色亮度

        Args:
            color: 颜色

        Returns:
            亮度
        """
        hex_color = color.lstrip("#")
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16) / 255
            g = int(hex_color[2:4], 16) / 255
            b = int(hex_color[4:6], 16) / 255

            r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
            g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
            b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4

            return 0.2126 * r + 0.7152 * g + 0.0722 * b

        return 0.0

    def run_full_check(self, html_content: str) -> dict[str, Any]:
        """运行完整无障碍检查

        Args:
            html_content: HTML 内容

        Returns:
            检查报告
        """
        results = []

        results.append({
            "check": "document_language",
            "passed": "lang" in html_content,
            "message": "检查文档语言属性" if "lang" in html_content else "缺少 lang 属性",
        })

        results.append({
            "check": "landmark_regions",
            "passed": "<main" in html_content and "<nav" in html_content,
            "message": "检查地标区域" if "<main" in html_content and "<nav" in html_content else "缺少主要地标区域",
        })

        return {
            "total_checks": len(results),
            "passed_checks": sum(
                1 for r in results if r.get(
                    "passed",
                    False)),
            "results": results,
            "score": round(
                sum(
                    1 for r in results if r.get(
                        "passed",
                        False)) /
                len(results) *
                100,
                2) if results else 0,
        }


class AccessibilityService:
    """无障碍访问服务"""

    def __init__(self):
        self.aria_helper = ARIAHelper()
        self.keyboard_navigation = KeyboardNavigation()
        self.accessibility_checker = AccessibilityChecker()

    async def generate_aria_attributes(
        self,
        component_type: str,
        label: str,
        **kwargs,
    ) -> dict[str, Any]:
        """生成 ARIA 属性

        Args:
            component_type: 组件类型
            label: 标签
            **kwargs: 其他参数

        Returns:
            ARIA 属性
        """
        generators = {
            "button": self.aria_helper.generate_button_label,
            "input": self.aria_helper.generate_input_label,
            "dialog": self.aria_helper.generate_dialog_label,
            "list": self.aria_helper.generate_list_label,
            "status": self.aria_helper.generate_live_region,
        }

        generator = generators.get(
            component_type, self.aria_helper.generate_label)
        return generator(label, **kwargs)

    async def check_accessibility(self, html_content: str) -> dict[str, Any]:
        """检查无障碍

        Args:
            html_content: HTML 内容

        Returns:
            检查报告
        """
        return self.accessibility_checker.run_full_check(html_content)

    async def get_keyboard_guide(self) -> list[dict[str, str]]:
        """获取键盘导航指南

        Returns:
            指南列表
        """
        return self.keyboard_navigation.generate_keyboard_guide()

    async def get_stats(self) -> dict[str, Any]:
        """获取统计信息

        Returns:
            统计数据
        """
        return {
            "registered_shortcuts": len(self.keyboard_navigation._shortcuts),
            "focus_elements": len(self.keyboard_navigation._focus_order),
        }


# 单例实例
accessibility_service = AccessibilityService()


async def generate_aria_attributes(
    component_type: str,
    label: str,
    **kwargs,
) -> dict[str, Any]:
    """便捷函数：生成 ARIA 属性

    Args:
        component_type: 组件类型
        label: 标签
        **kwargs: 其他参数

    Returns:
        ARIA 属性
    """
    return await accessibility_service.generate_aria_attributes(
        component_type=component_type,
        label=label,
        **kwargs,
    )


async def check_accessibility(html_content: str) -> dict[str, Any]:
    """便捷函数：检查无障碍

    Args:
        html_content: HTML 内容

    Returns:
        检查报告
    """
    return await accessibility_service.check_accessibility(html_content)
