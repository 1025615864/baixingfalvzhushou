"""MCP (Model Context Protocol) 工具系统基类"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List  # pyright: ignore
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class ToolResult(BaseModel):  # pyright: ignore
    """工具执行结果"""
    success: bool = True
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[int] = None
    model_config = ConfigDict(  # pyright: ignore
        json_encoders={  # pyright: ignore
            datetime: lambda v: v.isoformat()  # pyright: ignore
        }
    )


class ToolSchema(BaseModel):  # pyright: ignore
    """工具参数Schema定义"""
    type: str = "object"
    properties: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)


class ToolInfo(BaseModel):  # pyright: ignore
    """工具元信息"""
    name: str
    description: str
    version: str = "1.0.0"
    author: str = "百姓法律助手"
    category: str = "general"
    parameters: ToolSchema = Field(default_factory=ToolSchema)
    examples: List[Dict[str, Any]] = Field(
        default_factory=list)  # pyright: ignore
    tags: List[str] = Field(default_factory=list)
    deprecated: bool = False
    deprecation_message: Optional[str] = None


class BaseTool(ABC):  # pyright: ignore
    """工具基类"""

    # 子类必须设置
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    category: str = "general"
    tags: List[str] = []

    def __init__(self):
        self._info: Optional[ToolInfo] = None

    @abstractmethod
    # pyright: ignore
    async def execute(self,
                      params: Dict[str,
                                   Any],
                      context: Optional[Dict[str,
                                             Any]] = None) -> ToolResult:
        """执行工具逻辑

        Args:
            params: 工具参数
            context: 执行上下文（包含用户信息、会话信息等）

        Returns:
            ToolResult: 执行结果
        """
        pass

    def get_info(self) -> ToolInfo:  # pyright: ignore
        """获取工具元信息"""
        if self._info is None:
            self._info = ToolInfo(
                name=self.name,
                description=self.description,
                version=self.version,
                category=self.category,
                parameters=self._get_parameters_schema(),
                tags=self.tags,
            )
        return self._info

    def _get_parameters_schema(self) -> ToolSchema:  # pyright: ignore
        """获取参数Schema，子类可重写"""
        return ToolSchema()

    # pyright: ignore
    def _validate_params(
            self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """验证参数，返回 (是否有效, 错误信息)"""
        required = self.get_info().parameters.required
        for field in required:
            if field not in params or params[field] is None:
                return False, f"缺少必需参数: {field}"
        return True, None

    def _format_error(self, error: str) -> str:  # pyright: ignore
        """格式化错误信息"""
        return f"[{self.name}] {error}"

    # pyright: ignore
    async def arun(self,
                   params: Dict[str,
                                Any],
                   context: Optional[Dict[str,
                                          Any]] = None) -> ToolResult:
        """异步执行工具（带错误处理包装）"""
        import time
        start_time = time.time()

        try:
            # 参数验证
            valid, error = self._validate_params(params)
            if not valid:
                return ToolResult(
                    success=False,
                    error=self._format_error(error or "Unknown error"),
                    execution_time_ms=int((time.time() - start_time) * 1000)
                )

            # 执行具体逻辑
            result = await self.execute(params, context)
            result.execution_time_ms = int((time.time() - start_time) * 1000)
            return result

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"工具执行错误: {self.name}")
            return ToolResult(
                success=False,
                error=self._format_error(str(e)),
                execution_time_ms=int((time.time() - start_time) * 1000)
            )


class ToolCategory:
    """工具分类常量"""
    DOCUMENT = "document"
    CALCULATOR = "calculator"
    KNOWLEDGE = "knowledge"
    LAWFIRM = "lawfirm"
    USER = "user"
    SYSTEM = "system"
    UTILITY = "utility"


class ToolPermission:
    """工具权限常量"""
    PUBLIC = "public"          # 公开，无需权限
    USER_REQUIRED = "user"     # 需要用户登录
    VIP_REQUIRED = "vip"       # 需要VIP会员
    ADMIN_REQUIRED = "admin"   # 需要管理员权限
