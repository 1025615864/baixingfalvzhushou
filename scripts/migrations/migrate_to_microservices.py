"""
数据库迁移脚本 - 微服务数据同步

此脚本用于在微服务拆分过程中，将主数据库中的数据迁移到各微服务数据库。

使用方式:
    python -m scripts.migrations.migrate_to_microservices --service <service_name>

服务列表:
    - user: 用户服务 (端口 8001)
    - news: 新闻服务 (端口 8006)
    - community: 社区服务 (端口 8007)
    - payment: 支付服务 (端口 8002)
    - points: 积分服务 (端口 8008)
    - notification: 通知服务 (端口 8009)
    - legal: 法律服务 (端口 8004)
"""

import argparse
import asyncio
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 主数据库连接 (遗留单体数据库)
MAIN_DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5432/baixing_main"

# 微服务数据库连接
SERVICE_DATABASES = {
    "user": "postgresql+asyncpg://user:pass@localhost:5432/baixing_user_service",
    "news": "postgresql+asyncpg://user:pass@localhost:5432/baixing_news_service",
    "community": "postgresql+asyncpg://user:pass@localhost:5432/baixing_community_service",
    "payment": "postgresql+asyncpg://user:pass@localhost:5432/baixing_payment_service",
    "points": "postgresql+asyncpg://user:pass@localhost:5432/baixing_points_service",
    "notification": "postgresql+asyncpg://user:pass@localhost:5432/baixing_notification_service",
    "legal": "postgresql+asyncpg://user:pass@localhost:5432/baixing_legal_service",
}


class MigrationService:
    """数据迁移服务基类"""
    
    def __init__(self, main_db: AsyncSession, service_db: AsyncSession):
        self.main_db = main_db
        self.service_db = service_db
    
    async def migrate(self) -> dict[str, int]:
        """执行迁移，返回迁移统计"""
        raise NotImplementedError


class UserMigration(MigrationService):
    """用户数据迁移"""
    
    async def migrate(self) -> dict[str, int]:
        stats = {"users": 0, "user_quotas": 0, "user_profiles": 0}
        
        # 迁移用户数据
        result = await self.main_db.execute(text("SELECT * FROM users LIMIT 1000"))
        users = result.fetchall()
        
        for user in users:
            await self.service_db.execute(
                text("""
                    INSERT INTO users (id, username, email, phone, password_hash, role, 
                                     is_active, created_at, updated_at)
                    VALUES (:id, :username, :email, :phone, :password_hash, :role,
                            :is_active, :created_at, :updated_at)
                    ON CONFLICT (id) DO UPDATE SET
                        email = EXCLUDED.email,
                        phone = EXCLUDED.phone
                """),
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "phone": user.phone,
                    "password_hash": user.password_hash,
                    "role": user.role,
                    "is_active": user.is_active,
                    "created_at": user.created_at,
                    "updated_at": user.updated_at,
                }
            )
            stats["users"] += 1
        
        await self.service_db.commit()
        logger.info(f"用户迁移完成: {stats}")
        return stats


class NewsMigration(MigrationService):
    """新闻数据迁移"""
    
    async def migrate(self) -> dict[str, int]:
        stats = {"news": 0, "news_comments": 0, "news_topics": 0}
        
        # 检查新闻表是否存在
        result = await self.main_db.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'news')")
        )
        if not result.scalar():
            logger.warning("主数据库中不存在 news 表，跳过新闻迁移")
            return stats
        
        # 迁移新闻数据
        result = await self.main_db.execute(text("SELECT * FROM news LIMIT 1000"))
        news_items = result.fetchall()
        
        for item in news_items:
            await self.service_db.execute(
                text("""
                    INSERT INTO news (id, title, content, summary, category, tags, 
                                     author, cover_image, status, view_count, like_count,
                                     published_at, created_at, updated_at)
                    VALUES (:id, :title, :content, :summary, :category, :tags,
                            :author, :cover_image, :status, :view_count, :like_count,
                            :published_at, :created_at, :updated_at)
                    ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        view_count = EXCLUDED.view_count
                """),
                {
                    "id": item.id,
                    "title": item.title,
                    "content": item.content,
                    "summary": getattr(item, 'summary', None),
                    "category": getattr(item, 'category', 'general'),
                    "tags": getattr(item, 'tags', '[]'),
                    "author": getattr(item, 'author', None),
                    "cover_image": getattr(item, 'cover_image', None),
                    "status": getattr(item, 'status', 'draft'),
                    "view_count": getattr(item, 'view_count', 0),
                    "like_count": getattr(item, 'like_count', 0),
                    "published_at": getattr(item, 'published_at', None),
                    "created_at": getattr(item, 'created_at', datetime.utcnow()),
                    "updated_at": getattr(item, 'updated_at', datetime.utcnow()),
                }
            )
            stats["news"] += 1
        
        await self.service_db.commit()
        logger.info(f"新闻迁移完成: {stats}")
        return stats


