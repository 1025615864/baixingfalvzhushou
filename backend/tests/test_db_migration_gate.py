import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import get_settings


@pytest.mark.asyncio
async def test_init_db_requires_alembic_head_when_debug_false(monkeypatch):
    """测试在非debug模式下 init_db 需要 Alembic head 检查"""
    from app import database as db

    settings = get_settings()
    orig_engine = db.engine
    orig_debug = settings.debug
    new_engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)

    try:
        # 修改 settings 的 debug 属性
        monkeypatch.setattr(settings, "debug", False)
        monkeypatch.delenv("DB_ALLOW_RUNTIME_DDL", raising=False)
        db.engine = new_engine

        # 在非debug模式下，init_db 应该尝试检查 Alembic head
        # 由于新引擎没有 Alembic 表，应该会失败
        with pytest.raises((RuntimeError, Exception)) as exc:
            await db.init_db()

        # 检查错误信息中包含 alembic 相关信息
        error_msg = str(exc.value).lower()
        assert any(word in error_msg for word in ["alembic", "upgrade", "head", "version", "table"])
    finally:
        await new_engine.dispose()
        db.engine = orig_engine
        monkeypatch.setattr(settings, "debug", orig_debug)


@pytest.mark.asyncio
async def test_init_db_allows_runtime_ddl_when_env_enabled(monkeypatch):
    """测试在启用 DB_ALLOW_RUNTIME_DDL 环境变量时允许运行时DDL"""
    from app import database as db

    settings = get_settings()
    orig_engine = db.engine
    orig_debug = settings.debug
    new_engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)

    try:
        # 修改 settings 的 debug 属性
        monkeypatch.setattr(settings, "debug", False)
        monkeypatch.setenv("DB_ALLOW_RUNTIME_DDL", "1")
        db.engine = new_engine

        # 在启用 DB_ALLOW_RUNTIME_DDL 时，应该可以正常执行
        # 注意：这可能会创建表，但在测试环境中应该可以运行
        await db.init_db()
    finally:
        await new_engine.dispose()
        db.engine = orig_engine
        monkeypatch.setattr(settings, "debug", orig_debug)
        monkeypatch.delenv("DB_ALLOW_RUNTIME_DDL", raising=False)
