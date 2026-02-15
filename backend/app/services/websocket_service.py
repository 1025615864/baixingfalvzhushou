"""WebSocket服务 - 实时消息推送（安全增强版）"""
import json
import logging
import time
from collections import defaultdict
from typing import Any, Literal
from fastapi import WebSocket
from datetime import datetime
from enum import Enum
from pydantic import BaseModel

from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class WebSocketPayloadType(str, Enum):
    """WS payload 类型定义 - 统一固化"""
    NOTIFICATION = "notification"
    CHAT_MESSAGE = "chat_message"
    SYSTEM = "system"
    COMMENT = "comment"
    REPLY = "reply"
    LIKE = "like"
    BOOKING = "booking"
    AI_RESPONSE = "ai_response"
    DOCUMENT_PROGRESS = "document_progress"


class WebSocketNotificationPayload(BaseModel):
    """统一通知 payload 结构"""
    type: Literal["notification"] = "notification"
    id: int | None = None
    title: str
    content: str
    link: str = ""
    category: str = "system"
    priority: int = 0
    created_at: str
    metadata: dict[str, Any] = {}


class WebSocketMessagePayload(BaseModel):
    """统一消息 payload 结构"""
    type: str
    id: str | None = None
    title: str
    content: str
    data: dict[str, Any] = {}
    timestamp: str


class WebSocketConnectionInfo:
    """WebSocket连接信息"""
    def __init__(self, websocket: WebSocket, user_id: int | None = None, client_ip: str = "unknown"):
        self.websocket = websocket
        self.user_id = user_id
        self.client_ip = client_ip
        self.connected_at = time.time()
        self.last_message_at = self.connected_at
        self.message_count = 0
        self.is_authorized = user_id is not None

    @property
    def age_seconds(self) -> float:
        """连接时长（秒）"""
        return time.time() - self.connected_at

    @property
    def idle_seconds(self) -> float:
        """空闲时长（秒）"""
        return time.time() - self.last_message_at

    def record_message(self) -> None:
        """记录消息"""
        self.message_count += 1
        self.last_message_at = time.time()


