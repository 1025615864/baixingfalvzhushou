"""运营配置服务"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.ops_models import OpsConfig
from app.utils.sensitive_words import SensitiveWordFilter


class ConfigService:
    def __init__(self, db: AsyncSession):
        self.db = db

    DEFAULT_COMMUNITY_RULES = {
        "post_min_length": 20,
        "post_max_length": 50000,
        "comment_max_length": 2000,
        "posts_per_day_limit": 5,
        "comments_per_hour_limit": 20,
        "new_user_post_delay_hours": 24,
        "auto_close_days": 90,
        "require_approval_for_new_users": False,
        "allow_anonymous_view": True,
        "lawyer_badge_enabled": True
    }

    DEFAULT_AUTO_MODERATION = {
        "ai_review_enabled": True,
        "ai_confidence_threshold": 0.7,
        "auto_reject_threshold": 0.95,
        "new_user_always_review": True,
        "reported_threshold": 3,
        "link_in_post_trigger_review": True
    }

    async def get_community_rules(self) -> Dict[str, Any]:
        result = await self.db.execute(
            select(OpsConfig).where(OpsConfig.key == "community.rules")
        )
        config = result.scalar_one_or_none()

        if config and config.value:
            import json
            return json.loads(config.value)
        return self.DEFAULT_COMMUNITY_RULES.copy()

    async def update_community_rules(
        self,
        rules: Dict[str, Any],
        updated_by: int = 0
    ) -> bool:
        import json

        result = await self.db.execute(
            select(OpsConfig).where(OpsConfig.key == "community.rules")
        )
        config = result.scalar_one_or_none()

        if config:
            config.value = json.dumps(rules)
            config.updated_by = updated_by
        else:
            config = OpsConfig(
                key="community.rules",
                value=json.dumps(rules),
                updated_by=updated_by,
                description="社区规则配置"
            )
            self.db.add(config)

        await self.db.commit()
        return True

    async def get_auto_moderation_config(self) -> Dict[str, Any]:
        result = await self.db.execute(
            select(OpsConfig).where(OpsConfig.key == "auto_moderation.config")
        )
        config = result.scalar_one_or_none()

        if config and config.value:
            import json
            return json.loads(config.value)
        return self.DEFAULT_AUTO_MODERATION.copy()

    async def update_auto_moderation_config(
        self,
        config_data: Dict[str, Any],
        updated_by: int = 0
    ) -> bool:
        import json

        result = await self.db.execute(
            select(OpsConfig).where(OpsConfig.key == "auto_moderation.config")
        )
        config = result.scalar_one_or_none()

        if config:
            config.value = json.dumps(config_data)
            config.updated_by = updated_by
        else:
            config = OpsConfig(
                key="auto_moderation.config",
                value=json.dumps(config_data),
                updated_by=updated_by,
                description="自动审核配置"
            )
            self.db.add(config)

        await self.db.commit()
        return True

    async def get_sensitive_words(self, category: str = None) -> List[Dict[str, Any]]:
        filter_instance = SensitiveWordFilter()
        words = filter_instance.get_all_words()

        if category:
            return [{"word": w, "category": "general"} for w in words]
        return [{"word": w, "category": "general"} for w in words]

    async def add_sensitive_words(
        self,
        words: List[str],
        category: str = "general"
    ) -> int:
        filter_instance = SensitiveWordFilter()
        added = filter_instance.add_words(words)
        return added

    async def remove_sensitive_words(self, words: List[str]) -> int:
        filter_instance = SensitiveWordFilter()
        removed = filter_instance.remove_words(words)
        return removed
