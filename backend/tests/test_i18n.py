import pytest
import json
from app.services.i18n import TranslationManager, I18nService, t, set_user_language, get_user_language, i18n_service

class TestTranslationManager:
    def test_init(self):
        manager = TranslationManager()
        assert manager._translations == {}
        assert manager._default_lang == "zh-CN"

    def test_load_translations(self):
        manager = TranslationManager()
        translations = {"hello": "你好"}
        manager.load_translations("zh-CN", translations)
        assert manager._translations["zh-CN"]["hello"] == "你好"

        # Test update
        more_translations = {"world": "世界"}
        manager.load_translations("zh-CN", more_translations)
        assert manager._translations["zh-CN"]["hello"] == "你好"
        assert manager._translations["zh-CN"]["world"] == "世界"

    def test_translate(self):
        manager = TranslationManager()
        manager.load_translations("zh-CN", {"hello": "你好"})
        manager.load_translations("en", {"hello": "Hello"})

        # Exact match
        assert manager.translate("hello", "zh-CN") == "你好"
        assert manager.translate("hello", "en") == "Hello"

        # Fallback to default (zh-CN)
        assert manager.translate("hello", "fr") == "你好"

        # Key missing in target lang but present in default
        manager.load_translations("fr", {"other": "autre"})
        assert manager.translate("hello", "fr") == "你好"

        # Key missing everywhere
        assert manager.translate("missing_key", "en") == "missing_key"

    def test_get_supported_languages(self):
        manager = TranslationManager()
        langs = manager.get_supported_languages()
        assert len(langs) == 3
        codes = [l["code"] for l in langs]
        assert "zh-CN" in codes
        assert "en" in codes
        assert "zh-TW" in codes

class TestI18nService:
    @pytest.fixture
    def service(self):
        # Create a fresh instance for each test to avoid state pollution
        return I18nService()

    def test_init_loads_defaults(self, service):
        # Check if default translations are loaded
        assert "welcome" in service.translation_manager._translations["zh-CN"]
        assert "welcome" in service.translation_manager._translations["en"]

    def test_user_language_preferences(self, service):
        user_id = 123
        
        # Default should be zh-CN
        assert service.get_user_language(user_id) == "zh-CN"

        # Set valid language
        result = service.set_user_language(user_id, "en")
        assert result["success"] is True
        assert result["language"] == "en"
        assert service.get_user_language(user_id) == "en"

        # Set invalid language -> fallback to default
        result = service.set_user_language(user_id, "invalid-lang")
        assert result["language"] == "zh-CN"
        assert service.get_user_language(user_id) == "zh-CN"

    def test_translate_with_user_context(self, service):
        user_id = 456
        service.set_user_language(user_id, "en")

        # Should use user's language (en)
        assert service.translate("confirm", user_id=user_id) == "Confirm"

        # Override with explicit lang
        assert service.translate("confirm", user_id=user_id, lang="zh-CN") == "确认"

        # No user, explicit lang
        assert service.translate("confirm", lang="en") == "Confirm"

    def test_get_translations(self, service):
        # This test might fail if the bug I found is real
        translations = service.get_translations("zh-CN")
        assert "welcome" in translations
        
        empty = service.get_translations("non-existent")
        assert empty == {}

    def test_export_translations(self, service):
        json_str = service.export_translations("zh-CN")
        data = json.loads(json_str)
        assert "welcome" in data
        assert data["welcome"] == "欢迎使用百姓助手"

@pytest.mark.asyncio
async def test_helper_functions():
    # These use the global i18n_service instance
    
    # Reset for test consistency if needed, but we can just test behavior
    # t()
    assert t("confirm", "zh-CN") == "确认"
    assert t("confirm", "en") == "Confirm"

    # set_user_language / get_user_language
    user_id = 999
    await set_user_language(user_id, "en")
    assert await get_user_language(user_id) == "en"
    
    # Verify t() respects global state if we could wire it up to user_id, 
    # but t() currently only takes key and lang. 
    # The global helper t() signature is: def t(key: str, lang: str | None = None) -> str:
    # So it doesn't automatically look up user context unless extended.
