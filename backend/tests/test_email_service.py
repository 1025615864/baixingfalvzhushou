import importlib
from datetime import datetime, timedelta, timezone

import pytest
from unittest.mock import AsyncMock, MagicMock

import app.services.email_service as es
import app.services.email.password_reset as password_reset_module
import app.services.email.verification as verification_module
import app.services.email.core as email_core_module
import app.services.cache_service as cache_service_module
from app.services.email.storage import _reset_tokens as _reset_tokens_dict
from app.services.email.storage import _email_verification_tokens as _email_verification_tokens_dict


class FixedDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        _ = tz
        return datetime(2026, 1, 19, 12, 0, 0, tzinfo=timezone.utc)

    @classmethod
    def fromisoformat(cls, date_string: str):
        return datetime.fromisoformat(date_string)


@pytest.fixture(autouse=True, scope="function")
def _reset_state():
    # 清空邮件token内存存储
    _reset_tokens_dict.clear()
    _email_verification_tokens_dict.clear()
    # 确保缓存服务使用内存模式
    cache_service_module._memory_cache.clear()
    cache_service_module.cache_service._redis = None
    cache_service_module.cache_service._connected = False
    cache_service_module.cache_service.hits = 0
    cache_service_module.cache_service.misses = 0
    cache_service_module.cache_service.reset_stats()
    
    yield
    
    # 测试结束后再次清理
    _reset_tokens_dict.clear()
    _email_verification_tokens_dict.clear()
    cache_service_module._memory_cache.clear()


def test_configure_and_is_configured():
    svc = es.EmailService()
    assert svc.is_configured is False

    svc.configure(
        smtp_host="smtp.oyjz.online",
        smtp_port=587,
        smtp_user="u",
        smtp_password="p",
        from_email="from@oyjz.online",
    )

    assert svc.is_configured is True
    assert svc.smtp_host == "smtp.oyjz.online"
    assert svc.smtp_port == 587
    assert svc.smtp_user == "u"
    assert svc.smtp_password == "p"
    assert svc.from_email == "from@oyjz.online"


@pytest.mark.asyncio
async def test_generate_reset_token_cache_success(monkeypatch):
    svc = es.EmailService()

    # Monkeypatch datetime at the module level where it's used
    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            _ = tz
            return datetime(2026, 1, 19, 12, 0, 0, tzinfo=timezone.utc)

        @classmethod
        def fromisoformat(cls, date_string: str):
            return datetime.fromisoformat(date_string)

    # Patch the datetime used in the code
    import app.services.email_service as es_module
    monkeypatch.setattr(es_module, "datetime", FixedDatetime, raising=True)
    monkeypatch.setattr(password_reset_module, "datetime", FixedDatetime, raising=True)
    monkeypatch.setattr(es.secrets, "token_urlsafe", lambda _n: "tok", raising=True)

    called = {}

    async def fake_set_json(key, value, expire):
        called["key"] = key
        called["value"] = value
        called["expire"] = expire
        return True

    monkeypatch.setattr(es.cache_service, "set_json", fake_set_json, raising=True)

    token = await svc.generate_reset_token(user_id=1, email="test@oyjz.online")

    assert token == "tok"
    assert called["key"] == f"{es._RESET_TOKEN_PREFIX}tok"
    assert called["expire"] == es._RESET_TOKEN_TTL_SECONDS

    value = called["value"]
    assert value["user_id"] == 1
    assert value["email"] == "test@oyjz.online"
    assert value["used"] is False
    assert value["expires_at"] == (FixedDatetime.now() + timedelta(hours=1)).isoformat()


@pytest.mark.asyncio
async def test_generate_reset_token_fallback_on_cache_error(monkeypatch):
    svc = es.EmailService()

    monkeypatch.setattr(password_reset_module, "datetime", FixedDatetime, raising=True)
    monkeypatch.setattr(es.secrets, "token_urlsafe", lambda _n: "tok", raising=True)

    async def fake_set_json(*_args, **_kwargs):
        raise RuntimeError("cache down")

    monkeypatch.setattr(es.cache_service, "set_json", fake_set_json, raising=True)

    token = await svc.generate_reset_token(user_id=2, email="test2@oyjz.online")

    assert token == "tok"
    assert "tok" in _reset_tokens_dict
    assert _reset_tokens_dict["tok"]["user_id"] == 2


