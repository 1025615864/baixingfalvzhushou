"""初始化数据库表结构

此脚本用于手动创建数据库表，适用于开发环境或初始部署。
生产环境应使用 Alembic 迁移。
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base
from app.models import Post, Comment, PostLike, PostFavorite, PostTag, Report, Topic, BestAnswer


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("所有数据库表已创建成功!")


async def drop_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("所有数据库表已删除!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--drop":
        asyncio.run(drop_tables())
    else:
        asyncio.run(create_tables())
