"""管理员路由 - RBAC 角色权限管理与用户管理"""
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import AsyncSessionLocal
from ..models import User, UserProfile, AccountStatus
from ..models.rbac import (
    Role, Permission, UserAuditLog, user_roles, role_permissions,
    BUSINESS_DOMAINS, DOMAIN_ROLE_HIERARCHY,
)
from services.common.middleware.admin_auth import get_admin_user, AdminUser, require_domain_role

router = APIRouter(dependencies=[Depends(require_domain_role("global", roles=["super_admin", "admin"]))])


class DashboardResponse(BaseModel):
    total_users: int
    today_new: int
    active_users: int
    vip_users: int
    banned_users: int
    registration_trend: list[dict]


class UserListItem(BaseModel):
    id: int
    uid: str
    username: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    role: str
    status: str
    is_active: bool
    vip_expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class UserDetailResponse(BaseModel):
    id: int
    uid: str
    username: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    role: str
    status: str
    is_active: bool
    email_verified: bool
    phone_verified: bool
    vip_expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    roles: list[dict] = []

    class Config:
        from_attributes = True


class BanRequest(BaseModel):
    reason: str = ""


class RoleChangeRequest(BaseModel):
    role_code: str
    scope_id: Optional[int] = None


class RoleCreateRequest(BaseModel):
    name: str
    code: str
    domain: str = "global"
    description: Optional[str] = None


class RoleUpdateRequest(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None


class RolePermissionRequest(BaseModel):
    permission_ids: List[int]


class RoleResponse(BaseModel):
    id: int
    name: str
    code: str
    domain: str
    description: Optional[str]
    is_system: bool
    created_at: datetime
    permissions: list[dict] = []

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    operator_id: Optional[int]
    operator_name: Optional[str]
    action: str
    old_value: Optional[str]
    new_value: Optional[str]
    comment: Optional[str]
    extra_data: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    admin: AdminUser = Depends(get_admin_user),
    db: AsyncSession = Depends(AsyncSessionLocal),
):
    total_result = await db.execute(select(func.count(User.id)))
    total_users = total_result.scalar() or 0

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_result = await db.execute(
        select(func.count(User.id)).where(User.created_at >= today_start)
    )
    today_new = today_result.scalar() or 0

    active_result = await db.execute(
        select(func.count(User.id)).where(
            and_(User.is_active == True, User.status == AccountStatus.ACTIVE)
        )
    )
    active_users = active_result.scalar() or 0

    now = datetime.now(timezone.utc)
    vip_result = await db.execute(
        select(func.count(User.id)).where(
            and_(User.vip_expires_at != None, User.vip_expires_at > now)
        )
    )
    vip_users = vip_result.scalar() or 0

    banned_result = await db.execute(
        select(func.count(User.id)).where(User.status == AccountStatus.BANNED)
    )
    banned_users = banned_result.scalar() or 0

    trend = []
    for i in range(6, -1, -1):
        day = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=i)
        next_day = day + timedelta(days=1)
        count_result = await db.execute(
            select(func.count(User.id)).where(
                and_(User.created_at >= day, User.created_at < next_day)
            )
        )
        trend.append({"date": day.strftime("%Y-%m-%d"), "count": count_result.scalar() or 0})

    return DashboardResponse(
        total_users=total_users,
        today_new=today_new,
        active_users=active_users,
        vip_users=vip_users,
        banned_users=banned_users,
        registration_trend=trend,
    )


