"""FAQ自动生成路由"""

import json
from typing import Annotated
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ...database import get_db
from ...models.user import User
from ...models.consultation import Consultation, ChatMessage
from ...models.system import SystemConfig
from ...utils.deps import require_admin

router = APIRouter(prefix="/faq", tags=["FAQ自动生成"])


@router.post("/generate")
async def generate_faq(
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(30, description="统计天数"),
    max_items: int = Query(10, description="最大FAQ数量"),
    scan_limit: int = Query(50, description="扫描消息数量限制"),
):
    """FAQ自动生成"""
    since_date = datetime.now(timezone.utc) - timedelta(days=days)

    # 获取用户问题和助理回答的配对
    faq_items = []

    # 查找有评分的对话（评分>=3认为是好的回答）
    rated_messages_result = await db.execute(
        select(ChatMessage)
        .where(
            ChatMessage.created_at >= since_date,
            ChatMessage.role == "assistant",
            ChatMessage.rating.isnot(None),
            ChatMessage.rating >= 3
        )
        .order_by(ChatMessage.created_at.desc())
        .limit(scan_limit)
    )

    rated_messages = rated_messages_result.scalars().all()

    for assistant_msg in rated_messages:
        # 找到对应的用户问题
        user_msg_result = await db.execute(
            select(ChatMessage)
            .where(
                ChatMessage.consultation_id == assistant_msg.consultation_id,
                ChatMessage.role == "user",
                ChatMessage.created_at < assistant_msg.created_at
            )
            .order_by(ChatMessage.created_at.desc())
            .limit(1)
        )

        user_msg = user_msg_result.scalar_one_or_none()

        if user_msg and len(faq_items) < max_items:
            created_at_val = assistant_msg.created_at
            faq_items.append({
                "question": user_msg.content or "",
                "answer": assistant_msg.content or "",
                "rating": assistant_msg.rating,
                "consultation_id": assistant_msg.consultation_id,
                "created_at": created_at_val.isoformat() if created_at_val is not None else None
            })

    # 保存到系统配置
    config_key = "FAQ_PUBLIC_ITEMS_JSON"
    config_value = json.dumps(faq_items, ensure_ascii=False)

    # 检查是否已存在
    existing_config = await db.scalar(
        select(SystemConfig).where(SystemConfig.key == config_key)
    )

    if existing_config:
        existing_config.value = config_value
        existing_config.updated_at = datetime.now(timezone.utc)
    else:
        config = SystemConfig(
            key=config_key,
            value=config_value,
            description="自动生成的FAQ公开内容"
        )
        db.add(config)

    await db.commit()

    return {
        "key": config_key,
        "generated": len(faq_items),
        "items": faq_items,
        "message": f"成功生成 {len(faq_items)} 条FAQ"
    }


@router.get("/status")
async def get_faq_status(
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取FAQ生成状态"""
    # 检查是否有FAQ配置
    config = await db.scalar(
        select(SystemConfig).where(SystemConfig.key == "FAQ_PUBLIC_ITEMS_JSON")
    )

    if config and config.value:
        try:
            faq_items = json.loads(config.value)
            total_faq = len(faq_items)
        except json.JSONDecodeError:
            total_faq = 0
    else:
        total_faq = 0

    return {"enabled": total_faq > 0, "last_run": config.updated_at.isoformat(
    ) if config and config.updated_at else None, "total_faq": total_faq}
