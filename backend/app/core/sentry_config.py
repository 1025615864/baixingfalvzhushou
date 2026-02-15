"""Sentry错误追踪配置"""
from typing import Any, Optional
from sentry_sdk.integrations.fastapi import FastApiIntegration
from fastapi import Request
import logging

logger = logging.getLogger(__name__)

_sentry_initialized = False


def filter_sensitive_data(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any]:
    """过滤敏感数据（密码、Token等）
    
    Args:
        event: Sentry事件对象
        hint: 事件提示信息
        
    Returns:
        过滤后的事件对象
    """
    if 'request' in event:
        request_data = event['request']
        if 'data' in request_data:
            data = request_data['data']
            # 移除敏感字段
            if isinstance(data, dict):
                sensitive_fields = [
                    'password', 'token', 'api_key', 'secret',
                    'auth_token', 'access_token', 'refresh_token',
                    'api_secret', 'private_key', 'authorization'
                ]
                for field in sensitive_fields:
                    if field in data:
                        data[field] = '[REDACTED]'
    
    # 过滤查询参数中的敏感信息
    if 'request' in event and 'query_string' in event['request']:
        query_string = event['request']['query_string']
        if isinstance(query_string, str) and ('password' in query_string or 'token' in query_string):
            event['request']['query_string'] = '[REDACTED]'
    
    return event


def init_sentry(settings: Any) -> None:
    """初始化Sentry
    
    Args:
        settings: 应用配置对象
    """
    global _sentry_initialized
    
    try:
        import sentry_sdk
    except ImportError:
        logger.warning("sentry-sdk未安装，Sentry功能将被禁用")
        return
    
    # 检查是否已初始化
    if _sentry_initialized:
        logger.debug("Sentry已经初始化，跳过重复初始化")
        return
    
    # 获取配置
    dsn = getattr(settings, 'sentry_dsn', None)
    if not dsn:
        logger.info("未配置SENTRY_DSN，Sentry功能将被禁用")
        return
    
    # 获取环境配置
    environment = getattr(settings, 'sentry_environment', 
                         getattr(settings, 'ENVIRONMENT', 'development'))
    release = getattr(settings, 'sentry_release', 
                     getattr(settings, 'VERSION', '1.0.0'))
    traces_sample_rate = float(getattr(settings, 'sentry_traces_sample_rate', 0.1))
    profiles_sample_rate = float(getattr(settings, 'sentry_profiles_sample_rate', 0.0))
    
    # 初始化Sentry
    sentry_sdk.init(
        dsn=dsn,
        # 环境
        environment=environment,
        # 发布版本
        release=release,
        # 性能采样
        traces_sample_rate=max(0.0, min(1.0, traces_sample_rate)),
        # 性能分析采样
        profiles_sample_rate=max(0.0, min(1.0, profiles_sample_rate)),
        # 错误采样（100%）
        sample_rate=1.0,
        # 集成FastAPI
        integrations=[
            FastApiIntegration(),
        ],
        # 过滤敏感数据
        before_send=filter_sensitive_data,
        # 排除的错误类型
        ignore_errors=[
            KeyboardInterrupt,
            ConnectionResetError,
            BrokenPipeError,
            ConnectionAbortedError,
        ],
        # 发送未捕获的异常
        attach_stacktrace=True,
        # 采样率警告
        debug=False,
    )
    
    _sentry_initialized = True
    logger.info(f"Sentry初始化成功 - 环境: {environment}, 版本: {release}")


def capture_exception(exception: Exception, context: Optional[dict[str, Any]] = None) -> None:
    """捕获异常并发送到Sentry
    
    Args:
        exception: 异常对象
        context: 上下文信息
    """
    try:
        import sentry_sdk
    except ImportError:
        return
    
    if not _sentry_initialized:
        logger.debug("Sentry未初始化，跳过发送异常")
        return
    
    sentry_sdk.capture_exception(exception)


def capture_message(message: str, level: str = "info") -> None:
    """发送消息到Sentry
    
    Args:
        message: 消息内容
        level: 日志级别 (debug, info, warning, error, critical, fatal)
    """
    try:
        import sentry_sdk
    except ImportError:
        return
    
    if not _sentry_initialized:
        logger.debug("Sentry未初始化，跳过发送消息")
        return
    
    # 将字符串级别转换为有效的 LogLevel
    valid_levels = {"debug", "info", "warning", "error", "critical", "fatal"}
    sentry_level = level.lower() if level.lower() in valid_levels else "info"
    
    # type: ignore[arg-type] - Sentry SDK 类型定义限制，运行时正常工作
    sentry_sdk.capture_message(message, level=sentry_level)


def capture_user_feedback(user_id: int, feedback: str) -> None:
    """捕获用户反馈
    
    Args:
        user_id: 用户ID
        feedback: 反馈内容
    """
    try:
        import sentry_sdk
    except ImportError:
        return
    
    if not _sentry_initialized:
        logger.debug("Sentry未初始化，跳过发送反馈")
        return
    
    # type: ignore[arg-type] - Sentry SDK 类型定义限制，运行时正常工作
    sentry_sdk.capture_message(
        feedback,
        level="info",
        extras={
            "user_id": user_id,
            "type": "user_feedback"
        }
    )


def set_user_context(user_id: int, email: Optional[str] = None, username: Optional[str] = None) -> None:
    """设置用户上下文
    
    Args:
        user_id: 用户ID
        email: 用户邮箱
        username: 用户名
    """
    try:
        import sentry_sdk
    except ImportError:
        return
    
    if not _sentry_initialized:
        return
    
    user_data: dict[str, Any] = {"id": str(user_id)}
    if email:
        user_data["email"] = email
    if username:
        user_data["username"] = username
    
    sentry_sdk.set_user(user_data)


def set_tag(key: str, value: str) -> None:
    """设置标签
    
    Args:
        key: 标签键
        value: 标签值
    """
    try:
        import sentry_sdk
    except ImportError:
        return
    
    if not _sentry_initialized:
        return
    
    sentry_sdk.set_tag(key, value)


def set_extra(key: str, value: Any) -> None:
    """设置额外信息
    
    Args:
        key: 键
        value: 值
    """
    try:
        import sentry_sdk
    except ImportError:
        return
    
    if not _sentry_initialized:
        return
    
    sentry_sdk.set_extra(key, value)


def add_breadcrumb(message: str, category: Optional[str] = None, level: Optional[str] = None) -> None:
    """添加面包屑
    
    Args:
        message: 面包屑消息
        category: 面包屑类别
        level: 面包屑级别
    """
    try:
        import sentry_sdk
    except ImportError:
        return
    
    if not _sentry_initialized:
        return
    
    breadcrumb_data: dict[str, Any] = {"message": message}
    if category:
        breadcrumb_data["category"] = category
    if level:
        breadcrumb_data["level"] = level
    
    sentry_sdk.add_breadcrumb(**breadcrumb_data)


def configure_scope(callback: Any) -> None:
    """配置作用域
    
    Args:
        callback: 配置回调函数
    """
    try:
        import sentry_sdk
    except ImportError:
        return
    
    if not _sentry_initialized:
        return
    
    sentry_sdk.configure_scope(callback)


def is_initialized() -> bool:
    """检查Sentry是否已初始化
    
    Returns:
        True如果已初始化，否则False
    """
    return _sentry_initialized
