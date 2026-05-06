"""测试配置和 fixtures"""
import os
import sys
import pytest
from datetime import datetime
from typing import Generator
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["KAFKA_ENABLED"] = "false"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.models.archive import Base, LegalCase
from app.routers.archive import CaseCreateRequest, router


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """SQLite 内存数据库 session fixture"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_case_request() -> CaseCreateRequest:
    """示例案例创建请求数据"""
    return CaseCreateRequest(
        case_number="(2024)穗中法民初字第123号",
        case_type="civil",
        title="测试案例标题",
        facts="测试事实描述",
        legal_basis="《中华人民共和国民法典》第123条",
        judgment="测试判决",
        result="测试结果",
        category="合同纠纷",
        keywords="测试,案例",
        court="广州市中级人民法院",
        court_level="中院",
        judge_date=datetime(2024, 1, 15),
        cause_of_action="合同纠纷",
        judgment_result="胜诉",
        key_points="测试关键要点",
        applicable_laws="民法典",
        source="测试来源",
        source_url="https://example.com",
        is_guiding_case=False,
        effective_date=datetime(2024, 2, 1),
        weight=1,
        created_by=1,
        metadata={"test": True}
    )


@pytest.fixture
def sample_case(db_session: Session, sample_case_request: CaseCreateRequest) -> LegalCase:
    """创建示例案例并存入数据库"""
    from app.services.archive_service import ArchiveService
    service = ArchiveService(db_session)
    return service.create_case(sample_case_request)


@pytest.fixture
def get_db_override(db_session: Session):
    """用于覆盖 FastAPI 依赖的 get_db 函数"""
    def _override():
        try:
            yield db_session
        finally:
            pass
    return _override


@pytest.fixture
def client(get_db_override) -> TestClient:
    """FastAPI TestClient fixture"""
    from app.main import app
    from app.database import get_db
    app.dependency_overrides[get_db] = get_db_override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