class CommunityMigration(MigrationService):
    """社区数据迁移"""
    
    async def migrate(self) -> dict[str, int]:
        stats = {"posts": 0, "comments": 0}
        
        # 检查论坛表是否存在
        result = await self.main_db.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'forum_posts')")
        )
        if not result.scalar():
            logger.warning("主数据库中不存在 forum_posts 表，跳过社区迁移")
            return stats
        
        # 迁移帖子数据
        result = await self.main_db.execute(text("SELECT * FROM forum_posts LIMIT 1000"))
        posts = result.fetchall()
        
        for post in posts:
            await self.service_db.execute(
                text("""
                    INSERT INTO posts (id, user_id, title, content, category, 
                                     view_count, like_count, comment_count,
                                     is_pinned, is_hot, is_deleted, created_at, updated_at)
                    VALUES (:id, :user_id, :title, :content, :category,
                            :view_count, :like_count, :comment_count,
                            :is_pinned, :is_hot, :is_deleted, :created_at, :updated_at)
                    ON CONFLICT (id) DO UPDATE SET
                        view_count = EXCLUDED.view_count,
                        like_count = EXCLUDED.like_count
                """),
                {
                    "id": post.id,
                    "user_id": post.user_id,
                    "title": post.title,
                    "content": post.content,
                    "category": getattr(post, 'category', None),
                    "view_count": getattr(post, 'view_count', 0),
                    "like_count": getattr(post, 'like_count', 0),
                    "comment_count": getattr(post, 'comment_count', 0),
                    "is_pinned": getattr(post, 'is_pinned', False),
                    "is_hot": getattr(post, 'is_hot', False),
                    "is_deleted": getattr(post, 'is_deleted', False),
                    "created_at": post.created_at,
                    "updated_at": getattr(post, 'updated_at', post.created_at),
                }
            )
            stats["posts"] += 1
        
        await self.service_db.commit()
        logger.info(f"社区迁移完成: {stats}")
        return stats


class NotificationMigration(MigrationService):
    """通知数据迁移"""
    
    async def migrate(self) -> dict[str, int]:
        stats = {"notifications": 0}
        
        # 检查通知表是否存在
        result = await self.main_db.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'notifications')")
        )
        if not result.scalar():
            logger.warning("主数据库中不存在 notifications 表，跳过通知迁移")
            return stats
        
        # 迁移通知数据
        result = await self.main_db.execute(text("SELECT * FROM notifications LIMIT 1000"))
        notifications = result.fetchall()
        
        for notif in notifications:
            await self.service_db.execute(
                text("""
                    INSERT INTO notifications (id, user_id, type, title, content, 
                                             is_read, link, dedupe_key, related_user_id,
                                             related_post_id, related_comment_id,
                                             created_at, read_at)
                    VALUES (:id, :user_id, :type, :title, :content,
                            :is_read, :link, :dedupe_key, :related_user_id,
                            :related_post_id, :related_comment_id,
                            :created_at, :read_at)
                    ON CONFLICT (id) DO UPDATE SET
                        is_read = EXCLUDED.is_read
                """),
                {
                    "id": notif.id,
                    "user_id": notif.user_id,
                    "type": notif.type,
                    "title": notif.title,
                    "content": getattr(notif, 'content', None),
                    "is_read": getattr(notif, 'is_read', False),
                    "link": getattr(notif, 'link', None),
                    "dedupe_key": getattr(notif, 'dedupe_key', None),
                    "related_user_id": getattr(notif, 'related_user_id', None),
                    "related_post_id": getattr(notif, 'related_post_id', None),
                    "related_comment_id": getattr(notif, 'related_comment_id', None),
                    "created_at": notif.created_at,
                    "read_at": getattr(notif, 'read_at', None),
                }
            )
            stats["notifications"] += 1
        
        await self.service_db.commit()
        logger.info(f"通知迁移完成: {stats}")
        return stats


MIGRATION_SERVICES = {
    "user": UserMigration,
    "news": NewsMigration,
    "community": CommunityMigration,
    "notification": NotificationMigration,
}


async def run_migration(service_name: str) -> dict[str, int]:
    """运行指定服务的迁移"""
    if service_name not in SERVICE_DATABASES:
        raise ValueError(f"未知服务: {service_name}. 可用服务: {list(SERVICE_DATABASES.keys())}")
    
    if service_name not in MIGRATION_SERVICES:
        logger.warning(f"暂不支持迁移服务: {service_name}")
        return {}
    
    main_engine = create_async_engine(MAIN_DATABASE_URL, echo=False)
    service_engine = create_async_engine(SERVICE_DATABASES[service_name], echo=False)
    
    async with main_engine.connect() as main_conn, service_engine.connect() as service_conn:
        main_session = AsyncSession(main_conn)
        service_session = AsyncSession(service_conn)
        
        migration_class = MIGRATION_SERVICES[service_name]
        migration = migration_class(main_session, service_session)
        
        stats = await migration.migrate()
        
        await main_session.close()
        await service_session.close()
    
    await main_engine.dispose()
    await service_engine.dispose()
    
    return stats


async def main():
    parser = argparse.ArgumentParser(description="微服务数据迁移工具")
    parser.add_argument(
        "--service", 
        "-s", 
        required=True,
        choices=list(SERVICE_DATABASES.keys()),
        help="目标服务名称"
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="列出所有可用服务"
    )
    
    args = parser.parse_args()
    
    if args.list:
        print("可用服务:")
        for service in SERVICE_DATABASES:
            print(f"  - {service}")
        return
    
    logger.info(f"开始迁移服务: {args.service}")
    stats = await run_migration(args.service)
    logger.info(f"迁移完成: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