def test_cleanup_expired_tokens_removes_past_expiry():
    svc = es.EmailService()
    es._reset_tokens["old"] = {
        "user_id": 1,
        "email": "test@oyjz.online",
        "expires_at": "2000-01-01T00:00:00",
        "used": False,
    }

    svc._cleanup_expired_tokens()
    assert "old" not in es._reset_tokens


@pytest.mark.asyncio
async def test_verify_reset_token_cache_hit(monkeypatch):
    svc = es.EmailService()

    async def fake_get_json(_key):
        return {
            "user_id": 1,
            "email": "test@oyjz.online",
            "expires_at": "2026-01-19T13:00:00",
            "used": False,
        }

    monkeypatch.setattr(es.cache_service, "get_json", fake_get_json, raising=True)

    data = await svc.verify_reset_token("tok")
    assert data is not None
    assert data["user_id"] == 1
    assert data["email"] == "test@oyjz.online"


@pytest.mark.asyncio
async def test_verify_reset_token_cache_used_returns_none(monkeypatch):
    svc = es.EmailService()

    async def fake_get_json(_key):
        return {
            "user_id": 1,
            "email": "test@oyjz.online",
            "expires_at": "2026-01-19T13:00:00",
            "used": True,
        }

    monkeypatch.setattr(es.cache_service, "get_json", fake_get_json, raising=True)

    assert await svc.verify_reset_token("tok") is None


@pytest.mark.asyncio
async def test_verify_reset_token_fallback_invalid_or_expired(monkeypatch):
    svc = es.EmailService()
    monkeypatch.setattr(password_reset_module, "datetime", FixedDatetime, raising=True)

    _reset_tokens_dict["bad"] = {
        "user_id": 1,
        "email": "test@oyjz.online",
        "expires_at": "not-iso",
        "used": False,
    }

    assert await svc.verify_reset_token("bad") is None
    assert "bad" not in _reset_tokens_dict

    _reset_tokens_dict["expired"] = {
        "user_id": 1,
        "email": "test@oyjz.online",
        "expires_at": (FixedDatetime.now() - timedelta(seconds=1)).isoformat(),
        "used": False,
    }

    assert await svc.verify_reset_token("expired") is None
    assert "expired" not in _reset_tokens_dict


@pytest.mark.asyncio
async def test_verify_reset_token_cache_exception_fallback_memory_valid(monkeypatch):
    svc = es.EmailService()
    # Monkeypatch datetime at the module level
    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            _ = tz
            return datetime(2026, 1, 19, 12, 0, 0, tzinfo=timezone.utc)

        @classmethod
        def fromisoformat(cls, date_string: str):
            return datetime.fromisoformat(date_string)

    import app.services.email_service as es_module
    monkeypatch.setattr(es_module, "datetime", FixedDatetime, raising=True)
    monkeypatch.setattr(password_reset_module, "datetime", FixedDatetime, raising=True)

    async def fake_get_json(*_args, **_kwargs):
        raise RuntimeError("cache down")

    monkeypatch.setattr(es.cache_service, "get_json", fake_get_json, raising=True)

    _reset_tokens_dict["tok"] = {
        "user_id": 9,
        "email": "test@oyjz.online",
        "expires_at": (FixedDatetime.now() + timedelta(seconds=10)).isoformat(),
        "used": False,
    }

    data = await svc.verify_reset_token("tok")
    assert data is not None
    assert data["user_id"] == 9


@pytest.mark.asyncio
async def test_verify_reset_token_fallback_used_returns_none(monkeypatch):
    svc = es.EmailService()

    async def fake_get_json(*_args, **_kwargs):
        raise RuntimeError("cache down")

    monkeypatch.setattr(es.cache_service, "get_json", fake_get_json, raising=True)

    _reset_tokens_dict["tok"] = {
        "user_id": 1,
        "email": "test@oyjz.online",
        "expires_at": "2026-01-19T13:00:00",
        "used": True,
    }
    assert await svc.verify_reset_token("tok") is None


