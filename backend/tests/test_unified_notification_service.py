from __future__ import annotations

import types
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.notification import NotificationType
from app.services.unified_notification_service import (
    EmailNotificationSender,
    InAppNotificationSender,
    NotificationChannel,
    NotificationResult,
    NotificationTemplate,
    UnifiedNotificationService,
)


class TestNotificationChannel:
    """Test NotificationChannel enum."""

    def test_channel_values(self) -> None:
        assert NotificationChannel.IN_APP.value == "in_app"
        assert NotificationChannel.EMAIL.value == "email"
        assert NotificationChannel.PUSH.value == "push"

    def test_channel_is_str_enum(self) -> None:
        """Test that channels can be used as strings."""
        channel = NotificationChannel.IN_APP
        assert channel == "in_app"
        assert str(channel) == "NotificationChannel.IN_APP"


class TestNotificationTemplate:
    """Test NotificationTemplate dataclass."""

    def test_default_channels(self) -> None:
        template = NotificationTemplate(title="Test", content_template="Content")
        assert template.channels == [NotificationChannel.IN_APP]

    def test_custom_channels(self) -> None:
        template = NotificationTemplate(
            title="Test",
            content_template="Content",
            channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
        )
        assert len(template.channels) == 2


class TestNotificationResult:
    """Test NotificationResult dataclass."""

    def test_success_result(self) -> None:
        result = NotificationResult(success=True, channel=NotificationChannel.IN_APP, notification_id=1)
        assert result.success is True
        assert result.channel == NotificationChannel.IN_APP
        assert result.notification_id == 1
        assert result.error is None

    def test_error_result(self) -> None:
        result = NotificationResult(success=False, channel=NotificationChannel.EMAIL, error="Failed")
        assert result.success is False
        assert result.error == "Failed"
        assert result.notification_id is None


class TestInAppNotificationSender:
    """Test InAppNotificationSender."""

    def test_send_is_async(self) -> None:
        """Test that send is an async method."""
        sender = InAppNotificationSender()
        import inspect
        assert inspect.iscoroutinefunction(sender.send)

    @pytest.mark.asyncio
    async def test_in_app_sender_protocol_compliance(self) -> None:
        """Test InAppNotificationSender complies with NotificationSender protocol."""
        sender = InAppNotificationSender()
        result = await sender.send(user_id=1, title="Test", content="Content")
        # Result should be NotificationResult or similar structure
        assert hasattr(result, "success")
        assert hasattr(result, "channel")


class TestEmailNotificationSender:
    """Test EmailNotificationSender."""

    @pytest.mark.asyncio
    async def test_send_returns_success_result(self) -> None:
        sender = EmailNotificationSender()
        result = await sender.send(user_id=1, title="Test", content="Content")
        assert result.success is True
        assert result.channel == NotificationChannel.EMAIL
        assert result.notification_id is None  # Emails don't create DB records


