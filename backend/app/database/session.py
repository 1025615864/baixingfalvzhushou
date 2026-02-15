"""数据库会话管理"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from .engine import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话
    
    用作 FastAPI 依赖，每次请求创建一个新的数据库会话，
    请求结束后自动关闭。
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
