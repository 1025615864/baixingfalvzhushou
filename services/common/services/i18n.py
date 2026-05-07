"""多语言基础框架服务

提供国际化（i18n）框架和中英文文案分离功能。
"""
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class TranslationManager:
    """翻译管理器"""

    def __init__(self):
        self._translations: dict[str, dict[str, str]] = {}
        self._default_lang = "zh-CN"

    def load_translations(
            self, lang: str, translations: dict[str, str]) -> None:
        """加载翻译

        Args:
            lang: 语言代码
            translations: 翻译字典
        """
        if lang not in self._translations:
            self._translations[lang] = {}

        self._translations[lang].update(translations)
        logger.info(f"Loaded {len(translations)} translations for {lang}")

    def translate(self, key: str, lang: str | None = None) -> str:
        """翻译

        Args:
            key: 翻译键
            lang: 语言代码

        Returns:
            翻译文本
        """
        target_lang = lang or self._default_lang

        if target_lang in self._translations and key in self._translations[target_lang]:
            return self._translations[target_lang][key]

        if self._default_lang in self._translations and key in self._translations[
                self._default_lang]:
            return self._translations[self._default_lang][key]

        return key

    def get_supported_languages(self) -> list[dict[str, str]]:
        """获取支持的语言列表

        Returns:
            语言列表
        """
        return [
            {"code": "zh-CN", "name": "简体中文", "native_name": "简体中文"},
            {"code": "en", "name": "English", "native_name": "English"},
            {"code": "zh-TW", "name": "繁體中文", "native_name": "繁體中文"},
        ]


class I18nService:
    """国际化服务"""

    def __init__(self):
        self.translation_manager = TranslationManager()
        self._user_preferences: dict[int, str] = {}

        self._load_default_translations()

    def _load_default_translations(self) -> None:
        """加载默认翻译"""
        zh_cn = {
            "welcome": "欢迎使用百姓助手",
            "consultation": "法律咨询",
            "contracts": "合同服务",
            "lawyers": "律师团队",
            "my_cases": "我的案件",
            "settings": "设置",
            "logout": "退出登录",
            "login": "登录",
            "register": "注册",
            "search": "搜索",
            "submit": "提交",
            "cancel": "取消",
            "confirm": "确认",
            "delete": "删除",
            "edit": "编辑",
            "save": "保存",
            "loading": "加载中...",
            "no_results": "暂无数据",
            "error": "出错了",
            "success": "操作成功",
            "retry": "重试",
        }

        en = {
            "welcome": "Welcome to Baixing Assistant",
            "consultation": "Legal Consultation",
            "contracts": "Contract Services",
            "lawyers": "Lawyer Team",
            "my_cases": "My Cases",
            "settings": "Settings",
            "logout": "Logout",
            "login": "Login",
            "register": "Register",
            "search": "Search",
            "submit": "Submit",
            "cancel": "Cancel",
            "confirm": "Confirm",
            "delete": "Delete",
            "edit": "Edit",
            "save": "Save",
            "loading": "Loading...",
            "no_results": "No results",
            "error": "An error occurred",
            "success": "Success",
            "retry": "Retry",
        }

        self.translation_manager.load_translations("zh-CN", zh_cn)
        self.translation_manager.load_translations("en", en)

    def set_user_language(self, user_id: int, lang: str) -> dict[str, Any]:
        """设置用户语言偏好

        Args:
            user_id: 用户ID
            lang: 语言代码

        Returns:
            设置结果
        """
        supported_langs = [lang["code"]
                           for lang in self.translation_manager.get_supported_languages()]

        if lang not in supported_langs:
            lang = self.translation_manager._default_lang

        self._user_preferences[user_id] = lang

        return {
            "user_id": user_id,
            "language": lang,
            "success": True,
        }

    def get_user_language(self, user_id: int) -> str:
        """获取用户语言偏好

        Args:
            user_id: 用户ID

        Returns:
            语言代码
        """
        return self._user_preferences.get(
            user_id, self.translation_manager._default_lang)

    def translate(
        self,
        key: str,
        user_id: int | None = None,
        lang: str | None = None,
    ) -> str:
        """翻译文本

        Args:
            key: 翻译键
            user_id: 用户ID
            lang: 语言代码

        Returns:
            翻译文本
        """
        target_lang = lang

        if user_id is not None and target_lang is None:
            target_lang = self.get_user_language(user_id)

        return self.translation_manager.translate(key, target_lang)

    def get_translations(self, lang: str) -> dict[str, str]:
        """获取翻译字典

        Args:
            lang: 语言代码

        Returns:
            翻译字典
        """
        if lang in self.translation_manager._translations:
            return self.translation_manager._translations[lang]

        return {}

    def export_translations(self, lang: str) -> str:
        """导出翻译为 JSON

        Args:
            lang: 语言代码

        Returns:
            JSON 字符串
        """
        translations = self.get_translations(lang)
        return json.dumps(translations, ensure_ascii=False, indent=2)


# 单例实例
i18n_service = I18nService()


def t(key: str, lang: str | None = None) -> str:
    """便捷翻译函数

    Args:
        key: 翻译键
        lang: 语言代码

    Returns:
        翻译文本
    """
    return i18n_service.translate(key, lang=lang)


async def set_user_language(user_id: int, lang: str) -> dict[str, Any]:
    """便捷函数：设置用户语言

    Args:
        user_id: 用户ID
        lang: 语言代码

    Returns:
        设置结果
    """
    return i18n_service.set_user_language(user_id, lang)


async def get_user_language(user_id: int) -> str:
    """便捷函数：获取用户语言

    Args:
        user_id: 用户ID

    Returns:
        语言代码
    """
    return i18n_service.get_user_language(user_id)