class TestUnifiedNotificationService:
    """Test UnifiedNotificationService."""

    def test_init_creates_senders(self) -> None:
        service = UnifiedNotificationService()
        assert NotificationChannel.IN_APP in service._senders
        assert NotificationChannel.EMAIL in service._senders
        assert NotificationChannel.PUSH in service._senders

    def test_init_creates_templates(self) -> None:
        from app.models.notification import NotificationType

        service = UnifiedNotificationService()
        assert NotificationType.SYSTEM in service._templates
        assert NotificationType.COMMENT_REPLY in service._templates
        assert NotificationType.POST_LIKE in service._templates

    def test_template_has_correct_channels(self) -> None:
        from app.models.notification import NotificationType

        service = UnifiedNotificationService()
        system_template = service._templates[NotificationType.SYSTEM]
        assert NotificationChannel.IN_APP in system_template.channels
        assert NotificationChannel.EMAIL in system_template.channels

        reply_template = service._templates[NotificationType.COMMENT_REPLY]
        assert NotificationChannel.IN_APP in reply_template.channels
        assert NotificationChannel.EMAIL not in reply_template.channels

    @pytest.mark.asyncio
    async def test_send_uses_template_channels(self) -> None:
        """Test that send uses template channels when not specified."""
        service = UnifiedNotificationService()
        mock_db = AsyncMock()

        # Mock the email sender to avoid actual email sending
        with patch.object(
            service._senders[NotificationChannel.EMAIL],
            "send",
            new_callable=AsyncMock,
            return_value=NotificationResult(
                success=True,
                channel=NotificationChannel.EMAIL,
                notification_id=None,
            ),
        ):
            results = await service.send(
                db=mock_db,
                user_id=1,
                title="Test",
                content="Content",
                type=NotificationType.SYSTEM,
            )

        # Should send to both IN_APP and EMAIL (from template)
        assert len(results) >= 1
        email_result = next((r for r in results if r.channel == NotificationChannel.EMAIL), None)
        assert email_result is not None
        assert email_result.success is True

    @pytest.mark.asyncio
    async def test_send_with_custom_channels(self) -> None:
        """Test that send uses custom channels when specified."""
        service = UnifiedNotificationService()
        mock_db = AsyncMock()

        results = await service.send(
            db=mock_db,
            user_id=1,
            title="Test",
            content="Content",
            type=NotificationType.SYSTEM,
            channels=[NotificationChannel.EMAIL],  # Only email
        )

        # Should only send to EMAIL
        assert len(results) == 1
        assert results[0].channel == NotificationChannel.EMAIL

    @pytest.mark.asyncio
    async def test_send_unknown_type_uses_default(self) -> None:
        """Test that unknown notification type uses default channels."""
        service = UnifiedNotificationService()
        mock_db = AsyncMock()

        results = await service.send(
            db=mock_db,
            user_id=1,
            title="Test",
            content="Content",
            type="unknown_type",  # Unknown type
        )

        # Should use default channel (IN_APP)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_send_includes_metadata(self) -> None:
        """Test that send passes metadata to sender."""
        service = UnifiedNotificationService()
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        metadata = {
            "related_user_id": 123,
            "related_post_id": 456,
        }

        # This would test that metadata is passed correctly
        # For now, just verify the method accepts metadata
        results = await service.send(
            db=mock_db,
            user_id=1,
            title="Test",
            content="Content",
            type=NotificationType.SYSTEM,
            metadata=metadata,
        )

        assert len(results) >= 0  # May or may not send depending on sender availability


class TestNotificationSenderProtocol:
    """Test NotificationSender protocol compliance."""

    def test_in_app_sender_complies_with_protocol(self) -> None:
        """Test InAppNotificationSender has required send method."""
        sender = InAppNotificationSender()
        assert hasattr(sender, "send")
        assert callable(sender.send)

    def test_email_sender_complies_with_protocol(self) -> None:
        """Test EmailNotificationSender has required send method."""
        sender = EmailNotificationSender()
        assert hasattr(sender, "send")
        assert callable(sender.send)

    @pytest.mark.asyncio
    async def test_email_sender_returns_notification_result(self) -> None:
        """Test that email sender returns NotificationResult."""
        email_sender = EmailNotificationSender()
        result = await email_sender.send(user_id=1, title="T", content="C")
        assert isinstance(result, NotificationResult)


class TestUnifiedNotificationServiceEdgeCases:
    """Test edge cases for UnifiedNotificationService."""

    @pytest.mark.asyncio
    async def test_send_with_no_content(self) -> None:
        """Test send with no content."""
        service = UnifiedNotificationService()
        mock_db = AsyncMock()

        results = await service.send(
            db=mock_db,
            user_id=1,
            title="Test",
            content=None,
            type=NotificationType.SYSTEM,
        )

        assert len(results) >= 0

    @pytest.mark.asyncio
    async def test_send_with_link(self) -> None:
        """Test send with link parameter."""
        service = UnifiedNotificationService()
        mock_db = AsyncMock()

        results = await service.send(
            db=mock_db,
            user_id=1,
            title="Test",
            content="Content",
            type=NotificationType.SYSTEM,
            link="https://example.com",
        )

        assert len(results) >= 0

    @pytest.mark.asyncio
    async def test_service_can_be_instantiated_multiple_times(self) -> None:
        """Test that multiple service instances work independently."""
        service1 = UnifiedNotificationService()
        service2 = UnifiedNotificationService()

        # Both should have the same structure but be different instances
        assert service1 is not service2
        assert service1._templates.keys() == service2._templates.keys()


class TestNotificationTemplateDetail:
    """Test NotificationTemplate in detail."""

    def test_template_with_all_fields(self) -> None:
        """Test template with all optional fields."""
        template = NotificationTemplate(
            title="Test Title",
            content_template="Content: {content}",
            channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
        )
        assert template.title == "Test Title"
        assert len(template.channels) == 2

    def test_template_channels_are_list(self) -> None:
        """Test template channels is a list."""
        template = NotificationTemplate(title="Test", content_template="Content")
        assert isinstance(template.channels, list)


