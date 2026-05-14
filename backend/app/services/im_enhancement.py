"""IM 增强服务 - 离线消息、快捷回复、会话超时管理"""
import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class OfflineMessageQueue:
    """离线消息队列 - 用户离线时暂存消息，重连后推送"""

    MAX_QUEUE_SIZE = 100
    MAX_AGE_SECONDS = 86400  # 24小时

    def __init__(self):
        self._pending: dict[int, list[dict[str, Any]]] = defaultdict(list)

    def enqueue(self, user_id: int, message: dict[str, Any]) -> None:
        """入队离线消息"""
        message["_queued_at"] = time.time()
        queue = self._pending[user_id]

        if len(queue) >= self.MAX_QUEUE_SIZE:
            queue.pop(0)

        queue.append(message)
        logger.debug(f"离线消息入队: user={user_id}, queue_size={len(queue)}")

    def dequeue_all(self, user_id: int) -> list[dict[str, Any]]:
        """获取并清空用户离线消息"""
        messages = self._pending.pop(user_id, [])
        now = time.time()

        valid = []
        expired = 0
        for msg in messages:
            queued_at = msg.get("_queued_at", now)
            if now - queued_at <= self.MAX_AGE_SECONDS:
                msg.pop("_queued_at", None)
                valid.append(msg)
            else:
                expired += 1

        if expired:
            logger.info(f"清理过期离线消息: user={user_id}, expired={expired}")

        if valid:
            logger.info(f"离线消息推送: user={user_id}, count={len(valid)}")

        return valid

    def get_pending_count(self, user_id: int) -> int:
        """获取待推送消息数量"""
        return len(self._pending.get(user_id, []))

    def cleanup_expired(self) -> int:
        """清理所有过期消息"""
        now = time.time()
        cleaned = 0

        for user_id in list(self._pending.keys()):
            queue = self._pending[user_id]
            valid = [
                m for m in queue
                if now - m.get("_queued_at", now) <= self.MAX_AGE_SECONDS
            ]
            cleaned += len(queue) - len(valid)

            if valid:
                self._pending[user_id] = valid
            else:
                del self._pending[user_id]

        if cleaned:
            logger.info(f"清理过期离线消息: {cleaned} 条")

        return cleaned


class SessionTimeoutTracker:
    """会话超时跟踪器 - 管理咨询会话的超时与自动关闭"""

    SESSION_TIMEOUT_MINUTES = 30
    EVALUATION_REMINDER_DELAY_MINUTES = 5

    def __init__(self):
        self._sessions: dict[int, dict[str, Any]] = {}

    def start_session(self, consultation_id: int, lawyer_id: int, user_id: int) -> None:
        """开始跟踪会话"""
        self._sessions[consultation_id] = {
            "consultation_id": consultation_id,
            "lawyer_id": lawyer_id,
            "user_id": user_id,
            "started_at": time.time(),
            "last_activity": time.time(),
            "message_count": 0,
            "closed": False,
        }
        logger.info(f"会话跟踪开始: consultation={consultation_id}")

    def record_activity(self, consultation_id: int) -> None:
        """记录会话活动"""
        if consultation_id in self._sessions:
            self._sessions[consultation_id]["last_activity"] = time.time()
            self._sessions[consultation_id]["message_count"] += 1

    def close_session(self, consultation_id: int) -> dict | None:
        """关闭会话"""
        session = self._sessions.pop(consultation_id, None)
        if session:
            session["closed"] = True
            session["duration"] = time.time() - session["started_at"]
            logger.info(f"会话关闭: consultation={consultation_id}, duration={session['duration']:.0f}s")
        return session

    def check_timeouts(self) -> list[dict]:
        """检查超时会话，返回需要关闭的会话列表"""
        now = time.time()
        timeout_seconds = self.SESSION_TIMEOUT_MINUTES * 60
        expired = []

        for consultation_id, session in list(self._sessions.items()):
            if session.get("closed"):
                continue

            idle = now - session["last_activity"]
            if idle > timeout_seconds:
                session["closed"] = True
                session["duration"] = now - session["started_at"]
                expired.append(dict(session))
                del self._sessions[consultation_id]
                logger.info(f"会话超时自动关闭: consultation={consultation_id}, idle={idle:.0f}s")

        return expired

    def get_session_status(self, consultation_id: int) -> dict | None:
        """获取会话状态"""
        session = self._sessions.get(consultation_id)
        if not session:
            return None

        return {
            "consultation_id": consultation_id,
            "started_at": datetime.fromtimestamp(session["started_at"]).isoformat(),
            "last_activity": datetime.fromtimestamp(session["last_activity"]).isoformat(),
            "message_count": session["message_count"],
            "idle_seconds": time.time() - session["last_activity"],
            "closed": session.get("closed", False),
        }

    def get_active_sessions(self) -> list[int]:
        """获取活跃会话列表"""
        return [cid for cid, s in self._sessions.items() if not s.get("closed")]


# 全局实例
offline_queue = OfflineMessageQueue()
session_tracker = SessionTimeoutTracker()


def create_chat_message(
    consultation_id: int,
    sender_id: int,
    sender_role: str,
    content: str,
    msg_type: str = "chat_message",
) -> dict[str, Any]:
    """创建标准聊天消息"""
    return {
        "type": msg_type,
        "consultation_id": consultation_id,
        "sender_id": sender_id,
        "sender_role": sender_role,
        "content": content,
        "timestamp": datetime.now().isoformat(),
    }


async def send_or_queue_message(
    consultation_id: int,
    sender_id: int,
    sender_role: str,
    content: str,
    recipient_id: int,
    connection_manager,
) -> dict[str, Any]:
    """发送消息或加入离线队列"""
    message = create_chat_message(
        consultation_id=consultation_id,
        sender_id=sender_id,
        sender_role=sender_role,
        content=content,
    )

    online_users = connection_manager.get_online_users()

    if recipient_id in online_users:
        sent = await connection_manager.send_personal_message(recipient_id, message)
        if sent:
            message["delivery_status"] = "delivered"
        else:
            offline_queue.enqueue(recipient_id, message)
            message["delivery_status"] = "sent"
    else:
        offline_queue.enqueue(recipient_id, message)
        message["delivery_status"] = "queued"

    return message


def get_pending_messages_for_user(user_id: int) -> list[dict[str, Any]]:
    """获取用户离线消息"""
    return offline_queue.dequeue_all(user_id)


def get_pending_message_count(user_id: int) -> int:
    """获取用户待推送消息数"""
    return offline_queue.get_pending_count(user_id)