@router.get("/users", response_model=PaginatedResponse)
async def list_users(
    search: Optional[str] = Query(None, description="搜索用户名/手机/邮箱"),
    role: Optional[str] = Query(None, description="角色筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: AdminUser = Depends(get_admin_user),
    db: AsyncSession = Depends(AsyncSessionLocal),
):
    conditions = []
    if search:
        conditions.append(
            (User.username.ilike(f"%{search}%"))
            | (User.phone.ilike(f"%{search}%"))
            | (User.email.ilike(f"%{search}%"))
        )
    if role:
        conditions.append(User.role == role)
    if status:
        conditions.append(User.status == status)

    where_clause = and_(*conditions) if conditions else True

    total_result = await db.execute(select(func.count(User.id)).where(where_clause))
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        select(User)
        .where(where_clause)
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    users = result.scalars().all()

    items = [
        UserListItem(
            id=u.id,
            uid=u.uid,
            username=u.username,
            phone=u.phone,
            email=u.email,
            role=u.role,
            status=u.status,
            is_active=u.is_active,
            vip_expires_at=u.vip_expires_at,
            created_at=u.created_at,
        )
        for u in users
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


class DomainResponse(BaseModel):
    code: str
    name: str


class DomainRoleResponse(BaseModel):
    id: int
    name: str
    code: str
    domain: str
    description: Optional[str]
    is_system: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DomainHierarchyResponse(BaseModel):
    domain: str
    domain_name: str
    hierarchy: dict[str, list[str]]


@router.get("/domains", response_model=list[DomainResponse])
async def list_domains(
    admin: AdminUser = Depends(get_admin_user),
):
    return [DomainResponse(code=code, name=name) for code, name in BUSINESS_DOMAINS.items()]


@router.get("/domains/{domain}/roles", response_model=list[DomainRoleResponse])
async def get_domain_roles(
    domain: str,
    admin: AdminUser = Depends(get_admin_user),
    db: AsyncSession = Depends(AsyncSessionLocal),
):
    if domain not in BUSINESS_DOMAINS:
        raise HTTPException(status_code=404, detail=f"业务域不存在: {domain}")

    result = await db.execute(
        select(Role).where(Role.domain == domain).order_by(Role.id)
    )
    roles = result.scalars().all()

    return [
        DomainRoleResponse(
            id=r.id,
            name=r.name,
            code=r.code,
            domain=r.domain,
            description=r.description,
            is_system=r.is_system,
            created_at=r.created_at,
        )
        for r in roles
    ]


@router.get("/domains/{domain}/hierarchy", response_model=DomainHierarchyResponse)
async def get_domain_hierarchy(
    domain: str,
    admin: AdminUser = Depends(get_admin_user),
):
    if domain not in BUSINESS_DOMAINS:
        raise HTTPException(status_code=404, detail=f"业务域不存在: {domain}")

    hierarchy = DOMAIN_ROLE_HIERARCHY.get(domain, {})

    return DomainHierarchyResponse(
        domain=domain,
        domain_name=BUSINESS_DOMAINS[domain],
        hierarchy=hierarchy,
    )


@router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: int,
    admin: AdminUser = Depends(get_admin_user),
    db: AsyncSession = Depends(AsyncSessionLocal),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = profile_result.scalar_one_or_none()

    roles_result = await db.execute(
        select(Role).join(user_roles, user_roles.c.role_id == Role.id).where(
            user_roles.c.user_id == user_id
        )
    )
    roles = roles_result.scalars().all()

    return UserDetailResponse(
        id=user.id,
        uid=user.uid,
        username=user.username,
        phone=user.phone,
        email=user.email,
        role=user.role,
        status=user.status,
        is_active=user.is_active,
        email_verified=user.email_verified,
        phone_verified=user.phone_verified,
        vip_expires_at=user.vip_expires_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
        nickname=profile.nickname if profile else None,
        avatar=profile.avatar if profile else None,
        roles=[{"id": r.id, "code": r.code, "name": r.name} for r in roles],
    )


@router.post("/users/{user_id}/ban")
async def ban_user(
    user_id: int,
    req: BanRequest,
    admin: AdminUser = Depends(get_admin_user),
    db: AsyncSession = Depends(AsyncSessionLocal),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.status == AccountStatus.BANNED:
        raise HTTPException(status_code=400, detail="用户已被封禁")

    old_status = user.status
    user.status = AccountStatus.BANNED
    user.is_active = False

    audit = UserAuditLog(
        user_id=user_id,
        operator_id=admin.user_id,
        operator_name=admin.role,
        action="ban",
        old_value=old_status,
        new_value=AccountStatus.BANNED,
        comment=req.reason,
    )
    db.add(audit)
    await db.commit()

    return {"success": True, "message": "用户已封禁"}


@router.post("/users/{user_id}/unban")
async def unban_user(
    user_id: int,
    admin: AdminUser = Depends(get_admin_user),
    db: AsyncSession = Depends(AsyncSessionLocal),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.status != AccountStatus.BANNED:
        raise HTTPException(status_code=400, detail="用户未被封禁")

    old_status = user.status
    user.status = AccountStatus.ACTIVE
    user.is_active = True

    audit = UserAuditLog(
        user_id=user_id,
        operator_id=admin.user_id,
        operator_name=admin.role,
        action="unban",
        old_value=old_status,
        new_value=AccountStatus.ACTIVE,
    )
    db.add(audit)
    await db.commit()

    return {"success": True, "message": "用户已解封"}


@router.put("/users/{user_id}/role")
async def change_user_role(
    user_id: int,
    req: RoleChangeRequest,
    admin: AdminUser = Depends(get_admin_user),
    db: AsyncSession = Depends(AsyncSessionLocal),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    role_result = await db.execute(
        select(Role).where(Role.code == req.role_code)
    )
    target_role = role_result.scalar_one_or_none()
    if not target_role:
        raise HTTPException(status_code=404, detail="角色不存在")

    old_role = user.role
    user.role = req.role_code

    existing = await db.execute(
        select(user_roles).where(
            and_(user_roles.c.user_id == user_id, user_roles.c.role_id == target_role.id)
        )
    )
    if not existing.scalar_one_or_none():
        values = {"user_id": user_id, "role_id": target_role.id}
        if req.scope_id is not None:
            values["scope_id"] = req.scope_id
        await db.execute(user_roles.insert().values(**values))

    audit = UserAuditLog(
        user_id=user_id,
        operator_id=admin.user_id,
        operator_name=admin.role,
        action="role_change",
        old_value=old_role,
        new_value=req.role_code,
        extra_data={"scope_id": req.scope_id} if req.scope_id is not None else None,
    )
    db.add(audit)
    await db.commit()

    return {"success": True, "message": f"角色已变更为 {req.role_code}"}


@router.get("/roles", response_model=list[RoleResponse])
async def list_roles(
    domain: Optional[str] = Query(None, description="按业务域筛选角色"),
    admin: AdminUser = Depends(get_admin_user),
    db: AsyncSession = Depends(AsyncSessionLocal),
):
    query = select(Role).options(selectinload(Role.permissions)).order_by(Role.id)
    if domain:
        if domain not in BUSINESS_DOMAINS:
            raise HTTPException(status_code=400, detail=f"无效的业务域: {domain}")
        query = query.where(Role.domain == domain)
    result = await db.execute(query)
    roles = result.scalars().all()

    return [
        RoleResponse(
            id=r.id,
            name=r.name,
            code=r.code,
            domain=r.domain,
            description=r.description,
            is_system=r.is_system,
            created_at=r.created_at,
            permissions=[
                {"id": p.id, "code": p.code, "name": p.name, "resource": p.resource, "action": p.action}
                for p in r.permissions
            ],
        )
        for r in roles
    ]


@router.post("/roles", response_model=RoleResponse, status_code=201)
async def create_role(
    req: RoleCreateRequest,
    admin: AdminUser = Depends(get_admin_user),
    db: AsyncSession = Depends(AsyncSessionLocal),
):
    existing = await db.execute(select(Role).where(Role.code == req.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="角色编码已存在")

    if req.domain not in BUSINESS_DOMAINS:
        raise HTTPException(status_code=400, detail=f"无效的业务域: {req.domain}")

    role = Role(name=req.name, code=req.code, domain=req.domain, description=req.description, is_system=False)
    db.add(role)
    await db.commit()
    await db.refresh(role)

    return RoleResponse(
        id=role.id,
        name=role.name,
        code=role.code,
        domain=role.domain,
        description=role.description,
        is_system=role.is_system,
        created_at=role.created_at,
        permissions=[],
    )


@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    req: RoleUpdateRequest,
    admin: AdminUser = Depends(get_admin_user),
    db: AsyncSession = Depends(AsyncSessionLocal),
):
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    if req.name is not None:
        role.name = req.name
    if req.domain is not None:
        if req.domain not in BUSINESS_DOMAINS:
            raise HTTPException(status_code=400, detail=f"无效的业务域: {req.domain}")
        role.domain = req.domain
    if req.description is not None:
        role.description = req.description

    await db.commit()
    await db.refresh(role)

    perms_result = await db.execute(
        select(Permission).join(role_permissions, role_permissions.c.permission_id == Permission.id).where(
            role_permissions.c.role_id == role_id
        )
    )
    perms = perms_result.scalars().all()

    return RoleResponse(
        id=role.id,
        name=role.name,
        code=role.code,
        domain=role.domain,
        description=role.description,
        is_system=role.is_system,
        created_at=role.created_at,
        permissions=[
            {"id": p.id, "code": p.code, "name": p.name, "resource": p.resource, "action": p.action}
            for p in perms
        ],
    )


@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: int,
    admin: AdminUser = Depends(get_admin_user),
    db: AsyncSession = Depends(AsyncSessionLocal),
):
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    if role.is_system:
        raise HTTPException(status_code=400, detail="系统角色不可删除")

    await db.execute(user_roles.delete().where(user_roles.c.role_id == role_id))
    await db.execute(role_permissions.delete().where(role_permissions.c.role_id == role_id))
    await db.delete(role)
    await db.commit()

    return {"success": True, "message": "角色已删除"}


@router.put("/roles/{role_id}/permissions")
async def assign_permissions(
    role_id: int,
    req: RolePermissionRequest,
    admin: AdminUser = Depends(get_admin_user),
    db: AsyncSession = Depends(AsyncSessionLocal),
):
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    perm_count_result = await db.execute(
        select(func.count(Permission.id)).where(Permission.id.in_(req.permission_ids))
    )
    perm_count = perm_count_result.scalar() or 0
    if perm_count != len(req.permission_ids):
        raise HTTPException(status_code=400, detail="部分权限ID不存在")

    await db.execute(role_permissions.delete().where(role_permissions.c.role_id == role_id))

    if req.permission_ids:
        await db.execute(
            role_permissions.insert(),
            [{"role_id": role_id, "permission_id": pid} for pid in req.permission_ids],
        )

    audit = UserAuditLog(
        user_id=role_id,
        operator_id=admin.user_id,
        operator_name=admin.role,
        action="assign_permissions",
        new_value=str(req.permission_ids),
        extra_data={"role_code": role.code},
    )
    db.add(audit)
    await db.commit()

    return {"success": True, "message": "权限已更新"}


@router.get("/audit-logs", response_model=PaginatedResponse)
async def get_audit_logs(
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: AdminUser = Depends(get_admin_user),
    db: AsyncSession = Depends(AsyncSessionLocal),
):
    conditions = []
    if user_id:
        conditions.append(UserAuditLog.user_id == user_id)
    if action:
        conditions.append(UserAuditLog.action == action)
    if start_date:
        conditions.append(UserAuditLog.created_at >= start_date)
    if end_date:
        conditions.append(UserAuditLog.created_at <= end_date)

    where_clause = and_(*conditions) if conditions else True

    total_result = await db.execute(
        select(func.count(UserAuditLog.id)).where(where_clause)
    )
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        select(UserAuditLog)
        .where(where_clause)
        .order_by(UserAuditLog.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    logs = result.scalars().all()

    items = [
        AuditLogResponse(
            id=l.id,
            user_id=l.user_id,
            operator_id=l.operator_id,
            operator_name=l.operator_name,
            action=l.action,
            old_value=l.old_value,
            new_value=l.new_value,
            comment=l.comment,
            extra_data=l.extra_data,
            created_at=l.created_at,
        )
        for l in logs
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )
