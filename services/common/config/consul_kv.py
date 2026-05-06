"""Consul KV 配置版本控制

支持：
- 配置版本管理
- 配置变更历史
- 配置回滚
- 配置审计
"""

import json
import logging
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ConfigChangeType(Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


@dataclass
class ConfigVersion:
    version: int
    key: str
    value: Any
    change_type: ConfigChangeType
    created_at: float
    created_by: str
    comment: str = ""


@dataclass
class ConfigEntry:
    key: str
    value: Any
    version: int
    modified_index: int
    created_index: int


class ConsulKVClient:
    """Consul KV 客户端 - 支持版本控制"""

    def __init__(
        self,
        url: str = "http://localhost:8500",
        token: str = "",
        prefix: str = "baixing/config",
    ):
        self.url = url
        self.token = token
        self.prefix = prefix.rstrip("/")
        self._session = None

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["X-Consul-Token"] = self.token
        return headers

    def _full_key(self, key: str) -> str:
        return f"{self.prefix}/{key.lstrip('/')}"

    async def get(
        self,
        key: str,
        recurse: bool = False,
    ) -> Optional[Any]:
        """获取配置值"""
        import httpx

        url = f"{self.url}/v1/kv/{self._full_key(key)}"
        params = {"recurse": recurse} if recurse else {}
        params["raw"] = True

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                    params=params,
                    timeout=10.0,
                )

                if response.status_code == 200:
                    if recurse:
                        result = []
                        for item in response.json():
                            config_key = item["Key"].replace(f"{self.prefix}/", "")
                            result.append(
                                ConfigEntry(
                                    key=config_key,
                                    value=item["Value"],
                                    version=item["Version"],
                                    modified_index=item["ModifyIndex"],
                                    created_index=item["CreateIndex"],
                                )
                            )
                        return result
                    else:
                        value = response.text
                        try:
                            return json.loads(value)
                        except json.JSONDecodeError:
                            return value
                elif response.status_code == 404:
                    return None
                else:
                    logger.error(f"Consul KV get failed: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Consul KV get error: {e}")
            return None

    async def put(
        self,
        key: str,
        value: Any,
        comment: str = "",
        created_by: str = "system",
    ) -> bool:
        """设置配置值"""
        import httpx

        if not isinstance(value, str):
            value = json.dumps(value)

        url = f"{self.url}/v1/kv/{self._full_key(key)}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    url,
                    content=value,
                    headers=self._get_headers(),
                    timeout=10.0,
                )

                if response.status_code == 200:
                    logger.info(f"Consul KV put: {key} by {created_by} - {comment}")
                    return True
                else:
                    logger.error(f"Consul KV put failed: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"Consul KV put error: {e}")
            return False

    async def delete(self, key: str, recurse: bool = False) -> bool:
        """删除配置"""
        import httpx

        url = f"{self.url}/v1/kv/{self._full_key(key)}"
        params = {"recurse": recurse} if recurse else {}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    url,
                    headers=self._get_headers(),
                    params=params,
                    timeout=10.0,
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Consul KV delete error: {e}")
            return False

    async def get_version_history(
        self,
        key: str,
        limit: int = 10,
    ) -> List[ConfigVersion]:
        """获取配置版本历史"""
        import httpx

        url = f"{self.url}/v1/kv/{self._full_key(key)}"
        params = {"versions": limit + 1}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                    params=params,
                    timeout=10.0,
                )

                if response.status_code == 200:
                    versions = []
                    for item in response.json():
                        version_num = item["Version"]
                        if version_num > 0:
                            versions.append(
                                ConfigVersion(
                                    version=version_num,
                                    key=key,
                                    value=item["Value"],
                                    change_type=ConfigChangeType.UPDATE,
                                    created_at=item["ModifyTime"],
                                    created_by="system",
                                )
                            )
                    return sorted(versions, key=lambda v: v.version, reverse=True)[:limit]
                return []
        except Exception as e:
            logger.error(f"Consul KV version history error: {e}")
            return []

    async def rollback(
        self,
        key: str,
        target_version: int,
        created_by: str = "system",
    ) -> bool:
        """回滚到指定版本"""
        import httpx

        url = f"{self.url}/v1/kv/{self._full_key(key)}"
        params = {"version": target_version}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                    params=params,
                    timeout=10.0,
                )

                if response.status_code == 200:
                    value = response.text
                    return await self.put(
                        key,
                        value,
                        comment=f"Rollback to version {target_version}",
                        created_by=created_by,
                    )
                return False
        except Exception as e:
            logger.error(f"Consul KV rollback error: {e}")
            return False

    async def list_keys(self, prefix: str = "") -> List[str]:
        """列出所有配置键"""
        import httpx

        url = f"{self.url}/v1/kv/{self.prefix}/{prefix}"
        params = {"keys": True}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                    params=params,
                    timeout=10.0,
                )

                if response.status_code == 200:
                    keys = response.json()
                    return [k.replace(f"{self.prefix}/", "") for k in keys]
                return []
        except Exception as e:
            logger.error(f"Consul KV list keys error: {e}")
            return []


class VersionedConfigManager:
    """带版本控制的配置管理器"""

    def __init__(self, consul_client: ConsulKVClient):
        self._consul = consul_client
        self._local_cache: Dict[str, Any] = {}

    async def get(self, key: str, use_cache: bool = True) -> Optional[Any]:
        """获取配置（优先本地缓存）"""
        if use_cache and key in self._local_cache:
            return self._local_cache[key]
        return await self._consul.get(key)

    async def set(
        self,
        key: str,
        value: Any,
        comment: str = "",
        created_by: str = "system",
        update_cache: bool = True,
    ) -> bool:
        """设置配置"""
        result = await self._consul.put(key, value, comment, created_by)
        if result and update_cache:
            self._local_cache[key] = value
        return result

    async def delete(self, key: str, recurse: bool = False) -> bool:
        """删除配置"""
        result = await self._consul.delete(key, recurse)
        if result:
            if recurse:
                self._local_cache = {
                    k: v for k, v in self._local_cache.items() if not k.startswith(key)
                }
            else:
                self._local_cache.pop(key, None)
        return result

    async def get_history(self, key: str, limit: int = 10) -> List[ConfigVersion]:
        """获取版本历史"""
        return await self._consul.get_version_history(key, limit)

    async def rollback(
        self,
        key: str,
        target_version: int,
        created_by: str = "system",
    ) -> bool:
        """回滚配置"""
        return await self._consul.rollback(key, target_version, created_by)

    async def sync_cache(self):
        """同步本地缓存"""
        keys = await self._consul.list_keys()
        for key in keys:
            value = await self._consul.get(key)
            if value is not None:
                self._local_cache[key] = value


_consul_client: Optional[ConsulKVClient] = None
_versioned_manager: Optional[VersionedConfigManager] = None


def get_consul_kv_client(
    url: Optional[str] = None,
    token: Optional[str] = None,
    prefix: str = "baixing/config",
) -> ConsulKVClient:
    """获取 Consul KV 客户端单例"""
    global _consul_client
    if _consul_client is None:
        _consul_client = ConsulKVClient(
            url=url or os.getenv("CONSUL_URL", "http://localhost:8500"),
            token=token or os.getenv("CONSUL_TOKEN", ""),
            prefix=prefix,
        )
    return _consul_client


def get_versioned_config_manager() -> VersionedConfigManager:
    """获取版本化配置管理器单例"""
    global _versioned_manager
    if _versioned_manager is None:
        _versioned_manager = VersionedConfigManager(get_consul_kv_client())
    return _versioned_manager
