"""数据库迁移相关功能"""
import os
from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.engine import Connection
from sqlalchemy import text

from .engine import engine


def _get_backend_dir() -> Path:
    """获取后端目录路径"""
    return Path(__file__).resolve().parents[2]


def _get_alembic_script_directory() -> ScriptDirectory:
    """获取 Alembic 脚本目录"""
    backend_dir = _get_backend_dir()
    ini_path = backend_dir / "alembic.ini"
    config = Config(str(ini_path))
    config.set_main_option("script_location", str(backend_dir / "alembic"))
    return ScriptDirectory.from_config(config)


def _get_alembic_expected_heads() -> tuple[str, ...]:
    """获取 Alembic 预期的 heads"""
    script = _get_alembic_script_directory()
    return tuple(script.get_heads())


def _get_alembic_current_heads(conn: Connection) -> tuple[str, ...]:
    """获取当前数据库的 Alembic heads"""
    ctx = MigrationContext.configure(conn)
    return tuple(ctx.get_current_heads())


def _assert_alembic_head(conn: Connection) -> None:
    """断言数据库 schema 处于 Alembic head
    
    检查数据库 schema 是否与 Alembic 迁移脚本一致。
    如果不一致会抛出 RuntimeError。
    
    可以通过设置环境变量 DB_ALLOW_RUNTIME_DDL=1 来跳过此检查。
    """
    # 检查是否允许运行时DDL
    allow_runtime_ddl = os.getenv("DB_ALLOW_RUNTIME_DDL", "0") == "1"
    if allow_runtime_ddl:
        return
    
    expected = _get_alembic_expected_heads()
    current = _get_alembic_current_heads(conn)
    if set(current) != set(expected):
        raise RuntimeError(
            f"Database schema is not at Alembic head. current={list(current)} expected={list(expected)}. "
            "Run `py scripts/alembic_cmd.py upgrade head` (or `alembic upgrade head`). "
            "If the database already has the full schema and you only want to mark it, run `py scripts/alembic_cmd.py stamp head`. "
            "You may temporarily set DB_ALLOW_RUNTIME_DDL=1 to bypass this check.")