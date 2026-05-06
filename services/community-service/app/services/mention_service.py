"""@提及用户服务"""
import re
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

MENTION_PATTERN = re.compile(r"@(\w+)")


class MentionService:
    def __init__(self, user_client=None):
        self.user_client = user_client

    def extract_mentions(self, content: str) -> List[str]:
        if not content:
            return []
        return MENTION_PATTERN.findall(content)

    async def resolve_mentioned_users(self, usernames: List[str]) -> List[dict]:
        if not usernames or not self.user_client:
            return []

        resolved = []
        for username in usernames:
            try:
                user_info = await self.user_client.get_user_by_nickname(username)
                if user_info and "id" in user_info:
                    resolved.append({
                        "username": username,
                        "user_id": user_info["id"],
                        "nickname": user_info.get("nickname", username)
                    })
            except Exception as e:
                logger.warning(f"Failed to resolve mention @{username}: {e}")

        return resolved

    async def create_mention_notifications(
        self,
        content: str,
        author_id: int,
        post_id: int,
        comment_id: Optional[int] = None
    ) -> List[dict]:
        usernames = self.extract_mentions(content)
        if not usernames:
            return []

        mentioned_users = await self.resolve_mentioned_users(usernames)
        notifications = []

        for user in mentioned_users:
            if user["user_id"] == author_id:
                continue

            notification = {
                "event_type": "community.user.mentioned",
                "mentioned_user_id": user["user_id"],
                "author_id": author_id,
                "post_id": post_id,
                "comment_id": comment_id,
                "payload": {
                    "username": user["username"],
                    "nickname": user["nickname"],
                    "preview": content[:100] if content else ""
                }
            }
            notifications.append(notification)

        return notifications


mention_service = MentionService()
