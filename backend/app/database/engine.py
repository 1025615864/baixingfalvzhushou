"""数据库引擎配置"""
import logging
import os
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from sqlalchemy.pool import StaticPool

from ..config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)

# SQLite 数据库路径处理
if settings.database_url.startswith("sqlite"):
    parts = settings.database_url.split("///", 1)
    if len(parts) == 2:
        db_path = parts[1]
        if db_path.startswith("./"):
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

# SQL 日志级别配置
sql_echo_raw = os.getenv("SQL_ECHO", "").strip().lower()
engine_echo = sql_echo_raw in {"1", "true", "yes", "on"}

sql_level = logging.INFO if engine_echo else logging.WARNING
logging.getLogger("sqlalchemy").setLevel(sql_level)
logging.getLogger("sqlalchemy.engine").setLevel(sql_level)
logging.getLogger("sqlalchemy.engine.Engine").setLevel(sql_level)
logging.getLogger("sqlalchemy.pool").setLevel(sql_level)

# 检测是否为 SQLite
_is_sqlite = settings.database_url.startswith("sqlite")

# 创建异步数据库引擎
if _is_sqlite:
    # SQLite 配置（使用 StaticPool，不支持连接池参数）
    engine = create_async_engine(
        settings.database_url,
        echo=engine_echo,
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
else:
    # PostgreSQL/MySQL 配置（使用 QueuePool 连接池）
    engine = create_async_engine(
        settings.database_url,
        echo=engine_echo,
        future=True,
        # 连接池配置优化（根据负载调整）
        pool_size=int(os.getenv("DB_POOL_SIZE", "20")),  # 核心连接数：20（生产环境推荐值）
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "30")),  # 最大溢出连接数：30（高峰期支持更多并发）
        pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "1800")),  # 连接回收时间：30分钟（更频繁回收，避免长时间空闲）
        pool_pre_ping=True,  # 启用连接健康检查
        pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),  # 连接获取超时：30秒
    )


AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


def _env_truthy(name: str) -> bool:
    """检查环境变量是否为真值"""
    raw = os.getenv(name, "").strip().lower()
    return raw in {"1", "true", "yes", "on"}