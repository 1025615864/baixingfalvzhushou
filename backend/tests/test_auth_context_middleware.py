"""测试认证上下文中间件"""
from fastapi import FastAPI, Request
from httpx import AsyncClient, ASGITransport
import pytest

from app.middleware.auth_context_middleware import AuthContextMiddleware


@pytest.mark.asyncio
async def test_auth_context_middleware_sub_not_int_sets_none(monkeypatch):
    """测试当sub不是整数时设置user_id为None"""
    import app.middleware.auth_context_middleware as m

    def fake_decode_token(token: str):
        return {"sub": "abc"}

    monkeypatch.setattr(m, "decode_access_token", fake_decode_token, raising=True)

    app = FastAPI()
    app.add_middleware(AuthContextMiddleware)

    @app.get("/x")
    async def x(request: Request):
        return {"user_id": request.state.user_id}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/x", headers={"Authorization": "Bearer token"})
        assert res.status_code == 200
        assert res.json()["user_id"] is None


@pytest.mark.asyncio
async def test_auth_context_middleware_decode_token_raises_sets_none(monkeypatch):
    """测试当decode_token抛出异常时设置user_id为None"""
    import app.middleware.auth_context_middleware as m

    def fake_decode_token(token: str):
        raise RuntimeError("boom")

    monkeypatch.setattr(m, "decode_access_token", fake_decode_token, raising=True)

    app = FastAPI()
    app.add_middleware(AuthContextMiddleware)

    @app.get("/x")
    async def x(request: Request):
        return {"user_id": request.state.user_id}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/x", headers={"Authorization": "Bearer token"})
        assert res.status_code == 200
        assert res.json()["user_id"] is None


@pytest.mark.asyncio
async def test_auth_context_middleware_valid_token_via_header(monkeypatch):
    """测试通过Authorization Header的有效token"""
    import app.middleware.auth_context_middleware as m

    def fake_decode_token(token: str):
        return {"sub": "123"}

    monkeypatch.setattr(m, "decode_access_token", fake_decode_token, raising=True)

    app = FastAPI()
    app.add_middleware(AuthContextMiddleware)

    @app.get("/x")
    async def x(request: Request):
        return {"user_id": request.state.user_id}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/x", headers={"Authorization": "Bearer valid_token"})
        assert res.status_code == 200
        assert res.json()["user_id"] == 123


@pytest.mark.asyncio
async def test_auth_context_middleware_valid_token_via_cookie(monkeypatch):
    """测试通过Cookie的有效token"""
    import app.middleware.auth_context_middleware as m

    def fake_decode_token(token: str):
        return {"sub": "456"}

    monkeypatch.setattr(m, "decode_access_token", fake_decode_token, raising=True)

    app = FastAPI()
    app.add_middleware(AuthContextMiddleware)

    @app.get("/x")
    async def x(request: Request):
        return {"user_id": request.state.user_id}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/x", cookies={"access_token": "valid_cookie_token"})
        assert res.status_code == 200
        assert res.json()["user_id"] == 456


@pytest.mark.asyncio
async def test_auth_context_middleware_header_takes_priority_over_cookie(monkeypatch):
    """测试Authorization Header优先于Cookie"""
    import app.middleware.auth_context_middleware as m

    def fake_decode_token(token: str):
        # 返回不同的user_id来区分来源
        if "header_token" in token:
            return {"sub": "100"}
        elif "cookie_token" in token:
            return {"sub": "200"}
        return None

    monkeypatch.setattr(m, "decode_access_token", fake_decode_token, raising=True)

    app = FastAPI()
    app.add_middleware(AuthContextMiddleware)

    @app.get("/x")
    async def x(request: Request):
        return {"user_id": request.state.user_id}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 同时提供Header和Cookie，应优先使用Header
        res = await ac.get("/x",
                         headers={"Authorization": "Bearer header_token"},
                         cookies={"access_token": "cookie_token"})
        assert res.status_code == 200
        assert res.json()["user_id"] == 100


@pytest.mark.asyncio
async def test_auth_context_middleware_no_authentication():
    """测试没有认证的情况"""
    app = FastAPI()
    app.add_middleware(AuthContextMiddleware)

    @app.get("/x")
    async def x(request: Request):
        return {"user_id": request.state.user_id}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/x")
        assert res.status_code == 200
        assert res.json()["user_id"] is None


