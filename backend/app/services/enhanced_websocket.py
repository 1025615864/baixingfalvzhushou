"""增强的 WebSocket 服务 - 实时消息推送

增强功能:
- 房间/频道订阅- 实时事件
推送
- AI 流式响应支持
- 在线状态管理
"""

import json
import logging
from typing import Any, Dict, Optional, Set
from fastapi import WebSocket
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型常量"""
    NOTIFICATION = "notification"
    CHAT_MESSAGE = "chat_message"
    SYSTEM = "system"
    COMMENT = "comment"
    REPLY = "reply"
    LIKE = "like"
    BOOKING = "booking"
    AI_STREAM = "ai_stream"  # AI 流式响应
    AI_COMPLETE = "ai_complete"  # AI 响应完成
    PRESENCE = "presence"  # 在线状态
    FORUM = "forum"  # 论坛相关
    ORDER = "order"  # 订单相关


@dataclass
class Room:
    """消息房间/频道"""
    room_id: str
    room_type: str  # chat, forum, notification, ai
    members: Set[int] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)


class EnhancedConnectionManager:
    """增强版 WebSocket 连接管理器"""

    def __init__(self):
        # 用户连接: {user_id: {websocket: connection, rooms: set}}
        self._user_connections: Dict[int, Dict[str, Any]] = {}
        # 匿名连接
        self._anonymous_connections: list[WebSocket] = []
        # 房间: {room_id: Room}
        self._rooms: Dict[str, Room] = {}
        # 最后活动时间
        self._last_activity: Dict[int, datetime] = {}

    async def connect(
        self,
        websocket: WebSocket,
        user_id: Optional[int] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """建立 WebSocket 连接，返回连接 ID"""
        await websocket.accept()

        connection_id = (
            f"{user_id or 'anonymous'}_{datetime.now().timestamp()}"
        )

        if user_id:
            self._user_connections[user_id] = {
                "websocket": websocket,
                "connection_id": connection_id,
                "rooms": set(),
                "metadata": metadata or {},
            }
            self._last_activity[user_id] = datetime.now()
            logger.info(
                f"User {user_id} connected via WebSocket (id: {connection_id})")
        else:
            self._anonymous_connections.append(websocket)
            logger.info(f"Anonymous user connected (id: {connection_id})")

        return connection_id

    def disconnect(
        self,
        websocket: WebSocket,
        user_id: Optional[int] = None,
        connection_id: Optional[str] = None,
    ) -> None:
        """断开连接"""
        if user_id and user_id in self._user_connections:
            # 退出所有房间
            rooms = self._user_connections[user_id].get("rooms", set())
            for room_id in list(rooms):
                self.leave_room(user_id, room_id)

            del self._user_connections[user_id]
            if user_id in self._last_activity:
                del self._last_activity[user_id]

            # 广播离线状态
            self._broadcast_presence(user_id, "offline")

            logger.info(f"User {user_id} disconnected")
        elif websocket in self._anonymous_connections:
            self._anonymous_connections.remove(websocket)
            logger.info("Anonymous user disconnected")

    # === 房间管理 ===

    def create_room(
        self,
        room_id: str,
        room_type: str,
        initial_members: Optional[Set[int]] = None,
    ) -> Room:
        """创建房间"""
        room = Room(
            room_id=room_id,
            room_type=room_type,
            members=initial_members or set(),
        )
        self._rooms[room_id] = room
        return room

    def join_room(self, user_id: int, room_id: str) -> bool:
        """用户加入房间"""
        if room_id not in self._rooms:
            return False

        room = self._rooms[room_id]
        room.members.add(user_id)

        if user_id in self._user_connections:
            self._user_connections[user_id]["rooms"].add(room_id)

        # 广播用户加入
        import asyncio
        asyncio.create_task(self._broadcast_to_room(room_id, {
            "type": MessageType.PRESENCE.value,
            "action": "join",
            "user_id": user_id,
            "room_id": room_id,
            "timestamp": datetime.now().isoformat(),
        }))

        return True

    def leave_room(self, user_id: int, room_id: str) -> bool:
        """用户离开房间"""
        if room_id not in self._rooms:
            return False

        room = self._rooms[room_id]
        room.members.discard(user_id)

        if user_id in self._user_connections:
            self._user_connections[user_id]["rooms"].discard(room_id)

        # 广播用户离开
        import asyncio
        asyncio.create_task(self._broadcast_to_room(room_id, {
            "type": MessageType.PRESENCE.value,
            "action": "leave",
            "user_id": user_id,
            "room_id": room_id,
            "timestamp": datetime.now().isoformat(),
        }))

        return True

    def get_room_members(self, room_id: str) -> Set[int]:
        """获取房间成员"""
        if room_id in self._rooms:
            return self._rooms[room_id].members.copy()
        return set()

    # === 消息发送 ===

    async def send_personal_message(
        self,
        user_id: int,
        message: Dict[str, Any],
    ) -> bool:
        """发送个人消息"""
        if user_id not in self._user_connections:
            return False

        try:
            await self._user_connections[user_id]["websocket"].send_json(message)
            return True
        except Exception as e:
            logger.error(f"Failed to send message to user {user_id}: {e}")
            return False

    async def send_to_connection(
        self,
        connection_id: str,
        message: Dict[str, Any],
    ) -> bool:
        """根据连接 ID 发送消息"""
        for user_id, conn_info in self._user_connections.items():
            if conn_info.get("connection_id") == connection_id:
                try:
                    await conn_info["websocket"].send_json(message)
                    return True
                except Exception:
                    pass
        return False

    async def _broadcast_to_room(
        self,
        room_id: str,
        message: Dict[str, Any],
    ) -> int:
        """向房间内所有成员广播消息"""
        if room_id not in self._rooms:
            return 0

        room = self._rooms[room_id]
        sent_count = 0

        for user_id in room.members:
            if await self.send_personal_message(user_id, message):
                sent_count += 1

        return sent_count

    async def broadcast(
        self,
        message: Dict[str, Any],
        user_ids: Optional[Set[int]] = None,
    ) -> int:
        """广播消息"""
        message_json = json.dumps(message, ensure_ascii=False, default=str)
        sent_count = 0

        target_users = user_ids or set(self._user_connections.keys())

        for user_id in target_users:
            if user_id in self._user_connections:
                try:
                    await self._user_connections[user_id]["websocket"].send_text(message_json)
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Broadcast failed for user {user_id}: {e}")

        # 发送给匿名用户
        for connection in self._anonymous_connections:
            try:
                await connection.send_text(message_json)
                sent_count += 1
            except Exception:
                pass

        return sent_count

    # === 在线状态 ===

    def _broadcast_presence(self, user_id: int, status: str):
        """广播用户在线状态"""
        message = {
            "type": MessageType.PRESENCE.value,
            "user_id": user_id,
            "status": status,
            "timestamp": datetime.now().isoformat(),
        }
        # 广播给所有在线用户
        import asyncio
        asyncio.create_task(self.broadcast(message))

    def get_online_users(self) -> Set[int]:
        """获取在线用户列表"""
        return set(self._user_connections.keys())

    def get_total_connections(self) -> int:
        """获取总连接数"""
        return len(self._user_connections) + len(self._anonymous_connections)

    def is_online(self, user_id: int) -> bool:
        """检查用户是否在线"""
        return user_id in self._user_connections

    # === AI 流式响应支持 ===

    async def send_ai_chunk(
        self,
        user_id: int,
        conversation_id: str,
        chunk: str,
        is_complete: bool = False,
    ):
        """发送 AI 响应片段"""
        message = {
            "type": (MessageType.AI_COMPLETE.value if is_complete
                     else MessageType.AI_STREAM.value),
            "conversation_id": conversation_id,
            "content": chunk,
            "is_complete": is_complete,
            "timestamp": datetime.now().isoformat(),
        }

        await self.send_personal_message(user_id, message)

    # === 通知推送 ===

    async def notify(
        self,
        user_id: int,
        notification_type: str,
        title: str,
        content: str,
        data: Optional[Dict] = None,
    ):
        """发送通知"""
        message = {
            "type": MessageType.NOTIFICATION.value,
            "notification_type": notification_type,
            "title": title,
            "content": content,
            "data": data or {},
            "timestamp": datetime.now().isoformat(),
        }

        await self.send_personal_message(user_id, message)


# 创建全局实例
enhanced_manager = EnhancedConnectionManager()


def create_message(
    msg_type: MessageType,
    title: str,
    content: str,
    data: Optional[Dict] = None,
) -> Dict[str, Any]:
    """创建标准消息格式"""
    return {
        "type": msg_type.value if isinstance(
            msg_type,
            MessageType) else msg_type,
        "title": title,
        "content": content,
        "data": data or {},
        "timestamp": datetime.now().isoformat(),
    }


async def notify_user(
    user_id: int,
    msg_type: MessageType,
    title: str,
    content: str,
    data: Optional[Dict] = None,
) -> bool:
    """发送通知给指定用户"""
    message = create_message(msg_type, title, content, data)
    return await enhanced_manager.send_personal_message(user_id, message)


async def broadcast_system_message(title: str, content: str) -> int:
    """广播系统消息"""
    message = create_message(MessageType.SYSTEM, title, content)
    return await enhanced_manager.broadcast(message)


async def notify_comment(
    post_author_id: int,
    commenter_id: int,
    commenter_name: str,
    post_title: str,
    comment_preview: str,
):
    """通知帖子作者有新评论"""
    from .unified_notification_service import unified_notification_service

    await unified_notification_service.notify_ws(
        user_id=post_author_id,
        title="您有新的评论",
        content=f"{commenter_name} 评论了您的帖子《{post_title}》",
    )


async def notify_reply(
    comment_author_id: int,
    replier_id: int,
    replier_name: str,
    original_comment: str,
    reply_preview: str,
):
    """通知评论作者有新回复"""
    from .unified_notification_service import unified_notification_service

    await unified_notification_service.notify_ws(
        user_id=comment_author_id,
        title="您有新的回复",
        content=f"{replier_name} 回复了您的评论",
    )


async def notify_like(
    author_id: int,
    liker_id: int,
    liker_name: str,
    content_type: str,  # post, comment
    content_id: int,
):
    """通知有人点赞"""
    from .unified_notification_service import unified_notification_service

    await unified_notification_service.notify_ws(
        user_id=author_id,
        title="您有新的点赞",
        content=f"{liker_name} 赞了您的{content_type}",
    )


async def notify_booking_status(
    user_id: int,
    lawyer_name: str,
    booking_time: str,
    status: str,  # confirmed, cancelled, completed
):
    """通知预约状态变更"""
    status_messages = {
        "confirmed": "已确认",
        "cancelled": "已取消",
        "completed": "已完成",
    }

    from .unified_notification_service import unified_notification_service

    await unified_notification_service.notify_ws(
        user_id=user_id,
        title=f"预约{status_messages.get(status, status)}",
        content=f"您与 {lawyer_name} 的咨询预约{status_messages.get(status, status)}",
    )
