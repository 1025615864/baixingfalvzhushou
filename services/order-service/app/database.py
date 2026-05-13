"""数据库配置"""
import logging
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

logger = logging.getLogger(__name__)

database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/order.db")

engine = create_async_engine(database_url, echo=False)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    """ORM 基础类"""
    pass


async def get_db():
    """获取数据库会话"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            logger.exception("Database session error, rolling back")
            await session.rollback()
            raise
        finally:
            await session.close()
