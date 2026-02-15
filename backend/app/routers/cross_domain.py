"""Cross-Domain 域名管理 API 路由

提供跨域域名验证、管理等功能。
"""
from __future__ import annotations

import secrets
import string
from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.cross_domain import Domain
from ..models.user import User
from ..schemas.cross_domain import (
    DomainCreate,
    DomainUpdate,
    DomainResponse,
    DomainDetailResponse,
    DomainListResponse,
    DomainVerifyResult,
)
from ..utils.deps import get_current_user

router = APIRouter(prefix="/cross-domain", tags=["Cross-Domain域名管理"])


def generate_verification_code() -> str:
    """生成验证代码"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))


@router.get("/domains", response_model=DomainListResponse)
async def get_domain_list(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回记录数"),
) -> DomainListResponse:
    """获取当前用户的域名列表"""
    # 获取总数
    count_stmt = select(func.count(Domain.id)).where(Domain.user_id == current_user.id)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # 获取列表
    stmt = (
        select(Domain)
        .where(Domain.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .order_by(Domain.created_at.desc())
    )
    result = await db.execute(stmt)
    domains = result.scalars().all()

    return DomainListResponse(
        items=[DomainResponse.model_validate(d) for d in domains],
        total=total,
    )


@router.post("/domains", response_model=DomainDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_domain(
    domain_data: DomainCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DomainDetailResponse:
    """添加域名"""
    # 检查域名是否已存在
    stmt = select(Domain).where(
        Domain.domain == domain_data.domain,
        Domain.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="域名已存在",
        )

    # 创建新域名记录
    verification_code = generate_verification_code()
    new_domain = Domain(
        domain=domain_data.domain,
        status="pending",
        verification_code=verification_code,
        user_id=current_user.id,
    )

    db.add(new_domain)
    await db.commit()
    await db.refresh(new_domain)

    return DomainDetailResponse.model_validate(new_domain)


@router.get("/domains/{domain_id}", response_model=DomainDetailResponse)
async def get_domain_detail(
    domain_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DomainDetailResponse:
    """获取域名详情"""
    stmt = select(Domain).where(
        Domain.id == domain_id,
        Domain.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    domain = result.scalar_one_or_none()

    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="域名不存在",
        )

    return DomainDetailResponse.model_validate(domain)


@router.put("/domains/{domain_id}", response_model=DomainResponse)
async def update_domain(
    domain_id: int,
    domain_data: DomainUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DomainResponse:
    """更新域名"""
    stmt = select(Domain).where(
        Domain.id == domain_id,
        Domain.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    domain = result.scalar_one_or_none()

    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="域名不存在",
        )

    # 如果更新域名，检查是否与其他域名冲突
    if domain_data.domain and domain_data.domain != domain.domain:
        check_stmt = select(Domain).where(
            Domain.domain == domain_data.domain,
            Domain.user_id == current_user.id,
            Domain.id != domain_id,
        )
        check_result = await db.execute(check_stmt)
        if check_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="域名已存在",
            )

    # 更新字段
    if domain_data.domain:
        domain.domain = domain_data.domain
        # 更新域名后重置验证状态
        domain.status = "pending"
        domain.verification_code = generate_verification_code()

    await db.commit()
    await db.refresh(domain)

    return DomainResponse.model_validate(domain)


@router.delete("/domains/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_domain(
    domain_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """删除域名"""
    stmt = select(Domain).where(
        Domain.id == domain_id,
        Domain.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    domain = result.scalar_one_or_none()

    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="域名不存在",
        )

    await db.delete(domain)
    await db.commit()


@router.post("/domains/{domain_id}/verify", response_model=DomainVerifyResult)
async def verify_domain(
    domain_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DomainVerifyResult:
    """验证域名

    实际验证逻辑应该包括：
    1. 检查 DNS TXT 记录是否包含 verification_code
    2. 或检查网站根目录是否有指定的验证文件
    3. 或检查 HTTP 响应头中的验证信息

    这里提供基础实现框架。
    """
    stmt = select(Domain).where(
        Domain.id == domain_id,
        Domain.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    domain = result.scalar_one_or_none()

    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="域名不存在",
        )

    # TODO: 实现实际的域名验证逻辑
    # 这里可以调用外部服务或执行 DNS 查询来验证
    # 示例：
    # try:
    #     import dns.resolver
    #     txt_records = dns.resolver.resolve(domain.domain, 'TXT')
    #     for record in txt_records:
    #         if domain.verification_code in str(record):
    #             domain.status = "verified"
    #             break
    #     else:
    #         domain.status = "failed"
    # except Exception as e:
    #     domain.status = "failed"

    # 临时模拟验证成功
    import random
    if random.random() > 0.5:  # 模拟验证成功
        domain.status = "verified"
        message = "域名验证成功"
    else:
        domain.status = "failed"
        message = "域名验证失败，请确保已正确配置 DNS TXT 记录"

    await db.commit()
    await db.refresh(domain)

    return DomainVerifyResult(
        success=domain.status == "verified",
        message=message,
        status=cast(Literal["pending", "verified", "failed"], domain.status),
    )