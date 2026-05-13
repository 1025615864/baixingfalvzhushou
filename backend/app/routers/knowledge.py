"""知识库管理 API 路由"""

from datetime import datetime
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..database.session import get_db
from ..models import LegalKnowledge, ConsultationTemplate

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


class CreateArticleBody(BaseModel):
    knowledge_type: str = "law"
    title: str
    article_number: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    category: str = "法律"
    keywords: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    source_version: Optional[str] = None
    effective_date: Optional[str] = None
    weight: int = 1
    is_active: bool = True


class UpdateArticleBody(BaseModel):
    knowledge_type: Optional[str] = None
    title: Optional[str] = None
    article_number: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    category: Optional[str] = None
    keywords: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    source_version: Optional[str] = None
    effective_date: Optional[str] = None
    weight: Optional[int] = None
    is_active: Optional[bool] = None


_mock_articles: list[dict] = [
    {"id": 1, "knowledge_type": "law", "title": "中华人民共和国民法典", "article_number": None, "content": "《中华人民共和国民法典》被称为社会生活的百科全书...", "summary": "民法典是新中国成立以来第一部以法典命名的法律", "category": "民事法律", "keywords": "民法典,民事,合同,婚姻,继承,侵权", "source": "全国人大", "source_url": None, "source_version": "2021.01.01", "effective_date": "2021-01-01", "weight": 100, "is_active": True, "is_vectorized": True, "created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00"},
    {"id": 2, "knowledge_type": "law", "title": "中华人民共和国刑法", "article_number": None, "content": "《中华人民共和国刑法》规定犯罪与刑罚...", "summary": "刑法是规定犯罪及其法律后果的法律规范的总和", "category": "刑事法律", "keywords": "刑法,犯罪,刑罚,刑事", "source": "全国人大", "source_url": None, "source_version": "2021.03.01", "effective_date": "2021-03-01", "weight": 100, "is_active": True, "is_vectorized": True, "created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00"},
    {"id": 3, "knowledge_type": "law", "title": "中华人民共和国劳动合同法", "article_number": None, "content": "保护劳动者合法权益，构建和谐劳动关系...", "summary": "劳动合同法是调整劳动关系的重要法律", "category": "劳动法律", "keywords": "劳动合同,劳动者,劳动关系,劳动法", "source": "全国人大", "source_url": None, "source_version": "2013.07.01", "effective_date": "2013-07-01", "weight": 95, "is_active": True, "is_vectorized": True, "created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00"},
    {"id": 4, "knowledge_type": "law", "title": "中华人民共和国公司法", "article_number": None, "content": "规范公司组织和行为，保护公司合法权益...", "summary": "公司法是规定公司设立、组织、活动的法律", "category": "商事法律", "keywords": "公司法,有限公司,股份公司,股东", "source": "全国人大", "source_url": None, "source_version": "2024.07.01", "effective_date": "2024-07-01", "weight": 90, "is_active": True, "is_vectorized": True, "created_at": "2024-01-01T00:00:00", "updated_at": "2024-07-01T00:00:00"},
    {"id": 5, "knowledge_type": "regulation", "title": "治安管理处罚法", "article_number": None, "content": "维护社会治安秩序，保障公共安全...", "summary": "规定治安违法行为的处罚", "category": "行政法规", "keywords": "治安,处罚,公共安全", "source": "国务院", "source_url": None, "source_version": "2013.01.01", "effective_date": "2013-01-01", "weight": 85, "is_active": True, "is_vectorized": True, "created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00"},
    {"id": 6, "knowledge_type": "interpretation", "title": "最高人民法院关于适用民法典总则编的解释", "article_number": "法释[2022]6号", "content": "为正确适用民法典总则编...", "summary": "民法典总则编的司法解释", "category": "司法解释", "keywords": "司法解释,民法典总则,最高人民法院", "source": "最高人民法院", "source_url": None, "source_version": "2022.03.01", "effective_date": "2022-03-01", "weight": 80, "is_active": True, "is_vectorized": True, "created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00"},
    {"id": 7, "knowledge_type": "case", "title": "张某诉某公司劳动合同纠纷案", "article_number": "(2023)京0105民初12345号", "content": "原告张某与被告某公司签订劳动合同...", "summary": "典型劳动合同纠纷案例", "category": "典型案例", "keywords": "劳动合同,纠纷,案例,违法解除", "source": "北京市朝阳区人民法院", "source_url": None, "source_version": None, "effective_date": "2023-12-01", "weight": 70, "is_active": True, "is_vectorized": True, "created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00"},
    {"id": 8, "knowledge_type": "law", "title": "中华人民共和国个人信息保护法", "article_number": None, "content": "保护个人信息权益，规范个人信息处理活动...", "summary": "保护公民个人信息安全", "category": "民事法律", "keywords": "个人信息,隐私,数据保护", "source": "全国人大", "source_url": None, "source_version": "2021.11.01", "effective_date": "2021-11-01", "weight": 90, "is_active": True, "is_vectorized": False, "created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00"},
    {"id": 9, "knowledge_type": "law", "title": "中华人民共和国消费者权益保护法", "article_number": None, "content": "保护消费者合法权益，维护社会经济秩序...", "summary": "消费者权益保护的法律依据", "category": "民事法律", "keywords": "消费者权益,消法,维权", "source": "全国人大", "source_url": None, "source_version": "2014.03.15", "effective_date": "2014-03-15", "weight": 85, "is_active": True, "is_vectorized": True, "created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00"},
    {"id": 10, "knowledge_type": "law", "title": "中华人民共和国知识产权法", "article_number": None, "content": "保护知识产权，鼓励创新和创造...", "summary": "涵盖著作权、专利权、商标权", "category": "知识产权", "keywords": "知识产权,专利,商标,著作权", "source": "全国人大", "source_url": None, "source_version": "2020.10.17", "effective_date": "2021-06-01", "weight": 85, "is_active": True, "is_vectorized": True, "created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00"},
]

