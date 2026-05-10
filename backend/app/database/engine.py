"""数据库引擎配置"""
import logging
import os
import time
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text, event
from sqlalchemy.pool import StaticPool

from ..config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)
slow_query_logger = logging.getLogger("sqlalchemy.slow_query")

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
    # 针对百万用户优化配置
    engine = create_async_engine(
        settings.database_url,
        echo=engine_echo,
        future=True,
        # 连接池配置优化（根据负载调整）
        pool_size=int(os.getenv("DB_POOL_SIZE", "30")),  # 核心连接数：30（百万用户推荐值 20-50）
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "40")),  # 最大溢出连接数：40（高峰期支持更多并发）
        pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "1800")),  # 连接回收时间：30分钟
        pool_pre_ping=True,  # 启用连接健康检查
        pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),  # 连接获取超时：30秒
        # PostgreSQL 特定优化
        connect_args={
            "server_settings": {
                "statement_timeout": "30000",  # SQL 超时 30s
                "idle_in_transaction_session_timeout": "60000",  # 事务空闲 60s 超时
                "jit": "off",  # 关闭 JIT 编译，减少 CPU 消耗
            },
            "command_timeout": 30,
        },
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


# ==========================================
# 慢查询日志配置
# ==========================================

_slow_query_threshold_ms = float(os.getenv("SLOW_QUERY_THRESHOLD_MS", "100"))


@event.listens_for(engine.sync_engine, "before_cursor_execute")
def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """记录查询开始时间"""
    context._query_start_time = time.time()


@event.listens_for(engine.sync_engine, "after_cursor_execute")
def _after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """记录慢查询"""
    if not hasattr(context, "_query_start_time"):
        return
    total = (time.time() - context._query_start_time) * 1000  # 毫秒
    if total >= _slow_query_threshold_ms:
        truncated = statement[:200] + "..." if len(statement) > 200 else statement
        slow_query_logger.warning(
            "SLOW QUERY: %.0fms | %s | params=%s",
            total,
            truncated,
            parameters if len(str(parameters)) < 100 else str(parameters)[:100] + "...",
        )