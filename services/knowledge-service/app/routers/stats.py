"""知识库统计API"""
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.config.settings import get_settings
from app.database import Base

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

router = APIRouter(prefix="/api/v1/knowledge", tags=["知识库统计"])


class CategoryStats(BaseModel):
    name: str
    count: int
    percentage: float


class KnowledgeStats(BaseModel):
    total_count: int
    vectorized_count: int
    active_count: int
    category_stats: list[CategoryStats]
    type_stats: dict


class KnowledgeItem(BaseModel):
    id: int
    knowledge_type: str
    title: str
    article_number: Optional[str]
    category: Optional[str]
    keywords: Optional[str]
    is_vectorized: bool
    created_at: str


class KnowledgeListResponse(BaseModel):
    items: list[KnowledgeItem]
    total: int
    page: int
    page_size: int


class VectorStoreInfo(BaseModel):
    collection_name: str
    embedding_model: str
    total_vectors: int
    path: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/stats", response_model=KnowledgeStats)
async def get_knowledge_stats():
    """获取知识库统计信息"""
    from app.models.knowledge import LegalKnowledge, KnowledgeCategory

    db = SessionLocal()
    try:
        total_result = db.execute(select(func.count()).select_from(LegalKnowledge)).scalar()
        vectorized_result = db.execute(
            select(func.count()).select_from(LegalKnowledge).where(LegalKnowledge.is_vectorized == True)
        ).scalar()
        active_result = db.execute(
            select(func.count()).select_from(LegalKnowledge).where(LegalKnowledge.is_active == True)
        ).scalar()

        category_results = db.execute(
            select(
                LegalKnowledge.category,
                func.count(LegalKnowledge.id).label("count")
            ).group_by(LegalKnowledge.category)
        ).all()

        category_stats = []
        for row in category_results:
            if row[0]:
                category_stats.append(CategoryStats(
                    name=row[0],
                    count=row[1],
                    percentage=round(row[1] / total_result * 100, 2) if total_result > 0 else 0
                ))

        type_results = db.execute(
            select(
                LegalKnowledge.knowledge_type,
                func.count(LegalKnowledge.id).label("count")
            ).group_by(LegalKnowledge.knowledge_type)
        ).all()

        type_stats = {row[0]: row[1] for row in type_results if row[0]}

        return KnowledgeStats(
            total_count=total_result or 0,
            vectorized_count=vectorized_result or 0,
            active_count=active_result or 0,
            category_stats=category_stats,
            type_stats=type_stats
        )
    finally:
        db.close()


@router.get("/vector-info", response_model=VectorStoreInfo)
async def get_vector_store_info():
    """获取向量库信息"""
    try:
        import chromadb
        from app.services.knowledge_vector_store import ChineseEmbeddingFunction

        client = chromadb.PersistentClient(path=settings.vector_store_path)
        collection = client.get_or_create_collection(
            name="knowledge_laws",
            embedding_function=ChineseEmbeddingFunction()
        )

        return VectorStoreInfo(
            collection_name="knowledge_laws",
            embedding_model=settings.embedding_model,
            total_vectors=collection.count(),
            path=settings.vector_store_path
        )
    except Exception as e:
        return VectorStoreInfo(
            collection_name="knowledge_laws",
            embedding_model=settings.embedding_model,
            total_vectors=0,
            path=settings.vector_store_path
        )


@router.get("/list", response_model=KnowledgeListResponse)
async def list_knowledge(
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    knowledge_type: Optional[str] = None,
    is_vectorized: Optional[bool] = None
):
    """获取知识列表"""
    from app.models.knowledge import LegalKnowledge

    db = SessionLocal()
    try:
        query = select(LegalKnowledge)

        if category:
            query = query.where(LegalKnowledge.category == category)
        if knowledge_type:
            query = query.where(LegalKnowledge.knowledge_type == knowledge_type)
        if is_vectorized is not None:
            query = query.where(LegalKnowledge.is_vectorized == is_vectorized)

        total_result = db.execute(select(func.count()).select_from(query.subquery())).scalar()

        query = query.order_by(LegalKnowledge.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        results = db.execute(query).all()

        items = []
        for row in results:
            items.append(KnowledgeItem(
                id=row[0],
                knowledge_type=row[1],
                title=row[2],
                article_number=row[3],
                category=row[5],
                keywords=row[6],
                is_vectorized=row[8],
                created_at=row[10].isoformat() if hasattr(row[10], 'isoformat') else str(row[10])
            ))

        return KnowledgeListResponse(
            items=items,
            total=total_result or 0,
            page=page,
            page_size=page_size
        )
    finally:
        db.close()


@router.get("/categories")
async def get_categories():
    """获取知识分类列表"""
    from app.models.knowledge import KnowledgeCategory

    db = SessionLocal()
    try:
        results = db.execute(
            select(KnowledgeCategory).where(KnowledgeCategory.is_active == True).order_by(KnowledgeCategory.sort_order)
        ).all()

        categories = []
        for row in results:
            count_result = db.execute(
                select(func.count()).select_from(LegalKnowledge).where(LegalKnowledge.category == row[1])
            ).scalar()
            categories.append({
                "id": row[0],
                "name": row[1],
                "description": row[3],
                "count": count_result or 0
            })

        return {"categories": categories}
    finally:
        db.close()