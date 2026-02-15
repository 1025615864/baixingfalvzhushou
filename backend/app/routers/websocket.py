"""WebSocket路由（安全增强版）"""
import logging
import json
import asyncio
from typing import Annotated
from datetime import datetime, timedelta
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy import select

from ..config import get_settings
from ..database import AsyncSessionLocal
from ..models.user import User
from ..services.websocket_service import manager, MessageType, create_message
from ..utils.security import decode_access_token

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])

# 连接速率限制: {user_id_or_ip: [(timestamp, count), ...]}
_connection_rate_tracker: dict[str, list[tuple[float, int]]] = {}

# 活跃连接计数: {user_id: count}
_user_connection_count: dict[int, int] = {}

# 每用户最大连接数
MAX_CONNECTIONS_PER_USER = 5

# 每秒最大消息数
MAX_MESSAGES_PER_SECOND = 10

# 消息大小限制 (10KB)
MAX_MESSAGE_SIZE = 10 * 1024

# 心跳超时时间 (秒)
HEARTBEAT_TIMEOUT = 60


def _get_client_ip(websocket: WebSocket) -> str:
    """获取客户端真实IP"""
    # 优先从 X-Forwarded-For 获取
    forwarded_for = websocket.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    # 其次从 X-Real-IP 获取
    real_ip = websocket.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    
    # 最后从 client 获取
    client = websocket.client
    if client and client.host:
        return client.host
    return "unknown"


def _get_token_from_websocket(websocket: WebSocket, query_token: str | None) -> str | None:
    """从WebSocket请求中获取token"""
    # 优先从Authorization header中获取
    auth = websocket.headers.get("authorization")
    if auth:
        parts = auth.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
    return query_token


def _check_connection_rate_limit(identifier: str) -> tuple[bool, str]:
    """检查连接速率限制（防止连接洪泛攻击）"""
    now = time.time()
    window = 60  # 60秒窗口
    max_connections = 10  # 每窗口最大连接数
    
    if identifier not in _connection_rate_tracker:
        _connection_rate_tracker[identifier] = []
    
    # 清理过期记录
    cutoff = now - window
    _connection_rate_tracker[identifier] = [
        (ts, count) for ts, count in _connection_rate_tracker[identifier] if ts > cutoff
    ]
    
    # 计算当前窗口内的连接数
    total = sum(count for _, count in _connection_rate_tracker[identifier])
    
    if total >= max_connections:
        return False, f"连接过于频繁，请稍后再试（每{window}秒最多{max_connections}次）"
    
    # 记录本次连接
    _connection_rate_tracker[identifier].append((now, 1))
    return True, ""


def _check_user_connection_limit(user_id: int) -> tuple[bool, str]:
    """检查用户连接数限制"""
    current = _user_connection_count.get(user_id, 0)
    if current >= MAX_CONNECTIONS_PER_USER:
        return False, f"该用户连接数已达上限 ({MAX_CONNECTIONS_PER_USER})"
    return True, ""


def _increment_user_connection(user_id: int) -> None:
    """增加用户连接计数"""
    _user_connection_count[user_id] = _user_connection_count.get(user_id, 0) + 1


def _decrement_user_connection(user_id: int) -> None:
    """减少用户连接计数"""
    if user_id in _user_connection_count:
        _user_connection_count[user_id] = max(0, _user_connection_count[user_id] - 1)
        if _user_connection_count[user_id] == 0:
            del _user_connection_count[user_id]


