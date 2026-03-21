"""AI配置管理器服务

提供AI配置的加载、缓存、轮换和健康检查功能。
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.system import AIModelConfig
from ...utils.secret_crypto import decrypt_secret

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class RotationStrategy(Enum):
    """配置轮换策略"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"
    LEAST_USED = "least_used"
    PRIORITY = "priority"


class HealthStatus(Enum):
    """健康状态"""
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class AIConfig:
    """AI配置数据类"""
    id: int
    name: str
    provider: str
    model_id: str
    api_key: str
    base_url: str | None
    enabled: bool
    weight: int
    priority: int
    is_primary: bool
    max_tokens: int | None
    temperature: float | None
    call_count: int
    error_count: int
    last_used_at: datetime | None
    health_status: str
    last_health_check: datetime | None
    health_check_message: str | None

    @classmethod
    def from_model(cls, model: AIModelConfig) -> "AIConfig":
        """从数据库模型创建"""
        api_key = decrypt_secret(str(model.api_key or ""))
        return cls(
            id=int(model.id),
            name=str(model.name),
            provider=str(model.provider),
            model_id=str(model.model_id),
            api_key=api_key,
            base_url=model.base_url,
            enabled=bool(model.enabled),
            weight=int(model.weight),
            priority=int(model.priority),
            is_primary=bool(model.is_primary),
            max_tokens=int(model.max_tokens) if model.max_tokens else None,
            temperature=float(model.temperature) if model.temperature else None,
            call_count=int(model.call_count),
            error_count=int(model.error_count),
            last_used_at=model.last_used_at,
            health_status=str(model.health_status),
            last_health_check=model.last_health_check,
            health_check_message=model.health_check_message,
        )


@dataclass
class ConfigCache:
    """配置缓存"""
    configs: list[AIConfig] = field(default_factory=list)
    last_refresh: float = 0.0
    ttl: float = 300.0  # 5分钟TTL

    def is_expired(self) -> bool:
        """检查缓存是否过期"""
        return time.time() - self.last_refresh > self.ttl

    def get_enabled_configs(self, provider: str | None = None) -> list[AIConfig]:
        """获取启用的配置"""
        configs = [c for c in self.configs if c.enabled]
        if provider:
            configs = [c for c in configs if c.provider == provider]
        return configs


