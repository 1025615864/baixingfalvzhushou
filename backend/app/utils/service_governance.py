"""服务治理框架

提供服务注册与发现、负载均衡、健康检查、限流配置等服务治理能力。

功能模块:
    - 服务注册与发现: 管理服务实例的注册和发现
    - 负载均衡策略: 支持轮询、加权、随机、最少连接等策略
    - 服务健康检查: 定期检查服务实例的健康状态
    - 限流配置: 基于令牌桶和滑动窗口的限流策略
    - 熔断器集成: 与circuit_breaker模块集成提供服务保护

使用示例:
    ```python
    from app.utils.service_governance import (
        ServiceRegistry,
        LoadBalancer,
        HealthChecker,
        RateLimiterConfig,
        get_service_registry,
    )

    # 注册服务
    registry = get_service_registry()
    await registry.register("payment_service", "http://localhost:8001")

    # 获取服务实例
    instance = await registry.discover("payment_service")

    # 使用负载均衡
    lb = LoadBalancer(strategy="round_robin")
    instance = lb.select(instances)
    ```
"""
from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, Union
from datetime import datetime, timezone

logger = logging.getLogger("service_governance")


class LoadBalanceStrategy(str, Enum):
    """负载均衡策略"""
    ROUND_ROBIN = "round_robin"      # 轮询
    WEIGHTED = "weighted"             # 加权轮询
    RANDOM = "random"                 # 随机
    LEAST_CONNECTIONS = "least_connections"  # 最少连接
    CONSISTENT_HASH = "consistent_hash"  # 一致性哈希


