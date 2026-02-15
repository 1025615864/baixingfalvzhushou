"""MCP (Model Context Protocol) 工具系统

提供标准化的工具接口，让 AI 能够调用各种服务能力。

主要组件:
- BaseTool: 工具基类
- ToolRegistry: 工具注册表
- MCPManager: 工具管理器
- 各类具体工具实现
"""

from .base import (
    BaseTool,
    ToolResult,
    ToolInfo,
    ToolSchema,
    ToolCategory,
    ToolPermission,
)

from .registry import (
    ToolRegistry,
    get_registry,
    register_tool,
    get_tool,
    list_tools,
)

from .manager import (
    MCPManager,
    get_mcp_manager,
    execute_tool,
    get_tools_for_prompt,
)

__all__ = [
    # 基类
    "BaseTool",
    "ToolResult",
    "ToolInfo",
    "ToolSchema",
    "ToolCategory",
    "ToolPermission",

    # 注册表
    "ToolRegistry",
    "get_registry",
    "register_tool",
    "get_tool",
    "list_tools",

    # 管理器
    "MCPManager",
    "get_mcp_manager",
    "execute_tool",
    "get_tools_for_prompt",
]
