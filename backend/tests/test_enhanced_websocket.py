"""Enhanced WebSocket 服务测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from fastapi import WebSocket


class TestEnhancedConnectionManager:
    """增强连接管理器测试"""

    @pytest.fixture
    def manager(self):
        """创建连接管理器实例"""
        from app.services.enhanced_websocket import EnhancedConnectionManager
        return EnhancedConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        """创建模拟WebSocket"""
        ws = MagicMock(spec=WebSocket)
        ws.accept = AsyncMock()
        return ws

    def test_initial_state(self, manager):
        """测试初始状态"""
        assert manager._user_connections == {}
        assert manager._anonymous_connections == []
        assert manager._rooms == {}
        assert manager._last_activity == {}

    @pytest.mark.asyncio
    async def test_connect_with_user(self, manager, mock_websocket):
        """测试用户连接"""
        connection_id = await manager.connect(mock_websocket, user_id=123)

        assert connection_id is not None
        assert 123 in manager._user_connections
        assert manager._user_connections[123]["websocket"] == mock_websocket
        assert "connection_id" in manager._user_connections[123]
        assert 123 in manager._last_activity

    @pytest.mark.asyncio
    async def test_connect_anonymous(self, manager, mock_websocket):
        """测试匿名连接"""
        connection_id = await manager.connect(mock_websocket, user_id=None)

        assert connection_id is not None
        assert mock_websocket in manager._anonymous_connections

    def test_disconnect_user(self, manager):
        """测试用户断开"""
        ws = MagicMock()
        manager._user_connections[123] = {
            "websocket": ws,
            "connection_id": "test",
            "rooms": set(["room1"]),
            "metadata": {}
        }
        manager._last_activity[123] = datetime.now(timezone.utc)

        # Use a mock that properly handles the coroutine to suppress warnings
        mock_task = MagicMock()
        mock_task.cancel = MagicMock()

        # Import asyncio locally to patch it where it's imported
        import asyncio
        with patch.object(asyncio, 'create_task', return_value=mock_task):
            manager.disconnect(ws, user_id=123)

        assert 123 not in manager._user_connections
        assert 123 not in manager._last_activity

    def test_disconnect_anonymous(self, manager):
        """测试匿名断开"""
        ws = MagicMock()
        manager._anonymous_connections.append(ws)

        manager.disconnect(ws, user_id=None)

        assert ws not in manager._anonymous_connections

    def test_create_room(self, manager):
        """测试创建房间"""
        room = manager.create_room("room1", "chat")

        assert room.room_id == "room1"
        assert room.room_type == "chat"
        assert "room1" in manager._rooms

    def test_join_room(self, manager):
        """测试加入房间"""
        manager.create_room("room1", "chat")
        manager._user_connections[123] = {
            "websocket": MagicMock(),
            "connection_id": "test",
            "rooms": set(),
            "metadata": {}
        }

        # Use a mock that properly handles the coroutine to suppress warnings
        mock_task = MagicMock()
        mock_task.cancel = MagicMock()

        import asyncio
        with patch.object(asyncio, 'create_task', return_value=mock_task):
            manager.join_room(123, "room1")

        assert "room1" in manager._user_connections[123]["rooms"]
        assert 123 in manager._rooms["room1"].members

    def test_leave_room(self, manager):
        """测试离开房间"""
        manager.create_room("room1", "chat")
        manager._user_connections[123] = {
            "websocket": MagicMock(),
            "connection_id": "test",
            "rooms": set(["room1"]),
            "metadata": {}
        }
        manager._rooms["room1"].members.add(123)

        # Use a mock that properly handles the coroutine to suppress warnings
        mock_task = MagicMock()
        mock_task.cancel = MagicMock()

        import asyncio
        with patch.object(asyncio, 'create_task', return_value=mock_task):
            manager.leave_room(123, "room1")

        assert "room1" not in manager._user_connections[123]["rooms"]
        assert 123 not in manager._rooms["room1"].members

    def test_get_user_rooms(self, manager):
        """测试获取用户房间"""
        manager.create_room("room1", "chat")
        manager.create_room("room2", "forum")
        manager._user_connections[123] = {
            "websocket": MagicMock(),
            "connection_id": "test",
            "rooms": set(["room1", "room2"]),
            "metadata": {}
        }

        rooms = manager._user_connections[123]["rooms"]

        assert len(rooms) == 2
        assert "room1" in rooms
        assert "room2" in rooms

    def test_get_connection_count(self, manager):
        """测试连接计数"""
        manager._user_connections[1] = {"websocket": MagicMock()}
        manager._user_connections[2] = {"websocket": MagicMock()}
        manager._anonymous_connections = [MagicMock(), MagicMock()]

        count = manager.get_total_connections()

        assert count == 4

    def test_get_room_count(self, manager):
        """测试房间计数"""
        manager.create_room("room1", "chat")
        manager.create_room("room2", "forum")
        manager.create_room("room3", "ai")

        count = len(manager._rooms)

        assert count == 3


class TestMessageType:
    """消息类型测试"""

    def test_message_types(self):
        """测试消息类型枚举"""
        from app.services.enhanced_websocket import MessageType

        assert MessageType.NOTIFICATION.value == "notification"
        assert MessageType.CHAT_MESSAGE.value == "chat_message"
        assert MessageType.SYSTEM.value == "system"
        assert MessageType.COMMENT.value == "comment"
        assert MessageType.LIKE.value == "like"
        assert MessageType.AI_STREAM.value == "ai_stream"
        assert MessageType.AI_COMPLETE.value == "ai_complete"
        assert MessageType.PRESENCE.value == "presence"


class TestRoom:
    """房间测试"""

    def test_room_creation(self):
        """测试房间创建"""
        from app.services.enhanced_websocket import Room

        room = Room(room_id="test_room", room_type="chat")

        assert room.room_id == "test_room"
        assert room.room_type == "chat"
        assert room.members == set()
        assert room.created_at is not None

    def test_room_with_members(self):
        """测试带成员的房间"""
        from app.services.enhanced_websocket import Room

        room = Room(room_id="test_room", room_type="chat", members={1, 2, 3})

        assert len(room.members) == 3
        assert 1 in room.members
        assert 2 in room.members
        assert 3 in room.members


class TestCreateMessage:
    """create_message 函数测试"""

    def test_create_notification_message(self):
        """测试创建通知消息"""
        from app.services.enhanced_websocket import create_message, MessageType

        msg = create_message(
            MessageType.NOTIFICATION,
            "测试标题",
            "测试内容"
        )

        assert msg["type"] == "notification"
        assert msg["title"] == "测试标题"
        assert msg["content"] == "测试内容"
        assert "timestamp" in msg

    def test_create_chat_message(self):
        """测试创建聊天消息"""
        from app.services.enhanced_websocket import create_message, MessageType

        msg = create_message(
            MessageType.CHAT_MESSAGE,
            "",
            "你好"
        )

        assert msg["type"] == "chat_message"
        assert msg["content"] == "你好"

    def test_create_system_message(self):
        """测试创建系统消息"""
        from app.services.enhanced_websocket import create_message, MessageType

        msg = create_message(
            MessageType.SYSTEM,
            "系统通知",
            "系统维护通知"
        )

        assert msg["type"] == "system"
        assert msg["title"] == "系统通知"