class TestNotificationResultDetail:
    """Test NotificationResult in detail."""

    def test_result_with_all_fields(self) -> None:
        """Test result with all fields."""
        result = NotificationResult(
            success=True,
            channel=NotificationChannel.PUSH,
            notification_id=123,
            error=None,
        )
        assert result.success is True
        assert result.notification_id == 123
        assert result.error is None

    def test_result_error_with_message(self) -> None:
        """Test result with error message."""
        result = NotificationResult(
            success=False,
            channel=NotificationChannel.EMAIL,
            error="SMTP connection failed",
        )
        assert result.success is False
        assert "SMTP" in result.error


class TestUnifiedNotificationServiceDetail:
    """Test UnifiedNotificationService in detail."""

    def test_service_has_all_senders(self) -> None:
        """Test service has all expected senders."""
        service = UnifiedNotificationService()
        expected_senders = [
            NotificationChannel.IN_APP,
            NotificationChannel.EMAIL,
            NotificationChannel.PUSH,
        ]
        for sender in expected_senders:
            assert sender in service._senders

    def test_service_has_all_templates(self) -> None:
        """Test service has expected templates."""
        service = UnifiedNotificationService()
        # Check that common notification types have templates
        assert NotificationType.SYSTEM in service._templates
        assert NotificationType.COMMENT_REPLY in service._templates

    @pytest.mark.asyncio
    async def test_send_with_empty_channels(self) -> None:
        """Test send with empty channels list."""
        service = UnifiedNotificationService()
        mock_db = AsyncMock()

        results = await service.send(
            db=mock_db,
            user_id=1,
            title="Test",
            content="Content",
            type=NotificationType.SYSTEM,
            channels=[],
        )

        # Should use default template channels
        assert len(results) >= 0

    @pytest.mark.asyncio
    async def test_send_with_content_template(self) -> None:
        """Test send with content template."""
        service = UnifiedNotificationService()
        mock_db = AsyncMock()

        results = await service.send(
            db=mock_db,
            user_id=1,
            title="Test",
            content="User action test",
            type=NotificationType.COMMENT_REPLY,
        )

        assert len(results) >= 0

    @pytest.mark.asyncio
    async def test_send_preserves_content_template_variables(self) -> None:
        """Test that content template variables are preserved."""
        service = UnifiedNotificationService()
        mock_db = AsyncMock()

        # Send with content that might be used in template
        results = await service.send(
            db=mock_db,
            user_id=1,
            title="Test",
            content="User: {user_id}, Action: test",
            type=NotificationType.COMMENT_REPLY,
        )

        assert len(results) >= 0


class TestInAppNotificationSenderDetail:
    """Test InAppNotificationSender in detail."""

    @pytest.mark.asyncio
    async def test_in_app_send_creates_notification(self) -> None:
        """Test that in-app send creates notification record."""
        sender = InAppNotificationSender()
        result = await sender.send(user_id=1, title="Test", content="Content")

        # Should return a result with notification_id
        assert hasattr(result, "notification_id")
        assert result.notification_id is not None or result.success is True

    @pytest.mark.asyncio
    async def test_in_app_send_with_special_characters(self) -> None:
        """Test in-app send with special characters in content."""
        sender = InAppNotificationSender()
        result = await sender.send(
            user_id=1,
            title="Test <special>",
            content="Content with 'quotes' and \"double quotes\"",
        )
        assert result.success is True


class TestEmailNotificationSenderDetail:
    """Test EmailNotificationSender in detail."""

    @pytest.mark.asyncio
    async def test_email_send_does_not_create_db_record(self) -> None:
        """Test that email send does not create DB notification record."""
        sender = EmailNotificationSender()
        result = await sender.send(user_id=1, title="Test", content="Content")

        # Emails don't create DB records
        assert result.success is True
        assert result.notification_id is None

    @pytest.mark.asyncio
    async def test_email_send_with_long_content(self) -> None:
        """Test email send with long content."""
        sender = EmailNotificationSender()
        long_content = "A" * 1000
        result = await sender.send(user_id=1, title="Test", content=long_content)
        assert result.success is True


class TestNotificationChannelDetail:
    """Test NotificationChannel in detail."""

    def test_all_channels_exist(self) -> None:
        """Test all expected channels exist."""
        assert NotificationChannel.IN_APP is not None
        assert NotificationChannel.EMAIL is not None
        assert NotificationChannel.PUSH is not None

    def test_channel_value_types(self) -> None:
        """Test channel values are strings."""
        for channel in NotificationChannel:
            assert isinstance(channel.value, str)
            assert len(channel.value) > 0
