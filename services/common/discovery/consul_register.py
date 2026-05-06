"""Consul 服务注册模块"""
import os
import logging
from typing import Optional

import consul

logger = logging.getLogger(__name__)


class ConsulServiceRegistration:
    """Consul 服务注册与注销（基于 python-consul 库）"""

    def __init__(
        self,
        service_name: str,
        service_port: int,
        service_host: str = "localhost",
        health_check_path: str = "/health/ready",
        health_check_interval: str = "10s",
    ):
        self.service_name = service_name
        self.service_port = service_port
        self.service_host = service_host
        self.health_check_path = health_check_path
        self.health_check_interval = health_check_interval

        consul_host = os.getenv("CONSUL_HOST", "localhost")
        consul_port = int(os.getenv("CONSUL_PORT", "8500"))

        self.consul = consul.Consul(host=consul_host, port=consul_port)
        self._registered = False

    def register(self) -> bool:
        """注册服务到 Consul"""
        if self._registered:
            logger.warning(f"Service {self.service_name} already registered")
            return True

        try:
            health_check_url = f"http://{self.service_host}:{self.service_port}{self.health_check_path}"

            self.consul.agent.service.register(
                self.service_name,
                port=self.service_port,
                address=self.service_host,
                check=consul.Check.http(
                    health_check_url,
                    interval=self.health_check_interval,
                    timeout="5s",
                    deregister="30s",
                ),
            )
            self._registered = True
            logger.info(f"Service {self.service_name} registered to Consul successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to register service {self.service_name} to Consul: {e}")
            return False

    def deregister(self) -> bool:
        """从 Consul 注销服务"""
        if not self._registered:
            logger.warning(f"Service {self.service_name} not registered, skipping deregister")
            return True

        try:
            self.consul.agent.service.deregister(self.service_name)
            self._registered = False
            logger.info(f"Service {self.service_name} deregistered from Consul successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to deregister service {self.service_name} from Consul: {e}")
            return False

    @property
    def is_registered(self) -> bool:
        return self._registered


_registration_instances: dict[str, ConsulServiceRegistration] = {}


def get_registration(
    service_name: str,
    service_port: int,
    service_host: str = "localhost",
) -> Optional[ConsulServiceRegistration]:
    """获取或创建服务注册实例"""
    enable_consul = os.getenv("CONSUL_SERVICE_ENABLED", "false").lower() == "true"

    if not enable_consul:
        logger.info("Consul service registration is disabled")
        return None

    key = f"{service_name}:{service_port}"
    if key not in _registration_instances:
        _registration_instances[key] = ConsulServiceRegistration(
            service_name=service_name,
            service_port=service_port,
            service_host=service_host,
            health_check_interval=os.getenv("CONSUL_HEALTH_CHECK_INTERVAL", "10s"),
        )
    return _registration_instances[key]
