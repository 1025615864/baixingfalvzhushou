"""
Income测试专用配置
避免导入main.py以解决依赖问题
"""
import pytest
import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.models.settlement import LawyerWallet, LawyerIncomeRecord
from app.models.lawfirm import Lawyer, LawyerConsultation
from app.models.payment import PaymentOrder
from app.models.user import User

# 使用SQLite进行测试
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


@pytest.fixture(scope="function")
async def db():
    """创建测试数据库会话"""
    from app.models import Base
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# 创建测试用户
@pytest.fixture
async def test_user(db: AsyncSession):
    """创建测试用户"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed",
        is_active=True,
        role="user",
        phone="13800138000",
        nickname="测试用户",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# 创建测试律师
@pytest.fixture
async def test_lawyer(db: AsyncSession, test_user: User):
    """创建测试律师"""
    lawyer = Lawyer(
        user_id=test_user.id,
        name="测试律师",
        phone="13800138000",
        license_no="LIC123456",
        specialization=["民法", "刑法"],
        experience_years=5,
        rating=4.5,
        is_verified=True,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(lawyer)
    await db.commit()
    await db.refresh(lawyer)
    return lawyer