class HealthStatus(str, Enum):
    """健康状态"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"  # 降级状态
    UNKNOWN = "unknown"


@dataclass
class ServiceInstance:
    """服务实例"""
    name: str
    address: str
    port: int
    weight: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    health_status: HealthStatus = HealthStatus.UNKNOWN
    last_health_check: Optional[float] = None
    consecutive_failures: int = 0
    active_connections: int = 0
    
    @property
    def url(self) -> str:
        """获取服务URL"""
        return f"{self.address}:{self.port}"
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "address": self.address,
            "port": self.port,
            "weight": self.weight,
            "metadata": self.metadata,
            "health_status": self.health_status.value,
            "last_health_check": self.last_health_check,
            "consecutive_failures": self.consecutive_failures,
            "active_connections": self.active_connections,
        }


@dataclass
class HealthCheckConfig:
    """健康检查配置"""
    interval_seconds: float = 30.0       # 检查间隔
    timeout_seconds: float = 5.0         # 超时时间
    unhealthy_threshold: int = 3         # 不健康阈值
    healthy_threshold: int = 2           # 健康阈值
    
    # 检查类型
    check_type: str = "http"             # http, tcp, grpc
    check_path: str = "/health"          # HTTP检查路径
    expected_status: int = 200           # 期望的HTTP状态码


@dataclass
class RateLimiterConfig:
    """限流配置"""
    requests_per_second: float = 100.0   # 每秒请求数
    burst_size: int = 200                # 突发流量大小
    enabled: bool = True                 # 是否启用
    
    # 滑动窗口配置
    window_size_seconds: float = 1.0     # 窗口大小
    window_limit: int = 100              # 窗口内最大请求数


@dataclass
class ServiceConfig:
    """服务配置"""
    name: str
    instances: list[ServiceInstance] = field(default_factory=list)
    load_balance_strategy: LoadBalanceStrategy = LoadBalanceStrategy.ROUND_ROBIN
    health_check: HealthCheckConfig = field(default_factory=HealthCheckConfig)
    rate_limiter: RateLimiterConfig = field(default_factory=RateLimiterConfig)
    
    # 熔断器配置（可选）
    circuit_breaker_enabled: bool = True
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_timeout_seconds: float = 30.0
    
    # 超时配置
    request_timeout_seconds: float = 30.0
    connect_timeout_seconds: float = 5.0
    
    # 重试配置
    retry_enabled: bool = True
    retry_max_attempts: int = 3
    retry_backoff_factor: float = 0.5


class LoadBalancer:
    """负载均衡器
    
    支持多种负载均衡策略:
    - round_robin: 轮询
    - weighted: 加权轮询
    - random: 随机选择
    - least_connections: 最少连接
    - consistent_hash: 一致性哈希
    """
    
    def __init__(
        self,
        strategy: Union[LoadBalanceStrategy, str] = LoadBalanceStrategy.ROUND_ROBIN,
    ):
        self.strategy = LoadBalanceStrategy(strategy) if isinstance(strategy, str) else strategy
        self._current_index: dict[str, int] = {}
        self._hash_ring: dict[str, list[tuple[int, ServiceInstance]]] = {}
    
    def select(
        self,
        instances: list[ServiceInstance],
        service_name: str = "default",
        hash_key: Optional[str] = None,
    ) -> Optional[ServiceInstance]:
        """选择一个服务实例
        
        Args:
            instances: 可用的服务实例列表
            service_name: 服务名称（用于维护轮询状态）
            hash_key: 一致性哈希的键值
            
        Returns:
            选中的服务实例，如果没有可用实例则返回None
        """
        if not instances:
            return None
        
        # 过滤健康的实例
        healthy_instances = [
            inst for inst in instances
            if inst.health_status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)
        ]
        
        if not healthy_instances:
            logger.warning(f"No healthy instances available for {service_name}")
            return None
        
        if self.strategy == LoadBalanceStrategy.ROUND_ROBIN:
            return self._round_robin(healthy_instances, service_name)
        elif self.strategy == LoadBalanceStrategy.WEIGHTED:
            return self._weighted(healthy_instances)
        elif self.strategy == LoadBalanceStrategy.RANDOM:
            return self._random(healthy_instances)
        elif self.strategy == LoadBalanceStrategy.LEAST_CONNECTIONS:
            return self._least_connections(healthy_instances)
        elif self.strategy == LoadBalanceStrategy.CONSISTENT_HASH:
            return self._consistent_hash(healthy_instances, service_name, hash_key)
        else:
            return self._round_robin(healthy_instances, service_name)
    
    def _round_robin(
        self,
        instances: list[ServiceInstance],
        service_name: str,
    ) -> ServiceInstance:
        """轮询策略"""
        if service_name not in self._current_index:
            self._current_index[service_name] = 0
        
        index = self._current_index[service_name] % len(instances)
        self._current_index[service_name] += 1
        return instances[index]
    
    def _weighted(self, instances: list[ServiceInstance]) -> ServiceInstance:
        """加权轮询策略"""
        total_weight = sum(inst.weight for inst in instances)
        if total_weight <= 0:
            return random.choice(instances)
        
        r = random.randint(1, total_weight)
        current_weight = 0
        for inst in instances:
            current_weight += inst.weight
            if r <= current_weight:
                return inst
        
        return instances[-1]
    
    def _random(self, instances: list[ServiceInstance]) -> ServiceInstance:
        """随机策略"""
        return random.choice(instances)
    
    def _least_connections(self, instances: list[ServiceInstance]) -> ServiceInstance:
        """最少连接策略"""
        return min(instances, key=lambda x: x.active_connections)
    
    def _consistent_hash(
        self,
        instances: list[ServiceInstance],
        service_name: str,
        hash_key: Optional[str] = None,
    ) -> ServiceInstance:
        """一致性哈希策略"""
        if not hash_key:
            hash_key = str(time.time())
        
        # 简化的一致性哈希实现
        hash_value = hash(hash_key)
        
        # 构建哈希环（如果需要）
        ring_key = f"{service_name}:{len(instances)}"
        if ring_key not in self._hash_ring:
            self._hash_ring[ring_key] = []
            for i, inst in enumerate(instances):
                # 每个实例在环上有多个虚拟节点
                for j in range(inst.weight * 10):
                    node_hash = hash(f"{inst.address}:{inst.port}:{j}")
                    self._hash_ring[ring_key].append((node_hash, inst))
            self._hash_ring[ring_key].sort(key=lambda x: x[0])
        
        ring = self._hash_ring[ring_key]
        if not ring:
            return instances[0]
        
        # 查找顺时针最近的节点
        for node_hash, inst in ring:
            if hash_value <= node_hash:
                return inst
        
        return ring[0][1]


class HealthChecker:
    """健康检查器
    
    定期检查服务实例的健康状态
    """
    
    def __init__(self, config: Optional[HealthCheckConfig] = None):
        self.config = config or HealthCheckConfig()
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def check_http(
        self,
        instance: ServiceInstance,
    ) -> bool:
        """HTTP健康检查"""
        import aiohttp
        
        url = f"http://{instance.url}{self.config.check_path}"
        try:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    return response.status == self.config.expected_status
        except Exception as e:
            logger.debug(f"Health check failed for {instance.url}: {e}")
            return False
    
    async def check_tcp(
        self,
        instance: ServiceInstance,
    ) -> bool:
        """TCP健康检查"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(instance.address, instance.port),
                timeout=self.config.timeout_seconds,
            )
            writer.close()
            await writer.wait_closed()
            return True
        except Exception as e:
            logger.debug(f"TCP health check failed for {instance.url}: {e}")
            return False
    
    async def check(
        self,
        instance: ServiceInstance,
    ) -> HealthStatus:
        """执行健康检查"""
        try:
            if self.config.check_type == "http":
                is_healthy = await self.check_http(instance)
            elif self.config.check_type == "tcp":
                is_healthy = await self.check_tcp(instance)
            else:
                is_healthy = await self.check_http(instance)
            
            instance.last_health_check = time.time()
            
            if is_healthy:
                instance.consecutive_failures = 0
                return HealthStatus.HEALTHY
            else:
                instance.consecutive_failures += 1
                
                if instance.consecutive_failures >= self.config.unhealthy_threshold:
                    return HealthStatus.UNHEALTHY
                elif instance.consecutive_failures >= self.config.healthy_threshold:
                    return HealthStatus.DEGRADED
                return HealthStatus.HEALTHY
                
        except Exception as e:
            logger.error(f"Health check error for {instance.url}: {e}")
            instance.consecutive_failures += 1
            return HealthStatus.UNHEALTHY