@pytest.mark.asyncio
async def test_invalidate_token_cache_path(monkeypatch):
    svc = es.EmailService()

    async def fake_get_json(_key):
        return {
            "user_id": 1,
            "email": "test@oyjz.online",
            "expires_at": "2026-01-19T13:00:00",
            "used": False,
        }

    called = {}

    async def fake_set_json(key, value, expire):
        called["key"] = key
        called["value"] = value
        called["expire"] = expire
        return True

    monkeypatch.setattr(es.cache_service, "get_json", fake_get_json, raising=True)
    monkeypatch.setattr(es.cache_service, "set_json", fake_set_json, raising=True)

    await svc.invalidate_token("tok")

    assert called["key"] == f"{es._RESET_TOKEN_PREFIX}tok"
    assert called["value"]["used"] is True


@pytest.mark.asyncio
async def test_invalidate_token_fallback_sets_memory_used(monkeypatch):
    svc = es.EmailService()

    async def fake_get_json(*_args, **_kwargs):
        raise RuntimeError("cache down")

    monkeypatch.setattr(es.cache_service, "get_json", fake_get_json, raising=True)

    _reset_tokens_dict["tok"] = {
        "user_id": 1,
        "email": "test@oyjz.online",
        "expires_at": "2026-01-19T13:00:00",
        "used": False,
    }

    await svc.invalidate_token("tok")
    assert _reset_tokens_dict["tok"]["used"] is True


@pytest.mark.asyncio
async def test_generate_and_verify_email_verification_token_cache(monkeypatch):
    svc = es.EmailService()

    monkeypatch.setattr(password_reset_module, "datetime", FixedDatetime, raising=True)
    monkeypatch.setattr(es.secrets, "token_urlsafe", lambda _n: "etok", raising=True)

    async def fake_set_json(*_args, **_kwargs):
        return True

    async def fake_get_json(_key):
        return {
            "user_id": 3,
            "email": "verify@oyjz.online",
            "expires_at": (FixedDatetime.now() + timedelta(seconds=es._EMAIL_VERIFY_TOKEN_TTL_SECONDS)).isoformat(),
            "used": False,
        }

    monkeypatch.setattr(es.cache_service, "set_json", fake_set_json, raising=True)
    monkeypatch.setattr(es.cache_service, "get_json", fake_get_json, raising=True)

    token = await svc.generate_email_verification_token(3, "verify@oyjz.online")
    assert token == "etok"

    data = await svc.verify_email_verification_token("etok")
    assert data is not None
    assert data["user_id"] == 3


@pytest.mark.asyncio
async def test_generate_email_verification_token_fallback_and_cleanup_bad_reset_expires(monkeypatch):
    svc = es.EmailService()
    monkeypatch.setattr(verification_module, "datetime", FixedDatetime, raising=True)
    monkeypatch.setattr(es.secrets, "token_urlsafe", lambda _n: "etok2", raising=True)

    async def fake_set_json(*_args, **_kwargs):
        raise RuntimeError("cache down")

    monkeypatch.setattr(es.cache_service, "set_json", fake_set_json, raising=True)

    _reset_tokens_dict["bad"] = {
        "user_id": 1,
        "email": "test@oyjz.online",
        "expires_at": "not-iso",
        "used": False,
    }

    token = await svc.generate_email_verification_token(1, "test@oyjz.online")
    assert token == "etok2"
    assert "etok2" in _email_verification_tokens_dict
    assert "bad" not in _reset_tokens_dict


@pytest.mark.asyncio
async def test_verify_email_verification_token_fallback_invalid_or_expired(monkeypatch):
    svc = es.EmailService()
    monkeypatch.setattr(verification_module, "datetime", FixedDatetime, raising=True)

    _email_verification_tokens_dict["bad"] = {
        "user_id": 1,
        "email": "test@oyjz.online",
        "expires_at": "not-iso",
        "used": False,
    }

    assert await svc.verify_email_verification_token("bad") is None
    assert "bad" not in _email_verification_tokens_dict

    _email_verification_tokens_dict["expired"] = {
        "user_id": 1,
        "email": "test@oyjz.online",
        "expires_at": (FixedDatetime.now() - timedelta(seconds=1)).isoformat(),
        "used": False,
    }

    assert await svc.verify_email_verification_token("expired") is None
    assert "expired" not in _email_verification_tokens_dict