@pytest.mark.asyncio
async def test_auth_context_middleware_invalid_token_format(monkeypatch):
    """测试无效的token格式"""
    import app.middleware.auth_context_middleware as m

    def fake_decode_token(token: str):
        return {"sub": "123"}

    monkeypatch.setattr(m, "decode_access_token", fake_decode_token, raising=True)

    app = FastAPI()
    app.add_middleware(AuthContextMiddleware)

    @app.get("/x")
    async def x(request: Request):
        return {"user_id": request.state.user_id}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 使用无效的Bearer格式
        res = await ac.get("/x", headers={"Authorization": "InvalidFormat token"})
        assert res.status_code == 200
        assert res.json()["user_id"] is None


@pytest.mark.asyncio
async def test_auth_context_middleware_missing_bearer_prefix(monkeypatch):
    """测试缺少Bearer前缀的情况"""
    import app.middleware.auth_context_middleware as m

    call_count = [0]

    def fake_decode_token(token: str):
        call_count[0] += 1
        return {"sub": "123"}

    monkeypatch.setattr(m, "decode_access_token", fake_decode_token, raising=True)

    app = FastAPI()
    app.add_middleware(AuthContextMiddleware)

    @app.get("/x")
    async def x(request: Request):
        return {"user_id": request.state.user_id, "decode_calls": call_count[0]}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 没有Bearer前缀，但有大写BEARER
        res = await ac.get("/x", headers={"Authorization": "BEARER token"})
        assert res.status_code == 200
        data = res.json()
        assert data["user_id"] == 123
        assert data["decode_calls"] == 1  # 应该调用一次decode


@pytest.mark.asyncio
async def test_auth_context_middleware_empty_header(monkeypatch):
    """测试空的Authorization Header"""
    import app.middleware.auth_context_middleware as m

    call_count = [0]

    def fake_decode_token(token: str):
        call_count[0] += 1
        return {"sub": "123"}

    monkeypatch.setattr(m, "decode_access_token", fake_decode_token, raising=True)

    app = FastAPI()
    app.add_middleware(AuthContextMiddleware)

    @app.get("/x")
    async def x(request: Request):
        return {"user_id": request.state.user_id, "decode_calls": call_count[0]}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 空的Authorization Header
        res = await ac.get("/x", headers={"Authorization": ""})
        assert res.status_code == 200
        data = res.json()
        assert data["user_id"] is None
        assert data["decode_calls"] == 0  # 不应该调用decode


@pytest.mark.asyncio
async def test_auth_context_middleware_none_sub_in_payload(monkeypatch):
    """测试payload中sub为None的情况"""
    import app.middleware.auth_context_middleware as m

    def fake_decode_token(token: str):
        return {"sub": None}

    monkeypatch.setattr(m, "decode_access_token", fake_decode_token, raising=True)

    app = FastAPI()
    app.add_middleware(AuthContextMiddleware)

    @app.get("/x")
    async def x(request: Request):
        return {"user_id": request.state.user_id}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/x", headers={"Authorization": "Bearer token"})
        assert res.status_code == 200
        assert res.json()["user_id"] is None


@pytest.mark.asyncio
async def test_auth_context_middleware_missing_sub_in_payload(monkeypatch):
    """测试payload中缺少sub字段的情况"""
    import app.middleware.auth_context_middleware as m

    def fake_decode_token(token: str):
        return {"user_id": "123"}  # 没有sub字段

    monkeypatch.setattr(m, "decode_access_token", fake_decode_token, raising=True)

    app = FastAPI()
    app.add_middleware(AuthContextMiddleware)

    @app.get("/x")
    async def x(request: Request):
        return {"user_id": request.state.user_id}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/x", headers={"Authorization": "Bearer token"})
        assert res.status_code == 200
        assert res.json()["user_id"] is None


@pytest.mark.asyncio
async def test_auth_context_middleware_empty_cookie_token(monkeypatch):
    """测试Cookie中有空的access_token"""
    import app.middleware.auth_context_middleware as m

    call_count = [0]

    def fake_decode_token(token: str):
        call_count[0] += 1
        return {"sub": "123"}

    monkeypatch.setattr(m, "decode_access_token", fake_decode_token, raising=True)

    app = FastAPI()
    app.add_middleware(AuthContextMiddleware)

    @app.get("/x")
    async def x(request: Request):
        return {"user_id": request.state.user_id, "decode_calls": call_count[0]}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 空的cookie token
        res = await ac.get("/x", cookies={"access_token": ""})
        assert res.status_code == 200
        data = res.json()
        assert data["user_id"] is None
        assert data["decode_calls"] == 0  # 不应该调用decode
