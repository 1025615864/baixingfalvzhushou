import pytest
from unittest.mock import AsyncMock, Mock
from app.services.ai_compliance import (
    AIComplianceService,
    AIComplianceMiddleware,
    record_ai_consent,
    check_ai_consent,
    get_ai_statement,
    get_ai_consent_notice,
    AI_COMPLIANCE_STATEMENT,
    AI_CONSENT_NOTICE
)
from fastapi import Request

@pytest.mark.asyncio
class TestAIComplianceService:
    async def test_record_consent(self):
        service = AIComplianceService()
        record = await service.record_consent(
            user_id=1,
            consent_type="ai_service",
            ip_address="127.0.0.1",
            user_agent="test-agent"
        )
        
        assert record["user_id"] == 1
        assert record["consent_type"] == "ai_service"
        assert record["ip_address"] == "127.0.0.1"
        assert record["user_agent"] == "test-agent"
        assert "consent_time" in record

    async def test_check_consent_exists(self):
        service = AIComplianceService()
        await service.record_consent(1, "ai_service")
        
        result = await service.check_consent(1, "ai_service")
        assert result["has_consent"] is True
        assert result["version"] == "1.0"
        assert result["consent_time"] is not None

    async def test_check_consent_not_exists(self):
        service = AIComplianceService()
        result = await service.check_consent(999, "ai_service")
        assert result["has_consent"] is False
        assert result["consent_time"] is None

    async def test_revoke_consent(self):
        service = AIComplianceService()
        await service.record_consent(1, "ai_service")
        
        success = await service.revoke_consent(1, "ai_service")
        assert success is True
        
        # Verify revoked
        result = await service.check_consent(1, "ai_service")
        assert result["has_consent"] is False

    async def test_revoke_consent_not_found(self):
        service = AIComplianceService()
        success = await service.revoke_consent(999, "ai_service")
        assert success is False

    async def test_log_compliance_event(self):
        service = AIComplianceService()
        await service.log_compliance_event(
            event_type="test_event",
            user_id=1,
            details={"info": "test"}
        )
        
        # We can't access _compliance_logs directly easily unless we inspect internal state or use get_compliance_report
        # Let's inspect internal state for test
        assert len(service._compliance_logs) == 1
        log = service._compliance_logs[0]
        assert log["event_type"] == "test_event"
        assert log["user_id"] == 1
        assert log["details"]["info"] == "test"

    async def test_get_compliance_report(self):
        service = AIComplianceService()
        await service.record_consent(1, "ai_service")
        await service.record_consent(2, "ai_service")
        await service.log_compliance_event("event_a")
        await service.log_compliance_event("event_b")
        await service.log_compliance_event("event_a")
        
        report = await service.get_compliance_report(days=7)
        assert report["period_days"] == 7
        assert report["total_consents"] == 2
        assert report["event_counts"]["event_a"] == 2
        assert report["event_counts"]["event_b"] == 1
        assert report["compliance_status"] == "active"

    def test_get_statement(self):
        service = AIComplianceService()
        assert service.get_statement() == AI_COMPLIANCE_STATEMENT.strip()

    def test_get_consent_notice(self):
        service = AIComplianceService()
        assert service.get_consent_notice() == AI_CONSENT_NOTICE


@pytest.mark.asyncio
class TestAIComplianceMiddleware:
    async def test_extract_consent_info(self):
        mock_request = Mock(spec=Request)
        mock_request.client = Mock(host="1.2.3.4")
        mock_request.headers = {
            "User-Agent": "test-agent",
            "X-AI-Consent-Version": "1.0"
        }
        
        info = await AIComplianceMiddleware.extract_consent_info(mock_request)
        assert info["ip_address"] == "1.2.3.4"
        assert info["user_agent"] == "test-agent"
        assert info["consent_version"] == "1.0"

    async def test_check_consent_header(self):
        mock_request = Mock(spec=Request)
        mock_request.headers = {"X-AI-Consent-Accepted": "true"}
        assert await AIComplianceMiddleware.check_consent_header(mock_request) is True
        
        mock_request.headers = {"X-AI-Consent-Accepted": "false"}
        assert await AIComplianceMiddleware.check_consent_header(mock_request) is False
        
        mock_request.headers = {}
        assert await AIComplianceMiddleware.check_consent_header(mock_request) is False


@pytest.mark.asyncio
class TestConvenienceFunctions:
    async def test_record_ai_consent(self):
        record = await record_ai_consent(1, "ai_service")
        assert record["user_id"] == 1
        assert "consent_time" in record

    async def test_check_ai_consent(self):
        await record_ai_consent(2, "ai_service")
        result = await check_ai_consent(2)
        assert result["has_consent"] is True

    def test_get_ai_texts(self):
        assert get_ai_statement() == AI_COMPLIANCE_STATEMENT.strip()
        assert get_ai_consent_notice() == AI_CONSENT_NOTICE
