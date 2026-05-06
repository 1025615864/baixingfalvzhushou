"""User Service Provider 契约测试

作为 Provider，验证 User Service 正确响应其他服务（Consumer）依赖的契约。

Consumer 列表:
- LegalService: 依赖 UserService 验证律师资质
- CommunityService: 依赖 UserService 获取用户信息
- PaymentService: 依赖 UserService 验证用户配额
- AIService: 依赖 UserService 验证用户权限
"""
import pytest
from pact import Provider, V3Pact
from pact.matchers import like, something_like, each_like, Term
from datetime import datetime


class TestUserServiceProvider:
    """User Service Provider 契约测试"""

    @pytest.fixture
    def pact(self, tmp_path):
        log_dir = tmp_path / "logs"
        log_dir.mkdir(exist_ok=True)

        pact_dir = tmp_path / "pacts"
        pact_dir.mkdir(exist_ok=True)

        pact = V3Pact(
            consumer=V3Pact.consumer("CommunityService"),
            provider=V3Pact.provider("UserService"),
            pact_dir=str(pact_dir),
            log_dir=str(log_dir),
        )
        return pact

    def test_get_user_profile(self, pact):
        """CommunityService 获取用户信息"""
        (
            pact
            .given("User with ID 12345 exists", provider_state="user_exists")
            .upon_receiving("a request for user profile")
            .with_request(
                method="GET",
                path="/api/v1/users/12345",
                headers={
                    "Accept": "application/json",
                    "X-Request-ID": "test-request-123",
                }
            )
            .will_respond_with(
                status=200,
                headers={
                    "Content-Type": "application/json",
                    "X-Request-ID": "test-request-123",
                },
                body={
                    "id": 12345,
                    "username": like("testuser"),
                    "nickname": like("Test User"),
                    "email": like("test@example.com"),
                    "phone": like("13800138000"),
                    "role": like("user"),
                    "status": like("active"),
                    "avatar": like("https://example.com/avatar.jpg"),
                    "is_active": True,
                    "email_verified": False,
                    "created_at": Term(
                        matcher=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
                        generate="2024-01-01T00:00:00"
                    ),
                }
            )
        )

        import httpx
        with pact:
            response = httpx.get(
                f"{pact.mock_service}/api/v1/users/12345",
                headers={
                    "Accept": "application/json",
                    "X-Request-ID": "test-request-123",
                }
            )

            assert response.status_code == 200

    def test_get_user_by_phone(self, pact):
        """通过手机号获取用户信息"""
        (
            pact
            .given("User with phone 13800138000 exists", provider_state="user_with_phone_exists")
            .upon_receiving("a request for user by phone")
            .with_request(
                method="GET",
                path="/api/v1/users/by-phone/13800138000",
                headers={"Accept": "application/json"}
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body={
                    "id": like(12345),
                    "phone": "13800138000",
                    "role": like("user"),
                    "status": like("active"),
                }
            )
        )

        import httpx
        with pact:
            response = httpx.get(
                f"{pact.mock_service}/api/v1/users/by-phone/13800138000",
                headers={"Accept": "application/json"}
            )

            assert response.status_code == 200

    def test_validate_token(self, pact):
        """验证 JWT Token"""
        (
            pact
            .given("A valid token for user 12345", provider_state="valid_token_exists")
            .upon_receiving("a request to validate token")
            .with_request(
                method="POST",
                path="/api/v1/auth/validate",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                body={
                    "token": like("eyJhbGcOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
                }
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body={
                    "valid": True,
                    "user_id": 12345,
                    "role": like("user"),
                    "exp": like(1734288000),
                }
            )
        )

        import httpx
        with pact:
            response = httpx.post(
                f"{pact.mock_service}/api/v1/auth/validate",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                json={"token": "eyJhbGcOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
            )

            assert response.status_code == 200

    def test_get_membership_info(self, pact):
        """获取会员信息"""
        (
            pact
            .given("User 12345 is a VIP member", provider_state="user_vip_member")
            .upon_receiving("a request for membership info")
            .with_request(
                method="GET",
                path="/api/v1/membership/user/12345",
                headers={"Accept": "application/json"}
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body={
                    "user_id": 12345,
                    "level": like("vip"),
                    "level_name": like("VIP会员"),
                    "expired_at": Term(
                        matcher=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
                        generate="2025-12-31T23:59:59"
                    ),
                    "benefits": each_like("免费咨询", min=3),
                }
            )
        )

        import httpx
        with pact:
            response = httpx.get(
                f"{pact.mock_service}/api/v1/membership/user/12345",
                headers={"Accept": "application/json"}
            )

            assert response.status_code == 200

    def test_check_permission(self, pact):
        """检查用户权限"""
        (
            pact
            .given("User 12345 has lawyer permission", provider_state="user_is_lawyer")
            .upon_receiving("a request to check lawyer permission")
            .with_request(
                method="POST",
                path="/api/v1/users/check-permission",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                body={
                    "user_id": 12345,
                    "permission": "post_legal_content",
                }
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body={
                    "allowed": True,
                    "user_id": 12345,
                    "permission": "post_legal_content",
                }
            )
        )

        import httpx
        with pact:
            response = httpx.post(
                f"{pact.mock_service}/api/v1/users/check-permission",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                json={
                    "user_id": 12345,
                    "permission": "post_legal_content",
                }
            )

            assert response.status_code == 200


class TestUserServiceBatchProvider:
    """User Service 批量操作 Provider 契约测试"""

    @pytest.fixture
    def pact(self, tmp_path):
        log_dir = tmp_path / "logs"
        log_dir.mkdir(exist_ok=True)

        pact_dir = tmp_path / "pacts"
        pact_dir.mkdir(exist_ok=True)

        pact = V3Pact(
            consumer=V3Pact.consumer("CommunityService"),
            provider=V3Pact.provider("UserService"),
            pact_dir=str(pact_dir),
            log_dir=str(log_dir),
        )
        return pact

    def test_batch_get_users(self, pact):
        """批量获取用户信息 (N+1 优化)"""
        (
            pact
            .given("Users 1, 2, 3 exist", provider_state="multiple_users_exist")
            .upon_receiving("a request to batch get users")
            .with_request(
                method="POST",
                path="/api/v1/users/batch",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                body={
                    "user_ids": [1, 2, 3],
                }
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body={
                    "users": each_like(
                        {
                            "id": like(1),
                            "username": like("user1"),
                            "nickname": like("User One"),
                            "avatar": like("https://example.com/avatar1.jpg"),
                            "role": like("user"),
                            "status": like("active"),
                        },
                        min=3
                    ),
                    "not_found": [],
                }
            )
        )

        import httpx
        with pact:
            response = httpx.post(
                f"{pact.mock_service}/api/v1/users/batch",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                json={"user_ids": [1, 2, 3]}
            )

            assert response.status_code == 200


class TestUserServiceHealthProvider:
    """User Service 健康检查 Provider 契约测试"""

    @pytest.fixture
    def pact(self, tmp_path):
        log_dir = tmp_path / "logs"
        log_dir.mkdir(exist_ok=True)

        pact_dir = tmp_path / "pacts"
        pact_dir.mkdir(exist_ok=True)

        pact = V3Pact(
            consumer=V3Pact.consumer("GatewayService"),
            provider=V3Pact.provider("UserService"),
            pact_dir=str(pact_dir),
            log_dir=str(log_dir),
        )
        return pact

    def test_health_check(self, pact):
        """健康检查端点"""
        (
            pact
            .given("UserService is running")
            .upon_receiving("a health check request")
            .with_request(
                method="GET",
                path="/health"
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body={
                    "status": "healthy",
                    "service": "user-service",
                }
            )
        )

        import httpx
        with pact:
            response = httpx.get(f"{pact.mock_service}/health")
            assert response.status_code == 200

    def test_readiness_check(self, pact):
        """就绪检查端点 (依赖检查)"""
        (
            pact
            .given("UserService is ready")
            .upon_receiving("a readiness check request")
            .with_request(
                method="GET",
                path="/health/ready"
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body={
                    "status": "ready",
                    "checks": {
                        "database": "ok",
                        "redis": "ok",
                    }
                }
            )
        )

        import httpx
        with pact:
            response = httpx.get(f"{pact.mock_service}/health/ready")
            assert response.status_code == 200
