"""FAQ知识库API路由"""
import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.faq import FAQ
from ..schemas.faq import (
    FAQCreate, FAQUpdate, FAQResponse, FAQListResponse,
    FAQSearchRequest, FAQCategoryResponse, FAQPopularResponse,
    FAQSmartSearchRequest, FAQSmartSearchResponse
)
from ..services.faq_service import faq_service
from ..utils.deps import get_current_user, require_admin
from ..models.user import User

router = APIRouter(prefix="/faq", tags=["FAQ知识库"])


def _parse_tags(tags_json: str | None) -> list[str] | None:
    """解析标签JSON"""
    if not tags_json:
        return None
    try:
        tags = json.loads(tags_json)
        if isinstance(tags, list):
            return tags
    except (json.JSONDecodeError, TypeError):
        pass
    return None


def _faq_to_response(faq: FAQ) -> FAQResponse:
    """将FAQ模型转换为响应对象"""
    return FAQResponse(
        id=faq.id,
        question=faq.question,
        answer=faq.answer,
        category=faq.category,
        tags=_parse_tags(faq.tags),
        priority=faq.priority,
        is_active=faq.is_active,
        view_count=faq.view_count,
        created_at=faq.created_at,
        updated_at=faq.updated_at,
    )


# ============ 公开API ============

