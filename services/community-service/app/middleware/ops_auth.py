"""运营权限中间件"""
import logging
from typing import List, Optional
from fastapi import Request, HTTPException, Depends
from starlette.status import HTTP_403_FORBIDDEN

from app.models.ops_models import OpsRole, VALID_OPS_ROLES

logger = logging.getLogger(__name__)


class OpsAuthMiddleware:
    def __init__(self, user_client=None):
        self.user_client = user_client

    async def get_current_ops_user(self, request: Request) -> dict:
        from app.middleware.auth import get_current_user
        user = await get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="未登录")
        return user

    async def check_ops_role(self, request: Request, required_actions: List[str]) -> dict:
        user = await self.get_current_ops_user(request)

        if user.get("role") == "admin":
            return user

        from app.database import AsyncSessionLocal
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(OpsRole).where(
                    OpsRole.user_id == user["id"],
                    OpsRole.is_active == True
                )
            )
            ops_role = result.scalar_one_or_none()

            if not ops_role:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN,
                    detail="您没有运营权限"
                )

            role_permissions = VALID_OPS_ROLES.get(ops_role.role, [])

            if "*" not in role_permissions:
                for action in required_actions:
                    if action not in role_permissions:
                        raise HTTPException(
                            status_code=HTTP_403_FORBIDDEN,
                            detail=f"您没有【{action}】权限，需要【{ops_role.role}】角色"
                        )

            user["ops_role"] = ops_role.role
            return user


def require_ops_actions(*actions):
    async def dependency(request: Request):
        middleware = OpsAuthMiddleware()
        return await middleware.check_ops_role(request, list(actions))
    return dependency


def require_ops_role(*roles):
    async def dependency(request: Request):
        middleware = OpsAuthMiddleware()
        user = await middleware.get_current_ops_user(request)

        if user.get("role") == "admin":
            return user

        from app.database import AsyncSessionLocal
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(OpsRole).where(
                    OpsRole.user_id == user["id"],
                    OpsRole.is_active == True
                )
            )
            ops_role = result.scalar_one_or_none()

            if not ops_role or ops_role.role not in roles:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN,
                    detail=f"需要【{'或'.join(roles)}】角色"
                )

            user["ops_role"] = ops_role.role
            return user

    return dependency


async def log_audit(
    request: Request,
    action: str,
    target_type: str,
    target_id: int = None,
    detail: str = None
):
    from app.database import AsyncSessionLocal
    from app.models.ops_models import OpsAuditLog

    user = request.state.__dict__.get("user") if hasattr(request, "state") else None

    async with AsyncSessionLocal() as session:
        log = OpsAuditLog(
            operator_id=user.get("id") if user else 0,
            operator_role=user.get("ops_role") if user else None,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        session.add(log)
        await session.commit()


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
