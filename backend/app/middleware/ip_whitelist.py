"""IP白名单中间件

实现IP白名单和黑名单机制。
"""
from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, Request, status

from ..utils.security import get_client_ip


class IPWhitelistMiddleware:
    """IP白名单中间件"""

    def __init__(
        self,
        whitelist: Optional[list[str]] = None,
        blacklist: Optional[list[str]] = None,
        admin_whitelist: Optional[list[str]] = None
    ) -> None:
        self.whitelist = set(whitelist or [])
        self.blacklist = set(blacklist or [])
        self.admin_whitelist = set(admin_whitelist or [])

    def is_whitelisted(self, ip: str) -> bool:
        """检查IP是否在白名单中"""
        if not self.whitelist:
            return True
        return ip in self.whitelist

    def is_blacklisted(self, ip: str) -> bool:
        """检查IP是否在黑名单中"""
        return ip in self.blacklist

    def is_admin_whitelisted(self, ip: str) -> bool:
        """检查IP是否在管理员白名单中"""
        if not self.admin_whitelist:
            return True
        return ip in self.admin_whitelist

    async def __call__(self, request: Request, call_next) -> None:
        """处理请求"""
        ip = get_client_ip(request)
        path = request.url.path

        # 检查黑名单
        if self.is_blacklisted(ip):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="IP地址已被封禁"
            )

        # 检查管理员路径
        if path.startswith("/admin"):
            if not self.is_admin_whitelisted(ip):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权访问管理员接口"
                )

        # 检查白名单
        if not self.is_whitelisted(ip):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="IP地址不在白名单中"
            )

        # 继续处理请求
        return await call_next(request)


# 默认IP白名单中间件（无限制）
ip_whitelist_middleware = IPWhitelistMiddleware()
