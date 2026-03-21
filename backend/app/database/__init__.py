"""数据库配置模块

该模块提供数据库相关的所有功能，包括：
- 数据库引擎配置
- 会话管理
- 数据库迁移
- 表结构自修复
- 数据种子

为了保持向后兼容性，所有原来的导入路径仍然有效：
    from app.database import SessionLocal, engine, Base, get_db, init_db
"""

# 从 engine 模块导出
from .engine import engine, AsyncSessionLocal, _env_truthy

# 从 base 模块导出
from .base import Base

# 从 session 模块导出
from .session import get_db

# 从 migrations 模块导出
from .migrations import (
    _get_backend_dir,
    _get_alembic_script_directory,
    _get_alembic_expected_heads,
    _get_alembic_current_heads,
    _assert_alembic_head,
)

# 从 repair 模块导出
from .repair import repair_database_schema

# 从 seeding 模块导出
from .seeding import seed_document_templates, seed_all

# 为了保持向后兼容，保留原来的 SessionLocal 别名
SessionLocal = AsyncSessionLocal


# 初始化数据库
async def init_db() -> None:
    """初始化数据库表（协调函数）
    
    简化版本：删除运行时DDL代码，使用Alembic迁移管理schema变更。
    """
    _import_all_models()

    from ..config import get_settings
    from .engine import engine
    from .migrations import _assert_alembic_head
    from .seeding import seed_document_templates
    
    settings = get_settings()

    # 检查Alembic版本（生产环境强制检查）
    if not settings.debug:
        from sqlalchemy import text
        async with engine.connect() as conn:
            _ = await conn.execute(text("SELECT 1"))
            await conn.run_sync(_assert_alembic_head)
        return

    # 开发环境：创建表（仅用于开发）
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await seed_document_templates()


def _import_all_models() -> None:
    """导入所有模型
    
    确保 SQLAlchemy 能识别所有模型类，用于创建表结构。
    """
    import importlib
    
    module_names = [
        "app.models.user",
        "app.models.user_quota",
        "app.models.user_consent",
        "app.models.consultation",
        "app.models.consultation_review",
        "app.models.lawfirm",
        "app.models.settlement",
        "app.models.knowledge",
        "app.models.document",
        "app.models.document_template",
        "app.models.notification",
        "app.models.system",
        "app.models.calendar",
        "app.models.feedback",
        "app.models.membership",
        "app.models.video_consultation",
        "app.models.user_profile",
        "app.models.user_security",
        "app.models.periodic_task",
        "app.models.channel",
        "app.models.contracts",
        "app.models.cross_domain",
        "app.models.moderation",
        "app.models.faq",
        "app.models.payment",
    ]
    for module_name in module_names:
        _ = importlib.import_module(module_name)


__all__ = [
    # 引擎和会话
    "engine",
    "AsyncSessionLocal",
    "SessionLocal",  # 向后兼容
    "Base",
    "get_db",
    
    # 初始化
    "init_db",
    
    # 迁移相关
    "_get_backend_dir",
    "_get_alembic_script_directory",
    "_get_alembic_expected_heads",
    "_get_alembic_current_heads",
    "_assert_alembic_head",
    
    # 修复和种子
    "repair_database_schema",
    "seed_document_templates",
    "seed_all",
    
    # 工具函数
    "_env_truthy",
    "_import_all_models",
]