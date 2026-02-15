"""无障碍访问优化服务测试"""
from __future__ import annotations

import pytest

from app.services.accessibility import (
    ARIAHelper,
    KeyboardNavigation,
    AccessibilityChecker,
    AccessibilityService,
    accessibility_service,
    generate_aria_attributes,
    check_accessibility,
)


class TestARIAHelper:
    """ARIA 属性助手测试"""

    def test_generate_label(self):
        """测试生成 ARIA 标签"""
        result = ARIAHelper.generate_label(
            component_type="button",
            label="提交",
            description="提交表单",
        )

        assert result["role"] == "button"
        assert result["aria-label"] == "提交"
        assert result["aria-description"] == "提交表单"

    def test_generate_label_without_description(self):
        """测试生成 ARIA 标签（无描述）"""
        result = ARIAHelper.generate_label(
            component_type="button",
            label="提交",
        )

        assert result["role"] == "button"
        assert result["aria-label"] == "提交"
        assert "aria-description" not in result

    def test_generate_button_label(self):
        """测试生成按钮 ARIA 标签"""
        result = ARIAHelper.generate_button_label(
            label="提交",
            disabled=True,
            expanded=True,
        )

        assert result["role"] == "button"
        assert result["aria-label"] == "提交"
        assert result["aria-disabled"] == "true"
        assert result["aria-expanded"] == "true"

    def test_generate_button_label_defaults(self):
        """测试生成按钮 ARIA 标签（默认值）"""
        result = ARIAHelper.generate_button_label(label="提交")

        assert result["role"] == "button"
        assert result["aria-label"] == "提交"
        assert "aria-disabled" not in result
        assert "aria-expanded" not in result

    def test_generate_input_label(self):
        """测试生成输入框 ARIA 标签"""
        result = ARIAHelper.generate_input_label(
            label="用户名",
            required=True,
            invalid=True,
            error_message="用户名不能为空",
        )

        assert result["aria-label"] == "用户名"
        assert result["aria-required"] == "true"
        assert result["aria-invalid"] == "true"
        assert result["aria-errormessage"] == "用户名不能为空"

    def test_generate_input_label_defaults(self):
        """测试生成输入框 ARIA 标签（默认值）"""
        result = ARIAHelper.generate_input_label(label="用户名")

        assert result["aria-label"] == "用户名"
        assert "aria-required" not in result
        assert "aria-invalid" not in result
        assert "aria-errormessage" not in result

    def test_generate_dialog_label(self):
        """测试生成对话框 ARIA 标签"""
        result = ARIAHelper.generate_dialog_label(
            label="确认对话框",
            modal=True,
        )

        assert result["role"] == "dialog"
        assert result["aria-label"] == "确认对话框"
        assert result["aria-modal"] == "true"

    def test_generate_dialog_label_non_modal(self):
        """测试生成对话框 ARIA 标签（非模态）"""
        result = ARIAHelper.generate_dialog_label(
            label="提示框",
            modal=False,
        )

        assert result["role"] == "dialog"
        assert result["aria-label"] == "提示框"
        assert "aria-modal" not in result

    def test_generate_list_label(self):
        """测试生成列表 ARIA 标签"""
        result = ARIAHelper.generate_list_label(
            label="用户列表",
            item_count=10,
        )

        assert result["role"] == "list"
        assert result["aria-label"] == "用户列表"
        assert result["aria-setsize"] == "10"

    def test_generate_live_region(self):
        """测试生成实时区域 ARIA 标签"""
        result = ARIAHelper.generate_live_region(
            content="操作成功",
            atomic=True,
            politeness="polite",
        )

        assert result["role"] == "status"
        assert result["aria-live"] == "polite"
        assert result["aria-atomic"] == "true"


class TestKeyboardNavigation:
    """键盘导航管理器测试"""

    def test_register_focus_order(self):
        """测试注册焦点顺序"""
        nav = KeyboardNavigation()
        nav.register_focus_order("button1", 1)
        nav.register_focus_order("button2", 2)

        assert nav.get_focus_order("button1") == 1
        assert nav.get_focus_order("button2") == 2

    def test_get_focus_order_not_registered(self):
        """测试获取未注册元素的焦点顺序"""
        nav = KeyboardNavigation()
        order = nav.get_focus_order("nonexistent")
        assert order == 0

    def test_register_shortcut(self):
        """测试注册快捷键"""
        nav = KeyboardNavigation()
        result = nav.register_shortcut(
            key="Ctrl+S",
            target_id="save-button",
            description="保存文档",
        )

        assert result["key"] == "Ctrl+S"
        assert result["target"] == "save-button"
        assert result["registered"] is True

    def test_get_shortcuts(self):
        """测试获取所有快捷键"""
        nav = KeyboardNavigation()
        nav.register_shortcut("Ctrl+S", "save-button", "保存")
        nav.register_shortcut("Ctrl+Z", "undo-button", "撤销")

        shortcuts = nav.get_shortcuts()
        assert len(shortcuts) == 2
        assert "Ctrl+S" in shortcuts
        assert "Ctrl+Z" in shortcuts

    def test_generate_keyboard_guide(self):
        """测试生成键盘导航指南"""
        nav = KeyboardNavigation()
        guide = nav.generate_keyboard_guide()

        assert len(guide) > 0
        assert any(item["key"] == "Tab" for item in guide)
        assert any(item["key"] == "Enter" for item in guide)
        assert any(item["key"] == "Escape" for item in guide)


