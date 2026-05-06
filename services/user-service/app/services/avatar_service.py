"""头像服务"""
import re
import logging
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

ALLOWED_AVATAR_DOMAINS = {
    "cdn.example.com",
    "oss.example.com",
    "img.example.com",
    "images.unsplash.com",
    "avatars.githubusercontent.com",
    "lh3.googleusercontent.com",
}

MAX_AVATAR_URL_LENGTH = 500

AVATAR_URL_PATTERN = re.compile(
    r"^https?://"
    r"(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}|"
    r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)|"
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    r"(?::\d+)?"
    r"(?:/?|[/?]\S+)$"
)


class AvatarValidationError(Exception):
    """头像验证错误"""
    pass


class AvatarService:
    """头像服务"""

    @staticmethod
    def validate_avatar_url(url: str) -> tuple[bool, Optional[str]]:
        """验证头像URL

        Args:
            url: 头像URL

        Returns:
            (is_valid, error_message)
        """
        if not url:
            return False, "头像URL不能为空"

        if len(url) > MAX_AVATAR_URL_LENGTH:
            return False, f"头像URL长度不能超过{MAX_AVATAR_URL_LENGTH}字符"

        if not AVATAR_URL_PATTERN.match(url):
            return False, "头像URL格式不正确"

        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        allowed = False
        for allowed_domain in ALLOWED_AVATAR_DOMAINS:
            if domain == allowed_domain or domain.endswith(f".{allowed_domain}"):
                allowed = True
                break

        if not allowed:
            logger.warning(f"Avatar URL domain not in whitelist: {domain}")

        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
        path_lower = parsed.path.lower()
        if not any(path_lower.endswith(ext) for ext in image_extensions):
            return False, "头像必须是图片格式 (jpg, png, gif, webp)"

        return True, None

    @staticmethod
    def generate_default_avatar(user_id: int, nickname: Optional[str] = None) -> str:
        """生成默认头像URL

        Args:
            user_id: 用户ID
            nickname: 用户昵称

        Returns:
            默认头像URL
        """
        if nickname:
            initial = nickname[0].upper()
        else:
            initial = str(user_id % 10)

        return f"https://cdn.example.com/avatars/default/{initial}.svg"

    @staticmethod
    def is_default_avatar(url: str) -> bool:
        """检查是否是默认头像

        Args:
            url: 头像URL

        Returns:
            是否是默认头像
        """
        return "default" in url.lower() or url.startswith("https://cdn.example.com/avatars/default/")
