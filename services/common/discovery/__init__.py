"""Consul 服务注册与发现

功能：
- 服务注册
- 服务发现
- 健康检查
- 动态端点更新
"""

import asyncio
import logging
import os
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass
import json

import httpx

logger = logging.getLogger(__name__)


@dataclass
class ServiceInstance:
    service_id: str
    service_name: str
    host: str
    port: int
    metadata: Dict[str, str]
    health_check: str
    tags: List[str]

    @property
    def address(self) -> str:
        return f"{self.host}:{self.port}"

    @property
    def url(self) -> str:
        return f"http://{self.address}"


class ConsulServiceRegistry:
    def __init__(
        self,
        consul_url: Optional[str] = None,
        token: Optional[str] = None,
        datacenter: Optional[str] = None,
    ):
        self.consul_url = consul_url or os.getenv("CONSUL_URL", "http://localhost:8500")
        self.token = token or os.getenv("CONSUL_TOKEN", "")
        self.datacenter = datacenter or os.getenv("CONSUL_DATACENTER", "dc1")
        self._client: Optional[httpx.AsyncClient] = None
        self._registered_instances: Dict[str, str] = {}

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.consul_url,
                headers={"X-Consul-Token": self.token} if self.token else {},
                timeout=30.0,
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def register_service(
        self,
        service_name: str,
        service_id: str,
        host: str,
        port: int,
        metadata: Optional[Dict[str, str]] = None,
        tags: Optional[List[str]] = None,
        health_check_url: Optional[str] = None,
        interval: str = "10s",
    ) -> bool:
        """注册服务到 Consul"""
        client = await self._get_client()

        registration = {
            "ID": service_id,
            "Name": service_name,
            "Address": host,
            "Port": port,
            "Meta": metadata or {},
            "Tags": tags or [],
        }

        if health_check_url:
            registration["Check"] = {
                "HTTP": health_check_url,
                "Interval": interval,
                "Timeout": "5s",
                "DeregisterCriticalServiceAfter": "30s",
            }

        try:
            response = await client.put(
                "/v1/agent/service/register",
                json=registration,
            )
            if response.status_code == 200:
                self._registered_instances[service_id] = service_name
                logger.info(f"Service registered: {service_name}/{service_id}")
                return True
            else:
                logger.error(f"Failed to register service: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error registering service: {e}")
            return False

    async def deregister_service(self, service_id: str) -> bool:
        """从 Consul 注销服务"""
        client = await self._get_client()

        try:
            response = await client.put(f"/v1/agent/service/deregister/{service_id}")
            if response.status_code == 200:
                if service_id in self._registered_instances:
                    del self._registered_instances[service_id]
                logger.info(f"Service deregistered: {service_id}")
                return True
            else:
                logger.error(f"Failed to deregister service: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error deregistering service: {e}")
            return False

    async def discover_service(
        self,
        service_name: str,
        passing_only: bool = True,
        tag: Optional[str] = None,
    ) -> List[ServiceInstance]:
        """发现服务实例"""
        client = await self._get_client()

        params = {"passing": "true"} if passing_only else {}
        if tag:
            params["tag"] = tag

        try:
            response = await client.get(
                f"/v1/health/service/{service_name}",
                params=params,
            )
            if response.status_code == 200:
                services = response.json()
                instances = []
                for svc in services:
                    for node in svc.get("Service", {}).get("Meta", {}).keys():
                        pass
                    service_info = svc.get("Service", {})
                    instance = ServiceInstance(
                        service_id=service_info.get("ID", ""),
                        service_name=service_info.get("Service", ""),
                        host=service_info.get("Address", ""),
                        port=service_info.get("Port", 0),
                        metadata=service_info.get("Meta", {}),
                        health_check=service_info.get("Check", {}).get("HTTP", ""),
                        tags=service_info.get("Tags", []),
                    )
                    instances.append(instance)
                logger.info(f"Discovered {len(instances)} instances of {service_name}")
                return instances
            else:
                logger.warning(f"Failed to discover service: {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error discovering service: {e}")
            return []

    async def get_service_address(
        self,
        service_name: str,
        tag: Optional[str] = None,
    ) -> Optional[str]:
        """获取服务地址（单个）"""
        instances = await self.discover_service(service_name, tag=tag)
        if instances:
            return instances[0].address
        return None

    async def watch_service(
        self,
        service_name: str,
        callback: Callable[[List[ServiceInstance]], None],
        interval: int = 30,
    ):
        """监控服务变化"""
        while True:
            try:
                instances = await self.discover_service(service_name)
                await callback(instances)
            except Exception as e:
                logger.error(f"Error watching service: {e}")
            await asyncio.sleep(interval)


class ServiceDiscovery:
    """服务发现客户端 - 用于替换硬编码地址"""

    def __init__(self, registry: ConsulServiceRegistry):
        self.registry = registry
        self._cache: Dict[str, List[ServiceInstance]] = {}
        self._cache_ttl: Dict[str, float] = {}
        self._cache_duration = 30.0

    async def get_endpoint(
        self,
        service_name: str,
        use_cache: bool = True,
        tag: Optional[str] = None,
    ) -> Optional[str]:
        """获取服务端点地址"""
        import time

        cache_key = f"{service_name}:{tag or ''}"

        if use_cache and cache_key in self._cache:
            if time.time() - self._cache_ttl.get(cache_key, 0) < self._cache_duration:
                instances = self._cache[cache_key]
                if instances:
                    return instances[0].address

        instances = await self.registry.discover_service(service_name, tag=tag)
        if instances:
            self._cache[cache_key] = instances
            self._cache_ttl[cache_key] = time.time()
            return instances[0].address

        return None

    async def get_all_endpoints(
        self,
        service_name: str,
        use_cache: bool = True,
    ) -> List[str]:
        """获取所有服务端点地址"""
        import time

        cache_key = f"{service_name}:all"

        if use_cache and cache_key in self._cache:
            if time.time() - self._cache_ttl.get(cache_key, 0) < self._cache_duration:
                return [inst.address for inst in self._cache[cache_key]]

        instances = await self.registry.discover_service(service_name)
        if instances:
            self._cache[cache_key] = instances
            self._cache_ttl[cache_key] = time.time()
            return [inst.address for inst in instances]

        return []

    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()
        self._cache_ttl.clear()


_registry: Optional[ConsulServiceRegistry] = None
_discovery: Optional[ServiceDiscovery] = None


def get_consul_registry(
    consul_url: Optional[str] = None,
    token: Optional[str] = None,
) -> ConsulServiceRegistry:
    global _registry
    if _registry is None:
        _registry = ConsulServiceRegistry(consul_url, token)
    return _registry


def get_service_discovery() -> ServiceDiscovery:
    global _discovery
    if _discovery is None:
        _discovery = ServiceDiscovery(get_consul_registry())
    return _discovery