class TestAccessibilityChecker:
    """无障碍检查器测试"""

    def test_check_image_alt_missing(self):
        """测试检查图片 alt 属性（缺失）"""
        checker = AccessibilityChecker()
        result = checker.check_image_alt(has_alt=False)

        assert result["check"] == "image_alt"
        assert result["passed"] is False
        assert "缺少 alt 属性" in result["issue"]

    def test_check_image_alt_too_long(self):
        """测试检查图片 alt 属性（过长）"""
        checker = AccessibilityChecker()
        long_text = "a" * 126
        result = checker.check_image_alt(has_alt=True, alt_text=long_text)

        assert result["check"] == "image_alt"
        assert result["passed"] is False
        assert "alt 文本过长" in result["issue"]

    def test_check_image_alt_valid(self):
        """测试检查图片 alt 属性（有效）"""
        checker = AccessibilityChecker()
        result = checker.check_image_alt(has_alt=True, alt_text="一张风景图片")

        assert result["check"] == "image_alt"
        assert result["passed"] is True

    def test_check_heading_structure_valid(self):
        """测试检查标题结构（有效）"""
        checker = AccessibilityChecker()
        headings = [
            {"level": 1, "text": "标题1"},
            {"level": 2, "text": "标题2"},
            {"level": 3, "text": "标题3"},
        ]
        result = checker.check_heading_structure(headings)

        assert result["check"] == "heading_structure"
        assert result["passed"] is True

    def test_check_heading_structure_invalid(self):
        """测试检查标题结构（无效）"""
        checker = AccessibilityChecker()
        headings = [
            {"level": 1, "text": "标题1"},
            {"level": 3, "text": "标题3"},  # 跳过了 h2
        ]
        result = checker.check_heading_structure(headings)

        assert result["check"] == "heading_structure"
        assert result["passed"] is False
        assert len(result["issues"]) > 0

    def test_check_color_contrast_low(self):
        """测试检查颜色对比度（低）"""
        checker = AccessibilityChecker()
        result = checker.check_color_contrast(
            foreground="#999999",
            background="#FFFFFF",
        )

        assert result["check"] == "color_contrast"
        assert result["passed"] is False
        assert "对比度不足" in result["issue"]

    def test_check_color_contrast_high(self):
        """测试检查颜色对比度（高）"""
        checker = AccessibilityChecker()
        result = checker.check_color_contrast(
            foreground="#000000",
            background="#FFFFFF",
        )

        assert result["check"] == "color_contrast"
        assert result["passed"] is True

    def test_run_full_check(self):
        """测试运行完整无障碍检查"""
        checker = AccessibilityChecker()
        html = '<html lang="zh-CN"><main><nav>导航</nav></main></html>'
        result = checker.run_full_check(html)

        assert result["total_checks"] == 2
        assert result["passed_checks"] == 2
        assert result["score"] == 100

    def test_run_full_check_failures(self):
        """测试运行完整无障碍检查（失败）"""
        checker = AccessibilityChecker()
        html = '<html><body>内容</body></html>'
        result = checker.run_full_check(html)

        assert result["total_checks"] == 2
        assert result["passed_checks"] < result["total_checks"]


class TestAccessibilityService:
    """无障碍访问服务测试"""

    @pytest.mark.asyncio
    async def test_generate_aria_attributes_button(self):
        """测试生成 ARIA 属性（按钮）"""
        result = await accessibility_service.generate_aria_attributes(
            component_type="button",
            label="提交",
            disabled=True,
        )

        assert result["role"] == "button"
        assert result["aria-label"] == "提交"

    @pytest.mark.asyncio
    async def test_check_accessibility(self):
        """测试检查无障碍"""
        html = '<html lang="zh-CN"><main><nav>导航</nav></main></html>'
        result = await accessibility_service.check_accessibility(html)

        assert result["total_checks"] == 2
        assert result["passed_checks"] == 2

    @pytest.mark.asyncio
    async def test_get_keyboard_guide(self):
        """测试获取键盘导航指南"""
        guide = await accessibility_service.get_keyboard_guide()

        assert len(guide) > 0
        assert any(item["key"] == "Tab" for item in guide)

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """测试获取统计信息"""
        accessibility_service.keyboard_navigation.register_shortcut(
            "Ctrl+S", "save-button", "保存",
        )
        accessibility_service.keyboard_navigation.register_focus_order("button1", 1)

        stats = await accessibility_service.get_stats()

        assert stats["registered_shortcuts"] == 1
        assert stats["focus_elements"] == 1


class TestConvenienceFunctions:
    """便捷函数测试"""

    @pytest.mark.asyncio
    async def test_generate_aria_attributes_function(self):
        """测试生成 ARIA 属性便捷函数"""
        result = await generate_aria_attributes(
            component_type="input",
            label="用户名",
            required=True,
        )

        assert result["aria-label"] == "用户名"
        assert result["aria-required"] == "true"

    @pytest.mark.asyncio
    async def test_check_accessibility_function(self):
        """测试检查无障碍便捷函数"""
        html = '<html lang="zh-CN"><main><nav>导航</nav></main></html>'
        result = await check_accessibility(html)

        assert result["total_checks"] == 2


class TestSingletonService:
    """单例服务测试"""

    def test_accessibility_service_singleton(self):
        """测试无障碍服务单例"""
        assert accessibility_service is not None
        assert isinstance(accessibility_service, AccessibilityService)
