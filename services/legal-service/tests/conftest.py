"""pytest 配置"""
import pytest
import asyncio
from typing import AsyncGenerator

from app.main import app
from app.database import AsyncSessionLocal, engine, Base


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_database():
    """创建测试数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
async def client():
    """获取测试客户端"""
    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client