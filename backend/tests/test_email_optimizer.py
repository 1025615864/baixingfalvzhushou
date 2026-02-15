"""Tests for email optimizer module."""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.email.optimizer import (
    EmailTemplateManager,
    EmailMetrics,
    OptimizedEmailService,
    optimized_email_service,
    send_email_with_template,
    get_email_delivery_report,
)


class TestEmailTemplateManager:
    """Test EmailTemplateManager class."""

    def test_get_template_text(self):
        """Test getting text template."""
        template = EmailTemplateManager.get_template("password_reset", "text")
        assert template is not None
        assert "重置密码" in template
        assert "{reset_url}" in template

    def test_get_template_html(self):
        """Test getting HTML template."""
        template = EmailTemplateManager.get_template("password_reset", "html")
        assert template is not None
        assert "<!DOCTYPE html>" in template
        assert "{reset_url}" in template

    def test_get_template_not_found(self):
        """Test getting non-existent template."""
        template = EmailTemplateManager.get_template("nonexistent", "text")
        assert template is None

    def test_render_template(self):
        """Test rendering text template."""
        result = EmailTemplateManager.render_template(
            "password_reset", {"reset_url": "http://oyjz.online/reset"}
        )
        assert "http://oyjz.online/reset" in result
        assert "{reset_url}" not in result

    def test_render_template_not_found(self):
        """Test rendering non-existent template returns empty string."""
        result = EmailTemplateManager.render_template(
            "nonexistent", {"reset_url": "http://oyjz.online/reset"}
        )
        assert result == ""

    def test_render_html_template(self):
        """Test rendering HTML template."""
        result = EmailTemplateManager.render_html_template(
            "email_verification", {"verify_url": "http://oyjz.online/verify"}
        )
        assert "http://oyjz.online/verify" in result
        assert "{verify_url}" not in result

    def test_render_html_template_not_found(self):
        """Test rendering non-existent HTML template returns empty string."""
        result = EmailTemplateManager.render_html_template(
            "nonexistent", {"verify_url": "http://oyjz.online/verify"}
        )
        assert result == ""

    def test_get_subject(self):
        """Test getting template subject."""
        subject = EmailTemplateManager.get_subject("password_reset")
        assert "密码重置" in subject

    def test_get_subject_not_found(self):
        """Test getting subject for non-existent template."""
        subject = EmailTemplateManager.get_subject("nonexistent")
        assert subject == ""


class TestEmailMetrics:
    """Test EmailMetrics class."""

    @pytest.mark.asyncio
    async def test_record_send_success(self):
        """Test recording successful send."""
        metrics = EmailMetrics()
        await metrics.record_send("password_reset", True)
        assert len(metrics._stats["sent"]) > 0

    @pytest.mark.asyncio
    async def test_record_send_failure(self):
        """Test recording failed send."""
        metrics = EmailMetrics()
        await metrics.record_send("password_reset", False, "timeout")
        assert len(metrics._stats["failed"]) > 0

    @pytest.mark.asyncio
    async def test_get_delivery_stats(self):
        """Test getting delivery statistics."""
        metrics = EmailMetrics()
        await metrics.record_send("password_reset", True)
        await metrics.record_send("password_reset", False, "error")
        
        stats = await metrics.get_delivery_stats()
        assert "period_days" in stats
        assert "total_sent" in stats
        assert "delivery_rate" in stats
        assert "by_template" in stats

    @pytest.mark.asyncio
    async def test_get_delivery_stats_by_template(self):
        """Test getting delivery stats for specific template."""
        metrics = EmailMetrics()
        await metrics.record_send("password_reset", True)
        
        stats = await metrics.get_delivery_stats(template_name="password_reset")
        assert "password_reset" in stats["by_template"]


class TestOptimizedEmailService:
    """Test OptimizedEmailService class."""

    def test_service_exists(self):
        """Test OptimizedEmailService exists."""
        assert OptimizedEmailService is not None

    def test_singleton_exists(self):
        """Test optimized_email_service singleton exists."""
        assert optimized_email_service is not None
        assert isinstance(optimized_email_service, OptimizedEmailService)

    @pytest.mark.asyncio
    async def test_send_templated_email_not_configured(self):
        """Test sending templated email when not configured."""
        service = OptimizedEmailService()
        success, error = await service.send_templated_email(
            "password_reset", "test@oyjz.online", {"reset_url": "http://oyjz.online"}
        )
        assert success is False
        assert "not configured" in error

    @pytest.mark.asyncio
    async def test_send_templated_email_success(self):
        """Test sending templated email successfully."""
        service = OptimizedEmailService()
        
        # Mock email service to be configured and send successfully
        with patch('app.services.email.optimizer.email_service') as mock_email_service:
            mock_email_service.is_configured = True
            mock_email_service.last_error = None
            mock_email_service._create_message = MagicMock(return_value=MagicMock())
            mock_email_service._send_mime_message = AsyncMock(return_value=True)
            
            success, error = await service.send_templated_email(
                "password_reset", "test@oyjz.online", {"reset_url": "http://oyjz.online"}
            )
            
            assert success is True
            assert error == ""

    @pytest.mark.asyncio
    async def test_send_templated_email_failure(self):
        """Test sending templated email when send fails."""
        service = OptimizedEmailService()
        
        # Mock email service to be configured but send fails
        with patch('app.services.email.optimizer.email_service') as mock_email_service:
            mock_email_service.is_configured = True
            mock_email_service.last_error = "Send failed"
            mock_email_service._create_message = MagicMock(return_value=MagicMock())
            mock_email_service._send_mime_message = AsyncMock(return_value=False)
            
            success, error = await service.send_templated_email(
                "password_reset", "test@oyjz.online", {"reset_url": "http://oyjz.online"}
            )
            
            assert success is False
            assert "Send failed" in error

    @pytest.mark.asyncio
    async def test_send_templated_email_exception(self):
        """Test sending templated email when exception occurs."""
        service = OptimizedEmailService()
        
        # Mock email service to raise exception
        with patch('app.services.email.optimizer.email_service') as mock_email_service:
            mock_email_service.is_configured = True
            mock_email_service._create_message = MagicMock(side_effect=Exception("Network error"))
            
            success, error = await service.send_templated_email(
                "password_reset", "test@oyjz.online", {"reset_url": "http://oyjz.online"}
            )
            
            assert success is False
            assert "Network error" in error

    @pytest.mark.asyncio
    async def test_get_delivery_report(self):
        """Test getting delivery report."""
        service = OptimizedEmailService()
        report = await service.get_delivery_report()
        assert "period_days" in report
        assert "total_sent" in report


class TestConvenienceFunctions:
    """Test convenience functions."""

    @pytest.mark.asyncio
    async def test_send_email_with_template(self):
        """Test send_email_with_template function."""
        success, error = await send_email_with_template(
            "password_reset", "test@oyjz.online", {"reset_url": "http://oyjz.online"}
        )
        assert isinstance(success, bool)
        assert isinstance(error, str)

    @pytest.mark.asyncio
    async def test_get_email_delivery_report(self):
        """Test get_email_delivery_report function."""
        report = await get_email_delivery_report()
        assert isinstance(report, dict)
        assert "period_days" in report