def _validate_message_format(data: str) -> tuple[bool, str, dict | None]:
    """
    验证WebSocket消息格式和内容
    
    Returns:
        (is_valid, error_message, parsed_data)
    """
    # 检查消息大小
    message_size = len(data.encode('utf-8'))
    if message_size > MAX_MESSAGE_SIZE:
        return False, f"消息过大（最大{MAX_MESSAGE_SIZE}字节）", None
    
    # 检查消息是否为空
    if not data or not data.strip():
        return False, "消息不能为空", None
    
    # 尝试解析JSON
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError:
        # 非JSON消息（如ping）允许通过
        if data.strip().lower() in ['ping', 'pong', 'heartbeat']:
            return True, "", {"type": "heartbeat"}
        return False, "消息必须是有效的JSON格式", None
    
    # 验证必需字段
    if not isinstance(parsed, dict):
        return False, "消息必须是JSON对象", None
    
    # 检查消息类型字段
    msg_type = parsed.get('type')
    if msg_type and not isinstance(msg_type, str):
        return False, "消息类型必须是字符串", None
    
    # 检查内容长度
    content = parsed.get('content', '')
    if content and len(str(content)) > 5000:
        return False, "消息内容过长（最大5000字符）", None
    
    return True, "", parsed


class MessageRateLimiter:
    """消息速率限制器（每秒限制）"""
    
    def __init__(self, max_per_second: int = MAX_MESSAGES_PER_SECOND):
        self.max_per_second = max_per_second
        self.message_times: list[float] = []
    
    def check_rate(self) -> tuple[bool, str]:
        """检查是否超过速率限制"""
        now = time.time()
        
        # 清理1秒前的记录
        cutoff = now - 1.0
        self.message_times = [t for t in self.message_times if t > cutoff]
        
        # 检查是否超过限制
        if len(self.message_times) >= self.max_per_second:
            return False, f"消息发送过于频繁（每秒最多{self.max_per_second}条）"
        
        # 记录本次消息
        self.message_times.append(now)
        return True, ""


