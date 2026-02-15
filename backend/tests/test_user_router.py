"""
测试用户API路由

测试用户相关的所有端点，包括：
- 用户注册
- 用户登录
- 用户信息获取和更新
- 密码管理（修改、重置）
- 邮箱验证
- 短信验证
- 配额管理
- 管理员功能
"""
import pytest
from httpx import AsyncClient
from datetime import datetime, timezone
from pytest import MonkeyPatch

from tests.helpers.test_data_factory import UserFactory
from tests.helpers.assertion_helpers import assert_response_success


class TestUserRegister:
    """测试用户注册功能"""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient, db):
        """测试成功注册新用户"""
        # Arrange
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "nickname": "新用户",
            "agree_terms": True,
            "agree_privacy": True,
            "agree_ai_disclaimer": True,
        }

        # Act
        response = await client.post("/api/user/register", json=user_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["username"] == "newuser"
        assert data["user"]["email"] == "newuser@example.com"
        assert "user" in data
        assert "id" in data["user"]
        assert data["message"] is not None

    @pytest.mark.asyncio
    async def test_register_missing_agreements(self, client: AsyncClient):
        """测试未同意协议时的注册失败"""
        # Arrange
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "agree_terms": False,
            "agree_privacy": False,
            "agree_ai_disclaimer": False,
        }

        # Act
        response = await client.post("/api/user/register", json=user_data)

        # Assert
        assert response.status_code == 400
        assert "请阅读并同意" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient, db):
        """测试重复用户名注册失败"""
        # Arrange - 先创建一个用户
        existing_user = await UserFactory.create_user(
            db,
            username="existinguser",
            email="existing@example.com"
        )

        # Act - 尝试用相同用户名注册
        user_data = {
            "username": "existinguser",
            "email": "newuser@example.com",
            "password": "password123",
            "agree_terms": True,
            "agree_privacy": True,
            "agree_ai_disclaimer": True,
        }
        response = await client.post("/api/user/register", json=user_data)

        # Assert
        assert response.status_code == 400
        assert "用户名已被使用" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, db):
        """测试重复邮箱注册失败"""
        # Arrange
        existing_user = await UserFactory.create_user(
            db,
            username="user1",
            email="existing@example.com"
        )

        # Act
        user_data = {
            "username": "newuser",
            "email": "existing@example.com",
            "password": "password123",
            "agree_terms": True,
            "agree_privacy": True,
            "agree_ai_disclaimer": True,
        }
        response = await client.post("/api/user/register", json=user_data)

        # Assert
        assert response.status_code == 400
        assert "邮箱已被注册" in response.json()["detail"]


