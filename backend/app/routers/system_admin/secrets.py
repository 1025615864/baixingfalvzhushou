"""密钥管理路由"""

from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.system import SystemSecret
from ...models.user import User
from ...utils.deps import require_admin
from ...utils.secret_crypto import encrypt_secret
from .logs import log_admin_action

router = APIRouter(prefix="/secrets", tags=["密钥管理"])


class SecretResponse(BaseModel):
    """密钥响应"""
    key: str
    value: str | None
    description: str | None
    updated_at: datetime | None


def _mask_secret_value(value: str | None) -> str | None:
    """掩码密钥值"""
    if value is None:
        return None
    if not str(value).strip():
        return None
    return "***"


@router.get("", response_model=list[SecretResponse])
async def get_all_secrets(
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取所有密钥"""
    result = await db.execute(select(SystemSecret).order_by(SystemSecret.key))
    items = result.scalars().all()
    return [
        SecretResponse(
            key=str(it.key),
            value=_mask_secret_value(it.value),
            description=it.description,
            updated_at=it.updated_at,
        )
        for it in items
    ]


@router.get("/{key}")
async def get_secret(key: str, _current_user: Annotated[User, Depends(
        require_admin)], db: AsyncSession = Depends(get_db)):
    """获取单个密钥"""
    result = await db.execute(select(SystemSecret).where(SystemSecret.key == key))
    row = result.scalar_one_or_none()
    if not row:
        return {"key": key, "value": None}
    return {"key": str(row.key), "value": _mask_secret_value(row.value)}


@router.put("/{key}")
async def update_secret(
    key: str,
    value: str | None,
    description: str | None,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    """更新密钥"""
    # 处理特殊值
    masked_placeholders = {"***", "••••••••••••••••"}
    if value is not None:
        value_str = str(value).strip()
        if not value_str:
            value = None
        elif value_str in masked_placeholders:
            value = None

    encrypted_value = encrypt_secret(str(value)) if value is not None else None

    result = await db.execute(select(SystemSecret).where(SystemSecret.key == key))
    row = result.scalar_one_or_none()

    is_new = False
    if row:
        if value is not None:
            row.value = encrypted_value
        if description:
            row.description = description
    else:
        is_new = True
        row = SystemSecret(
            key=key,
            value=encrypted_value,
            description=description)
        db.add(row)

    await db.commit()
    
    # 记录审计日志
    action = "create" if is_new else "update"
    description_text = f"{'创建' if is_new else '更新'}密钥: {key}"
    await log_admin_action(
        db=db,
        user_id=current_user.id,
        action=action,
        module="secret",
        target_id=row.id,
        description=description_text,
        request=request,
    )
    await db.commit()
    
    return {"message": "密钥已更新", "key": key,
            "value": _mask_secret_value(row.value) if row else None}


@router.delete("/{key}")
async def delete_secret(
    key: str,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    """删除密钥"""
    result = await db.execute(select(SystemSecret).where(SystemSecret.key == key))
    row = result.scalar_one_or_none()

    if row:
        secret_id = row.id
        await db.delete(row)
        await db.commit()
        
        # 记录审计日志
        await log_admin_action(
            db=db,
            user_id=current_user.id,
            action="delete",
            module="secret",
            target_id=secret_id,
            description=f"删除密钥: {key}",
            request=request,
        )
        await db.commit()
        
        return {"message": "密钥已删除"}
    raise HTTPException(status_code=404, detail="密钥不存在")