class HeartbeatManager:
    """心跳管理器"""
    
    def __init__(self, websocket: WebSocket, timeout: int = HEARTBEAT_TIMEOUT):
        self.websocket = websocket
        self.timeout = timeout
        self.last_pong = time.time()
        self._running = False
        self._task: asyncio.Task | None = None
    
    async def start(self) -> None:
        """启动心跳检测"""
        self._running = True
        self._task = asyncio.create_task(self._heartbeat_loop())
    
    async def stop(self) -> None:
        """停止心跳检测"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def _heartbeat_loop(self) -> None:
        """心跳检测循环"""
        while self._running:
            try:
                await asyncio.sleep(30)  # 每30秒检查一次
                
                # 检查是否超时
                if time.time() - self.last_pong > self.timeout:
                    logger.warning(f"心跳超时，关闭连接")
                    await self.websocket.close(code=1001, reason="Heartbeat timeout")
                    break
                
                # 发送ping
                await self.websocket.send_text('{"type": "ping"}')
            except Exception as e:
                logger.debug(f"Heartbeat loop error: {e}")
                break
    
    def record_pong(self) -> None:
        """记录pong响应"""
        self.last_pong = time.time()


import time  # 确保time模块被导入


async def _get_active_user_id(token: str | None) -> int | None:
    """
    验证token并获取用户ID
    
    Returns:
        用户ID（无效返回None）
    """
    if not token:
        return None

    payload = decode_access_token(token)
    if payload is None:
        return None

    # 支持多种用户ID字段名：sub（标准JWT）或 user_id（向后兼容）
    user_id_value = payload.get("sub") or payload.get("user_id")
    if user_id_value is None:
        return None
    
    try:
        user_id = int(str(user_id_value))
    except (TypeError, ValueError):
        return None

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            return None
        if not user.is_active:
            return None
        return user.id


def _validate_websocket_message(data: str) -> tuple[bool, str]:
    """
    验证WebSocket消息格式和大小
    
    Returns:
        (is_valid, error_message)
    """
    # 检查消息大小
    message_size = len(data.encode('utf-8'))
    if message_size > settings.ws_max_message_size:
        return False, f"消息过大（最大{settings.ws_max_message_size}字节）"

    # 检查消息是否为空
    if not data or not data.strip():
        return False, "消息不能为空"

    return True, ""


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Annotated[str | None, Query()] = None,
):
    """
    WebSocket连接端点（安全增强版）

    连接方式: ws://host/ws?token=<jwt_token>

    安全特性:
    - 每IP连接数限制
    - 每用户连接数限制
    - 消息速率限制
    - 消息大小限制
    - 连接超时检测
    - 重试限制

    消息格式:
    {
        "type": "notification|chat_message|system",
        "title": "消息标题",
        "content": "消息内容",
        "data": {},
        "timestamp": "2024-01-01T00:00:00"
    }
    """
    client_ip = _get_client_ip(websocket)
    auth_token = _get_token_from_websocket(websocket, token)
    
    # 验证用户认证
    if auth_token:
        user_id = await _get_active_user_id(auth_token)
        if user_id is None:
            logger.warning(f"WebSocket认证失败: {client_ip}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="认证失败")
            return
    else:
        user_id = None

    # 建立连接（带安全检查）
    success, msg = await manager.connect(websocket, user_id, client_ip)
    if not success:
        logger.warning(f"WebSocket连接被拒绝: {client_ip} - {msg}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=msg)
        return

    connection_info = None
    try:
        # 查找连接信息
        if user_id and user_id in manager.active_connections:
            for conn_info in manager.active_connections[user_id]:
                if conn_info.websocket == websocket:
                    connection_info = conn_info
                    break
        else:
            for conn_info in manager.anonymous_connections:
                if conn_info.websocket == websocket:
                    connection_info = conn_info
                    break

        # 发送连接成功消息
        welcome_msg = create_message(
            MessageType.SYSTEM, "连接成功", "WebSocket连接已建立", {
                "user_id": user_id,
                "online_count": manager.get_total_connections(),
                "connection_timeout": settings.ws_connection_timeout,
                "rate_limit": {
                    "max_messages": settings.ws_message_rate_limit,
                    "window_seconds": settings.ws_message_rate_window,
                }
            })
        await websocket.send_json(welcome_msg)

        logger.info(f"WebSocket连接建立成功: user={user_id}, ip={client_ip}")

        # 保持连接并处理消息
        while True:
            data = await websocket.receive_text()

            # 验证消息格式
            valid, validate_msg = _validate_websocket_message(data)
            if not valid:
                logger.warning(f"无效的WebSocket消息: user={user_id}, ip={client_ip}, error={validate_msg}")
                await websocket.send_json(create_message(
                    MessageType.SYSTEM, "错误", validate_msg
                ))
                continue

            # 检查消息限制
            if connection_info:
                allowed, limit_msg = await manager.check_message_limit(connection_info)
                if not allowed:
                    logger.warning(f"消息限制触发: user={user_id}, ip={client_ip}, error={limit_msg}")
                    await websocket.send_json(create_message(
                        MessageType.SYSTEM, "限制", limit_msg
                    ))
                    continue
                
                # 记录消息
                await manager.receive_message(data, connection_info)

            # 心跳检测
            if data == "ping":
                await websocket.send_text("pong")
                continue

            # 可以在这里处理客户端发送的其他消息
            logger.debug(f"Received from user {user_id}: {data}")

    except WebSocketDisconnect as e:
        manager.disconnect(websocket, user_id, client_ip)
        logger.info(f"User {user_id} disconnected normally (code={e.code}, reason={e.reason})")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}", exc_info=True)
        manager.disconnect(websocket, user_id, client_ip)


@router.get("/ws/status")
async def websocket_status():
    """获取WebSocket连接状态"""
    stats = manager.get_connection_stats()
    return {
        "total_connections": stats["total_connections"],
        "user_connections": stats["user_connections"],
        "anonymous_connections": stats["anonymous_connections"],
        "anonymous_count": stats["anonymous_connections"],
        "online_users": manager.get_online_users(),
        "unique_ips": stats["unique_ips"],
    }


@router.get("/ws/config")
async def websocket_config():
    """获取WebSocket配置信息（用于前端）"""
    return {
        "connection_timeout": settings.ws_connection_timeout,
        "ping_interval": 30,  # 建议的心跳间隔（秒）
        "max_message_size": settings.ws_max_message_size,
        "rate_limit": {
            "max_messages": settings.ws_message_rate_limit,
            "window_seconds": settings.ws_message_rate_window,
        },
        "max_reconnect_attempts": settings.ws_max_reconnect_attempts,
        "reconnect_backoff": settings.ws_reconnect_backoff,
    }