@pytest.mark.asyncio
async def test_verify_email_verification_token_cache_exception_fallback_memory_valid(monkeypatch):
    svc = es.EmailService()
    # Monkeypatch datetime at the module level
    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            _ = tz
            return datetime(2026, 1, 19, 12, 0, 0, tzinfo=timezone.utc)

        @classmethod
        def fromisoformat(cls, date_string: str):
            return datetime.fromisoformat(date_string)

    import app.services.email_service as es_module
    monkeypatch.setattr(es_module, "datetime", FixedDatetime, raising=True)
    monkeypatch.setattr(verification_module, "datetime", FixedDatetime, raising=True)

    async def fake_get_json(*_args, **_kwargs):
        raise RuntimeError("cache down")

    monkeypatch.setattr(es.cache_service, "get_json", fake_get_json, raising=True)

    _email_verification_tokens_dict["tok"] = {
        "user_id": 7,
        "email": "v@e.com",
        "expires_at": (FixedDatetime.now() + timedelta(seconds=10)).isoformat(),
        "used": False,
    }

    data = await svc.verify_email_verification_token("tok")
    assert data is not None
    assert data["user_id"] == 7


@pytest.mark.asyncio
async def test_verify_email_verification_token_fallback_used_returns_none(monkeypatch):
    svc = es.EmailService()

    async def fake_get_json(*_args, **_kwargs):
        raise RuntimeError("cache down")

    monkeypatch.setattr(es.cache_service, "get_json", fake_get_json, raising=True)

    _email_verification_tokens_dict["tok"] = {
        "user_id": 7,
        "email": "v@e.com",
        "expires_at": "2026-01-19T13:00:00",
        "used": True,
    }
    assert await svc.verify_email_verification_token("tok") is None


@pytest.mark.asyncio
async def test_invalidate_email_verification_token_cache_path(monkeypatch):
    svc = es.EmailService()

    async def fake_get_json(_key):
        return {
            "user_id": 3,
            "email": "v@e.com",
            "expires_at": "2026-01-19T13:00:00",
            "used": False,
        }

    called = {}

    async def fake_set_json(key, value, expire):
        called["key"] = key
        called["value"] = value
        called["expire"] = expire
        return True

    monkeypatch.setattr(es.cache_service, "get_json", fake_get_json, raising=True)
    monkeypatch.setattr(es.cache_service, "set_json", fake_set_json, raising=True)

    await svc.invalidate_email_verification_token("tok")
    assert called["key"] == f"{es._EMAIL_VERIFY_TOKEN_PREFIX}tok"
    assert called["value"]["used"] is True


@pytest.mark.asyncio
async def test_invalidate_email_verification_token_fallback_sets_memory_used(monkeypatch):
    svc = es.EmailService()

    async def fake_get_json(*_args, **_kwargs):
        raise RuntimeError("cache down")

    monkeypatch.setattr(es.cache_service, "get_json", fake_get_json, raising=True)

    _email_verification_tokens_dict["tok"] = {
        "user_id": 3,
        "email": "v@e.com",
        "expires_at": "2026-01-19T13:00:00",
        "used": False,
    }

    await svc.invalidate_email_verification_token("tok")
    assert _email_verification_tokens_dict["tok"]["used"] is True


@pytest.mark.asyncio
async def test_send_password_reset_email_not_configured_returns_true():
    svc = es.EmailService()
    ok = await svc.send_password_reset_email(
        email="test@oyjz.online",
        reset_token="tok",
        reset_url="http://oyjz.online/reset",
    )
    assert ok is True


@pytest.mark.asyncio
async def test_send_password_reset_email_configured_importerror(monkeypatch):
    svc = es.EmailService()
    svc.configure("smtp.oyjz.online", 587, "u", "p")

    def fake_import_module(_name):
        raise ImportError("no aiosmtplib")

    monkeypatch.setattr(importlib, "import_module", fake_import_module, raising=True)

    ok = await svc.send_password_reset_email(
        email="test@oyjz.online",
        reset_token="tok",
        reset_url="http://oyjz.online/reset",
    )
    assert ok is False


