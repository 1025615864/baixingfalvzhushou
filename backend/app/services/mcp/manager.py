"""MCP 工具管理器 - 与 AI 助手集成"""

import json
import logging
from datetime import datetime
from typing import Any, Optional, Dict, List

from .base import ToolResult
from .registry import get_registry

logger = logging.getLogger(__name__)


class MCPManager:  # pyright: ignore
    """MCP 工具管理器"""

    _instance: Optional["MCPManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def initialize(self) -> None:  # pyright: ignore
        """初始化 MCP 管理器"""
        if self._initialized:
            return

        self._execution_history: List[Dict[str, Any]] = []  # pyright: ignore
        self._max_history: int = 1000
        self._tools_usage_stats: Dict[str,
                                      Dict[str, Any]] = {}  # pyright: ignore

        # 自动注册内置工具
        self._register_builtin_tools()

        self._initialized = True
        logger.info("MCP 工具管理器已初始化")

    def _register_builtin_tools(self) -> None:  # pyright: ignore
        """注册内置工具"""
        registry = get_registry()

        try:
            from .tools.document_tool import DocumentGenerationTool
            registry.register(DocumentGenerationTool())
            logger.info("已注册文档生成工具")
        except ImportError as e:
            logger.warning(f"注册文档生成工具失败: {e}")

        try:
            from .tools.calculator_tool import CalculatorTool
            registry.register(CalculatorTool())
            logger.info("已注册计算器工具")
        except ImportError as e:
            logger.warning(f"注册计算器工具失败: {e}")

        try:
            from .tools.lawfirm_tool import LawfirmSearchTool
            registry.register(LawfirmSearchTool())
            logger.info("已注册律所查询工具")
        except ImportError as e:
            logger.warning(f"注册律所查询工具失败: {e}")

        try:
            from .tools.knowledge_tool import KnowledgeSearchTool
            registry.register(KnowledgeSearchTool())
            logger.info("已注册知识库搜索工具")
        except ImportError as e:
            logger.warning(f"注册知识库搜索工具失败: {e}")

        try:
            from .tools.calendar_tool import CalendarTool
            registry.register(CalendarTool())
            logger.info("已注册日历工具")
        except ImportError as e:
            logger.warning(f"注册日历工具失败: {e}")

    async def execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        conversation_id: Optional[str] = None,
    ) -> ToolResult:
        """执行工具

        Args:
            tool_name: 工具名称
            params: 工具参数
            context: 执行上下文
            user_id: 用户ID
            conversation_id: 会话ID

        Returns:
            ToolResult: 执行结果
        """
        registry = get_registry()
        tool = registry.get_enabled(tool_name)

        if tool is None:
            return ToolResult(
                success=False,
                error=f"工具不存在或已禁用: {tool_name}"
            )

        # 记录调用
        self._record_execution(
            tool_name=tool_name,
            params=params,
            context=context,
            user_id=user_id,
            conversation_id=conversation_id,
        )

        # 更新使用统计
        self._update_usage_stats(tool_name)

        # 执行工具
        result = await tool.arun(params, context)

        # 记录执行结果
        self._record_result(tool_name, result)

        return result

    async def execute_tools_parallel(
        self,
        requests: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, ToolResult]:
        """并行执行多个工具

        Args:
            requests: 请求列表，每项包含 tool_name, params
            context: 执行上下文
            user_id: 用户ID
            conversation_id: 会话ID

        Returns:
            Dict[tool_name, ToolResult]
        """
        import asyncio

        tasks: List[Any] = []  # pyright: ignore
        for req in requests:
            tool_name = req.get("tool_name")
            params = req.get("params", {})
            if tool_name:
                tasks.append(  # pyright: ignore
                    self.execute_tool(
                        tool_name=tool_name,
                        params=params,
                        context=context,
                        user_id=user_id,
                        conversation_id=conversation_id,
                    )
                )

        # pyright: ignore
        results = await asyncio.gather(*tasks, return_exceptions=True)

        output: Dict[str, ToolResult] = {}  # pyright: ignore
        for i, req in enumerate(requests):
            tool_name = req.get("tool_name", f"tool_{i}")
            if isinstance(results[i], Exception):
                output[tool_name] = ToolResult(
                    success=False,
                    error=str(results[i])
                )
            else:
                output[tool_name] = results[i]  # pyright: ignore

        return output  # pyright: ignore

    # pyright: ignore
    def get_tools_for_prompt(
            self, context: Optional[Dict[str, Any]] = None) -> str:
        """生成工具列表描述，用于注入到 AI prompt

        Args:
            context: 上下文信息

        Returns:
            工具描述字符串
        """
        registry = get_registry()
        tools = registry.get_available_tools(context)

        if not tools:
            return "当前无可用工具。"

        descriptions: List[str] = ["可用工具列表：\n"]  # pyright: ignore
        for tool in tools:
            if tool.deprecated:
                continue

            desc = f"- **{tool.name}** (v{tool.version}, {tool.category})\n"
            desc += f"  {tool.description}\n"

            params = tool.parameters.properties
            if params:
                required_fields = tool.parameters.required
                param_desc: List[str] = []  # pyright: ignore
                for name, info in params.items():
                    p_type = info.get("type", "any")
                    is_required = name in required_fields
                    desc_str = f"{name} ({p_type})"
                    if is_required:
                        desc_str += " [必填]"
                    param_desc.append(desc_str)  # pyright: ignore
                desc += f"  参数: {', '.join(param_desc)}\n"

            descriptions.append(desc)  # pyright: ignore

        return "\n".join(descriptions)  # pyright: ignore

    # pyright: ignore
    def format_tool_result_for_prompt(
            self, tool_name: str, result: ToolResult) -> str:
        """格式化工具结果用于 prompt"""
        if result.success:
            data = result.data
            if isinstance(data, (dict, list)):
                try:
                    data = json.dumps(data, ensure_ascii=False, indent=2)
                except Exception:
                    pass
            return f"【{tool_name}】执行成功:\n{data}"
        else:
            return f"【{tool_name}】执行失败: {result.error}"

    def _record_execution(
        self,
        tool_name: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        user_id: Optional[int],
        conversation_id: Optional[str],
    ) -> None:  # pyright: ignore
        """记录工具执行"""
        entry: Dict[str, Any] = {  # pyright: ignore
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            "params": params,
            "user_id": user_id,
            "conversation_id": conversation_id,
        }
        self._execution_history.append(entry)  # pyright: ignore

        # pyright: ignore[reportUnknownMemberType]
        while len(self._execution_history) > self._max_history:
            self._execution_history.pop(0)  # pyright: ignore

    def _record_result(self, tool_name: str, result: ToolResult) -> None:  # pyright: ignore
        """记录执行结果"""
        if self._execution_history:  # pyright: ignore[reportUnknownMemberType]
            self._execution_history[-1]["result"] = {  # pyright: ignore
                "success": result.success,
                "error": result.error,
                "execution_time_ms": result.execution_time_ms,
            }

    def _update_usage_stats(self, tool_name: str) -> None:  # pyright: ignore
        """更新使用统计"""
        if tool_name not in self._tools_usage_stats:  # pyright: ignore[reportUnknownMemberType]
            self._tools_usage_stats[tool_name] = {  # pyright: ignore
                "total_calls": 0,
                "success_count": 0,
                "fail_count": 0,
                "total_time_ms": 0,
            }

        # pyright: ignore
        stats: Dict[str, Any] = self._tools_usage_stats[tool_name]
        stats["total_calls"] += 1

    def get_usage_stats(self) -> Dict[str, Dict[str, Any]]:  # pyright: ignore
        """获取使用统计"""
        return self._tools_usage_stats  # pyright: ignore

    def get_execution_history(
        self,
        user_id: Optional[int] = None,
        tool_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:  # pyright: ignore
        """获取执行历史"""
        results: List[Dict[str, Any]] = []  # pyright: ignore
        for entry in reversed(
                # pyright: ignore[reportUnknownMemberType]
                self._execution_history):
            if user_id and entry.get("user_id") != user_id:  # pyright: ignore
                continue
            if tool_name and entry.get(
                    "tool_name") != tool_name:  # pyright: ignore
                continue
            results.append(entry)  # pyright: ignore
            if len(results) >= limit:
                break
        return results


def get_mcp_manager() -> MCPManager:
    """获取 MCP 管理器单例"""
    manager = MCPManager()
    if not manager._initialized:
        manager.initialize()
    return manager


# 便捷函数
async def execute_tool(
    tool_name: str,
    params: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None,
    conversation_id: Optional[str] = None,
) -> ToolResult:
    """执行工具的便捷函数"""
    manager = get_mcp_manager()
    return await manager.execute_tool(
        tool_name=tool_name,
        params=params,
        context=context,
        user_id=user_id,
        conversation_id=conversation_id,
    )


def get_tools_for_prompt(context: Optional[Dict[str, Any]] = None) -> str:
    """获取工具列表描述"""
    manager = get_mcp_manager()
    return manager.get_tools_for_prompt(context)