class ServiceRegistry:
    """服务注册表
    
    管理服务的注册、发现和健康检查
    """
    
    def __init__(self):
        self._services: dict[str, ServiceConfig] = {}
        self._instances: dict[str, list[ServiceInstance]] = {}
        self._lock = asyncio.Lock()
        self._health_checker = HealthChecker()
        self._load_balancers: dict[str, LoadBalancer] = {}
    
    async def register(
        self,
        service_name: str,
        address: str,
        port: int,
        weight: int = 1,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ServiceInstance:
        """注册服务实例
        
        Args:
            service_name: 服务名称
            address: 服务地址
            port: 服务端口
            weight: 权重
            metadata: 元数据
            
        Returns:
            注册的服务实例
        """
        async with self._lock:
            instance = ServiceInstance(
                name=service_name,
                address=address,
                port=port,
                weight=weight,
                metadata=metadata or {},
            )
            
            if service_name not in self._instances:
                self._instances[service_name] = []
            
            # 检查是否已存在相同实例
            for existing in self._instances[service_name]:
                if existing.address == address and existing.port == port:
                    # 更新现有实例
                    existing.weight = weight
                    existing.metadata = metadata or {}
                    return existing
            
            self._instances[service_name].append(instance)
            logger.info(f"Registered service instance: {service_name} at {address}:{port}")
            
            return instance
    
    async def deregister(
        self,
        service_name: str,
        address: str,
        port: int,
    ) -> bool:
        """注销服务实例"""
        async with self._lock:
            if service_name not in self._instances:
                return False
            
            for i, instance in enumerate(self._instances[service_name]):
                if instance.address == address and instance.port == port:
                    self._instances[service_name].pop(i)
                    logger.info(f"Deregistered service instance: {service_name} at {address}:{port}")
                    return True
            
            return False
    
    async def discover(
        self,
        service_name: str,
    ) -> list[ServiceInstance]:
        """发现服务实例
        
        Args:
            service_name: 服务名称
            
        Returns:
            服务实例列表
        """
        return self._instances.get(service_name, [])
    
    async def get_one(
        self,
        service_name: str,
        strategy: Optional[Union[LoadBalanceStrategy, str]] = None,
        hash_key: Optional[str] = None,
    ) -> Optional[ServiceInstance]:
        """获取一个服务实例（使用负载均衡）
        
        Args:
            service_name: 服务名称
            strategy: 负载均衡策略（可选，默认使用服务配置的策略）
            hash_key: 一致性哈希的键值
            
        Returns:
            选中的服务实例
        """
        instances = await self.discover(service_name)
        if not instances:
            return None
        
        # 获取或创建负载均衡器
        lb_key = f"{service_name}:{strategy or 'default'}"
        if lb_key not in self._load_balancers:
            config = self._services.get(service_name)
            lb_strategy = strategy or (config.load_balance_strategy if config else LoadBalanceStrategy.ROUND_ROBIN)
            self._load_balancers[lb_key] = LoadBalancer(strategy=lb_strategy)
        
        return self._load_balancers[lb_key].select(instances, service_name, hash_key)
    
    async def health_check_all(self) -> dict[str, list[dict[str, Any]]]:
        """对所有服务实例执行健康检查"""
        results: dict[str, list[dict[str, Any]]] = {}
        
        for service_name, instances in self._instances.items():
            results[service_name] = []
            for instance in instances:
                status = await self._health_checker.check(instance)
                results[service_name].append({
                    "instance": instance.to_dict(),
                    "status": status.value,
                })
        
        return results
    
    def get_all_services(self) -> dict[str, list[dict[str, Any]]]:
        """获取所有服务信息"""
        return {
            name: [inst.to_dict() for inst in instances]
            for name, instances in self._instances.items()
        }
    
    def configure_service(self, config: ServiceConfig) -> None:
        """配置服务"""
        self._services[config.name] = config
        self._instances[config.name] = config.instances
        # 清除负载均衡器缓存
        keys_to_remove = [k for k in self._load_balancers if k.startswith(f"{config.name}:")]
        for key in keys_to_remove:
            del self._load_balancers[key]


# 全局服务注册表实例
_service_registry: Optional[ServiceRegistry] = None


def get_service_registry() -> ServiceRegistry:
    """获取全局服务注册表实例"""
    global _service_registry
    if _service_registry is None:
        _service_registry = ServiceRegistry()
    return _service_registry


# 预定义的服务配置
DEFAULT_SERVICE_CONFIGS: dict[str, ServiceConfig] = {
    "payment_service": ServiceConfig(
        name="payment_service",
        load_balance_strategy=LoadBalanceStrategy.LEAST_CONNECTIONS,
        health_check=HealthCheckConfig(
            interval_seconds=15.0,
            check_path="/health",
        ),
        rate_limiter=RateLimiterConfig(
            requests_per_second=50.0,
            burst_size=100,
        ),
        circuit_breaker_enabled=True,
        circuit_breaker_failure_threshold=3,
        request_timeout_seconds=30.0,
    ),
    "ai_service": ServiceConfig(
        name="ai_service",
        load_balance_strategy=LoadBalanceStrategy.WEIGHTED,
        health_check=HealthCheckConfig(
            interval_seconds=30.0,
            check_path="/health",
        ),
        rate_limiter=RateLimiterConfig(
            requests_per_second=20.0,
            burst_size=50,
        ),
        circuit_breaker_enabled=True,
        circuit_breaker_failure_threshold=5,
        request_timeout_seconds=60.0,
    ),
    "notification_service": ServiceConfig(
        name="notification_service",
        load_balance_strategy=LoadBalanceStrategy.ROUND_ROBIN,
        health_check=HealthCheckConfig(
            interval_seconds=30.0,
            check_path="/health",
        ),
        rate_limiter=RateLimiterConfig(
            requests_per_second=100.0,
            burst_size=200,
        ),
        circuit_breaker_enabled=True,
        circuit_breaker_failure_threshold=5,
        request_timeout_seconds=10.0,
    ),
}


def get_service_config(service_name: str) -> Optional[ServiceConfig]:
    """获取预定义的服务配置"""
    return DEFAULT_SERVICE_CONFIGS.get(service_name)


async def initialize_default_services() -> None:
    """初始化默认服务配置"""
    registry = get_service_registry()
    for config in DEFAULT_SERVICE_CONFIGS.values():
        registry.configure_service(config)
    logger.info("Initialized default service configurations")