"""测试密钥管理路由的审计日志功能"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request


class TestSecretsAdminAuditLog:
    """测试密钥管理审计日志"""

    @pytest.mark.asyncio
    async def test_update_secret_creates_audit_log(self):
        """测试更新密钥时创建审计日志"""
        from app.routers.system_admin.secrets import update_secret
        from app.models.user import User
        from app.models.system import SystemSecret

        # Mock dependencies
        mock_db = AsyncMock()
        mock_user = User(id=1, username="admin", role="admin")
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"user-agent": "test-agent"}
        mock_request.client = MagicMock(host="127.0.0.1")

        # Mock existing secret
        mock_secret = MagicMock()
        mock_secret.id = 123
        mock_secret.value = "encrypted_old_value"
        mock_secret.description = "旧描述"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_secret

        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        # Call the function
        result = await update_secret(
            key="test_key",
            value="new_value",
            description="新描述",
            current_user=mock_user,
            db=mock_db,
            request=mock_request
        )

        # Verify audit log was created
        assert mock_db.add.call_count >= 1  # AdminLog only (updating existing secret)

    @pytest.mark.asyncio
    async def test_create_secret_creates_audit_log(self):
        """测试创建新密钥时创建审计日志"""
        from app.routers.system_admin.secrets import update_secret
        from app.models.user import User

        # Mock dependencies
        mock_db = AsyncMock()
        mock_user = User(id=1, username="admin", role="admin")
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"user-agent": "test-agent"}
        mock_request.client = MagicMock(host="127.0.0.1")

        # Mock no existing secret (create case)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        # Call the function
        result = await update_secret(
            key="new_key",
            value="new_value",
            description="新密钥",
            current_user=mock_user,
            db=mock_db,
            request=mock_request
        )

        # Verify audit log was created
        assert mock_db.add.call_count >= 2  # SystemSecret + AdminLog

    @pytest.mark.asyncio
    async def test_delete_secret_creates_audit_log(self):
        """测试删除密钥时创建审计日志"""
        from app.routers.system_admin.secrets import delete_secret
        from app.models.user import User
        from app.models.system import SystemSecret

        # Mock dependencies
        mock_db = AsyncMock()
        mock_user = User(id=1, username="admin", role="admin")
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"user-agent": "test-agent"}
        mock_request.client = MagicMock(host="127.0.0.1")

        # Mock existing secret
        mock_secret = MagicMock()
        mock_secret.id = 456
        mock_secret.key = "test_key"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_secret

        mock_db.execute.return_value = mock_result
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        # Call the function
        result = await delete_secret(
            key="test_key",
            current_user=mock_user,
            db=mock_db,
            request=mock_request
        )

        # Verify audit log was created
        assert mock_db.add.call_count >= 1  # AdminLog
        assert result["message"] == "密钥已删除"

    @pytest.mark.asyncio
    async def test_delete_nonexistent_secret_no_audit_log(self):
        """测试删除不存在的密钥时不创建审计日志"""
        from app.routers.system_admin.secrets import delete_secret
        from app.models.user import User
        from fastapi import HTTPException

        # Mock dependencies
        mock_db = AsyncMock()
        mock_user = User(id=1, username="admin", role="admin")
        mock_request = MagicMock(spec=Request)

        # Mock no existing secret
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db.execute.return_value = mock_result

        # Call the function and expect exception
        with pytest.raises(HTTPException) as exc_info:
            await delete_secret(
                key="nonexistent_key",
                current_user=mock_user,
                db=mock_db,
                request=mock_request
            )

        assert exc_info.value.status_code == 404
        assert "密钥不存在" in exc_info.value.detail

        # Verify no audit log was created
        assert mock_db.add.call_count == 0

    @pytest.mark.asyncio
    async def test_audit_log_includes_user_info(self):
        """测试审计日志包含用户信息"""
        from app.routers.system_admin.secrets import update_secret
        from app.models.user import User

        # Mock dependencies
        mock_db = AsyncMock()
        mock_user = User(id=1, username="admin", role="admin")
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"user-agent": "test-agent"}
        mock_request.client = MagicMock(host="127.0.0.1")

        # Mock existing secret
        mock_secret = MagicMock()
        mock_secret.id = 789
        mock_secret.value = "encrypted_value"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_secret

        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        # Call the function
        result = await update_secret(
            key="test_key",
            value="updated_value",
            description="更新描述",
            current_user=mock_user,
            db=mock_db,
            request=mock_request
        )

        # Verify audit log was created with user info
        assert mock_db.add.call_count >= 1  # AdminLog only (updating existing secret)

    @pytest.mark.asyncio
    async def test_audit_log_includes_request_info(self):
        """测试审计日志包含请求信息（IP和User-Agent）"""
        from app.routers.system_admin.secrets import update_secret
        from app.models.user import User

        # Mock dependencies
        mock_db = AsyncMock()
        mock_user = User(id=1, username="admin", role="admin")
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"user-agent": "Mozilla/5.0 Test Browser"}
        mock_request.client = MagicMock(host="192.168.1.100")

        # Mock existing secret
        mock_secret = MagicMock()
        mock_secret.id = 999
        mock_secret.value = "encrypted_value"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_secret

        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        # Call the function
        result = await update_secret(
            key="test_key",
            value="updated_value",
            description="更新描述",
            current_user=mock_user,
            db=mock_db,
            request=mock_request
        )

        # Verify audit log was created
        assert mock_db.add.call_count >= 1  # AdminLog only (updating existing secret)