@router.get("/search", response_model=FAQListResponse, summary="搜索FAQ")
async def search_faqs(
    db: Annotated[AsyncSession, Depends(get_db)],
    keyword: Annotated[str | None, Query(description="搜索关键词")] = None,
    category: Annotated[str | None, Query(description="分类筛选")] = None,
    tags: Annotated[str | None, Query(description="标签筛选，多个标签用逗号分隔")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """搜索FAQ"""
    # 解析标签
    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    # 搜索FAQ
    faqs, total = await faq_service.search_faqs(
        db,
        keyword=keyword,
        category=category,
        tags=tag_list,
        is_active=True,
        page=page,
        page_size=page_size,
    )

    # 转换为响应对象
    items = [_faq_to_response(faq) for faq in faqs]

    return FAQListResponse(items=items, total=total,
                           page=page, page_size=page_size)


@router.get("/categories", response_model=FAQCategoryResponse,
            summary="获取FAQ分类")
async def get_faq_categories(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取所有FAQ分类"""
    categories = await faq_service.get_faq_categories(db)
    return FAQCategoryResponse(categories=categories)


@router.get("/popular", response_model=FAQPopularResponse, summary="获取热门FAQ")
async def get_popular_faqs(
    db: Annotated[AsyncSession, Depends(get_db)],
    category: Annotated[str | None, Query(description="分类筛选")] = None,
    limit: Annotated[int, Query(ge=1, le=20)] = 10,
):
    """获取热门FAQ（按浏览量排序）"""
    faqs = await faq_service.get_popular_faqs(db, limit=limit, category=category)
    items = [_faq_to_response(faq) for faq in faqs]
    return FAQPopularResponse(items=items)


@router.get("/{faq_id}", response_model=FAQResponse, summary="获取FAQ详情")
async def get_faq(
    faq_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取FAQ详情"""
    faq = await faq_service.get_faq_by_id(db, faq_id)
    if not faq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FAQ不存在")

    # 增加浏览量
    await faq_service.increment_view_count(db, faq_id)

    # 刷新FAQ对象以获取最新数据
    await db.refresh(faq)

    return _faq_to_response(faq)


@router.post("/smart-search", response_model=FAQSmartSearchResponse,
             summary="FAQ智能搜索（智能客服）")
async def smart_search_faq(
    data: FAQSmartSearchRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    FAQ智能搜索（用于智能客服）

    根据用户问题智能匹配FAQ，返回最佳答案和相关建议
    """
    # 搜索FAQ
    faqs, _ = await faq_service.search_faqs(
        db,
        keyword=data.question,
        category=data.category,
        is_active=True,
        page=1,
        page_size=data.limit,
    )

    # 如果没有匹配的FAQ
    if not faqs:
        return FAQSmartSearchResponse(
            matched=False,
            answer=None,
            faq_id=None,
            confidence=0.0,
            suggestions=[],
        )

    # 计算匹配置信度（简单实现：基于关键词匹配）
    best_faq = faqs[0]
    confidence = 0.0

    # 简单的匹配算法：检查问题是否包含关键词
    question_lower = data.question.lower()
    faq_question_lower = best_faq.question.lower()

    # 完全匹配
    if question_lower == faq_question_lower:
        confidence = 1.0
    # 包含匹配
    elif question_lower in faq_question_lower or faq_question_lower in question_lower:
        confidence = 0.8
    # 部分匹配
    else:
        # 计算共同词数
        question_words = set(question_lower.split())
        faq_words = set(faq_question_lower.split())
        common_words = question_words & faq_words
        if common_words:
            confidence = min(0.7, len(common_words) /
                             max(len(question_words), 1))

    # 转换为响应对象
    suggestions = [_faq_to_response(faq) for faq in faqs]

    # 如果置信度足够高，返回答案
    if confidence >= 0.6:
        return FAQSmartSearchResponse(
            matched=True,
            answer=best_faq.answer,
            faq_id=best_faq.id,
            confidence=confidence,
            suggestions=suggestions,
        )
    else:
        # 置信度不够，只返回建议
        return FAQSmartSearchResponse(
            matched=False,
            answer=None,
            faq_id=None,
            confidence=confidence,
            suggestions=suggestions,
        )


# ============ 管理员API ============

@router.post("/admin/faqs", response_model=FAQResponse, summary="管理员-创建FAQ")
async def admin_create_faq(
    data: FAQCreate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """管理员创建FAQ"""
    _ = current_user

    faq = await faq_service.create_faq(
        db,
        question=data.question,
        answer=data.answer,
        category=data.category,
        tags=data.tags,
        priority=data.priority,
        is_active=data.is_active,
    )

    return _faq_to_response(faq)


@router.put("/admin/faqs/{faq_id}",
            response_model=FAQResponse, summary="管理员-更新FAQ")
async def admin_update_faq(
    faq_id: int,
    data: FAQUpdate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """管理员更新FAQ"""
    _ = current_user

    faq = await faq_service.update_faq(
        db,
        faq_id=faq_id,
        question=data.question,
        answer=data.answer,
        category=data.category,
        tags=data.tags,
        priority=data.priority,
        is_active=data.is_active,
    )

    if not faq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FAQ不存在")

    return _faq_to_response(faq)


@router.delete("/admin/faqs/{faq_id}", summary="管理员-删除FAQ")
async def admin_delete_faq(
    faq_id: int,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """管理员删除FAQ"""
    _ = current_user

    success = await faq_service.delete_faq(db, faq_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FAQ不存在")

    return {"message": "删除成功"}


@router.get("/admin/faqs", response_model=FAQListResponse,
            summary="管理员-获取FAQ列表")
async def admin_list_faqs(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    keyword: Annotated[str | None, Query(description="搜索关键词")] = None,
    category: Annotated[str | None, Query(description="分类筛选")] = None,
    is_active: Annotated[bool | None, Query(description="是否激活")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """管理员获取FAQ列表（包含未激活的）"""
    _ = current_user

    # 解析标签
    tag_list = None

    # 搜索FAQ
    faqs, total = await faq_service.search_faqs(
        db,
        keyword=keyword,
        category=category,
        tags=tag_list,
        is_active=is_active if is_active is not None else None,
        page=page,
        page_size=page_size,
    )

    # 转换为响应对象
    items = [_faq_to_response(faq) for faq in faqs]

    return FAQListResponse(items=items, total=total,
                           page=page, page_size=page_size)