class ConnectionManager:
    """WebSocket连接管理器（安全增强版）"""

    def __init__(self):
        # 活跃连接: {user_id: [connection_info, ...]}
        self.active_connections: dict[int, list[WebSocketConnectionInfo]] = {}
        # 匿名连接: [connection_info, ...]
        self.anonymous_connections: list[WebSocketConnectionInfo] = []
        # 按IP分组的连接: {ip: count}
        self.ip_connections: dict[str, int] = defaultdict(int)
        # 消息速率限制: {connection_id: [(timestamp, count), ...]}
        self.message_rate_tracking: dict[int, list[tuple[float, int]]] = {}
        # 重试计数: {user_id: attempt_count}
        self.reconnect_attempts: dict[int, int] = defaultdict(int)
        # 连接超时检查周期（秒）
        self.timeout_check_interval = 60

    def _check_ip_connection_limit(self, client_ip: str) -> tuple[bool, str]:
        """检查IP连接限制"""
        current_ip_connections = self.ip_connections.get(client_ip, 0)
        max_connections = settings.ws_max_connections_per_ip

        if current_ip_connections >= max_connections:
            return False, f"该IP连接数已达上限 ({max_connections})"

        return True, ""

    def _check_user_connection_limit(self, user_id: int) -> tuple[bool, str]:
        """检查用户连接限制"""
        if user_id not in self.active_connections:
            return True, ""

        current_user_connections = len(self.active_connections[user_id])
        max_connections = settings.ws_max_connections_per_user

        if current_user_connections >= max_connections:
            return False, f"该用户连接数已达上限 ({max_connections})"

        return True, ""

    def _check_reconnect_limit(self, user_id: int) -> tuple[bool, int]:
        """检查重连限制"""
        if user_id not in self.reconnect_attempts:
            return True, 0

        attempts = self.reconnect_attempts[user_id]
        if attempts >= settings.ws_max_reconnect_attempts:
            return False, attempts

        return True, attempts

    def _check_message_rate(self, connection_id: int) -> tuple[bool, str]:
        """检查消息速率限制"""
        now = time.time()
        window = settings.ws_message_rate_window
        max_messages = settings.ws_message_rate_limit

        # 清理过期的记录
        if connection_id not in self.message_rate_tracking:
            self.message_rate_tracking[connection_id] = []

        cutoff = now - window
        self.message_rate_tracking[connection_id] = [
            (ts, count) for ts, count in self.message_rate_tracking[connection_id]
            if ts > cutoff
        ]

        # 计算当前窗口内的消息数
        total_messages = sum(count for _, count in self.message_rate_tracking[connection_id])

        if total_messages >= max_messages:
            return False, f"消息发送过于频繁，请稍后重试（{max_messages}条/{window}秒）"

        return True, ""

    def _update_message_rate(self, connection_id: int) -> None:
        """更新消息速率"""
        now = time.time()
        self.message_rate_tracking[connection_id].append((now, 1))

    async def connect(self, websocket: WebSocket,
                      user_id: int | None = None,
                      client_ip: str = "unknown") -> tuple[bool, str]:
        """建立WebSocket连接（带安全检查）"""
        # 检查IP连接限制
        ip_allowed, ip_msg = self._check_ip_connection_limit(client_ip)
        if not ip_allowed:
            logger.warning(f"IP连接限制: {client_ip} - {ip_msg}")
            return False, ip_msg

        # 检查用户连接限制
        if user_id:
            user_allowed, user_msg = self._check_user_connection_limit(user_id)
            if not user_allowed:
                logger.warning(f"用户连接限制: {user_id} - {user_msg}")
                return False, user_msg

        await websocket.accept()
        connection_info = WebSocketConnectionInfo(websocket, user_id, client_ip)

        if user_id:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = []
            self.active_connections[user_id].append(connection_info)
            self.ip_connections[client_ip] += 1
            # 重置重连计数
            self.reconnect_attempts[user_id] = 0
            logger.info(f"User {user_id} connected via WebSocket from {client_ip}")
        else:
            self.anonymous_connections.append(connection_info)
            self.ip_connections[client_ip] += 1
            logger.info(f"Anonymous user connected via WebSocket from {client_ip}")

        return True, "连接成功"

    async def check_message_limit(self, connection_info: WebSocketConnectionInfo) -> tuple[bool, str]:
        """检查消息限制"""
        # 检查消息速率
        connection_id = id(connection_info.websocket)
        rate_allowed, rate_msg = self._check_message_rate(connection_id)
        if not rate_allowed:
            return False, rate_msg

        # 检查连接超时
        if connection_info.idle_seconds > settings.ws_connection_timeout:
            return False, f"连接超时（{settings.ws_connection_timeout}秒无活动）"

        return True, ""

    async def receive_message(self, data: str,
                              connection_info: WebSocketConnectionInfo) -> tuple[bool, str]:
        """接收消息（带验证）"""
        # 检查消息大小
        message_size = len(data.encode('utf-8'))
        if message_size > settings.ws_max_message_size:
            return False, f"消息过大（最大{settings.ws_max_message_size}字节）"

        # 检查消息限制
        allowed, msg = await self.check_message_limit(connection_info)
        if not allowed:
            return False, msg

        # 记录消息
        connection_info.record_message()
        self._update_message_rate(id(connection_info.websocket))

        return True, ""

    def disconnect(self, websocket: WebSocket,
                   user_id: int | None = None,
                   client_ip: str = "unknown") -> None:
        """断开WebSocket连接"""
        # 更新IP连接计数
        if client_ip in self.ip_connections:
            self.ip_connections[client_ip] = max(0, self.ip_connections[client_ip] - 1)
            if self.ip_connections[client_ip] == 0:
                del self.ip_connections[client_ip]

        # 清理连接
        if user_id and user_id in self.active_connections:
            to_remove = None
            for conn_info in self.active_connections[user_id]:
                if conn_info.websocket == websocket:
                    to_remove = conn_info
                    break

            if to_remove:
                self.active_connections[user_id].remove(to_remove)
                # 清理速率追踪
                connection_id = id(websocket)
                if connection_id in self.message_rate_tracking:
                    del self.message_rate_tracking[connection_id]

            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected from WebSocket")
        else:
            for conn_info in self.anonymous_connections[:]:
                if conn_info.websocket == websocket:
                    self.anonymous_connections.remove(conn_info)
                    # 清理速率追踪
                    connection_id = id(websocket)
                    if connection_id in self.message_rate_tracking:
                        del self.message_rate_tracking[connection_id]
                    break
            logger.info("Anonymous user disconnected from WebSocket")

    def increment_reconnect_attempts(self, user_id: int) -> None:
        """增加重连尝试次数"""
        self.reconnect_attempts[user_id] += 1
        logger.info(f"User {user_id} reconnect attempt {self.reconnect_attempts[user_id]}")

    async def send_personal_message(
        self,
        user_id: int,
        message: dict[str, Any]
    ) -> bool:
        """发送个人消息"""
        if user_id not in self.active_connections:
            return False

        message_json = json.dumps(message, ensure_ascii=False, default=str)
        sent = False

        for connection_info in self.active_connections[user_id]:
            try:
                await connection_info.websocket.send_text(message_json)
                sent = True
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")

        return sent

    async def broadcast(self, message: dict[str, Any]) -> int:
        """广播消息给所有用户"""
        message_json = json.dumps(message, ensure_ascii=False, default=str)
        sent_count = 0

        # 发送给已登录用户
        for user_id, connections in self.active_connections.items():
            for connection_info in connections:
                try:
                    await connection_info.websocket.send_text(message_json)
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Broadcast failed for user {user_id}: {e}")

        # 发送给匿名用户
        for connection_info in self.anonymous_connections[:]:  # 使用切片创建副本
            try:
                await connection_info.websocket.send_text(message_json)
                sent_count += 1
            except Exception as e:
                logger.debug(f"Failed to send message to anonymous user: {e}")

        return sent_count

    async def cleanup_idle_connections(self) -> int:
        """清理空闲连接"""
        now = time.time()
        timeout = settings.ws_connection_timeout
        cleaned = 0

        # 清理用户连接
        to_remove_users = []
        for user_id, connections in self.active_connections.items():
            to_remove_conns = []
            for conn_info in connections:
                idle = now - conn_info.last_message_at
                if idle > timeout:
                    to_remove_conns.append(conn_info)

            for conn_info in to_remove_conns:
                try:
                    await conn_info.websocket.close(code=1001, reason="Connection timeout")
                except Exception as close_err:
                    logger.debug(f"Error closing websocket connection: {close_err}")
            # 从列表中移除（在迭代外部修改）
            for conn_info in to_remove_conns:
                if conn_info in connections:
                    connections.remove(conn_info)
                # 清理IP计数
                if conn_info.client_ip in self.ip_connections:
                    self.ip_connections[conn_info.client_ip] = max(0,
                        self.ip_connections[conn_info.client_ip] - 1)
                # 清理速率追踪
                connection_id = id(conn_info.websocket)
                if connection_id in self.message_rate_tracking:
                    del self.message_rate_tracking[connection_id]
                cleaned += 1

            if not connections:
                to_remove_users.append(user_id)

        for user_id in to_remove_users:
            del self.active_connections[user_id]

        # 清理匿名连接 - 使用切片创建副本避免迭代时修改列表
        to_remove_anon: list[WebSocketConnectionInfo] = []
        for conn_info in self.anonymous_connections[:]:
            idle = now - conn_info.last_message_at
            if idle > timeout:
                to_remove_anon.append(conn_info)

        for conn_info in to_remove_anon:
            try:
                await conn_info.websocket.close(code=1001, reason="Connection timeout")
            except Exception as close_err:
                logger.debug(f"Error closing anonymous websocket connection: {close_err}")
            # 从列表中移除并清理相关状态
            if conn_info in self.anonymous_connections:
                self.anonymous_connections.remove(conn_info)
            # 清理IP计数
            if conn_info.client_ip in self.ip_connections:
                self.ip_connections[conn_info.client_ip] = max(0,
                    self.ip_connections[conn_info.client_ip] - 1)
            # 清理速率追踪
            connection_id = id(conn_info.websocket)
            if connection_id in self.message_rate_tracking:
                del self.message_rate_tracking[connection_id]
            cleaned += 1

        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} idle connections")

        return cleaned

    def get_connection_stats(self) -> dict[str, Any]:
        """获取连接统计信息"""
        user_total = sum(len(conns) for conns in self.active_connections.values())
        anonymous_total = len(self.anonymous_connections)

        return {
            "total_connections": user_total + anonymous_total,
            "user_connections": user_total,
            "anonymous_connections": anonymous_total,
            "online_users": len(self.active_connections),
            "unique_ips": len(self.ip_connections),
        }

    def get_online_users(self) -> list[int]:
        """获取在线用户列表"""
        return list(self.active_connections.keys())

    def get_user_connection_count(self, user_id: int) -> int:
        """获取用户连接数"""
        return len(self.active_connections.get(user_id, []))

    def get_total_connections(self) -> int:
        """获取总连接数"""
        stats = self.get_connection_stats()
        return stats["total_connections"]


