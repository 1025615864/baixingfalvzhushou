"""知识库管理 API 路由

提供知识库批量导入、统计、分类管理等功能。
"""
from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..schemas.knowledge import LegalKnowledgeCreate, KnowledgeStats
from ..services.knowledge.core import KnowledgeService
from ..utils.deps import get_current_user_optional, get_current_user

router = APIRouter(prefix="/knowledge", tags=["知识库"])

knowledge_service = KnowledgeService()


@router.get("/stats")
async def get_knowledge_stats(
        db: Annotated[AsyncSession, Depends(get_db)]) -> KnowledgeStats:
    """获取知识库统计信息"""
    return await knowledge_service.get_stats(db)


@router.get("/categories")
async def get_categories(
        db: Annotated[AsyncSession, Depends(get_db)]) -> dict[str, int]:
    """获取知识分类统计"""
    return await knowledge_service.get_categories_with_count(db)


@router.post("/batch/import")
async def batch_import_knowledge(
    items: list[LegalKnowledgeCreate],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """批量导入知识条目

    支持批量导入法律条文、案例、法规等内容
    """
    success, failed = await knowledge_service.batch_import_knowledge(db, items)

    return {
        "success": success,
        "failed": failed,
        "total": len(items),
        "message": f"成功导入 {success} 条，失败 {failed} 条",
    }


@router.post("/import/sample")
async def import_sample_knowledge(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """导入示例知识数据（用于测试和演示）"""
    from ..schemas.knowledge import KnowledgeType

    sample_items = [
        # 劳动法相关
        LegalKnowledgeCreate(
            knowledge_type=KnowledgeType.LAW,
            title="中华人民共和国劳动合同法",
            article_number="第十条",
            content="建立劳动关系，应当订立书面劳动合同。已建立劳动关系，未同时订立书面劳动合同的，应当自用工之日起一个月内订立书面劳动合同。",
            summary="劳动合同订立的规定",
            category="劳动法",
            keywords="劳动合同,书面,订立,一个月",
            source="全国人民代表大会",
            source_version="2012年修订",
            effective_date="2013-07-01",
        ),
        LegalKnowledgeCreate(
            knowledge_type=KnowledgeType.LAW,
            title="中华人民共和国劳动合同法",
            article_number="第三十八条",
            content="用人单位有下列情形之一的，劳动者可以解除劳动合同：（一）未按照劳动合同约定提供劳动保护或者劳动条件的；（二）未及时足额支付劳动报酬的；（三）未依法为劳动者缴纳社会保险费的；（四）用人单位的规章制度违反法律、法规的规定，损害劳动者权益的；",
            summary="劳动者解除劳动合同的情形",
            category="劳动法",
            keywords="解除劳动合同,劳动保护,劳动报酬,社保",
            source="全国人民代表大会",
            source_version="2012年修订",
            effective_date="2013-07-01",
        ),
        # 婚姻法相关
        LegalKnowledgeCreate(
            knowledge_type=KnowledgeType.LAW,
            title="中华人民共和国民法典 - 婚姻家庭编",
            article_number="第一千零七十六条",
            content="夫妻双方自愿离婚的，应当签订书面离婚协议，并亲自到婚姻登记机关申请离婚登记。离婚协议应当载明双方自愿离婚的意思表示和对子女抚养、财产以及债务处理等事项协商一致的意见。",
            summary="自愿离婚的规定",
            category="婚姻法",
            keywords="离婚,离婚协议,子女抚养,财产分割",
            source="全国人民代表大会",
            source_version="2020年",
            effective_date="2021-01-01",
        ),
        LegalKnowledgeCreate(
            knowledge_type=KnowledgeType.LAW,
            title="中华人民共和国民法典 - 婚姻家庭编",
            article_number="第一千零八十四条",
            content="父母与子女间的关系，不因父母离婚而消除。离婚后，子女无论由父或者母直接抚养，仍是父母双方的子女。离婚后，父母对于子女仍有抚养、教育、保护的权利和义务。",
            summary="离婚后父母子女关系",
            category="婚姻法",
            keywords="离婚,子女抚养,抚养费,父母子女关系",
            source="全国人民代表大会",
            source_version="2020年",
            effective_date="2021-01-01",
        ),
        # 案例
        LegalKnowledgeCreate(
            knowledge_type=KnowledgeType.CASE,
            title="劳动争议案例：加班费计算纠纷",
            article_number="案例-2024-001",
            content="张某在某公司工作3年，离职后主张加班费共计5万元。公司辩称已支付加班工资。经审理，仲裁委员会认定公司未能提供完整考勤记录，判决公司支付差额加班费3.5万元。",
            summary="加班费争议举证责任分配",
            category="劳动争议",
            keywords="劳动争议,加班费,举证责任,考勤记录",
            source="典型案例汇编",
            source_version="2024版",
        ),
        LegalKnowledgeCreate(
            knowledge_type=KnowledgeType.CASE,
            title="离婚案例：财产分割协议效力",
            article_number="案例-2024-002",
            content="李某与王某离婚时签订财产分割协议，约定房产归男方所有。后女方主张该协议显失公平。法院审理认为，协议系双方真实意思表示，不存在欺诈胁迫，判决驳回女方诉讼请求。",
            summary="离婚财产分割协议效力认定",
            category="婚姻家庭",
            keywords="离婚,财产分割,协议效力,显失公平",
            source="典型案例汇编",
            source_version="2024版",
        ),
    ]

    success, failed = await knowledge_service.batch_import_knowledge(db, sample_items)

    return {
        "success": success,
        "failed": failed,
        "message": f"成功导入 {success} 条示例数据",
    }


@router.get("/search")
async def search_knowledge(
    db: Annotated[AsyncSession, Depends(get_db)],
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    knowledge_type: str | None = Query(
        None, description="知识类型：law/case/regulation/interpretation"),
    category: str | None = Query(None, description="分类"),
    page: int = Query(ge=1, default=1),
    page_size: int = Query(ge=1, le=100, default=20),
) -> dict:
    """搜索知识条目"""
    items, total = await knowledge_service.list_knowledge(
        db=db,
        page=page,
        page_size=page_size,
        knowledge_type=knowledge_type,
        category=category,
        keyword=keyword,
    )

    return {
        "items": [
            {
                "id": item.id,
                "knowledge_type": item.knowledge_type,
                "title": item.title,
                "article_number": item.article_number,
                "summary": item.summary,
                "category": item.category,
                "keywords": item.keywords,
            }
            for item in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/list")
async def list_knowledge(
    db: Annotated[AsyncSession, Depends(get_db)],
    knowledge_type: str | None = Query(None, description="知识类型"),
    category: str | None = Query(None, description="分类"),
    page: int = Query(ge=1, default=1),
    page_size: int = Query(ge=1, le=100, default=20),
) -> dict:
    """获取知识条目列表"""
    items, total = await knowledge_service.list_knowledge(
        db=db,
        page=page,
        page_size=page_size,
        knowledge_type=knowledge_type,
        category=category,
    )

    return {
        "items": [
            {
                "id": item.id,
                "knowledge_type": item.knowledge_type,
                "title": item.title,
                "article_number": item.article_number,
                "summary": item.summary,
                "category": item.category,
                "keywords": item.keywords,
                "is_vectorized": item.is_vectorized,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