class TestUserLogin:
    """测试用户登录功能"""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, db):
        """测试成功登录"""
        # Arrange - 创建测试用户并设置密码
        from app.utils.security import hash_password
        
        user = await UserFactory.create_user(db, username="testuser")
        user.hashed_password = hash_password("password123")
        await db.commit()

        # Act
        login_data = {"username": "testuser", "password": "password123"}
        response = await client.post("/api/user/login", json=login_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["username"] == "testuser"
        assert "token" in data
        assert "access_token" in data["token"]
        assert data["message"] == "登录成功"

    @pytest.mark.asyncio
    async def test_login_with_invalid_credentials(self, client: AsyncClient):
        """测试使用无效凭据登录"""
        # Arrange
        login_data = {"username": "nonexistent", "password": "wrongpass"}

        # Act
        response = await client.post("/api/user/login", json=login_data)

        # Assert
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_with_wrong_password(self, client: AsyncClient, db):
        """测试使用错误密码登录"""
        # Arrange
        from app.utils.security import hash_password
        
        user = await UserFactory.create_user(db, username="testuser")
        user.hashed_password = hash_password("password123")
        await db.commit()

        # Act
        login_data = {"username": "testuser", "password": "wrongpass"}
        response = await client.post("/api/user/login", json=login_data)

        # Assert
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_with_inactive_account(self, client: AsyncClient, db):
        """测试使用已禁用账号登录"""
        # Arrange
        from app.utils.security import hash_password
        
        user = await UserFactory.create_user(db, username="testuser")
        user.hashed_password = hash_password("password123")
        user.is_active = False  # 禁用账号
        await db.commit()

        # Act
        login_data = {"username": "testuser", "password": "password123"}
        response = await client.post("/api/user/login", json=login_data)

        # Assert
        assert response.status_code == 403
        assert "账号已被禁用" in response.json()["detail"]


class TestGetCurrentUser:
    """测试获取当前用户信息"""

    @pytest.mark.asyncio
    async def test_get_me_without_auth(self, client: AsyncClient):
        """测试未认证访问获取当前用户信息"""
        # Act
        response = await client.get("/api/user/me")

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_with_auth(self, client: AsyncClient, test_user):
        """测试认证后获取当前用户信息"""
        # Arrange
        from app.utils.security import create_access_token
        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = await client.get("/api/user/me", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email

    @pytest.mark.asyncio
    async def test_update_me_without_auth(self, client: AsyncClient):
        """测试未认证更新用户信息"""
        # Arrange
        update_data = {"nickname": "新昵称"}

        # Act
        response = await client.put("/api/user/me", json=update_data)

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_me_success(self, client: AsyncClient, test_user, db):
        """测试认证后成功更新用户信息"""
        # Arrange
        from app.utils.security import create_access_token
        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        update_data = {"nickname": "新昵称"}

        # Act
        response = await client.put("/api/user/me", json=update_data, headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["nickname"] == "新昵称"

    @pytest.mark.asyncio
    async def test_update_me_phone_directly_fails(self, client: AsyncClient, test_user, db):
        """测试直接更新手机号失败（需要短信验证）"""
        # Arrange
        from app.utils.security import create_access_token
        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        update_data = {"phone": "13800138000"}

        # Act
        response = await client.put("/api/user/me", json=update_data, headers=headers)

        # Assert
        assert response.status_code == 400
        assert "手机号请通过短信验证码完成绑定" in response.json()["detail"]


class TestUserPasswordChange:
    """测试密码修改功能"""

    @pytest.mark.asyncio
    async def test_change_password_without_auth(self, client: AsyncClient):
        """测试未认证修改密码"""
        # Arrange
        password_data = {
            "old_password": "oldpass",
            "new_password": "newpass123"
        }

        # Act
        response = await client.put("/api/user/me/password", json=password_data)

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_change_password_success(self, client: AsyncClient, test_user, db):
        """测试成功修改密码"""
        # Arrange
        from app.utils.security import create_access_token, hash_password
        test_user.hashed_password = hash_password("oldpass123")
        await db.commit()

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        password_data = {
            "old_password": "oldpass123",
            "new_password": "newpass123"
        }

        # Act
        response = await client.put("/api/user/me/password", json=password_data, headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "密码修改成功" in data["message"]
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_change_password_wrong_old_password(self, client: AsyncClient, test_user, db):
        """测试使用错误的旧密码修改"""
        # Arrange
        from app.utils.security import create_access_token, hash_password
        test_user.hashed_password = hash_password("oldpass123")
        await db.commit()

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        password_data = {
            "old_password": "wrongpass",
            "new_password": "newpass123"
        }

        # Act
        response = await client.put("/api/user/me/password", json=password_data, headers=headers)

        # Assert
        assert response.status_code == 400
        assert "当前密码错误" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_change_password_same_as_old(self, client: AsyncClient, test_user, db):
        """测试新密码与旧密码相同"""
        # Arrange
        from app.utils.security import create_access_token, hash_password
        test_user.hashed_password = hash_password("samepass123")
        await db.commit()

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        password_data = {
            "old_password": "samepass123",
            "new_password": "samepass123"
        }

        # Act
        response = await client.put("/api/user/me/password", json=password_data, headers=headers)

        # Assert
        assert response.status_code == 400
        assert "新密码不能与当前密码相同" in response.json()["detail"]


class TestPasswordReset:
    """测试密码重置功能"""

    @pytest.mark.asyncio
    async def test_request_password_reset_success(self, client: AsyncClient, db):
        """测试成功请求密码重置"""
        # Arrange
        user = await UserFactory.create_user(db, username="testuser", email="test@example.com")

        # Act
        request_data = {"email": "test@example.com"}
        response = await client.post("/api/user/password-reset/request", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "如果邮箱存在" in data["message"]

    @pytest.mark.asyncio
    async def test_request_password_reset_nonexistent_email(self, client: AsyncClient):
        """测试请求不存在的邮箱密码重置（出于安全考虑返回成功）"""
        # Arrange
        request_data = {"email": "nonexistent@example.com"}

        # Act
        response = await client.post("/api/user/password-reset/request", json=request_data)

        # Assert
        assert response.status_code == 200
        # 出于安全考虑，不透露邮箱是否存在
        data = response.json()
        assert "如果邮箱存在" in data["message"]

    @pytest.mark.asyncio
    async def test_confirm_password_reset_success(self, client: AsyncClient, db):
        """测试成功确认密码重置"""
        # Arrange
        from app.services.email_service import email_service

        user = await UserFactory.create_user(db, username="testuser", email="test@example.com")

        # 生成重置令牌
        reset_token = await email_service.generate_reset_token(user.id, user.email)

        # Act
        confirm_data = {
            "token": reset_token,
            "new_password": "newpass123"
        }
        response = await client.post("/api/user/password-reset/confirm", json=confirm_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "密码重置成功" in data["message"]

    @pytest.mark.asyncio
    async def test_confirm_password_reset_invalid_token(self, client: AsyncClient):
        """测试使用无效令牌确认密码重置"""
        # Arrange
        confirm_data = {
            "token": "invalid_token",
            "new_password": "newpass123"
        }

        # Act
        response = await client.post("/api/user/password-reset/confirm", json=confirm_data)

        # Assert
        assert response.status_code == 400
        assert "无效或已过期的重置令牌" in response.json()["detail"]


class TestEmailVerification:
    """测试邮箱验证功能"""

    @pytest.mark.asyncio
    async def test_request_email_verification_success(self, client: AsyncClient, test_user, db, monkeypatch: MonkeyPatch):
        """测试成功请求邮箱验证"""
        # Arrange
        from app.utils.security import create_access_token
        from app.services.email_service import email_service

        # Mock邮件配置
        async def mock_configure_from_db(db):
            return True

        async def mock_send_email_verification_email(email, verify_url, user_id=None):
            return True

        monkeypatch.setattr(email_service, "configure_from_db", mock_configure_from_db)
        monkeypatch.setattr(email_service, "send_email_verification_email", mock_send_email_verification_email)

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = await client.post("/api/user/email-verification/request", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "验证邮件已发送" in data["message"]

    @pytest.mark.asyncio
    async def test_verify_email_success(self, client: AsyncClient, db):
        """测试成功验证邮箱"""
        # Arrange
        from app.services.email_service import email_service

        user = await UserFactory.create_user(db, username="testuser", email="test@example.com")
        user.email_verified = False
        await db.commit()

        # 生成验证令牌
        verify_token = await email_service.generate_email_verification_token(user.id, user.email)

        # Act
        response = await client.get(f"/api/user/email-verification/verify?token={verify_token}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "邮箱验证成功" in data["message"]
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self, client: AsyncClient):
        """测试使用无效令牌验证邮箱"""
        # Act
        response = await client.get("/api/user/email-verification/verify?token=invalid_token")

        # Assert
        assert response.status_code == 400
        assert "无效或已过期的验证令牌" in response.json()["detail"]


class TestSMSVerification:
    """测试短信验证功能"""

    @pytest.mark.asyncio
    async def test_send_sms_code_success(self, client: AsyncClient, test_user, db, monkeypatch: MonkeyPatch):
        """测试成功发送短信验证码"""
        # Arrange
        from app.utils.security import create_access_token

        # 设置debug模式以获取验证码
        monkeypatch.setenv("DEBUG", "true")
        from app.config import get_settings
        get_settings.cache_clear()
        settings = get_settings()

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        sms_data = {
            "phone": "13800138000",
            "scene": "bind_phone"
        }

        # Act
        response = await client.post("/api/user/sms/send", json=sms_data, headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "code" in data if settings.debug else "code" not in data
        assert "验证码已发送" in data["message"]

    @pytest.mark.asyncio
    async def test_verify_sms_code_success(self, client: AsyncClient, test_user, db, monkeypatch: MonkeyPatch):
        """测试成功验证短信验证码并绑定手机号"""
        # Arrange
        from app.utils.security import create_access_token
        from app.services.cache_service import cache_service

        # 设置debug模式
        monkeypatch.setenv("DEBUG", "true")
        from app.config import get_settings
        get_settings.cache_clear()

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # 先发送验证码
        phone = "13800138000"
        cache_key = f"sms_code:bind_phone:{phone}"
        test_code = "123456"
        await cache_service.set_json(
            cache_key,
            {
                "code": test_code,
                "phone": phone,
                "scene": "bind_phone",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            expire=300,
        )

        # Act - 验证验证码
        verify_data = {
            "phone": phone,
            "code": test_code,
            "scene": "bind_phone"
        }
        response = await client.post("/api/user/sms/verify", json=verify_data, headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "手机验证成功" in data["message"]

    @pytest.mark.asyncio
    async def test_verify_sms_code_invalid_code(self, client: AsyncClient, test_user, db):
        """测试使用无效验证码"""
        # Arrange
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        verify_data = {
            "phone": "13800138000",
            "code": "wrongcode",
            "scene": "bind_phone"
        }

        # Act
        response = await client.post("/api/user/sms/verify", json=verify_data, headers=headers)

        # Assert
        assert response.status_code == 400
        assert "验证码无效或已过期" in response.json()["detail"]


class TestUserPermissions:
    """测试用户权限管理"""

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, client: AsyncClient, test_user, db):
        """测试成功获取指定用户信息"""
        # Act
        response = await client.get(f"/api/user/{test_user.id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["username"] == test_user.username

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, client: AsyncClient):
        """测试获取不存在的用户"""
        # Act
        response = await client.get("/api/user/99999")

        # Assert
        assert response.status_code == 404
        assert "用户不存在" in response.json()["detail"]


class TestAdminFunctions:
    """测试管理员功能"""

    @pytest.mark.asyncio
    async def test_admin_list_users_success(self, client: AsyncClient, test_admin_user, db):
        """测试管理员成功获取用户列表"""
        # Arrange
        from app.utils.security import create_access_token

        # 创建一些测试用户
        for i in range(5):
            await UserFactory.create_user(db, username=f"user{i}", email=f"user{i}@example.com")

        token = create_access_token(data={"sub": str(test_admin_user.id), "role": "admin"})
        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = await client.get("/api/user/admin/list", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 5

    @pytest.mark.asyncio
    async def test_admin_list_users_unauthorized(self, client: AsyncClient, test_user, db):
        """测试非管理员访问用户列表"""
        # Arrange
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id), "role": "user"})
        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = await client.get("/api/user/admin/list", headers=headers)

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_toggle_user_active_success(self, client: AsyncClient, test_admin_user, test_user, db):
        """测试管理员成功切换用户状态"""
        # Arrange
        from app.utils.security import create_access_token

        admin_token = create_access_token(data={"sub": str(test_admin_user.id), "role": "admin"})
        headers = {"Authorization": f"Bearer {admin_token}"}

        # Act
        response = await client.put(f"/api/user/admin/{test_user.id}/toggle-active", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        # 验证状态已切换（用户被禁用）
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_admin_toggle_user_active_cannot_toggle_self(self, client: AsyncClient, test_admin_user, db):
        """测试管理员不能切换自己的状态"""
        # Arrange
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_admin_user.id), "role": "admin"})
        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = await client.put(f"/api/user/admin/{test_admin_user.id}/toggle-active", headers=headers)

        # Assert
        assert response.status_code == 400
        assert "不能修改自己的状态" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_admin_update_user_role_success(self, client: AsyncClient, test_admin_user, test_user, db):
        """测试管理员成功修改用户角色"""
        # Arrange
        from app.utils.security import create_access_token

        admin_token = create_access_token(data={"sub": str(test_admin_user.id), "role": "admin"})
        headers = {"Authorization": f"Bearer {admin_token}"}

        # Act
        response = await client.put(f"/api/user/admin/{test_user.id}/role?role=lawyer", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "lawyer"

    @pytest.mark.asyncio
    async def test_admin_update_user_role_invalid_role(self, client: AsyncClient, test_admin_user, test_user, db):
        """测试使用无效角色修改"""
        # Arrange
        from app.utils.security import create_access_token

        admin_token = create_access_token(data={"sub": str(test_admin_user.id), "role": "admin"})
        headers = {"Authorization": f"Bearer {admin_token}"}

        # Act
        response = await client.put(f"/api/user/admin/{test_user.id}/role?role=invalidrole", headers=headers)

        # Assert
        assert response.status_code == 400
        assert "无效的角色" in response.json()["detail"]


class TestUserQuotas:
    """测试用户配额功能"""

    @pytest.mark.asyncio
    async def test_get_my_quotas(self, client: AsyncClient, test_user, db):
        """测试获取当前用户配额"""
        # Arrange
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = await client.get("/api/user/me/quotas", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        # 配额响应结构验证
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_get_quota_usage(self, client: AsyncClient, test_user, db):
        """测试获取配额消耗记录"""
        # Arrange
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = await client.get("/api/user/me/quota-usage?days=7&page=1&page_size=20", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        # 配额使用记录响应结构验证
        assert "usage" in data or isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_get_quota_usage_invalid_days(self, client: AsyncClient, test_user, db):
        """测试使用无效的天数参数"""
        # Arrange
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = await client.get("/api/user/me/quota-usage?days=500&page=1&page_size=20", headers=headers)

        # Assert
        assert response.status_code == 422  # Validation error


class TestDebugFunctions:
    """测试调试功能（仅debug模式）"""

    @pytest.mark.asyncio
    async def test_admin_debug_password_reset_token_not_in_debug(self, client: AsyncClient, test_admin_user, db):
        """测试非debug模式下访问调试端点"""
        # Arrange
        from app.utils.security import create_access_token

        # 确保不在debug模式
        import os
        if "DEBUG" in os.environ:
            del os.environ["DEBUG"]

        from app.config import get_settings
        get_settings.cache_clear()
        settings = get_settings()
        settings.debug = False

        admin_token = create_access_token(data={"sub": str(test_admin_user.id), "role": "admin"})
        headers = {"Authorization": f"Bearer {admin_token}"}

        request_data = {"email": "test@example.com"}

        # Act
        response = await client.post("/api/user/admin/debug/password-reset-token", json=request_data, headers=headers)

        # Assert
        assert response.status_code == 404
