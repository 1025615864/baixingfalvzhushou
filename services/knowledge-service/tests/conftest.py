import pytest
from datetime import datetime
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.models.knowledge import Base, LegalKnowledge
from app.routers.knowledge import (
    KnowledgeCreateRequest,
    KnowledgeUpdateRequest,
    router as knowledge_router,
)
from app.database import get_db
from fastapi import FastAPI


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_knowledge_request() -> KnowledgeCreateRequest:
    return KnowledgeCreateRequest(
        knowledge_type="law",
        title="测试知识标题",
        article_number="第123条",
        content="这是测试内容，包含了详细的法律条款描述。",
        summary="这是一个测试知识的摘要",
        category="劳动法",
        keywords="劳动,合同,测试",
        source="测试来源",
        effective_date=datetime.now(),
        expiry_date=None,
        law_number="TEST-2024-001",
        jurisdiction="中国",
        weight=1,
        created_by=1,
        metadata={"test": True}
    )


@pytest.fixture
def sample_knowledge(db_session: Session, sample_knowledge_request: KnowledgeCreateRequest) -> LegalKnowledge:
    from app.services.knowledge_service import KnowledgeService
    service = KnowledgeService(db_session)
    knowledge = service.create_knowledge(sample_knowledge_request)
    return knowledge


@pytest.fixture
def app() -> FastAPI:
    from app.main import app as main_app
    return main_app


@pytest.fixture
def client(app: FastAPI, db_session: Session) -> TestClient:
    def get_db_override():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = get_db_override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def published_knowledge(db_session: Session, sample_knowledge: LegalKnowledge) -> LegalKnowledge:
    from app.services.knowledge_service import KnowledgeService
    import asyncio

    async def publish():
        service = KnowledgeService(db_session)
        return await service.publish_knowledge(sample_knowledge.id, reviewed_by=1)

    knowledge = asyncio.get_event_loop().run_until_complete(publish())
    return knowledge
