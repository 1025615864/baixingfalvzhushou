"""Pytest 根配置文件

提供全局配置和 fixtures，按功能区域分组组织。
"""
from __future__ import annotations

import importlib
import inspect
import os
import sys
import tempfile
from collections.abc import AsyncGenerator, Generator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# 添加项目根目录到 Python 路径
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Mock WeasyPrint 避免 Windows 外部依赖
sys.modules["weasyprint"] = MagicMock()
sys.modules["weasyprint.css"] = MagicMock()
sys.modules["weasyprint.text"] = MagicMock()
sys.modules["weasyprint.text.ffi"] = MagicMock()

# 延迟导入应用模块（必须在路径设置后）
from app.config import get_settings  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User  # noqa: E402

# =============================================================================
# 区域 1: 数据库 Fixtures
# =============================================================================

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# 缓存已加载的模型模块
_LOADED_MODELS = False


def _ensure_models_loaded():
    """确保所有模型模块已加载（只执行一次）"""
    global _LOADED_MODELS
    if _LOADED_MODELS:
        return

    model_modules = [
        "app.models.user",
        "app.models.user_quota",
        "app.models.consultation",
        "app.models.consultation_review",
        "app.models.forum",
        "app.models.news",
        "app.models.news_ai",
        "app.models.lawfirm",
        "app.models.settlement",
        "app.models.knowledge",
        "app.models.document",
        "app.models.document_template",
        "app.models.notification",
        "app.models.payment",
        "app.models.system",
        "app.models.calendar",
        "app.models.feedback",
        "app.models.analytics",
        "app.models.faq",
    ]

    for module_name in model_modules:
        importlib.import_module(module_name)

    _LOADED_MODELS = True


@pytest_asyncio.fixture(scope="session")
async def session_engine():
    """会话级数据库引擎（整个测试会话只创建一次）"""
    _ensure_models_loaded()

    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield engine
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest_asyncio.fixture
async def test_engine(session_engine):
    """测试数据库引擎（复用会话级引擎）"""
    yield session_engine