@pytest.mark.asyncio
async def test_send_password_reset_email_configured_success(monkeypatch):
    svc = es.EmailService()
    svc.configure("smtp.oyjz.online", 587, "u", "p")

    called = {}

    class DummyAiOSMTP:
        @staticmethod
        async def send(message, **kwargs):
            called["message"] = message
            called["kwargs"] = kwargs
            return None

    def fake_import_module(name):
        assert name == "aiosmtplib"
        return DummyAiOSMTP

    monkeypatch.setattr(importlib, "import_module", fake_import_module, raising=True)

    ok = await svc.send_password_reset_email(
        email="test@oyjz.online",
        reset_token="tok",
        reset_url="http://oyjz.online/reset",
    )

    assert ok is True
    assert called["message"]["To"] == "test@oyjz.online"
    assert "密码重置" in str(called["message"]["Subject"])


@pytest.mark.asyncio
async def test_send_password_reset_email_configured_exception_returns_false(monkeypatch):
    svc = es.EmailService()
    svc.configure("smtp.oyjz.online", 587, "u", "p")

    class DummyAiOSMTP:
        @staticmethod
        async def send(*_args, **_kwargs):
            raise RuntimeError("smtp down")

    monkeypatch.setattr(importlib, "import_module", lambda _n: DummyAiOSMTP, raising=True)

    ok = await svc.send_password_reset_email(
        email="test@oyjz.online",
        reset_token="tok",
        reset_url="http://oyjz.online/reset",
    )
    assert ok is False


@pytest.mark.asyncio
async def test_send_notification_email_not_configured_returns_false():
    svc = es.EmailService()
    ok = await svc.send_notification_email(email="test@oyjz.online", subject="s", content="c")
    assert ok is False


@pytest.mark.asyncio
async def test_send_notification_email_configured_success(monkeypatch):
    svc = es.EmailService()
    svc.configure("smtp.oyjz.online", 587, "u", "p")

    svc._check_rate_limit = AsyncMock(return_value=(True, ""))

    class DummyAiOSMTP:
        @staticmethod
        async def send(_message, **_kwargs):
            return None

    monkeypatch.setattr(importlib, "import_module", lambda _n: DummyAiOSMTP, raising=True)

    ok = await svc.send_notification_email(email="test@oyjz.online", subject="s", content="c")
    assert ok is True


@pytest.mark.asyncio
async def test_send_notification_email_configured_importerror(monkeypatch):
    svc = es.EmailService()
    svc.configure("smtp.oyjz.online", 587, "u", "p")

    def fake_import_module(_name):
        raise ImportError("no aiosmtplib")

    monkeypatch.setattr(importlib, "import_module", fake_import_module, raising=True)

    ok = await svc.send_notification_email(email="test@oyjz.online", subject="s", content="c")
    assert ok is False


@pytest.mark.asyncio
async def test_send_notification_email_configured_exception_returns_false(monkeypatch):
    svc = es.EmailService()
    svc.configure("smtp.oyjz.online", 587, "u", "p")

    class DummyAiOSMTP:
        @staticmethod
        async def send(*_args, **_kwargs):
            raise RuntimeError("smtp down")

    monkeypatch.setattr(importlib, "import_module", lambda _n: DummyAiOSMTP, raising=True)

    ok = await svc.send_notification_email(email="test@oyjz.online", subject="s", content="c")
    assert ok is False


@pytest.mark.asyncio
async def test_send_email_verification_email_not_configured_returns_true():
    svc = es.EmailService()

    svc._check_rate_limit = AsyncMock(return_value=(True, ""))

    # 清除速率限制缓存
    from app.services.cache_service import cache_service
    await cache_service.clear_pattern("email_rate_limit:*")
    
    ok = await svc.send_email_verification_email(email="test@oyjz.online", verify_url="http://oyjz.online/verify")
    assert ok is True