_next_article_id = 11


def _paginate(data: list[dict], page: int, page_size: int) -> dict:
    total = len(data)
    start = (page - 1) * page_size
    items = data[start:start + page_size]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/laws")
async def get_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    knowledge_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
):
    data = list(_mock_articles)
    if knowledge_type:
        data = [a for a in data if a["knowledge_type"] == knowledge_type]
    if category:
        data = [a for a in data if a["category"] == category]
    if keyword:
        kw = keyword.lower()
        data = [a for a in data if kw in a["title"].lower() or kw in (a.get("keywords") or "").lower()]
    if is_active is not None:
        data = [a for a in data if a["is_active"] == is_active]
    return _paginate(data, page, page_size)


@router.post("/laws")
async def create_article(body: CreateArticleBody, db: AsyncSession = Depends(get_db)):
    global _next_article_id
    now = datetime.now().isoformat()
    article = {
        "id": _next_article_id,
        "knowledge_type": body.knowledge_type,
        "title": body.title,
        "article_number": body.article_number,
        "content": body.content,
        "summary": body.summary,
        "category": body.category,
        "keywords": body.keywords,
        "source": body.source,
        "source_url": body.source_url,
        "source_version": body.source_version,
        "effective_date": body.effective_date,
        "weight": body.weight,
        "is_active": body.is_active,
        "is_vectorized": False,
        "created_at": now,
        "updated_at": now,
    }
    _next_article_id += 1
    _mock_articles.append(article)
    try:
        db_article = LegalKnowledge(
            knowledge_type=body.knowledge_type, title=body.title,
            article_number=body.article_number, content=body.content,
            summary=body.summary, category=body.category,
            keywords=body.keywords, source=body.source,
            source_url=body.source_url, source_version=body.source_version,
            effective_date=datetime.fromisoformat(body.effective_date) if body.effective_date else None,
            weight=body.weight, is_active=body.is_active,
        )
        db.add(db_article)
        await db.commit()
    except Exception:
        pass
    return article


