"""数据库表结构自修复功能"""
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from .engine import engine

logger = logging.getLogger(__name__)


async def _apply_sqlite_migrations(conn: AsyncConnection) -> None:
    """应用 SQLite 特定的迁移修复"""
    # 获取所有表
    tables_result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
    tables = {row[0] for row in tables_result.fetchall()}
    
    # News 表修复
    if "news" in tables:
        news_cols_result = await conn.execute(text("PRAGMA table_info(news)"))
        news_cols = {row[1] for row in news_cols_result.fetchall()}
        
        if "scheduled_publish_at" not in news_cols:
            await conn.execute(text("ALTER TABLE news ADD COLUMN scheduled_publish_at DATETIME"))
        if "scheduled_unpublish_at" not in news_cols:
            await conn.execute(text("ALTER TABLE news ADD COLUMN scheduled_unpublish_at DATETIME"))
        if "source_url" not in news_cols:
            await conn.execute(text("ALTER TABLE news ADD COLUMN source_url VARCHAR(500)"))
        if "dedupe_hash" not in news_cols:
            await conn.execute(text("ALTER TABLE news ADD COLUMN dedupe_hash VARCHAR(40)"))
            try:
                await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_news_dedupe_hash ON news(dedupe_hash)"))
            except Exception:
                logger.exception("创建news dedupe_hash索引失败")
        if "source_site" not in news_cols:
            await conn.execute(text("ALTER TABLE news ADD COLUMN source_site VARCHAR(100)"))
        if "review_status" not in news_cols:
            await conn.execute(text("ALTER TABLE news ADD COLUMN review_status VARCHAR(20) DEFAULT 'approved'"))
        if "review_reason" not in news_cols:
            await conn.execute(text("ALTER TABLE news ADD COLUMN review_reason VARCHAR(200)"))
        if "reviewed_at" not in news_cols:
            await conn.execute(text("ALTER TABLE news ADD COLUMN reviewed_at DATETIME"))
    
    # Legal knowledge 表修复
    if "legal_knowledge" in tables:
        lk_cols_result = await conn.execute(text("PRAGMA table_info(legal_knowledge)"))
        lk_cols = {row[1] for row in lk_cols_result.fetchall()}
        if "source_url" not in lk_cols:
            await conn.execute(text("ALTER TABLE legal_knowledge ADD COLUMN source_url VARCHAR(500)"))
        if "source_version" not in lk_cols:
            await conn.execute(text("ALTER TABLE legal_knowledge ADD COLUMN source_version VARCHAR(50)"))
        if "source_hash" not in lk_cols:
            await conn.execute(text("ALTER TABLE legal_knowledge ADD COLUMN source_hash VARCHAR(64)"))
        if "ingest_batch_id" not in lk_cols:
            await conn.execute(text("ALTER TABLE legal_knowledge ADD COLUMN ingest_batch_id VARCHAR(36)"))
        try:
            await conn.execute(
                text("CREATE INDEX IF NOT EXISTS ix_legal_knowledge_source_hash ON legal_knowledge(source_hash)")
            )
            await conn.execute(
                text("CREATE INDEX IF NOT EXISTS ix_legal_knowledge_ingest_batch_id ON legal_knowledge(ingest_batch_id)")
            )
        except Exception:
            logger.exception("创建 legal_knowledge 索引失败")
    
    # Generated documents 表修复
    if "generated_documents" in tables:
        docs_cols_result = await conn.execute(text("PRAGMA table_info(generated_documents)"))
        docs_cols = {row[1] for row in docs_cols_result.fetchall()}
        if "template_key" not in docs_cols:
            await conn.execute(text("ALTER TABLE generated_documents ADD COLUMN template_key VARCHAR(50)"))
        if "template_version" not in docs_cols:
            await conn.execute(text("ALTER TABLE generated_documents ADD COLUMN template_version INTEGER"))
        try:
            await conn.execute(
                text("CREATE INDEX IF NOT EXISTS ix_generated_documents_template_key ON generated_documents(template_key)")
            )
        except Exception:
            logger.exception("创建generated_documents模板索引失败")
    
    # Payment callback events 表修复
    if "payment_callback_events" not in tables:
        await conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS payment_callback_events "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, provider VARCHAR(20) NOT NULL, "
                "order_no VARCHAR(64), trade_no VARCHAR(100), amount FLOAT, amount_cents INTEGER, "
                "verified BOOLEAN DEFAULT 0, error_message VARCHAR(200), raw_payload TEXT, "
                "raw_payload_hash VARCHAR(64), source_ip VARCHAR(45), user_agent VARCHAR(512), "
                "created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
            )
        )
    else:
        cb_cols_result = await conn.execute(text("PRAGMA table_info(payment_callback_events)"))
        cb_cols = {row[1] for row in cb_cols_result.fetchall()}
        if "raw_payload_hash" not in cb_cols:
            await conn.execute(text("ALTER TABLE payment_callback_events ADD COLUMN raw_payload_hash VARCHAR(64)"))
        if "source_ip" not in cb_cols:
            await conn.execute(text("ALTER TABLE payment_callback_events ADD COLUMN source_ip VARCHAR(45)"))
        if "user_agent" not in cb_cols:
            await conn.execute(text("ALTER TABLE payment_callback_events ADD COLUMN user_agent VARCHAR(512)"))
    
    try:
        await conn.execute(
            text("CREATE UNIQUE INDEX IF NOT EXISTS uq_payment_cb_provider_trade_no ON payment_callback_events(provider, trade_no)")
        )
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_payment_callback_events_provider ON payment_callback_events(provider)")
        )
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_payment_callback_events_order_no ON payment_callback_events(order_no)")
        )
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_payment_callback_events_trade_no ON payment_callback_events(trade_no)")
        )
    except Exception:
        logger.exception("创建 payment_callback_events 索引失败")
    
    # Users 表修复
    if "users" in tables:
        users_cols_result = await conn.execute(text("PRAGMA table_info(users)"))
        users_cols = {row[1] for row in users_cols_result.fetchall()}
        if "vip_expires_at" not in users_cols:
            await conn.execute(text("ALTER TABLE users ADD COLUMN vip_expires_at DATETIME"))
        if "email_verified" not in users_cols:
            await conn.execute(text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 0"))
        if "email_verified_at" not in users_cols:
            await conn.execute(text("ALTER TABLE users ADD COLUMN email_verified_at DATETIME"))
        if "phone_verified" not in users_cols:
            await conn.execute(text("ALTER TABLE users ADD COLUMN phone_verified BOOLEAN DEFAULT 0"))
        if "phone_verified_at" not in users_cols:
            await conn.execute(text("ALTER TABLE users ADD COLUMN phone_verified_at DATETIME"))
    
    # Notifications 表修复
    if "news_comments" not in tables:
        await conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS news_comments "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, news_id INTEGER NOT NULL, "
                "user_id INTEGER NOT NULL, content TEXT NOT NULL, is_deleted BOOLEAN DEFAULT 0, "
                "review_status VARCHAR(20) DEFAULT 'approved', review_reason VARCHAR(200), "
                "reviewed_at DATETIME, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
            )
        )
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_news_comments_news_id ON news_comments(news_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_news_comments_user_id ON news_comments(user_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_news_comments_created_at ON news_comments(created_at)"))
    else:
        comments_cols_result = await conn.execute(text("PRAGMA table_info(news_comments)"))
        comments_cols = {row[1] for row in comments_cols_result.fetchall()}
        if "is_deleted" not in comments_cols:
            await conn.execute(text("ALTER TABLE news_comments ADD COLUMN is_deleted BOOLEAN DEFAULT 0"))
        if "review_status" not in comments_cols:
            await conn.execute(text("ALTER TABLE news_comments ADD COLUMN review_status VARCHAR(20) DEFAULT 'approved'"))
        if "review_reason" not in comments_cols:
            await conn.execute(text("ALTER TABLE news_comments ADD COLUMN review_reason VARCHAR(200)"))
        if "reviewed_at" not in comments_cols:
            await conn.execute(text("ALTER TABLE news_comments ADD COLUMN reviewed_at DATETIME"))
    
    # News topics 表修复
    if "news_topics" not in tables:
        await conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS news_topics "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, title VARCHAR(200) NOT NULL, "
                "description VARCHAR(500), cover_image VARCHAR(255), is_active BOOLEAN DEFAULT 1, "
                "sort_order INTEGER DEFAULT 0, auto_category VARCHAR(50), auto_keyword VARCHAR(100), "
                "auto_limit INTEGER DEFAULT 0, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, "
                "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
            )
        )
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_news_topics_sort_order ON news_topics(sort_order)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_news_topics_is_active ON news_topics(is_active)"))
    else:
        topics_cols_result = await conn.execute(text("PRAGMA table_info(news_topics)"))
        topics_cols = {row[1] for row in topics_cols_result.fetchall()}
        if "auto_category" not in topics_cols:
            await conn.execute(text("ALTER TABLE news_topics ADD COLUMN auto_category VARCHAR(50)"))
        if "auto_keyword" not in topics_cols:
            await conn.execute(text("ALTER TABLE news_topics ADD COLUMN auto_keyword VARCHAR(100)"))
        if "auto_limit" not in topics_cols:
            await conn.execute(text("ALTER TABLE news_topics ADD COLUMN auto_limit INTEGER DEFAULT 0"))
    
    # News topic items 表修复
    if "news_topic_items" not in tables:
        await conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS news_topic_items "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, topic_id INTEGER NOT NULL, "
                "news_id INTEGER NOT NULL, position INTEGER DEFAULT 0, "
                "created_at DATETIME DEFAULT CURRENT_TIMESTAMP, UNIQUE(topic_id, news_id))"
            )
        )
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_news_topic_items_topic ON news_topic_items(topic_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_news_topic_items_news ON news_topic_items(news_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_news_topic_items_position ON news_topic_items(position)"))
    
    # Notifications 表修复
    if "notifications" in tables:
        notifications_cols_result = await conn.execute(text("PRAGMA table_info(notifications)"))
        notifications_cols = {row[1] for row in notifications_cols_result.fetchall()}
        if "dedupe_key" not in notifications_cols:
            await conn.execute(text("ALTER TABLE notifications ADD COLUMN dedupe_key VARCHAR(200)"))
        if "related_user_id" not in notifications_cols:
            await conn.execute(text("ALTER TABLE notifications ADD COLUMN related_user_id INTEGER"))
        if "related_post_id" not in notifications_cols:
            await conn.execute(text("ALTER TABLE notifications ADD COLUMN related_post_id INTEGER"))
        if "related_comment_id" not in notifications_cols:
            await conn.execute(text("ALTER TABLE notifications ADD COLUMN related_comment_id INTEGER"))
        try:
            await conn.execute(
                text(
                    "DELETE FROM notifications WHERE dedupe_key IS NOT NULL AND id NOT IN "
                    "(SELECT MIN(id) FROM notifications WHERE dedupe_key IS NOT NULL GROUP BY user_id, type, dedupe_key)"
                )
            )
        except Exception:
            logger.exception("notifications去重失败")
        try:
            await conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_notifications_user_type_dedupe_key "
                    "ON notifications (user_id, type, dedupe_key)"
                )
            )
        except Exception:
            logger.exception("创建notifications唯一索引失败（可能存在历史重复数据）")
    
    # Posts 表修复
    posts_cols_result = await conn.execute(text("PRAGMA table_info(posts)"))
    posts_cols = {row[1] for row in posts_cols_result.fetchall()}
    posts_missing: list[str] = []
    if "share_count" not in posts_cols:
        posts_missing.append("ALTER TABLE posts ADD COLUMN share_count INTEGER DEFAULT 0")
    if "is_hot" not in posts_cols:
        posts_missing.append("ALTER TABLE posts ADD COLUMN is_hot BOOLEAN DEFAULT 0")
    if "is_essence" not in posts_cols:
        posts_missing.append("ALTER TABLE posts ADD COLUMN is_essence BOOLEAN DEFAULT 0")
    if "heat_score" not in posts_cols:
        posts_missing.append("ALTER TABLE posts ADD COLUMN heat_score REAL DEFAULT 0.0")
    if "cover_image" not in posts_cols:
        posts_missing.append("ALTER TABLE posts ADD COLUMN cover_image VARCHAR(500)")
    if "images" not in posts_cols:
        posts_missing.append("ALTER TABLE posts ADD COLUMN images TEXT")
    if "attachments" not in posts_cols:
        posts_missing.append("ALTER TABLE posts ADD COLUMN attachments TEXT")
    if "updated_at" not in posts_cols:
        posts_missing.append("ALTER TABLE posts ADD COLUMN updated_at DATETIME")
    if "review_status" not in posts_cols:
        posts_missing.append("ALTER TABLE posts ADD COLUMN review_status VARCHAR(20) DEFAULT 'approved'")
    if "review_reason" not in posts_cols:
        posts_missing.append("ALTER TABLE posts ADD COLUMN review_reason VARCHAR(200)")
    if "reviewed_at" not in posts_cols:
        posts_missing.append("ALTER TABLE posts ADD COLUMN reviewed_at DATETIME")
    for stmt in posts_missing:
        await conn.execute(text(stmt))
    
    # Comments 表修复
    comments_cols_result = await conn.execute(text("PRAGMA table_info(comments)"))
    comments_cols = {row[1] for row in comments_cols_result.fetchall()}
    if "images" not in comments_cols:
        await conn.execute(text("ALTER TABLE comments ADD COLUMN images TEXT"))
    if "review_status" not in comments_cols:
        await conn.execute(text("ALTER TABLE comments ADD COLUMN review_status VARCHAR(20)"))
    if "review_reason" not in comments_cols:
        await conn.execute(text("ALTER TABLE comments ADD COLUMN review_reason VARCHAR(200)"))
    if "reviewed_at" not in comments_cols:
        await conn.execute(text("ALTER TABLE comments ADD COLUMN reviewed_at DATETIME"))
    
    # Chat messages 表修复
    chat_cols_result = await conn.execute(text("PRAGMA table_info(chat_messages)"))
    chat_cols = {row[1] for row in chat_cols_result.fetchall()}
    if "rating" not in chat_cols:
        await conn.execute(text("ALTER TABLE chat_messages ADD COLUMN rating INTEGER"))
    if "feedback" not in chat_cols:
        await conn.execute(text("ALTER TABLE chat_messages ADD COLUMN feedback TEXT"))
    
    # Payment orders 表修复
    payment_orders_cols_result = await conn.execute(text("PRAGMA table_info(payment_orders)"))
    payment_orders_cols = {row[1] for row in payment_orders_cols_result.fetchall()}
    payment_orders_missing: list[str] = []
    if "amount_cents" not in payment_orders_cols:
        payment_orders_missing.append("ALTER TABLE payment_orders ADD COLUMN amount_cents INTEGER")
    if "actual_amount_cents" not in payment_orders_cols:
        payment_orders_missing.append("ALTER TABLE payment_orders ADD COLUMN actual_amount_cents INTEGER")
    for stmt in payment_orders_missing:
        await conn.execute(text(stmt))
    
    # User balances 表修复
    user_balances_cols_result = await conn.execute(text("PRAGMA table_info(user_balances)"))
    user_balances_cols = {row[1] for row in user_balances_cols_result.fetchall()}
    user_balances_missing: list[str] = []
    if "balance_cents" not in user_balances_cols:
        user_balances_missing.append("ALTER TABLE user_balances ADD COLUMN balance_cents INTEGER")
    if "frozen_cents" not in user_balances_cols:
        user_balances_missing.append("ALTER TABLE user_balances ADD COLUMN frozen_cents INTEGER")
    if "total_recharged_cents" not in user_balances_cols:
        user_balances_missing.append("ALTER TABLE user_balances ADD COLUMN total_recharged_cents INTEGER")
    if "total_consumed_cents" not in user_balances_cols:
        user_balances_missing.append("ALTER TABLE user_balances ADD COLUMN total_consumed_cents INTEGER")
    for stmt in user_balances_missing:
        await conn.execute(text(stmt))
    
    # Balance transactions 表修复
    balance_tx_cols_result = await conn.execute(text("PRAGMA table_info(balance_transactions)"))
    balance_tx_cols = {row[1] for row in balance_tx_cols_result.fetchall()}
    balance_tx_missing: list[str] = []
    if "amount_cents" not in balance_tx_cols:
        balance_tx_missing.append("ALTER TABLE balance_transactions ADD COLUMN amount_cents INTEGER")
    if "balance_before_cents" not in balance_tx_cols:
        balance_tx_missing.append("ALTER TABLE balance_transactions ADD COLUMN balance_before_cents INTEGER")
    if "balance_after_cents" not in balance_tx_cols:
        balance_tx_missing.append("ALTER TABLE balance_transactions ADD COLUMN balance_after_cents INTEGER")
    for stmt in balance_tx_missing:
        await conn.execute(text(stmt))
    
    # 数据迁移：转换金额字段为分
    await conn.execute(
        text("UPDATE payment_orders SET amount_cents = CAST(ROUND(amount * 100) AS INTEGER) WHERE amount_cents IS NULL")
    )
    await conn.execute(
        text("UPDATE payment_orders SET actual_amount_cents = CAST(ROUND(actual_amount * 100) AS INTEGER) WHERE actual_amount_cents IS NULL")
    )
    await conn.execute(
        text("UPDATE user_balances SET balance_cents = CAST(ROUND(balance * 100) AS INTEGER) WHERE balance_cents IS NULL")
    )
    await conn.execute(
        text("UPDATE user_balances SET frozen_cents = CAST(ROUND(frozen * 100) AS INTEGER) WHERE frozen_cents IS NULL")
    )
    await conn.execute(
        text("UPDATE user_balances SET total_recharged_cents = CAST(ROUND(total_recharged * 100) AS INTEGER) WHERE total_recharged_cents IS NULL")
    )
    await conn.execute(
        text("UPDATE user_balances SET total_consumed_cents = CAST(ROUND(total_consumed * 100) AS INTEGER) WHERE total_consumed_cents IS NULL")
    )
    await conn.execute(
        text("UPDATE balance_transactions SET amount_cents = CAST(ROUND(amount * 100) AS INTEGER) WHERE amount_cents IS NULL")
    )
    await conn.execute(
        text("UPDATE balance_transactions SET balance_before_cents = CAST(ROUND(balance_before * 100) AS INTEGER) WHERE balance_before_cents IS NULL")
    )
    await conn.execute(
        text("UPDATE balance_transactions SET balance_after_cents = CAST(ROUND(balance_after * 100) AS INTEGER) WHERE balance_after_cents IS NULL")
    )


