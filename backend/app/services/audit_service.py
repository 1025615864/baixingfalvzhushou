"""审计日志服务

提供统一的审计日志记录功能，支持数据库存储和异步批量写入。

功能特性:
    - 异步批量写入数据库，提高性能
    - 支持多种操作类型（CREATE、UPDATE、DELETE、LOGIN等）
    - 支持审计上下文自动填充用户信息
    - 支持日志级别（debug、info、warning、error、critical）
    - 支持批量处理和队列缓冲

审计日志表结构:
    - action: 操作类型
    - resource_type: 资源类型（如 user、order、payment）
    - resource_id: 资源ID
    - user_id: 用户ID
    - username: 用户名
    - ip_address: IP地址
    - user_agent: 浏览器标识
    - request_id: 请求ID
    - details: 详细信息（JSON）
    - old_value: 修改前的值（JSON）
    - new_value: 修改后的值（JSON）
    - severity: 日志级别
    - success: 是否成功
    - error_message: 错误信息
    - duration_ms: 耗时（毫秒）

使用示例:
    ```python
    from app.services import get_audit_logger, log_audit, AuditContext, AuditAction

    # 使用便捷函数
    log_audit(
        action=AuditAction.CREATE,
        resource_type="order",
        resource_id="ORD-123",
        details={"amount": 100}
    )

    # 使用上下文管理器
    with AuditContext(user_id=123, username="张三", ip_address="192.168.1.1"):
        # 自动填充用户信息
        log_audit(
            action=AuditAction.UPDATE,
            resource_type="order",
            resource_id="ORD-123",
            old_value={"status": "pending"},
            new_value={"status": "paid"}
        )

    # 使用审计记录器
    logger = get_audit_logger()
    entry = logger.create_entry(
        action=AuditAction.DELETE,
        resource_type="user",
        resource_id="456",
        success=True
    )
    await logger.log(entry)
    ```

初始化:
    ```python
    from app.services.audit_service import init_audit_db

    # 在应用启动时调用
    await init_audit_db()
    ```
"""
from __future__ import annotations

import asyncio
import json
import logging
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

from ..database import engine

logger = logging.getLogger("audit")

Base = declarative_base()

audit_context: ContextVar[Optional[dict[str, Any]]] = ContextVar(
    "audit_context", default=None
)


class AuditAction(str, Enum):
    """审计操作类型枚举

    定义系统支持的所有审计操作类型。

    Attributes:
        CREATE: 创建操作
        READ: 读取操作
        UPDATE: 更新操作
        DELETE: 删除操作
        LOGIN: 登录成功
        LOGOUT: 登出
        LOGIN_FAILED: 登录失败
        PASSWORD_CHANGE: 密码修改
        PERMISSION_CHANGE: 权限变更
        EXPORT: 导出操作
        IMPORT: 导入操作
        ADMIN_ACTION: 管理员操作
        API_CALL: API调用
        SYSTEM: 系统操作
    """

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    PERMISSION_CHANGE = "permission_change"
    EXPORT = "export"
    IMPORT = "import"
    ADMIN_ACTION = "admin_action"
    API_CALL = "api_call"
    SYSTEM = "system"