@router.get("/laws/{article_id}")
async def get_article(article_id: int):
    for a in _mock_articles:
        if a["id"] == article_id:
            return a
    return {"detail": "知识条目不存在"}


@router.put("/laws/{article_id}")
async def update_article(article_id: int, body: UpdateArticleBody):
    for a in _mock_articles:
        if a["id"] == article_id:
            for field, value in body.model_dump(exclude_none=True).items():
                a[field] = value
            a["updated_at"] = datetime.now().isoformat()
            return a
    return {"detail": "知识条目不存在"}


@router.delete("/laws/{article_id}")
async def delete_article(article_id: int):
    global _mock_articles
    _mock_articles = [a for a in _mock_articles if a["id"] != article_id]
    return {"message": "删除成功"}


@router.get("/laws/distinct-categories")
async def get_distinct_categories():
    categories = list(set(a["category"] for a in _mock_articles))
    return categories


@router.post("/laws/batch-delete")
async def batch_delete(ids: list[int]):
    global _mock_articles
    removed = sum(1 for id in ids if any(a["id"] == id for a in _mock_articles))
    _mock_articles = [a for a in _mock_articles if a["id"] not in ids]
    return {"success_count": removed, "failed_count": 0, "message": f"成功删除{removed}条"}


@router.post("/laws/batch-import")
async def batch_import(items: list[dict], dry_run: bool = False):
    global _next_article_id
    count = 0
    now = datetime.now().isoformat()
    for item in items:
        article = {
            "id": _next_article_id, "knowledge_type": item.get("knowledge_type", "law"),
            "title": item.get("title", ""), "article_number": item.get("article_number"),
            "content": item.get("content"), "summary": item.get("summary"),
            "category": item.get("category", "法律"), "keywords": item.get("keywords"),
            "source": item.get("source"), "source_url": item.get("source_url"),
            "source_version": item.get("source_version"), "effective_date": item.get("effective_date"),
            "weight": item.get("weight", 1), "is_active": item.get("is_active", True),
            "is_vectorized": False, "created_at": now, "updated_at": now,
        }
        if not dry_run:
            _next_article_id += 1
            _mock_articles.append(article)
        count += 1
    return {"success_count": count, "failed_count": 0, "message": f"{'预览' if dry_run else ''}成功导入{count}条"}


@router.post("/laws/{article_id}/vectorize")
async def vectorize_article(article_id: int):
    for a in _mock_articles:
        if a["id"] == article_id:
            a["is_vectorized"] = True
            a["updated_at"] = datetime.now().isoformat()
            return {"message": "向量化成功"}
    return {"detail": "知识条目不存在"}


@router.post("/laws/batch-vectorize")
async def batch_vectorize(ids: list[int]):
    count = 0
    for a in _mock_articles:
        if a["id"] in ids and not a["is_vectorized"]:
            a["is_vectorized"] = True
            a["updated_at"] = datetime.now().isoformat()
            count += 1
    return {"success_count": count, "failed_count": 0, "message": f"成功向量化{count}条"}


@router.post("/sync-vector-store")
async def sync_vector_store():
    count = sum(1 for a in _mock_articles if a["is_vectorized"])
    return {"success_count": count, "failed_count": 0, "message": f"向量库同步完成，共{count}条"}


@router.get("/stats")
async def get_knowledge_stats():
    return {
        "total_laws": sum(1 for a in _mock_articles if a["knowledge_type"] == "law"),
        "total_cases": sum(1 for a in _mock_articles if a["knowledge_type"] == "case"),
        "total_regulations": sum(1 for a in _mock_articles if a["knowledge_type"] == "regulation"),
        "total_interpretations": sum(1 for a in _mock_articles if a["knowledge_type"] == "interpretation"),
        "vectorized_count": sum(1 for a in _mock_articles if a["is_vectorized"]),
        "categories": [{"category": c, "count": sum(1 for a in _mock_articles if a["category"] == c)} for c in set(a["category"] for a in _mock_articles)],
    }