async def _apply_postgresql_migrations(conn: AsyncConnection) -> None:
    """应用 PostgreSQL 特定的迁移修复"""
    # News 表修复
    await conn.execute(text("ALTER TABLE news ADD COLUMN IF NOT EXISTS scheduled_publish_at TIMESTAMPTZ"))
    await conn.execute(text("ALTER TABLE news ADD COLUMN IF NOT EXISTS scheduled_unpublish_at TIMESTAMPTZ"))
    await conn.execute(text("ALTER TABLE news ADD COLUMN IF NOT EXISTS source_url VARCHAR(500)"))
    await conn.execute(text("ALTER TABLE news ADD COLUMN IF NOT EXISTS dedupe_hash VARCHAR(40)"))
    try:
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_news_dedupe_hash ON news(dedupe_hash)"))
    except Exception:
        logger.exception("创建news dedupe_hash索引失败")
    await conn.execute(text("ALTER TABLE news ADD COLUMN IF NOT EXISTS source_site VARCHAR(100)"))
    await conn.execute(text("ALTER TABLE news ADD COLUMN IF NOT EXISTS review_status VARCHAR(20) DEFAULT 'approved'"))
    await conn.execute(text("ALTER TABLE news ADD COLUMN IF NOT EXISTS review_reason VARCHAR(200)"))
    await conn.execute(text("ALTER TABLE news ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ"))
    
    # Generated documents 表修复
    await conn.execute(text("ALTER TABLE generated_documents ADD COLUMN IF NOT EXISTS template_key VARCHAR(50)"))
    await conn.execute(text("ALTER TABLE generated_documents ADD COLUMN IF NOT EXISTS template_version INTEGER"))
    try:
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_generated_documents_template_key ON generated_documents(template_key)")
        )
    except Exception:
        logger.exception("创建generated_documents模板索引失败")
    
    # News AI annotations 表修复
    await conn.execute(text("ALTER TABLE news_ai_annotations ADD COLUMN IF NOT EXISTS highlights TEXT"))
    await conn.execute(text("ALTER TABLE news_ai_annotations ADD COLUMN IF NOT EXISTS keywords TEXT"))
    await conn.execute(text("ALTER TABLE news_ai_annotations ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0"))
    await conn.execute(text("ALTER TABLE news_ai_annotations ADD COLUMN IF NOT EXISTS last_error TEXT"))
    await conn.execute(text("ALTER TABLE news_ai_annotations ADD COLUMN IF NOT EXISTS last_error_at TIMESTAMPTZ"))
    
    # News comments 表修复
    await conn.execute(
        text(
            "CREATE TABLE IF NOT EXISTS news_comments "
            "(id SERIAL PRIMARY KEY, news_id INTEGER NOT NULL, user_id INTEGER NOT NULL, "
            "content TEXT NOT NULL, is_deleted BOOLEAN DEFAULT FALSE, "
            "review_status VARCHAR(20) DEFAULT 'approved', review_reason VARCHAR(200), "
            "reviewed_at TIMESTAMPTZ, created_at TIMESTAMPTZ DEFAULT NOW())"
        )
    )
    await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_news_comments_news_id ON news_comments(news_id)"))
    await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_news_comments_user_id ON news_comments(user_id)"))
    await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_news_comments_created_at ON news_comments(created_at)"))
    await conn.execute(text("ALTER TABLE news_comments ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE"))
    await conn.execute(text("ALTER TABLE news_comments ADD COLUMN IF NOT EXISTS review_status VARCHAR(20)"))
    await conn.execute(text("ALTER TABLE news_comments ADD COLUMN IF NOT EXISTS review_reason VARCHAR(200)"))
    await conn.execute(text("ALTER TABLE news_comments ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ"))
    
    # Notifications 表修复
    await conn.execute(text("ALTER TABLE notifications ADD COLUMN IF NOT EXISTS dedupe_key VARCHAR(200)"))
    await conn.execute(text("ALTER TABLE notifications ADD COLUMN IF NOT EXISTS related_user_id INTEGER"))
    await conn.execute(text("ALTER TABLE notifications ADD COLUMN IF NOT EXISTS related_post_id INTEGER"))
    await conn.execute(text("ALTER TABLE notifications ADD COLUMN IF NOT EXISTS related_comment_id INTEGER"))
    try:
        await conn.execute(
            text(
                "DELETE FROM notifications WHERE dedupe_key IS NOT NULL AND id NOT IN "
                "(SELECT MIN(id) FROM notifications WHERE dedupe_key IS NOT NULL GROUP BY user_id, type, dedupe_key)"
            )
        )
    except Exception:
        logger.exception("notifications去重失败")
    try:
        await conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_notifications_user_type_dedupe_key "
                "ON notifications (user_id, type, dedupe_key)"
            )
        )
    except Exception:
        logger.exception("创建notifications唯一索引失败（可能存在历史重复数据）")
    
    # News topics 表修复
    await conn.execute(text("ALTER TABLE news_topics ADD COLUMN IF NOT EXISTS auto_category VARCHAR(50)"))
    await conn.execute(text("ALTER TABLE news_topics ADD COLUMN IF NOT EXISTS auto_keyword VARCHAR(100)"))
    await conn.execute(text("ALTER TABLE news_topics ADD COLUMN IF NOT EXISTS auto_limit INTEGER DEFAULT 0"))
    
    # News topic items 表修复
    await conn.execute(
        text(
            "CREATE TABLE IF NOT EXISTS news_topic_items "
            "(id SERIAL PRIMARY KEY, topic_id INTEGER NOT NULL, news_id INTEGER NOT NULL, "
            "position INTEGER DEFAULT 0, created_at TIMESTAMPTZ DEFAULT NOW(), "
            "CONSTRAINT uq_news_topic_items_topic_news UNIQUE(topic_id, news_id))"
        )
    )
    await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_news_topic_items_topic ON news_topic_items(topic_id)"))
    await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_news_topic_items_news ON news_topic_items(news_id)"))
    await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_news_topic_items_position ON news_topic_items(position)"))
    
    # Posts 表修复
    await conn.execute(text("ALTER TABLE posts ADD COLUMN IF NOT EXISTS review_status VARCHAR(20)"))
    await conn.execute(text("ALTER TABLE posts ADD COLUMN IF NOT EXISTS review_reason VARCHAR(200)"))
    await conn.execute(text("ALTER TABLE posts ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ"))
    
    # Comments 表修复
    await conn.execute(text("ALTER TABLE comments ADD COLUMN IF NOT EXISTS review_status VARCHAR(20)"))
    await conn.execute(text("ALTER TABLE comments ADD COLUMN IF NOT EXISTS review_reason VARCHAR(200)"))
    await conn.execute(text("ALTER TABLE comments ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ"))
    
    # Payment 相关表修复
    await conn.execute(text("ALTER TABLE payment_orders ADD COLUMN IF NOT EXISTS amount_cents INTEGER"))
    await conn.execute(text("ALTER TABLE payment_orders ADD COLUMN IF NOT EXISTS actual_amount_cents INTEGER"))
    await conn.execute(text("ALTER TABLE user_balances ADD COLUMN IF NOT EXISTS balance_cents INTEGER"))
    await conn.execute(text("ALTER TABLE user_balances ADD COLUMN IF NOT EXISTS frozen_cents INTEGER"))
    await conn.execute(text("ALTER TABLE user_balances ADD COLUMN IF NOT EXISTS total_recharged_cents INTEGER"))
    await conn.execute(text("ALTER TABLE user_balances ADD COLUMN IF NOT EXISTS total_consumed_cents INTEGER"))
    await conn.execute(text("ALTER TABLE balance_transactions ADD COLUMN IF NOT EXISTS amount_cents INTEGER"))
    await conn.execute(text("ALTER TABLE balance_transactions ADD COLUMN IF NOT EXISTS balance_before_cents INTEGER"))
    await conn.execute(text("ALTER TABLE balance_transactions ADD COLUMN IF NOT EXISTS balance_after_cents INTEGER"))
    
    # 数据迁移：转换金额字段为分
    await conn.execute(
        text("UPDATE payment_orders SET amount_cents = CAST(ROUND(amount * 100) AS INTEGER) WHERE amount_cents IS NULL")
    )
    await conn.execute(
        text("UPDATE payment_orders SET actual_amount_cents = CAST(ROUND(actual_amount * 100) AS INTEGER) WHERE actual_amount_cents IS NULL")
    )
    await conn.execute(
        text("UPDATE user_balances SET balance_cents = CAST(ROUND(balance * 100) AS INTEGER) WHERE balance_cents IS NULL")
    )
    await conn.execute(
        text("UPDATE user_balances SET frozen_cents = CAST(ROUND(frozen * 100) AS INTEGER) WHERE frozen_cents IS NULL")
    )
    await conn.execute(
        text("UPDATE user_balances SET total_recharged_cents = CAST(ROUND(total_recharged * 100) AS INTEGER) WHERE total_recharged_cents IS NULL")
    )
    await conn.execute(
        text("UPDATE user_balances SET total_consumed_cents = CAST(ROUND(total_consumed * 100) AS INTEGER) WHERE total_consumed_cents IS NULL")
    )
    await conn.execute(
        text("UPDATE balance_transactions SET amount_cents = CAST(ROUND(amount * 100) AS INTEGER) WHERE amount_cents IS NULL")
    )
    await conn.execute(
        text("UPDATE balance_transactions SET balance_before_cents = CAST(ROUND(balance_before * 100) AS INTEGER) WHERE balance_before_cents IS NULL")
    )
    await conn.execute(
        text("UPDATE balance_transactions SET balance_after_cents = CAST(ROUND(balance_after * 100) AS INTEGER) WHERE balance_after_cents IS NULL")
    )