# 全局连接管理器实例
manager = ConnectionManager()


# 消息类型定义（已迁移至 WebSocketPayloadType，建议使用新枚举）
class MessageType:
    """消息类型常量（兼容旧接口）"""
    NOTIFICATION = WebSocketPayloadType.NOTIFICATION.value
    CHAT_MESSAGE = WebSocketPayloadType.CHAT_MESSAGE.value
    SYSTEM = WebSocketPayloadType.SYSTEM.value
    COMMENT = WebSocketPayloadType.COMMENT.value
    REPLY = WebSocketPayloadType.REPLY.value
    LIKE = WebSocketPayloadType.LIKE.value
    BOOKING = WebSocketPayloadType.BOOKING.value


def create_message(
    msg_type: str,
    title: str,
    content: str,
    data: dict[str, Any] | None = None
) -> dict[str, Any]:
    """创建标准消息格式（统一 payload）"""
    return {
        "type": msg_type,
        "title": title,
        "content": content,
        "data": data or {},
        "timestamp": datetime.now().isoformat()
    }


def create_notification_payload(
    title: str,
    content: str,
    notification_id: int | None = None,
    link: str = "",
    category: str = "system",
    priority: int = 0,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """创建统一通知 payload - 通知入口收敛"""
    return {
        "type": WebSocketPayloadType.NOTIFICATION.value,
        "id": notification_id,
        "title": title,
        "content": content,
        "link": link,
        "category": category,
        "priority": priority,
        "created_at": datetime.now().isoformat(),
        "metadata": metadata or {},
    }


async def notify_user(
    user_id: int,
    msg_type: str,
    title: str,
    content: str,
    data: dict[str, Any] | None = None
) -> bool:
    """发送通知给指定用户（统一入口）"""
    message = create_message(msg_type, title, content, data)
    return await manager.send_personal_message(user_id, message)


async def notify_user_unified(
    user_id: int,
    title: str,
    content: str,
    notification_id: int | None = None,
    link: str = "",
    category: str = "system",
    priority: int = 0,
    metadata: dict[str, Any] | None = None,
) -> bool:
    """统一通知入口 - 通知入口收敛

    所有通知统一通过此函数发送，确保 payload 结构一致，
    支持去重（通过 notification_id 避免重复推送）。
    """
    payload = create_notification_payload(
        title=title,
        content=content,
        notification_id=notification_id,
        link=link,
        category=category,
        priority=priority,
        metadata=metadata,
    )
    return await manager.send_personal_message(user_id, payload)


async def broadcast_system_message(title: str, content: str) -> int:
    """广播系统消息"""
    message = create_message(MessageType.SYSTEM, title, content)
    return await manager.broadcast(message)


async def broadcast_notification(
    title: str,
    content: str,
    category: str = "system",
    priority: int = 0,
) -> int:
    """广播通知 - 统一入口"""
    payload = create_notification_payload(
        title=title,
        content=content,
        category=category,
        priority=priority,
    )
    return await manager.broadcast(payload)