class AuditSeverity(str, Enum):
    """审计日志级别枚举

    Attributes:
        DEBUG: 调试级别
        INFO: 信息级别
        WARNING: 警告级别
        ERROR: 错误级别
        CRITICAL: 严重级别
    """

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditLogEntry:
    """审计日志条目

    用于构建审计日志记录的数据结构。

    Attributes:
        action: 操作类型
        resource_type: 资源类型
        resource_id: 资源ID
        user_id: 用户ID
        username: 用户名
        ip_address: IP地址
        user_agent: 浏览器标识
        request_id: 请求ID
        details: 详细信息
        old_value: 修改前的值
        new_value: 修改后的值
        severity: 日志级别
        success: 是否成功
        error_message: 错误信息
        duration_ms: 耗时（毫秒）
        metadata: 元数据
    """

    action: AuditAction
    resource_type: str
    resource_id: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    details: Optional[dict[str, Any]] = None
    old_value: Optional[dict[str, Any]] = None
    new_value: Optional[dict[str, Any]] = None
    severity: AuditSeverity = AuditSeverity.INFO
    success: bool = True
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    metadata: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典

        Returns:
            审计日志字典
        """
        return {
            "id": str(uuid4()),
            "action": self.action.value,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "user_id": self.user_id,
            "username": self.username,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "request_id": self.request_id,
            "details": self.details,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "severity": self.severity.value,
            "success": self.success,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


class AuditLog(Base):
    """审计日志数据库模型

    对应数据库中的 audit_logs 表。

    表索引:
        - idx_audit_resource: (resource_type, resource_id)
        - idx_audit_created_at: created_at
    """

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    action = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(255), nullable=True)
    user_id = Column(String(255), nullable=True, index=True)
    username = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(255), nullable=True)
    details = Column(Text, nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    severity = Column(String(20), nullable=False, default="info")
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)
    duration_ms = Column(String(20), nullable=True)
    extra_data = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_audit_resource", "resource_type", "resource_id"),
        Index("idx_audit_created_at", "created_at"),
    )


class AuditLogger:
    """审计日志记录器

    提供异步批量写入和队列缓冲功能的审计日志记录器。

    Features:
        - 异步处理，不阻塞主流程
        - 批量写入数据库，提高性能
        - 队列缓冲，防止内存溢出
        - 支持同步和异步两种模式

    Attributes:
        async_mode: 是否异步模式
        batch_size: 批量写入大小
        flush_interval: 刷新间隔（秒）

    Examples:
        ```python
        logger = AuditLogger(async_mode=True, batch_size=100, flush_interval=5.0)

        # 启动（异步模式需要）
        await logger.start()

        # 记录日志
        entry = logger.create_entry(
            action=AuditAction.CREATE,
            resource_type="order",
            resource_id="ORD-123"
        )
        await logger.log(entry)

        # 停止
        await logger.stop()
        ```
    """

    def __init__(
        self,
        async_mode: bool = True,
        batch_size: int = 100,
        flush_interval: float = 5.0,
    ) -> None:
        self.async_mode = async_mode
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._queue: asyncio.Queue[AuditLogEntry] = asyncio.Queue(
            maxsize=10000
        )
        self._task: Optional[asyncio.Task[None]] = None
        self._running = False

    async def start(self) -> None:
        """启动异步处理任务

        在异步模式下，需要调用此方法启动后台处理任务。
        """
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._process_queue())
        logger.info("Audit logger started")

    async def stop(self) -> None:
        """停止异步处理任务

        等待队列中的日志写入完成后停止。
        """
        if not self._running:
            return
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._flush()
        logger.info("Audit logger stopped")

    async def _process_queue(self) -> None:
        """处理队列中的日志

        持续从队列中获取日志，批量写入数据库。
        """
        buffer: list[AuditLogEntry] = []
        last_flush = asyncio.get_event_loop().time()

        while self._running or not self._queue.empty():
            try:
                timeout = max(
                    0.1,
                    self.flush_interval -
                    (asyncio.get_event_loop().time() - last_flush)
                )
                entry = await asyncio.wait_for(
                    self._queue.get(), timeout=timeout
                )  # noqa: E501
                buffer.append(entry)
            except asyncio.TimeoutError:
                pass

            if (
                len(buffer) >= self.batch_size or
                (buffer and
                 asyncio.get_event_loop().time() -
                 last_flush >= self.flush_interval)
            ):
                await self._write_batch(buffer)
                buffer.clear()
                last_flush = asyncio.get_event_loop().time()

        if buffer:
            await self._write_batch(buffer)

    async def _write_batch(self, entries: list[AuditLogEntry]) -> None:
        """写入一批日志到数据库

        Args:
            entries: 审计日志条目列表
        """
        if not entries:
            return

        try:
            from ..database import AsyncSessionLocal
            async with AsyncSessionLocal() as session:
                for entry in entries:
                    log = AuditLog(
                        action=entry.action.value,
                        resource_type=entry.resource_type,
                        resource_id=entry.resource_id,
                        user_id=str(entry.user_id) if entry.user_id else None,
                        username=entry.username,
                        ip_address=entry.ip_address,
                        user_agent=entry.user_agent,
                        request_id=entry.request_id,
                        details=json.dumps(
                            entry.details, ensure_ascii=False
                        ) if entry.details else None,
                        old_value=json.dumps(
                            entry.old_value, ensure_ascii=False
                        ) if entry.old_value else None,
                        new_value=json.dumps(
                            entry.new_value, ensure_ascii=False
                        ) if entry.new_value else None,
                        severity=entry.severity.value,
                        success=entry.success,
                        error_message=entry.error_message,
                        duration_ms=str(
                            entry.duration_ms
                        ) if entry.duration_ms else None,
                        extra_data=json.dumps(
                            entry.metadata, ensure_ascii=False
                        ) if entry.metadata else None,
                    )
                    session.add(log)
                await session.commit()
        except Exception as e:
            logger.exception(f"Failed to write audit log batch: {e}")

    async def _flush(self) -> None:
        """刷新队列

        将队列中剩余的日志写入数据库。
        """
        entries = []
        while not self._queue.empty():
            try:
                entry = self._queue.get_nowait()
                entries.append(entry)
            except asyncio.QueueEmpty:
                break
        if entries:
            await self._write_batch(entries)

    async def log(self, entry: AuditLogEntry) -> None:
        """记录审计日志

        Args:
            entry: 审计日志条目
        """
        if self.async_mode:
            try:
                self._queue.put_nowait(entry)
            except asyncio.QueueFull:
                logger.warning("Audit log queue full, dropping entry")
        else:
            await self._write_batch([entry])

    def log_sync(self, entry: AuditLogEntry) -> None:
        """同步记录审计日志

        在异步模式下创建后台任务执行。

        Args:
            entry: 审计日志条目
        """
        if not self.async_mode:
            asyncio.run(self._write_batch([entry]))
        else:
            asyncio.create_task(self.log(entry))

    def create_entry(
        self,
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        old_value: Optional[dict[str, Any]] = None,
        new_value: Optional[dict[str, Any]] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        success: bool = True,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> AuditLogEntry:
        """创建审计日志条目

        Args:
            action: 操作类型
            resource_type: 资源类型
            resource_id: 资源ID
            user_id: 用户ID
            username: 用户名
            ip_address: IP地址
            user_agent: 浏览器标识
            request_id: 请求ID
            details: 详细信息
            old_value: 修改前的值
            new_value: 修改后的值
            severity: 日志级别
            success: 是否成功
            error_message: 错误信息
            duration_ms: 耗时（毫秒）
            metadata: 元数据

        Returns:
            AuditLogEntry实例
        """
        return AuditLogEntry(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            details=details,
            old_value=old_value,
            new_value=new_value,
            severity=severity,
            success=success,
            error_message=error_message,
            duration_ms=duration_ms,
            metadata=metadata,
        )


audit_logger = AuditLogger(async_mode=True)


def get_audit_logger() -> AuditLogger:
    """获取全局审计日志器实例

    Returns:
        全局AuditLogger实例
    """
    return audit_logger


class AuditContext:
    """审计上下文管理器

    用于在代码块中设置审计上下文，自动填充用户信息。

    支持同步和异步上下文管理器。

    Examples:
        ```python
        # 同步使用
        with AuditContext(user_id=123, username="张三", ip_address="192.168.1.1"):
            log_audit(AuditAction.UPDATE, "order", "ORD-123")

        # 异步使用
        async with AuditContext(user_id=123, username="李四"):
            await logger.log(entry)
        ```
    """

    def __init__(
        self,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        self.user_id = user_id
        self.username = username
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.request_id = request_id
        self._token: Any = None

    def __enter__(self) -> AuditContext:
        ctx = {
            "user_id": self.user_id,
            "username": self.username,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "request_id": self.request_id,
        }
        self._token = audit_context.set(ctx)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        audit_context.reset(self._token)

    async def __aenter__(self) -> AuditContext:
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self.__exit__(exc_type, exc_val, exc_tb)


def get_current_audit_context() -> Optional[dict[str, Any]]:
    """获取当前审计上下文

    Returns:
        审计上下文字典，如果不存在则返回None
    """
    return audit_context.get()


def log_audit(
    action: AuditAction,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
    success: bool = True,
    error_message: Optional[str] = None,
    **kwargs,
) -> None:
    """便捷的审计日志记录函数

    自动从当前上下文获取用户信息并记录日志。

    Args:
        action: 操作类型
        resource_type: 资源类型
        resource_id: 资源ID
        details: 详细信息
        success: 是否成功
        error_message: 错误信息
        **kwargs: 其他参数（user_id、username、ip_address等）
    """
    ctx = get_current_audit_context() or {}
    entry = AuditLogEntry(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=kwargs.get("user_id") or ctx.get("user_id"),
        username=kwargs.get("username") or ctx.get("username"),
        ip_address=kwargs.get("ip_address") or ctx.get("ip_address"),
        user_agent=kwargs.get("user_agent") or ctx.get("user_agent"),
        request_id=kwargs.get("request_id") or ctx.get("request_id"),
        details=details,
        success=success,
        error_message=error_message,
        severity=kwargs.get("severity", AuditSeverity.INFO),
        duration_ms=kwargs.get("duration_ms"),
        old_value=kwargs.get("old_value"),
        new_value=kwargs.get("new_value"),
        metadata=kwargs.get("metadata"),
    )
    asyncio.create_task(audit_logger.log(entry))


async def init_audit_db() -> None:
    """初始化审计日志数据库表

    在应用启动时调用，创建所需的数据库表。
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Audit database tables created")