class AIConfigManager:
    """AI配置管理器

    功能:
    - 从数据库加载启用的配置（带缓存）
    - Key轮换策略（轮询、权重、最少使用、优先级）
    - 故障转移（一个Key失败自动切换）
    - 使用统计记录
    - 健康检查
    """

    def __init__(self, cache_ttl: float = 300.0):
        self._cache = ConfigCache(ttl=cache_ttl)
        self._round_robin_index: dict[str, int] = {}
        self._lock = asyncio.Lock()

    async def refresh(self, db: AsyncSession, force: bool = False) -> None:
        """刷新配置缓存

        Args:
            db: 数据库会话
            force: 是否强制刷新
        """
        async with self._lock:
            if not force and not self._cache.is_expired():
                return

            try:
                result = await db.execute(
                    select(AIModelConfig)
                    .where(AIModelConfig.enabled == True)
                    .order_by(
                        AIModelConfig.priority.desc(),
                        AIModelConfig.weight.desc(),
                        AIModelConfig.created_at
                    )
                )
                models = result.scalars().all()
                self._cache.configs = [AIConfig.from_model(m) for m in models]
                self._cache.last_refresh = time.time()
                logger.info("刷新AI配置缓存，共 %d 个配置", len(self._cache.configs))
            except Exception as e:
                logger.error("刷新AI配置缓存失败: %s", e)

    async def get_config(
        self,
        db: AsyncSession,
        provider: str | None = None,
        strategy: RotationStrategy = RotationStrategy.WEIGHTED,
    ) -> AIConfig | None:
        """获取下一个配置

        Args:
            db: 数据库会话
            provider: 提供商过滤（可选）
            strategy: 轮换策略

        Returns:
            AI配置，如果没有可用配置则返回None
        """
        # 确保缓存有效
        await self.refresh(db)

        configs = self._cache.get_enabled_configs(provider)
        if not configs:
            logger.warning("没有可用的AI配置 (provider=%s)", provider)
            return None

        # 过滤掉不健康的配置，但保留降级状态的
        healthy_configs = [
            c for c in configs
            if c.health_status in (HealthStatus.HEALTHY.value, HealthStatus.DEGRADED.value, HealthStatus.UNKNOWN.value)
        ]

        if not healthy_configs:
            logger.warning("所有AI配置都不健康，尝试使用所有配置")
            healthy_configs = configs

        # 根据策略选择配置
        selected = self._select_by_strategy(healthy_configs, strategy)

        if selected:
            logger.debug("选择配置: %s (provider=%s, strategy=%s)",
                        selected.name, selected.provider, strategy.value)

        return selected

    def _select_by_strategy(
        self,
        configs: list[AIConfig],
        strategy: RotationStrategy
    ) -> AIConfig | None:
        """根据策略选择配置"""
        if not configs:
            return None

        if len(configs) == 1:
            return configs[0]

        if strategy == RotationStrategy.ROUND_ROBIN:
            return self._select_round_robin(configs)
        elif strategy == RotationStrategy.WEIGHTED:
            return self._select_weighted(configs)
        elif strategy == RotationStrategy.LEAST_USED:
            return self._select_least_used(configs)
        elif strategy == RotationStrategy.PRIORITY:
            return self._select_priority(configs)
        else:
            return configs[0]

    def _select_round_robin(self, configs: list[AIConfig]) -> AIConfig:
        """轮询选择"""
        provider = configs[0].provider if configs else ""
        key = provider

        current_idx = self._round_robin_index.get(key, 0)
        if current_idx >= len(configs):
            current_idx = 0

        selected = configs[current_idx]
        self._round_robin_index[key] = (current_idx + 1) % len(configs)
        return selected

    def _select_weighted(self, configs: list[AIConfig]) -> AIConfig:
        """权重选择"""
        import random

        total_weight = sum(c.weight for c in configs)
        if total_weight <= 0:
            return configs[0]

        r = random.uniform(0, total_weight)
        current = 0
        for config in configs:
            current += config.weight
            if r <= current:
                return config

        return configs[-1]

    def _select_least_used(self, configs: list[AIConfig]) -> AIConfig:
        """最少使用选择"""
        return min(configs, key=lambda c: c.call_count)

    def _select_priority(self, configs: list[AIConfig]) -> AIConfig:
        """优先级选择（优先使用is_primary，其次按priority排序）"""
        primary_configs = [c for c in configs if c.is_primary]
        if primary_configs:
            return primary_configs[0]
        return max(configs, key=lambda c: c.priority)

    async def record_usage(
        self,
        config_id: int,
        success: bool,
        db: AsyncSession,
        error_message: str | None = None,
    ) -> None:
        """记录使用情况

        Args:
            config_id: 配置ID
            success: 是否成功
            db: 数据库会话
            error_message: 错误信息（可选）
        """
        try:
            now = datetime.utcnow()

            if success:
                await db.execute(
                    update(AIModelConfig)
                    .where(AIModelConfig.id == config_id)
                    .values(
                        call_count=AIModelConfig.call_count + 1,
                        last_used_at=now,
                    )
                )
            else:
                await db.execute(
                    update(AIModelConfig)
                    .where(AIModelConfig.id == config_id)
                    .values(
                        call_count=AIModelConfig.call_count + 1,
                        error_count=AIModelConfig.error_count + 1,
                        last_used_at=now,
                        health_status=HealthStatus.DEGRADED.value,
                        health_check_message=error_message or "调用失败",
                    )
                )

            await db.commit()
            logger.debug("记录配置使用: id=%d, success=%s", config_id, success)
        except Exception as e:
            logger.error("记录配置使用失败: %s", e)

    async def perform_health_check(
        self,
        config: AIConfig,
        db: AsyncSession,
    ) -> bool:
        """执行健康检查

        Args:
            config: AI配置
            db: 数据库会话

        Returns:
            是否健康
        """
        import httpx

        is_healthy = False
        message = ""

        try:
            # 根据提供商确定健康检查端点
            if config.provider == "openai":
                base_url = config.base_url or "https://api.openai.com"
                check_url = f"{base_url.rstrip('/')}/models"
            elif config.provider == "deepseek":
                base_url = config.base_url or "https://api.deepseek.com"
                check_url = f"{base_url.rstrip('/')}/models"
            elif config.provider == "qwen":
                base_url = config.base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
                check_url = f"{base_url.rstrip('/')}/models"
            elif config.provider == "zhipu":
                base_url = config.base_url or "https://open.bigmodel.cn/api/paas/v4"
                check_url = f"{base_url.rstrip('/')}/models"
            else:
                # 通用检查
                base_url = config.base_url or "https://api.openai.com"
                check_url = f"{base_url.rstrip('/')}/models"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    check_url,
                    headers={"Authorization": f"Bearer {config.api_key}"}
                )

                if response.status_code == 200:
                    is_healthy = True
                    message = "健康检查通过"
                elif response.status_code == 401:
                    is_healthy = False
                    message = "API密钥无效"
                else:
                    is_healthy = False
                    message = f"HTTP错误: {response.status_code}"

        except httpx.TimeoutException:
            is_healthy = False
            message = "连接超时"
        except Exception as e:
            is_healthy = False
            message = f"检查失败: {str(e)[:100]}"

        # 更新健康状态
        try:
            now = datetime.utcnow()
            health_status = HealthStatus.HEALTHY.value if is_healthy else HealthStatus.UNHEALTHY.value

            await db.execute(
                update(AIModelConfig)
                .where(AIModelConfig.id == config.id)
                .values(
                    health_status=health_status,
                    last_health_check=now,
                    health_check_message=message,
                )
            )
            await db.commit()
        except Exception as e:
            logger.error("更新健康状态失败: %s", e)

        return is_healthy

    async def get_stats(
        self,
        db: AsyncSession,
        provider: str | None = None,
    ) -> dict:
        """获取配置统计信息

        Args:
            db: 数据库会话
            provider: 提供商过滤（可选）

        Returns:
            统计信息字典
        """
        await self.refresh(db)

        configs = self._cache.configs
        if provider:
            configs = [c for c in configs if c.provider == provider]

        if not configs:
            return {
                "total": 0,
                "enabled": 0,
                "healthy": 0,
                "degraded": 0,
                "unhealthy": 0,
                "unknown": 0,
                "total_calls": 0,
                "total_errors": 0,
            }

        enabled = [c for c in configs if c.enabled]
        healthy = [c for c in configs if c.health_status == HealthStatus.HEALTHY.value]
        degraded = [c for c in configs if c.health_status == HealthStatus.DEGRADED.value]
        unhealthy = [c for c in configs if c.health_status == HealthStatus.UNHEALTHY.value]
        unknown = [c for c in configs if c.health_status == HealthStatus.UNKNOWN.value]

        return {
            "total": len(configs),
            "enabled": len(enabled),
            "healthy": len(healthy),
            "degraded": len(degraded),
            "unhealthy": len(unhealthy),
            "unknown": len(unknown),
            "total_calls": sum(c.call_count for c in configs),
            "total_errors": sum(c.error_count for c in configs),
        }

    def clear_cache(self) -> None:
        """清除缓存"""
        self._cache.configs = []
        self._cache.last_refresh = 0
        self._round_robin_index.clear()


# 全局配置管理器实例
_config_manager: AIConfigManager | None = None


def get_config_manager() -> AIConfigManager:
    """获取配置管理器实例（懒加载）"""
    global _config_manager
    if _config_manager is None:
        _config_manager = AIConfigManager()
    return _config_manager
