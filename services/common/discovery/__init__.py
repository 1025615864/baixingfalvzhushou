"""Consul 服务注册与发现"""
from .consul_register import (
    ConsulServiceRegistration,
    get_registration,
)
from .consul_discovery import (
    ConsulServiceDiscovery,
    get_discovery,
    ServiceInstance,
)

__all__ = [
    "ConsulServiceRegistration",
    "get_registration",
    "ConsulServiceDiscovery",
    "get_discovery",
    "ServiceInstance",
]
