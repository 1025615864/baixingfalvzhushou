"""MCP 工具注册表"""

import logging
from typing import Dict, List, Optional, Any  # pyright: ignore
from .base import BaseTool, ToolInfo, ToolResult  # pyright: ignore

logger = logging.getLogger(__name__)


class ToolRegistry:  # pyright: ignore
    """工具注册表，管理所有可用工具"""

    _instance: Optional["ToolRegistry"] = None
    _tools: Dict[str, BaseTool] = {}  # pyright: ignore
    # category -> tool names  # pyright: ignore
    _categories: Dict[str, List[str]] = {}
    # tool name -> enabled  # pyright: ignore
    _enabled_tools: Dict[str, bool] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, tool: BaseTool, enabled: bool = True) -> None:  # pyright: ignore
        """注册工具

        Args:
            tool: 工具实例
            enabled: 是否启用
        """
        name = tool.name
        if name in self._tools:
            logger.warning(f"工具 {name} 已存在，将被覆盖")

        self._tools[name] = tool
        self._enabled_tools[name] = enabled

        # 添加到分类
        category = tool.category
        if category not in self._categories:
            self._categories[category] = []
        if name not in self._categories[category]:
            self._categories[category].append(name)

        logger.info(
            f"工具已注册: {name} (category: {category}, enabled: {enabled})")

    def unregister(self, name: str) -> bool:  # pyright: ignore
        """注销工具"""
        if name in self._tools:
            tool = self._tools[name]
            category = tool.category
            if category in self._categories and name in self._categories[category]:
                self._categories[category].remove(name)

            del self._tools[name]
            del self._enabled_tools[name]
            logger.info(f"工具已注销: {name}")
            return True
        return False

    def get(self, name: str) -> Optional[BaseTool]:  # pyright: ignore
        """获取工具实例"""
        return self._tools.get(name)

    def get_enabled(self, name: str) -> Optional[BaseTool]:  # pyright: ignore
        """获取已启用的工具"""
        if self._enabled_tools.get(name, False):
            return self._tools.get(name)
        return None

    # pyright: ignore
    def list_all(self, include_disabled: bool = False) -> List[ToolInfo]:
        """列出所有工具信息"""
        results: List[ToolInfo] = []  # pyright: ignore
        for name, tool in self._tools.items():
            if include_disabled or self._enabled_tools.get(name, False):
                results.append(tool.get_info())  # pyright: ignore
        return results  # pyright: ignore

    # pyright: ignore
    def list_by_category(self, category: str,
                         enabled_only: bool = True) -> List[ToolInfo]:
        """按分类列出工具"""
        results: List[ToolInfo] = []  # pyright: ignore
        for name in self._categories.get(category, []):
            tool = self.get_enabled(name) if enabled_only else self.get(name)
            if tool:
                results.append(tool.get_info())  # pyright: ignore
        return results  # pyright: ignore

    def list_categories(self) -> List[str]:  # pyright: ignore
        """列出所有分类"""
        return list(self._categories.keys())

    def set_enabled(self, name: str, enabled: bool) -> bool:  # pyright: ignore
        """设置工具启用状态"""
        if name in self._tools:
            self._enabled_tools[name] = enabled
            logger.info(f"工具 {name} 已{'启用' if enabled else '禁用'}")
            return True
        return False

    def is_enabled(self, name: str) -> bool:  # pyright: ignore
        """检查工具是否启用"""
        return self._enabled_tools.get(name, False)

    # pyright: ignore
    def get_available_tools(
            self, context: Optional[Dict[str, Any]] = None) -> List[ToolInfo]:
        """获取上下文中可用的工具

        Args:
            context: 上下文信息，包含用户信息等

        Returns:
            可用工具列表
        """
        results: List[ToolInfo] = []  # pyright: ignore
        user_vip = context.get("is_vip", False) if context else False
        user_admin = context.get("is_admin", False) if context else False
        is_authenticated = context.get(
            "is_authenticated", False) if context else False

        for name, tool in self._tools.items():
            if not self._enabled_tools.get(name, False):
                continue

            # 检查权限
            permission = getattr(tool, "permission", "public")
            if permission == "public":
                results.append(tool.get_info())  # pyright: ignore
            elif permission == "user" and is_authenticated:
                results.append(tool.get_info())  # pyright: ignore
            elif permission == "vip" and user_vip:
                results.append(tool.get_info())  # pyright: ignore
            elif permission == "admin" and user_admin:
                results.append(tool.get_info())  # pyright: ignore

        return results  # pyright: ignore

    def clear(self) -> None:  # pyright: ignore
        """清空所有注册"""
        self._tools.clear()
        self._categories.clear()
        self._enabled_tools.clear()
        logger.info("工具注册表已清空")


def get_registry() -> ToolRegistry:  # pyright: ignore
    """获取工具注册表单例"""
    return ToolRegistry()


def register_tool(tool: BaseTool, enabled: bool = True) -> None:  # pyright: ignore
    """注册工具的便捷函数"""
    get_registry().register(tool, enabled)


def get_tool(name: str) -> Optional[BaseTool]:  # pyright: ignore
    """获取工具的便捷函数"""
    return get_registry().get(name)


# pyright: ignore
def list_tools(category: Optional[str] = None) -> List[ToolInfo]:
    """列出工具的便捷函数"""
    if category:
        return get_registry().list_by_category(category)
    return get_registry().list_all()
