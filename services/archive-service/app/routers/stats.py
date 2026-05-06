"""档案库统计API"""
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.config.settings import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

router = APIRouter(prefix="/api/v1/archive", tags=["档案库统计"])


class CaseTypeStats(BaseModel):
    name: str
    count: int
    percentage: float


class ArchiveStats(BaseModel):
    total_cases: int
    published_cases: int
    vectorized_cases: int
    case_type_stats: list[CaseTypeStats]
    category_stats: dict
    total_views: int


class CaseItem(BaseModel):
    id: int
    case_number: Optional[str]
    case_type: str
    title: str
    category: Optional[str]
    keywords: Optional[str]
    court: Optional[str]
    judge_date: Optional[str]
    is_published: bool
    is_vectorized: bool
    view_count: int
    created_at: str


class CaseListResponse(BaseModel):
    items: list[CaseItem]
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


@router.get("/stats", response_model=ArchiveStats)
async def get_archive_stats():
    """获取档案库统计信息"""
    from app.models.archive import LegalCase, CaseCategory

    db = SessionLocal()
    try:
        total_result = db.execute(select(func.count()).select_from(LegalCase)).scalar()
        published_result = db.execute(
            select(func.count()).select_from(LegalCase).where(LegalCase.is_published == True)
        ).scalar()
        vectorized_result = db.execute(
            select(func.count()).select_from(LegalCase).where(LegalCase.is_vectorized == True)
        ).scalar()
        views_result = db.execute(
            select(func.sum(LegalCase.view_count)).select_from(LegalCase)
        ).scalar()

        case_type_results = db.execute(
            select(
                LegalCase.case_type,
                func.count(LegalCase.id).label("count")
            ).group_by(LegalCase.case_type)
        ).all()

        case_type_stats = []
        for row in case_type_results:
            if row[0]:
                case_type_stats.append(CaseTypeStats(
                    name=row[0],
                    count=row[1],
                    percentage=round(row[1] / total_result * 100, 2) if total_result > 0 else 0
                ))

        category_results = db.execute(
            select(
                LegalCase.category,
                func.count(LegalCase.id).label("count")
            ).group_by(LegalCase.category)
        ).all()

        category_stats = {row[0]: row[1] for row in category_results if row[0]}

        return ArchiveStats(
            total_cases=total_result or 0,
            published_cases=published_result or 0,
            vectorized_cases=vectorized_result or 0,
            case_type_stats=case_type_stats,
            category_stats=category_stats,
            total_views=views_result or 0
        )
    finally:
        db.close()


@router.get("/vector-info", response_model=VectorStoreInfo)
async def get_vector_store_info():
    """获取向量库信息"""
    try:
        import chromadb
        from app.services.archive_vector_store import ChineseEmbeddingFunction

        client = chromadb.PersistentClient(path=settings.vector_store_path)
        collection = client.get_or_create_collection(
            name="archive_cases",
            embedding_function=ChineseEmbeddingFunction()
        )

        return VectorStoreInfo(
            collection_name="archive_cases",
            embedding_model=settings.embedding_model,
            total_vectors=collection.count(),
            path=settings.vector_store_path
        )
    except Exception as e:
        return VectorStoreInfo(
            collection_name="archive_cases",
            embedding_model=settings.embedding_model,
            total_vectors=0,
            path=settings.vector_store_path
        )


@router.get("/list", response_model=CaseListResponse)
async def list_cases(
    page: int = 1,
    page_size: int = 20,
    case_type: Optional[str] = None,
    category: Optional[str] = None,
    is_published: Optional[bool] = None
):
    """获取案例列表"""
    from app.models.archive import LegalCase

    db = SessionLocal()
    try:
        query = select(LegalCase)

        if case_type:
            query = query.where(LegalCase.case_type == case_type)
        if category:
            query = query.where(LegalCase.category == category)
        if is_published is not None:
            query = query.where(LegalCase.is_published == is_published)

        total_result = db.execute(select(func.count()).select_from(query.subquery())).scalar()

        query = query.order_by(LegalCase.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        results = db.execute(query).all()

        items = []
        for row in results:
            items.append(CaseItem(
                id=row[0],
                case_number=row[1],
                case_type=row[2],
                title=row[3],
                category=row[7],
                keywords=row[8],
                court=row[9],
                judge_date=row[10].isoformat() if row[10] and hasattr(row[10], 'isoformat') else None,
                is_published=row[11],
                is_vectorized=row[12],
                view_count=row[14],
                created_at=row[15].isoformat() if hasattr(row[15], 'isoformat') else str(row[15])
            ))

        return CaseListResponse(
            items=items,
            total=total_result or 0,
            page=page,
            page_size=page_size
        )
    finally:
        db.close()


@router.get("/categories")
async def get_categories():
    """获取案例分类列表"""
    from app.models.archive import CaseCategory

    db = SessionLocal()
    try:
        results = db.execute(
            select(CaseCategory).where(CaseCategory.is_active == True).order_by(CaseCategory.sort_order)
        ).all()

        categories = []
        for row in results:
            count_result = db.execute(
                select(func.count()).select_from(LegalCase).where(LegalCase.category == row[1])
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


@router.get("/case-types")
async def get_case_types():
    """获取案例类型统计"""
    from app.models.archive import LegalCase

    db = SessionLocal()
    try:
        results = db.execute(
            select(
                LegalCase.case_type,
                func.count(LegalCase.id).label("count")
            ).group_by(LegalCase.case_type)
        ).all()

        case_types = [
            {"name": row[0], "count": row[1]}
            for row in results if row[0]
        ]

        return {"case_types": case_types}
    finally:
        db.close()