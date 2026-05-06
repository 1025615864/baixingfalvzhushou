"""头像服务测试"""
import pytest
from app.services.avatar_service import AvatarService


class TestAvatarService:
    """头像服务测试"""

    def test_validate_valid_avatar_url(self):
        """测试有效头像URL验证"""
        valid_urls = [
            "https://cdn.example.com/avatars/user123.jpg",
            "https://oss.example.com/avatar.png",
            "https://img.example.com/user/avatar.gif",
            "https://example.com/avatars/test.webp",
            "https://images.unsplash.com/photo-123456.jpg",
        ]

        for url in valid_urls:
            is_valid, error = AvatarService.validate_avatar_url(url)
            if not is_valid:
                print(f"Failed for {url}: {error}")
            assert is_valid, f"URL should be valid: {url}, error: {error}"

    def test_validate_invalid_avatar_url(self):
        """测试无效头像URL验证"""
        invalid_urls = [
            "",
            None,
            "not-a-url",
            "ftp://example.com/file.jpg",
            "https://evil.com/malware.exe",
            "https://cdn.example.com/avatars/photo.mp3",
            "https://cdn.example.com/avatars/photo.bmp",
        ]

        for url in invalid_urls:
            is_valid, error = AvatarService.validate_avatar_url(url)
            assert not is_valid, f"URL should be invalid: {url}"
            assert error is not None

    def test_validate_avatar_url_too_long(self):
        """测试超长URL验证"""
        long_url = "https://cdn.example.com/" + "a" * 500 + ".jpg"
        is_valid, error = AvatarService.validate_avatar_url(long_url)
        assert not is_valid
        assert "500" in error

    def test_generate_default_avatar(self):
        """测试默认头像生成"""
        url1 = AvatarService.generate_default_avatar(user_id=1, nickname="张三")
        assert "default" in url1
        assert url1.endswith(".svg")

        url2 = AvatarService.generate_default_avatar(user_id=2)
        assert "default" in url2

    def test_is_default_avatar(self):
        """测试默认头像判断"""
        assert AvatarService.is_default_avatar("https://cdn.example.com/avatars/default/A.svg")
        assert not AvatarService.is_default_avatar("https://cdn.example.com/avatars/user123.jpg")