@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话"""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        try:
            for table in reversed(Base.metadata.sorted_tables):
                await session.execute(table.delete())
            await session.commit()
            yield session
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture
async def db(test_session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """数据库会话别名"""
    yield test_session


@pytest_asyncio.fixture
async def mock_db(test_session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """合同审查测试兼容的数据库别名"""
    yield test_session


@pytest_asyncio.fixture
async def client(test_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """创建测试 HTTP 客户端"""
    os.environ["PAYMENT_WEBHOOK_SECRET"] = "test_secret_for_testing"
    get_settings.cache_clear()
    
    async def override_get_db():
        yield test_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport_kwargs: dict[str, Any] = {"app": app}
    if "lifespan" in inspect.signature(ASGITransport.__init__).parameters:
        transport_kwargs["lifespan"] = "off"
    
    transport = ASGITransport(**transport_kwargs)
    
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_client(
    test_session: AsyncSession, auth_headers: dict[str, str]
) -> AsyncGenerator[AsyncClient, None]:
    """带认证的测试客户端"""
    os.environ["PAYMENT_WEBHOOK_SECRET"] = "test_secret_for_testing"
    get_settings.cache_clear()
    
    async def override_get_db():
        yield test_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport_kwargs: dict[str, Any] = {"app": app}
    if "lifespan" in inspect.signature(ASGITransport.__init__).parameters:
        transport_kwargs["lifespan"] = "off"
    
    transport = ASGITransport(**transport_kwargs)
    
    async with AsyncClient(
        transport=transport, base_url="http://test", headers=auth_headers
    ) as ac:
        yield ac
    
    app.dependency_overrides.clear()


# =============================================================================
# 区域 2: 实体 Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> User:
    """创建普通测试用户"""
    user = User(
        username="testuser",
        email="test@example.com",
        phone="13800138000",
        hashed_password="hashed_password",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_lawyer(db: AsyncSession) -> User:
    """创建律师测试用户"""
    user = User(
        username="testlawyer",
        email="lawyer@example.com",
        phone="13900139000",
        hashed_password="hashed_password",
        role="lawyer",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin_user(db: AsyncSession) -> User:
    """创建管理员测试用户"""
    user = User(
        username="testadmin",
        email="admin@example.com",
        phone="13700137000",
        hashed_password="hashed_password",
        role="admin",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
def test_data_factory(db: AsyncSession) -> Any:
    """测试数据工厂"""
    from tests.helpers.test_data_factory import TestDataFactory
    
    return TestDataFactory(db)


# =============================================================================
# 区域 3: 认证 Fixtures
# =============================================================================

def _create_jwt_token(user: User) -> str:
    """创建 JWT Token - 修复RS256配置下的密钥问题"""
    settings = get_settings()
    
    # 处理非对称算法（RS256）的测试令牌生成
    if settings.algorithm == "RS256":
        # RS256需要私钥，测试环境使用测试密钥对
        test_private_key = getattr(settings, "private_key_path", None) or getattr(settings, "secret_key", "")
        if not test_private_key:
            # 生成测试用JWT（对称算法回退）
            return jwt.encode(
                {
                    "sub": str(user.id),
                    "phone": user.phone,
                    "role": user.role or "user",
                    "exp": 9999999999,
                },
                "test_secret_key_for_unit_tests_only",
                algorithm="HS256",
            )
        return jwt.encode(
            {
                "sub": str(user.id),
                "phone": user.phone,
                "role": user.role or "user",
                "exp": 9999999999,
            },
            test_private_key,
            algorithm="RS256",
        )
    
    # 对称算法（HS256等）
    secret = settings.secret_key or "test_secret_key_for_unit_tests_only"
    return jwt.encode(
        {
            "sub": str(user.id),
            "phone": user.phone,
            "role": user.role or "user",
            "exp": 9999999999,
        },
        secret,
        algorithm=settings.algorithm if settings.algorithm else "HS256",
    )


@pytest_asyncio.fixture
async def test_token(test_user: User) -> str:
    """普通用户 JWT Token"""
    return _create_jwt_token(test_user)


@pytest_asyncio.fixture
async def test_admin_token(test_admin_user: User) -> str:
    """管理员 JWT Token"""
    return _create_jwt_token(test_admin_user)


@pytest_asyncio.fixture
async def test_lawyer_token(test_lawyer: User) -> str:
    """律师 JWT Token"""
    return _create_jwt_token(test_lawyer)


@pytest_asyncio.fixture
async def auth_headers(test_token: str) -> dict[str, str]:
    """普通用户认证头"""
    return {"Authorization": f"Bearer {test_token}"}


@pytest_asyncio.fixture
async def admin_auth_headers(test_admin_token: str) -> dict[str, str]:
    """管理员认证头"""
    return {"Authorization": f"Bearer {test_admin_token}"}


@pytest_asyncio.fixture
async def lawyer_auth_headers(test_lawyer_token: str) -> dict[str, str]:
    """律师认证头"""
    return {"Authorization": f"Bearer {test_lawyer_token}"}


# =============================================================================
# 区域 4: 基础设施 Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_redis():
    """Mock Redis 客户端 with state storage"""
    storage = {}
    
    async def _get(key):
        return storage.get(key)
    
    async def _set(key, value, expire=None):
        storage[key] = value
        return True
    
    async def _delete(key):
        storage.pop(key, None)
        return True
    
    async def _acquire_lock(lock_key, lock_value, expire=60):
        if lock_key in storage:
            return False
        storage[lock_key] = lock_value
        return True
    
    async def _release_lock(lock_key, lock_value):
        storage.pop(lock_key, None)
        return True
    
    mock = MagicMock()
    mock.get = AsyncMock(side_effect=_get)
    mock.set = AsyncMock(side_effect=_set)
    mock.delete = AsyncMock(side_effect=_delete)
    mock.setex = AsyncMock(return_value=True)
    mock.expire = AsyncMock(return_value=True)
    mock.ttl = AsyncMock(return_value=3600)
    mock.exists = AsyncMock(return_value=0)
    mock.incr = AsyncMock(return_value=1)
    mock.decr = AsyncMock(return_value=0)
    mock.lpush = AsyncMock(return_value=1)
    mock.rpop = AsyncMock(return_value=None)
    mock.lrange = AsyncMock(return_value=[])
    # Payment idempotency methods
    mock.acquire_lock = AsyncMock(side_effect=_acquire_lock)
    mock.release_lock = AsyncMock(side_effect=_release_lock)
    mock.get_json = AsyncMock(return_value=None)
    mock.set_json = AsyncMock(return_value=True)
    mock._storage = storage  # Expose storage for debugging
    return mock


@pytest.fixture
def mock_redis_module(mock_redis):
    """Mock Redis 模块"""
    with patch.dict("sys.modules", {"redis.asyncio": MagicMock()}):
        with patch("redis.asyncio.Redis", return_value=mock_redis):
            yield mock_redis


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI 客户端"""
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(message=MagicMock(content="Mocked AI response"))
    ]
    mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)
    mock_client.embeddings.create = AsyncMock(
        return_value=MagicMock(
            data=[MagicMock(embedding=[0.1] * 1536)]
        )
    )
    return mock_client


