"""pytest配置文件"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.config.settings import get_settings
import app.models  # noqa: F401 - Required to register models with Base.metadata
import app.models_ai  # noqa: F401 - Required to register AI models with Base.metadata
from app.database import Base

settings = get_settings()

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool,
    echo=False,
    connect_args={"check_same_thread": False},
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def app():
    """创建测试应用"""
    from app.main import create_app
    application = create_app()
    yield application


@pytest.fixture
def test_user_data():
    """测试用户数据"""
    return {
        "phone": "13800138000",
        "password": "Test1234",
        "username": "testuser",
    }


@pytest.fixture
def test_admin_data():
    """测试管理员数据"""
    return {
        "phone": "13900139000",
        "password": "Admin1234",
        "role": "admin",
    }
