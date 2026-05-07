"""Common services 模块单元测试"""
import pytest
from unittest.mock import MagicMock, patch

from services.common.services.i18n import TranslationManager
from services.common.services.storage_service import StorageProvider, LocalStorage, S3Storage, storage_manager


class TestTranslationManager:
    """翻译管理器测试"""

    @pytest.fixture
    def translator(self):
        """创建翻译管理器"""
        return TranslationManager()

    def test_add_translation(self, translator):
        """测试添加翻译"""
        translator.add_translation("en", "user.welcome", "Welcome")
        translator.add_translation("zh", "user.welcome", "欢迎")

        assert translator.get("user.welcome", "en") == "Welcome"
        assert translator.get("user.welcome", "zh") == "欢迎"

    def test_add_translations(self, translator):
        """测试批量添加翻译"""
        translator.add_translations("en", {
            "user.welcome": "Welcome",
            "user.goodbye": "Goodbye",
        })

        assert translator.get("user.welcome", "en") == "Welcome"
        assert translator.get("user.goodbye", "en") == "Goodbye"

    def test_get_existing(self, translator):
        """测试获取已有翻译"""
        translator.add_translation("en", "greeting", "Hello")
        assert translator.get("greeting", "en") == "Hello"

    def test_get_missing_returns_key(self, translator):
        """测试获取不存在的 key 返回 key 本身"""
        result = translator.get("nonexistent", "en")
        assert result == "nonexistent"

    def test_get_missing_returns_default(self, translator):
        """测试获取不存在的 key 返回默认值"""
        result = translator.get("nonexistent", "en", default="Default")
        assert result == "Default"

    def test_get_missing_language_returns_key(self, translator):
        """测试获取不存在的语言返回 key"""
        translator.add_translation("en", "key", "Value")
        result = translator.get("key", "fr")
        assert result == "key"

    def test_get_with_formatting(self, translator):
        """测试翻译格式化"""
        translator.add_translation("en", "user.greeting", "Hello, {name}!")
        result = translator.get("user.greeting", "en", name="Alice")
        assert result == "Hello, Alice!"

    def test_get_with_multiple_formatting(self, translator):
        """测试多参数格式化"""
        translator.add_translation("en", "order.status", "Order {id}: {status}")
        result = translator.get("order.status", "en", id="123", status="completed")
        assert result == "Order 123: completed"

    def test_get_missing_language_with_formatting(self, translator):
        """测试缺失语言时的格式化"""
        translator.add_translation("en", "greeting", "Hello, {name}!")
        result = translator.get("greeting", "fr", name="Bob")
        assert result == "greeting"

    def test_add_translation_file(self, translator, tmp_path):
        """测试从文件加载翻译"""
        import json
        translations = {"user.welcome": "Welcome", "user.logout": "Logout"}
        file_path = tmp_path / "en.json"
        file_path.write_text(json.dumps(translations))

        translator.add_translation_file("en", str(file_path))

        assert translator.get("user.welcome", "en") == "Welcome"
        assert translator.get("user.logout", "en") == "Logout"

    def test_supported_languages(self, translator):
        """测试支持的语言"""
        translator.add_translation("en", "key", "Value")
        translator.add_translation("zh", "key", "值")

        languages = translator.get_supported_languages()
        assert "en" in languages
        assert "zh" in languages

    def test_supported_languages_empty(self, translator):
        """测试空时的支持语言"""
        languages = translator.get_supported_languages()
        assert languages == []

    def test_clear_translations(self, translator):
        """测试清空翻译"""
        translator.add_translation("en", "key", "Value")
        translator.clear_translations()
        assert translator.get("key", "en") == "key"


class TestStorageProvider:
    """存储提供者基类测试"""

    def test_provider_interface(self):
        """测试提供者接口"""
        provider = LocalStorage(base_dir="/tmp")
        assert hasattr(provider, "upload")
        assert hasattr(provider, "download")
        assert hasattr(provider, "delete")
        assert hasattr(provider, "get_url")


class TestLocalStorage:
    """本地存储测试"""

    @pytest.fixture
    def local_storage(self, tmp_path):
        """创建本地存储"""
        return LocalStorage(base_dir=str(tmp_path))

    def test_upload_file(self, local_storage, tmp_path):
        """测试上传文件"""
        source = tmp_path / "test.txt"
        source.write_text("Hello World")

        result = local_storage.upload(
            str(source),
            key="test/hello.txt",
        )

        assert result["key"] == "test/hello.txt"
        assert result["url"].startswith("/")

    def test_get_url(self, local_storage):
        """测试获取 URL"""
        url = local_storage.get_url("test/hello.txt")
        assert "test/hello.txt" in url


class TestS3Storage:
    """S3 存储测试"""

    @pytest.fixture
    def s3_storage(self):
        """创建 S3 存储（mock）"""
        return S3Storage(
            bucket="test-bucket",
            region="us-east-1",
            access_key="test-key",
            secret_key="test-secret",
        )

    def test_get_url(self, s3_storage):
        """测试获取 S3 URL"""
        url = s3_storage.get_url("test/file.txt")
        assert "test-bucket" in url
        assert "test/file.txt" in url


class TestStorageManager:
    """存储管理器测试"""

    def test_set_provider(self):
        """测试设置提供者"""
        manager = storage_manager
        local = LocalStorage(base_dir="/tmp")
        manager.set_provider(local)
        assert manager.provider == local

    def test_singleton(self):
        """测试单例模式"""
        manager1 = storage_manager
        manager2 = storage_manager
        assert manager1 is manager2