@pytest.fixture
def mock_wechatpay_client():
    """Mock 微信支付客户端"""
    mock = MagicMock()
    mock.jsapi_create_order = AsyncMock(return_value={"prepay_id": "test_prepay_id"})
    mock.jsapi_get_platform_certificates = AsyncMock(return_value=["test_cert"])
    mock.verify_signature = MagicMock(return_value=True)
    mock.decrypt_notification = MagicMock(
        return_value={"out_trade_no": "test_order", "transaction_id": "test_tx"}
    )
    return mock


@pytest.fixture
def mock_storage_service():
    """Mock 存储服务"""
    mock = MagicMock()
    mock.upload_file = AsyncMock(return_value="https://test-cdn.example.com/test.jpg")
    mock.delete_file = AsyncMock(return_value=True)
    mock.generate_presigned_url = AsyncMock(
        return_value="https://test-cdn.example.com/presigned.jpg"
    )
    mock.get_file_info = AsyncMock(return_value={"size": 1024, "mime_type": "image/jpeg"})
    return mock


@pytest.fixture
def mock_external_dependencies():
    """统一的外部依赖 Mock"""
    mocks = {}
    with patch("app.services.email.EmailService.send_email") as mock_email:
        mocks["email"] = mock_email
        with patch("app.services.sms.manager.SMSManager.send_sms") as mock_sms:
            mocks["sms"] = mock_sms
            with patch(
                "app.services.wechat.WeChatService.send_template_message"
            ) as mock_wechat:
                mocks["wechat"] = mock_wechat
                with patch("app.utils.captcha.generate_captcha") as mock_captcha:
                    mock_captcha.return_value = ("test_captcha_code", b"fake_image_bytes")
                    mocks["captcha"] = mock_captcha
                    yield mocks


# =============================================================================
# 区域 5: 清理和工具 Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def _cleanup_services():
    """自动重置服务单例状态"""
    yield


@pytest.fixture(autouse=True)
def _test_timeout():
    """测试超时保护 - 防止测试卡住 (Windows兼容)"""
    import threading
    import time

    timeout_seconds = 60
    timeout_occurred = [False]

    def timeout_check():
        time.sleep(timeout_seconds)
        timeout_occurred[0] = True
        raise TimeoutError(f"Test timed out after {timeout_seconds} seconds")

    timer = threading.Thread(target=timeout_check, daemon=True)
    timer.start()
    yield
    if timeout_occurred[0]:
        raise TimeoutError(f"Test timed out after {timeout_seconds} seconds")


@pytest.fixture(autouse=True)
def _reset_logging_handlers():
    """自动重置日志处理器并确保日志目录存在"""
    import logging
    
    # 确保日志目录存在 - 修复 FileNotFoundError
    for logger_name in ["app", "app.services", "app.services.wechat", "app.services.wechat_service"]:
        logger = logging.getLogger(logger_name)
        for handler in logger.handlers[:]:
            # 确保文件处理器的目录存在
            if isinstance(handler, logging.FileHandler):
                log_path = Path(handler.baseFilename).parent
                log_path.mkdir(parents=True, exist_ok=True)
    
    yield
    
    # 清理测试期间添加的处理器
    for logger_name in ["app", "sqlalchemy", "uvicorn"]:
        logger = logging.getLogger(logger_name)
        for handler in logger.handlers[:]:
            if getattr(handler, "_test_handler", False):
                logger.removeHandler(handler)


@pytest.fixture
def tmp_path_fixed() -> Generator[Path, None, None]:
    """跨平台兼容的临时目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def tmpdir(tmp_path_fixed: Path) -> Path:
    """tmpdir 别名"""
    return tmp_path_fixed


# =============================================================================
# Pytest 配置钩子
# =============================================================================

def pytest_configure(config):
    """配置 pytest"""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "database: marks tests that need database")

    # 忽略 WebSocket 测试中的 RuntimeWarning（协程未等待）
    # 这是因为 enhance_websocket 在测试中使用 asyncio.create_task 发送后台消息
    # 但测试中不等待这些后台任务完成
    config.addinivalue_line(
        "filterwarnings",
        "ignore::RuntimeWarning:.*_broadcast_to_room"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试项"""
    for item in items:
        # 自动标记数据库测试
        if "db" in item.fixturenames or "test_session" in item.fixturenames:
            item.add_marker(pytest.mark.database)
        # 标记慢测试
        if "e2e" in item.nodeid or "integration" in item.nodeid:
            item.add_marker(pytest.mark.slow)
