"""管理后台API路由"""
from collections.abc import AsyncIterator, Mapping
from typing import Annotated, cast
import csv
import io
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..database import get_db
from ..models.user import User
from ..models.lawfirm import LawFirm
from ..models.consultation import Consultation, ChatMessage
from ..models.knowledge import LegalKnowledge
from ..utils.deps import require_admin
from ..utils.pii import sanitize_pii

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["管理后台"])


def _log_export_action(user_id: int, export_type: str, record_count: int) -> None:
    """记录导出操作审计日志"""
    logger.info(
        f"Admin export: user_id={user_id}, type={export_type}, records={record_count}"
    )


@router.get("/stats", summary="获取统计数据")
async def get_stats(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, int]:
    """获取系统统计数据（需要管理员权限）"""
    _ = current_user
    try:
        user_count = await db.execute(select(func.count()).select_from(User))
        total_users = user_count.scalar() or 0

        total_news = 0
        total_posts = 0
        total_comments = 0

        consultation_count = await db.execute(select(func.count()).select_from(Consultation))
        total_consultations = consultation_count.scalar() or 0

        firm_count = await db.execute(select(func.count()).select_from(LawFirm))
        total_firms = firm_count.scalar() or 0

        return {
            "users": total_users,
            "news": total_news,
            "posts": total_posts,
            "lawfirms": total_firms,
            "comments": total_comments,
            "consultations": total_consultations,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计数据失败: {str(e)}",
        )


# ============ 数据导出 API ============

def generate_csv(data: list[dict[str, object]],
                 fieldnames: list[str]) -> io.StringIO:
    """生成CSV内容"""
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
        extrasaction='ignore')
    writer.writeheader()
    for row in data:
        # 处理日期时间格式
        processed: dict[str, object] = {}
        for k, v in row.items():
            if isinstance(v, datetime):
                processed[k] = v.strftime("%Y-%m-%d %H:%M:%S")
            else:
                processed[k] = v
        writer.writerow(processed)
    _ = output.seek(0)
    return output


async def generate_csv_stream(
        fieldnames: list[str], rows_iter: AsyncIterator[Mapping[str, object]]):
    header_out = io.StringIO()
    _ = header_out.write("\ufeff")
    header_writer = csv.DictWriter(
        header_out,
        fieldnames=fieldnames,
        extrasaction='ignore',
        lineterminator="\n")
    header_writer.writeheader()
    yield header_out.getvalue()

    async for row in rows_iter:
        processed: dict[str, object] = {}
        for k, v in row.items():
            if isinstance(v, datetime):
                processed[k] = v.strftime("%Y-%m-%d %H:%M:%S")
            else:
                processed[k] = v

        out = io.StringIO()
        writer = csv.DictWriter(
            out,
            fieldnames=fieldnames,
            extrasaction='ignore',
            lineterminator="\n")
        writer.writerow(processed)
        yield out.getvalue()


@router.get("/export/users", summary="导出用户数据")
async def export_users(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    format: Annotated[str, Query(description="导出格式: csv")] = "csv",
):
    """导出所有用户数据为CSV（敏感字段已脱敏）"""
    user_id = current_user.id
    fieldnames = [
        "id",
        "username",
        "email",
        "nickname",
        "phone",
        "role",
        "is_active",
        "created_at"]

    async def row_generator():
        batch_size = 1000
        offset = 0
        record_count = 0
        while True:
            result = await db.execute(
                select(User).order_by(User.id).offset(offset).limit(batch_size)
            )
            users = result.scalars().all()
            if not users:
                break
            for u in users:
                record_count += 1
                yield {
                    "id": u.id,
                    "username": sanitize_pii(u.username),
                    "email": sanitize_pii(u.email),
                    "nickname": sanitize_pii(u.nickname or ""),
                    "phone": sanitize_pii(u.phone or ""),
                    "role": u.role,
                    "is_active": "是" if u.is_active else "否",
                    "created_at": u.created_at,
                }
            offset += batch_size

        # 记录审计日志
        _log_export_action(user_id, "users", record_count)

    filename = f"users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        generate_csv_stream(fieldnames, row_generator()),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/lawfirms", summary="导出律所数据")