async def repair_database_schema(conn: AsyncConnection) -> None:
    """修复数据库表结构
    
    根据数据库类型（SQLite/PostgreSQL）应用相应的修复。
    """
    backend_name = engine.url.get_backend_name()
    
    if backend_name == "sqlite":
        await _apply_sqlite_migrations(conn)
    elif backend_name == "postgresql":
        await _apply_postgresql_migrations(conn)
    
    # 通用修复：清理重复点赞数据
    try:
        post_dedup_result = await conn.execute(
            text("DELETE FROM post_likes WHERE id NOT IN (SELECT MIN(id) FROM post_likes GROUP BY post_id, user_id)")
        )
        comment_dedup_result = await conn.execute(
            text("DELETE FROM comment_likes WHERE id NOT IN (SELECT MIN(id) FROM comment_likes GROUP BY comment_id, user_id)")
        )
        logger.info(
            "重复点赞数据清理完成：post_likes=%s, comment_likes=%s",
            getattr(post_dedup_result, "rowcount", None),
            getattr(comment_dedup_result, "rowcount", None),
        )
    except Exception:
        logger.exception("清理重复点赞数据失败")
    
    # 创建唯一索引防止未来重复
    try:
        await conn.execute(
            text("CREATE UNIQUE INDEX IF NOT EXISTS uq_post_like_post_user ON post_likes (post_id, user_id)")
        )
        await conn.execute(
            text("CREATE UNIQUE INDEX IF NOT EXISTS uq_comment_like_comment_user ON comment_likes (comment_id, user_id)")
        )
    except Exception:
        logger.exception("创建唯一索引失败（可能存在历史重复数据）")