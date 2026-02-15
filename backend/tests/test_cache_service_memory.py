import pytest

from app.services import cache_service as cache_module


@pytest.fixture(autouse=True)
def _reset_cache_service_state():
    """Reset cache_service state before each test."""
    cache_module.cache_service._redis = None
    cache_module.cache_service._connected = False
    cache_module._memory_cache.clear()
    yield


@pytest.mark.asyncio
async def test_cache_service_memory_set_get_delete_clear_pattern(monkeypatch: pytest.MonkeyPatch) -> None:
    ok = await cache_module.cache_service.set("k1", "v1", expire=300)
    assert ok is True
    assert await cache_module.cache_service.get("k1") == "v1"

    ok = await cache_module.cache_service.set("user:1", "u1", expire=300)
    assert ok is True
    ok = await cache_module.cache_service.set("user:2", "u2", expire=300)
    assert ok is True

    deleted = await cache_module.cache_service.delete("user:1")
    assert deleted is True
    assert await cache_module.cache_service.get("user:1") is None

    cleared = await cache_module.cache_service.clear_pattern("user:*")
    assert cleared == 1
    assert await cache_module.cache_service.get("user:2") is None


@pytest.mark.asyncio
async def test_cache_service_memory_expired_entry_is_removed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cache_module.cache_service, "_connected", False, raising=False)
    monkeypatch.setattr(cache_module.cache_service, "_redis", None, raising=False)
    cache_module._memory_cache.clear()

    cache_module._memory_cache["expired"] = ("value", 0.0)
    assert await cache_module.cache_service.get("expired") is None
    assert "expired" not in cache_module._memory_cache


@pytest.mark.asyncio
async def test_cache_service_memory_json_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cache_module.cache_service, "_connected", False, raising=False)
    monkeypatch.setattr(cache_module.cache_service, "_redis", None, raising=False)
    cache_module._memory_cache.clear()

    payload = {"a": 1, "b": ["x", "y"]}
    ok = await cache_module.cache_service.set_json("json", payload, expire=60)
    assert ok is True

    got = await cache_module.cache_service.get_json("json")
    assert got == payload


@pytest.mark.asyncio
async def test_cache_service_memory_lock_lifecycle(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cache_module.cache_service, "_connected", False, raising=False)
    monkeypatch.setattr(cache_module.cache_service, "_redis", None, raising=False)
    cache_module._memory_cache.clear()

    assert await cache_module.cache_service.acquire_lock("lock", "v", expire=60) is True
    assert await cache_module.cache_service.acquire_lock("lock", "v", expire=60) is False

    assert await cache_module.cache_service.refresh_lock("lock", "bad", expire=60) is False
    assert await cache_module.cache_service.refresh_lock("lock", "v", expire=60) is True

    # release_lock 现在在值不匹配或键不存在时都返回 True
    assert await cache_module.cache_service.release_lock("lock", "bad") is True
    assert await cache_module.cache_service.release_lock("lock", "v") is True

    assert await cache_module.cache_service.release_lock("missing", "v") is True
    assert await cache_module.cache_service.acquire_lock("lock", "v", expire=60) is True