async def export_lawfirms(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """导出所有律所数据为CSV"""
    _ = current_user
    fieldnames = [
        "id",
        "name",
        "city",
        "province",
        "address",
        "phone",
        "email",
        "rating",
        "review_count",
        "is_verified",
        "is_active",
        "created_at"]

    async def row_generator():
        batch_size = 1000
        offset = 0
        while True:
            result = await db.execute(
                select(LawFirm).order_by(
                    LawFirm.id).offset(offset).limit(batch_size)
            )
            firms = result.scalars().all()
            if not firms:
                break
            for f in firms:
                yield {
                    "id": f.id,
                    "name": f.name,
                    "city": f.city or "",
                    "province": f.province or "",
                    "address": f.address or "",
                    "phone": f.phone or "",
                    "email": f.email or "",
                    "rating": f.rating,
                    "review_count": f.review_count,
                    "is_verified": "是" if f.is_verified else "否",
                    "is_active": "是" if f.is_active else "否",
                    "created_at": f.created_at,
                }
            offset += batch_size

    filename = f"lawfirms_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        generate_csv_stream(fieldnames, row_generator()),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/knowledge", summary="导出知识库数据")
async def export_knowledge(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """导出所有法律知识数据为CSV"""
    _ = current_user
    fieldnames = [
        "id",
        "knowledge_type",
        "title",
        "article_number",
        "category",
        "content",
        "keywords",
        "source",
        "is_active",
        "is_vectorized",
        "created_at"]

    async def row_generator():
        batch_size = 500
        offset = 0
        while True:
            result = await db.execute(
                select(LegalKnowledge).order_by(
                    LegalKnowledge.id).offset(offset).limit(batch_size)
            )
            knowledge_list = result.scalars().all()
            if not knowledge_list:
                break
            for k in knowledge_list:
                content_preview = k.content[:200] + \
                    "..." if len(k.content) > 200 else k.content
                yield {
                    "id": k.id,
                    "knowledge_type": k.knowledge_type,
                    "title": k.title,
                    "article_number": k.article_number or "",
                    "category": k.category,
                    "content": content_preview,
                    "keywords": k.keywords or "",
                    "source": k.source or "",
                    "is_active": "是" if k.is_active else "否",
                    "is_vectorized": "是" if k.is_vectorized else "否",
                    "created_at": k.created_at,
                }
            offset += batch_size

    filename = f"knowledge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        generate_csv_stream(fieldnames, row_generator()),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/consultations", summary="导出咨询记录")
async def export_consultations(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """导出所有咨询记录为CSV（敏感字段已脱敏）"""
    user_id = current_user.id
    fieldnames = [
        "id",
        "session_id",
        "user",
        "title",
        "status",
        "message_count",
        "created_at",
        "updated_at"]

    async def row_generator() -> AsyncIterator[Mapping[str, object]]:
        batch_size = 500
        offset = 0
        record_count = 0
        while True:
            result = await db.execute(
                select(
                    Consultation.id,
                    Consultation.session_id,
                    Consultation.title,
                    Consultation.created_at,
                    Consultation.updated_at,
                    User.username,
                    func.count(ChatMessage.id).label("message_count"),
                )
                .select_from(Consultation)
                .outerjoin(User, Consultation.user_id == User.id)
                .outerjoin(ChatMessage, ChatMessage.consultation_id == Consultation.id)
                .group_by(
                    Consultation.id,
                    Consultation.session_id,
                    Consultation.title,
                    Consultation.created_at,
                    Consultation.updated_at,
                    User.username,
                )
                .order_by(Consultation.id.desc())
                .offset(offset)
                .limit(batch_size)
            )
            rows = cast(list[tuple[int, str, str | None, datetime,
                        datetime, str | None, int]], result.all())
            if not rows:
                break
            for consultation_id, session_id, title, created_at, updated_at, username, message_count in rows:
                record_count += 1
                yield {
                    "id": consultation_id,
                    "session_id": session_id,
                    "user": sanitize_pii(username or ""),
                    "title": sanitize_pii(title or ""),
                    "status": "",
                    "message_count": int(message_count),
                    "created_at": created_at,
                    "updated_at": updated_at,
                }
            offset += batch_size

        # 记录审计日志
        _log_export_action(user_id, "consultations", record_count)

    filename = f"consultations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        generate_csv_stream(fieldnames, row_generator()),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