@pytest.mark.asyncio
async def test_send_email_verification_email_configured_importerror(monkeypatch):
    svc = es.EmailService()
    svc.configure("smtp.oyjz.online", 587, "u", "p")

    def fake_import_module(_name):
        raise ImportError("no aiosmtplib")

    monkeypatch.setattr(importlib, "import_module", fake_import_module, raising=True)

    ok = await svc.send_email_verification_email(email="test@oyjz.online", verify_url="http://oyjz.online/verify")
    assert ok is False


@pytest.mark.asyncio
async def test_core_check_rate_limit_no_identity_allows():
    svc = email_core_module.EmailService()
    ok, msg = await svc._check_rate_limit()
    assert ok is True
    assert msg == ""


@pytest.mark.asyncio
async def test_core_check_rate_limit_first_time_sets_counter(monkeypatch):
    svc = email_core_module.EmailService()

    cache_service_module.cache_service.get = AsyncMock(return_value=None)
    cache_service_module.cache_service.set = AsyncMock(return_value=True)

    ok, msg = await svc._check_rate_limit(user_id=123)
    assert ok is True
    assert msg == ""

    cache_service_module.cache_service.get.assert_awaited_once_with(
        f"{email_core_module._EMAIL_RATE_LIMIT_PREFIX}user:123"
    )
    cache_service_module.cache_service.set.assert_awaited_once_with(
        f"{email_core_module._EMAIL_RATE_LIMIT_PREFIX}user:123",
        "1",
        expire=email_core_module._EMAIL_RATE_LIMIT_WINDOW_SECONDS,
    )


@pytest.mark.asyncio
async def test_core_check_rate_limit_increments_counter(monkeypatch):
    svc = email_core_module.EmailService()

    cache_service_module.cache_service.get = AsyncMock(return_value="1")
    cache_service_module.cache_service.set = AsyncMock(return_value=True)

    ok, msg = await svc._check_rate_limit(email="test@oyjz.online")
    assert ok is True
    assert msg == ""

    cache_service_module.cache_service.set.assert_awaited_once_with(
        f"{email_core_module._EMAIL_RATE_LIMIT_PREFIX}email:test@oyjz.online",
        "2",
        expire=email_core_module._EMAIL_RATE_LIMIT_WINDOW_SECONDS,
    )


@pytest.mark.asyncio
async def test_core_check_rate_limit_exceeded_blocks(monkeypatch):
    svc = email_core_module.EmailService()

    cache_service_module.cache_service.get = AsyncMock(
        return_value=str(email_core_module._EMAIL_RATE_LIMIT_MAX_PER_MINUTE)
    )
    cache_service_module.cache_service.set = AsyncMock(return_value=True)

    ok, msg = await svc._check_rate_limit(user_id=1)
    assert ok is False
    assert "每分钟最多" in msg
    cache_service_module.cache_service.set.assert_not_called()


@pytest.mark.asyncio
async def test_core_check_rate_limit_cache_unavailable_allows(monkeypatch):
    svc = email_core_module.EmailService()

    # 清除邮件限流缓存
    from app.services.cache_service import cache_service
    await cache_service.clear_pattern("email_rate_limit:*")

    monkeypatch.setattr(
        "app.services.cache_service.cache_service.get",
        AsyncMock(side_effect=ConnectionError("down")),
        raising=False
    )
    monkeypatch.setattr(
        "app.services.cache_service.cache_service.set",
        AsyncMock(),
        raising=False
    )

    ok, msg = await svc._check_rate_limit(email="test@oyjz.online")
    assert ok is True
    assert msg == ""


