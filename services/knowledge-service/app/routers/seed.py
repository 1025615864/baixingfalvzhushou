"""种子数据初始化API"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional

try:
    from services.common.middleware.rate_limit import check_seed_rate_limit
except ImportError:
    def check_seed_rate_limit(*args, **kwargs):
        return True, 999

router = APIRouter(prefix="/api/v1/admin", tags=["系统管理"])


class SeedStatus(BaseModel):
    knowledge_seeded: bool
    guide_cases_seeded: bool
    categories_seeded: bool


class SeedResult(BaseModel):
    success: bool
    items_created: int
    message: str


@router.get("/seed/status", response_model=SeedStatus)
async def get_seed_status():
    """获取种子数据初始化状态"""
    from app.database import engine
    from sqlalchemy import text

    with engine.connect() as conn:
        knowledge_count = conn.execute(
            text("SELECT COUNT(*) FROM legal_knowledge WHERE source = '官方发布'")
        ).scalar()

        guide_case_count = conn.execute(
            text("SELECT COUNT(*) FROM legal_case WHERE is_guiding_case = true")
        ).scalar()

        category_count = conn.execute(
            text("SELECT COUNT(*) FROM knowledge_category")
        ).scalar()

    return SeedStatus(
        knowledge_seeded=knowledge_count > 0,
        guide_cases_seeded=guide_case_count > 0,
        categories_seeded=category_count > 0
    )


@router.post("/seed/knowledge", response_model=SeedResult)
async def seed_knowledge(force: bool = False, http_request: Request = None):
    """初始化法律知识种子数据"""
    if http_request:
        client_id = http_request.client.host if http_request.client else "unknown"
        is_allowed, remaining = check_seed_rate_limit(client_id)
        if not is_allowed:
            raise HTTPException(status_code=429, detail="种子数据操作限流，请稍后再试")

    from app.database import SessionLocal
    from app.models.knowledge import LegalKnowledge
    from app.services.knowledge_vector_store import index_knowledge
    from app.seed_data.legal_knowledge import LEGAL_KNOWLEDGE_SEED_DATA

    db = SessionLocal()
    try:
        existing = db.query(LegalKnowledge).filter(
            LegalKnowledge.source == "官方发布"
        ).count()

        if existing > 0 and not force:
            return SeedResult(
                success=True,
                items_created=0,
                message=f"知识数据已存在 ({existing} 条)，如需重新初始化请使用 force=true"
            )

        created = 0
        for item in LEGAL_KNOWLEDGE_SEED_DATA:
            existing_k = db.query(LegalKnowledge).filter(
                LegalKnowledge.title == item["title"]
            ).first()

            if existing_k and not force:
                continue

            if existing_k and force:
                for key, value in item.items():
                    setattr(existing_k, key, value)
                existing_k.status = "published"
                db.merge(existing_k)
            else:
                knowledge = LegalKnowledge(**item, status="published")
                db.add(knowledge)
            created += 1

        db.commit()

        for item in LEGAL_KNOWLEDGE_SEED_DATA[:3]:
            try:
                index_knowledge(
                    doc_id=str(created),
                    content=item["content"],
                    metadata={"title": item["title"], "category": item["category"]}
                )
            except Exception:
                logger.exception("Failed to seed knowledge data")

        return SeedResult(
            success=True,
            items_created=created,
            message=f"成功初始化 {created} 条法律知识"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/seed/guide-cases", response_model=SeedResult)
async def seed_guide_cases(force: bool = False):
    """初始化指导性案例种子数据"""
    from app.database import SessionLocal
    from app.models.archive import LegalCase
    from app.services.archive_vector_store import index_case
    from app.seed_data.legal_knowledge import GUIDE_CASES_SEED_DATA

    db = SessionLocal()
    try:
        existing = db.query(LegalCase).filter(
            LegalCase.is_guiding_case == True
        ).count()

        if existing > 0 and not force:
            return SeedResult(
                success=True,
                items_created=0,
                message=f"指导性案例已存在 ({existing} 条)，如需重新初始化请使用 force=true"
            )

        created = 0
        for item in GUIDE_CASES_SEED_DATA:
            existing_case = db.query(LegalCase).filter(
                LegalCase.case_number == item["case_number"]
            ).first()

            if existing_case and not force:
                continue

            if existing_case and force:
                for key, value in item.items():
                    setattr(existing_case, key, value)
                existing_case.status = "published"
                db.merge(existing_case)
            else:
                case = LegalCase(**item, status="published")
                db.add(case)
            created += 1

        db.commit()

        return SeedResult(
            success=True,
            items_created=created,
            message=f"成功初始化 {created} 条指导性案例"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/seed/categories")
async def seed_categories(http_request: Request = None):
    """初始化分类数据"""
    if http_request:
        client_id = http_request.client.host if http_request.client else "unknown"
        is_allowed, remaining = check_seed_rate_limit(client_id)
        if not is_allowed:
            raise HTTPException(status_code=429, detail="种子数据操作限流，请稍后再试")

    from app.database import SessionLocal
    from app.models.knowledge import KnowledgeCategory

    db = SessionLocal()
    try:
        categories = [
            {"name": "民法", "code": "civil", "description": "民事法律相关知识"},
            {"name": "刑法", "code": "criminal", "description": "刑事法律相关知识"},
            {"name": "劳动法", "code": "labor", "description": "劳动法律相关知识"},
            {"name": "公司法", "code": "company", "description": "公司法律相关知识"},
            {"name": "婚姻法", "code": "marriage", "description": "婚姻家庭相关知识"},
            {"name": "消费者权益", "code": "consumer", "description": "消费者权益保护相关"},
            {"name": "交通事故", "code": "traffic", "description": "交通事故处理相关"},
            {"name": "房产", "code": "property", "description": "房产相关法律知识"},
            {"name": "知识产权", "code": "ip", "description": "知识产权相关知识"},
            {"name": "行政法", "code": "administrative", "description": "行政法律相关知识"},
        ]

        created = 0
        for cat in categories:
            existing = db.query(KnowledgeCategory).filter(
                KnowledgeCategory.code == cat["code"]
            ).first()

            if not existing:
                db.add(KnowledgeCategory(**cat))
                created += 1

        db.commit()

        return {"success": True, "categories_created": created, "message": f"成功初始化 {created} 个分类"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/seed/all")
async def seed_all(http_request: Request = None):
    """初始化所有种子数据"""
    if http_request:
        client_id = http_request.client.host if http_request.client else "unknown"
        is_allowed, remaining = check_seed_rate_limit(client_id)
        if not is_allowed:
            raise HTTPException(status_code=429, detail="种子数据操作限流，请稍后再试")

    result = {"knowledge": None, "guide_cases": None, "categories": None}

    try:
        knowledge_result = await seed_knowledge()
        result["knowledge"] = knowledge_result.dict()
    except Exception as e:
        result["knowledge"] = {"success": False, "message": str(e)}

    try:
        categories_result = await seed_categories()
        result["categories"] = categories_result
    except Exception as e:
        result["categories"] = {"success": False, "message": str(e)}

    try:
        guide_cases_result = await seed_guide_cases()
        result["guide_cases"] = guide_cases_result.dict()
    except Exception as e:
        result["guide_cases"] = {"success": False, "message": str(e)}

    return result
