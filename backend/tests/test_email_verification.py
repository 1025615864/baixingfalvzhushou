"""Tests for email verification service."""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.email.verification import (
    EmailVerificationTokenData,
    email_verification_service,
    EmailVerificationService,
)


class TestEmailVerificationTokenDataTypedDict:
    """Test EmailVerificationTokenData TypedDict."""

    def test_token_data_is_typeddict(self) -> None:
        """Test EmailVerificationTokenData is a TypedDict."""
        # EmailVerificationTokenData is a TypedDict, not a class
        data: EmailVerificationTokenData = {
            "user_id": 123,
            "email": "test@oyjz.online",
            "expires_at": "2024-01-01T00:00:00Z",
            "used": False
        }
        assert data["user_id"] == 123
        assert data["email"] == "test@oyjz.online"
        assert data["expires_at"] == "2024-01-01T00:00:00Z"
        assert data["used"] is False

    def test_token_data_has_required_fields(self) -> None:
        """Test TypedDict has required fields."""
        data: EmailVerificationTokenData = {
            "user_id": 456,
            "email": "user@oyjz.online",
            "expires_at": "2024-12-31T23:59:59Z",
            "used": False
        }
        assert "user_id" in data
        assert "email" in data
        assert "expires_at" in data
        assert "used" in data

    def test_token_data_with_all_fields(self) -> None:
        """Test TypedDict with all fields."""
        data: EmailVerificationTokenData = {
            "user_id": 789,
            "email": "full@oyjz.online",
            "expires_at": "2024-06-15T12:30:00Z",
            "used": True
        }
        assert data["user_id"] == 789
        assert data["used"] is True


class TestEmailVerificationService:
    """Test EmailVerificationService class."""

    def test_service_exists(self) -> None:
        """Test EmailVerificationService class exists."""
        assert EmailVerificationService is not None

    def test_singleton_exists(self) -> None:
        """Test email_verification_service singleton exists."""
        assert email_verification_service is not None
        assert isinstance(email_verification_service, EmailVerificationService)

    def test_service_has_generate_token_method(self) -> None:
        """Test EmailVerificationService has generate_token method."""
        service = email_verification_service
        assert hasattr(service, 'generate_token')
        assert callable(service.generate_token)

    def test_service_has_verify_token_method(self) -> None:
        """Test EmailVerificationService has verify_token method."""
        service = email_verification_service
        assert hasattr(service, 'verify_token')
        assert callable(service.verify_token)

    def test_service_has_invalidate_token_method(self) -> None:
        """Test EmailVerificationService has invalidate_token method."""
        service = email_verification_service
        assert hasattr(service, 'invalidate_token')
        assert callable(service.invalidate_token)

    def test_service_can_be_instantiated(self) -> None:
        """Test EmailVerificationService can be instantiated."""
        service = EmailVerificationService()
        assert service is not None


class TestEmailVerificationServiceGeneration:
    """Test token generation methods."""

    def test_generate_token_is_async(self) -> None:
        """Test generate_token is an async method."""
        import inspect
        service = EmailVerificationService()
        assert inspect.iscoroutinefunction(service.generate_token)

    def test_generate_token_signature(self) -> None:
        """Test generate_token has correct signature."""
        import inspect
        sig = inspect.signature(EmailVerificationService.generate_token)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "user_id" in params
        assert "email" in params


class TestEmailVerificationServiceValidation:
    """Test validation methods."""

    def test_verify_token_is_async(self) -> None:
        """Test verify_token is an async method."""
        import inspect
        service = EmailVerificationService()
        assert hasattr(service, 'verify_token')
        assert inspect.iscoroutinefunction(service.verify_token)


class TestEmailVerificationServiceInvalidation:
    """Test invalidation methods."""

    def test_invalidate_token_is_async(self) -> None:
        """Test invalidate_token is an async method."""
        import inspect
        service = EmailVerificationService()
        assert inspect.iscoroutinefunction(service.invalidate_token)


class TestEmailVerificationServiceEdgeCases:
    """Test edge cases."""

    def test_service_constants_exist(self) -> None:
        """Test that service constants are defined."""
        from app.services.email.verification import (
            _EMAIL_VERIFY_TOKEN_PREFIX,
            _EMAIL_VERIFY_TOKEN_TTL_SECONDS,
        )
        assert isinstance(_EMAIL_VERIFY_TOKEN_PREFIX, str)
        assert isinstance(_EMAIL_VERIFY_TOKEN_TTL_SECONDS, int)
        assert _EMAIL_VERIFY_TOKEN_TTL_SECONDS > 0

    def test_ttl_is_24_hours(self) -> None:
        """Test that TTL is 24 hours."""
        from app.services.email.verification import _EMAIL_VERIFY_TOKEN_TTL_SECONDS
        # 24 hours = 86400 seconds
        assert _EMAIL_VERIFY_TOKEN_TTL_SECONDS == 60 * 60 * 24


class TestEmailVerificationServiceIntegration:
    """Integration tests."""

    def test_service_module_exports(self) -> None:
        """Test that module exports are correct."""
        from app.services.email import verification
        assert hasattr(verification, 'EmailVerificationTokenData')
        assert hasattr(verification, 'EmailVerificationService')
        assert hasattr(verification, 'email_verification_service')