@pytest.mark.asyncio
async def test_core_configure_from_db_success(monkeypatch):
    svc = email_core_module.EmailService()

    class CfgRow:
        def __init__(self, key: str, value: str | None):
            self.key = key
            self.value = value

    class SecRow:
        def __init__(self, key: str, value: str | None):
            self.key = key
            self.value = value

    class _CfgResult:
        def __init__(self, rows):
            self._rows = rows

        def scalars(self):
            return self

        def all(self):
            return self._rows

    class _SecResult:
        def __init__(self, row):
            self._row = row

        def scalar_one_or_none(self):
            return self._row

    cfg_rows = [
        CfgRow("EMAIL_SMTP_HOST", "smtp.oyjz.online"),
        CfgRow("EMAIL_SMTP_PORT", "465"),
        CfgRow("EMAIL_SMTP_USER", "noreply@oyjz.online"),
        CfgRow("EMAIL_FROM_EMAIL", ""),
        CfgRow("EMAIL_FROM_NAME", "百姓法律助手"),
        CfgRow("EMAIL_SMTP_USE_TLS", "true"),
        CfgRow("EMAIL_SMTP_START_TLS", "false"),
    ]
    sec_row = SecRow("EMAIL_SMTP_PASSWORD", "encrypted")

    db = MagicMock()
    db.execute = AsyncMock(side_effect=[_CfgResult(cfg_rows), _SecResult(sec_row)])

    monkeypatch.setattr(email_core_module, "decrypt_secret", lambda _v: "pwd", raising=True)

    ok = await svc.configure_from_db(db)
    assert ok is True
    assert svc.is_configured is True
    assert svc.smtp_host == "smtp.oyjz.online"
    assert svc.smtp_port == 465
    assert svc.smtp_user == "noreply@oyjz.online"
    assert svc.smtp_password == "pwd"
    assert svc.from_email == "noreply@oyjz.online"
    assert svc.smtp_use_tls is True
    assert svc.smtp_start_tls is False


@pytest.mark.asyncio
async def test_core_configure_from_db_missing_password_returns_false(monkeypatch):
    svc = email_core_module.EmailService()

    class CfgRow:
        def __init__(self, key: str, value: str | None):
            self.key = key
            self.value = value

    class _CfgResult:
        def __init__(self, rows):
            self._rows = rows

        def scalars(self):
            return self

        def all(self):
            return self._rows

    class _SecResult:
        def scalar_one_or_none(self):
            return None

    cfg_rows = [
        CfgRow("EMAIL_SMTP_HOST", "smtp.oyjz.online"),
        CfgRow("EMAIL_SMTP_PORT", "bad"),
        CfgRow("EMAIL_SMTP_USER", "noreply@oyjz.online"),
    ]

    db = MagicMock()
    db.execute = AsyncMock(side_effect=[_CfgResult(cfg_rows), _SecResult()])

    ok = await svc.configure_from_db(db)
    assert ok is False
    assert svc.is_configured is False


@pytest.mark.asyncio
async def test_send_email_verification_email_configured_success(monkeypatch):
    svc = es.EmailService()
    svc.configure("smtp.oyjz.online", 587, "u", "p")
 
    # 清除邮件限流缓存和验证令牌缓存 - 确保测试隔离
    from app.services.cache_service import cache_service
    await cache_service.clear_pattern("email_rate_limit:*")
    await cache_service.clear_pattern("email_verify:*")

    called = {}

    class DummyAiOSMTP:
        @staticmethod
        async def send(message, **_kwargs):
            called["message"] = message
            return None

    # 只拦截 aiosmtplib 的导入，避免影响其他模块
    original_import = importlib.import_module
    def mock_import(name, *args, **kwargs):
        if name == "aiosmtplib":
            return DummyAiOSMTP
        return original_import(name, *args, **kwargs)
    monkeypatch.setattr(importlib, "import_module", mock_import)

    ok = await svc.send_email_verification_email(email="test@oyjz.online", verify_url="http://oyjz.online/verify")
    assert ok is True
    assert called["message"]["To"] == "test@oyjz.online"
    assert "邮箱验证" in str(called["message"]["Subject"])


@pytest.mark.asyncio
async def test_send_email_verification_email_configured_exception_returns_false(monkeypatch):
    svc = es.EmailService()
    svc.configure("smtp.oyjz.online", 587, "u", "p")

    class DummyAiOSMTP:
        @staticmethod
        async def send(*_args, **_kwargs):
            raise RuntimeError("smtp down")

    monkeypatch.setattr(importlib, "import_module", lambda _n: DummyAiOSMTP, raising=True)

    ok = await svc.send_email_verification_email(email="test@oyjz.online", verify_url="http://oyjz.online/verify")
    assert ok is False
