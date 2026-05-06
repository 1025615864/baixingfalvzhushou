import pytest
import os
from pathlib import Path
from pact import Consumer, Provider


class TestUserLegalContract:
    """User Service 作为消费者，Legal Service 作为提供者的契约测试"""

    @pytest.fixture
    def pact(self, tmp_path):
        log_dir = tmp_path / "logs"
        log_dir.mkdir(exist_ok=True)

        pact_dir = tmp_path / "pacts"
        pact_dir.mkdir(exist_ok=True)

        consumer = Consumer("UserService", version="1.0.0")
        provider = Provider("LegalService")

        pact = consumer.has_pact_with(
            provider,
            pact_dir=str(pact_dir),
            log_dir=str(log_dir),
            publish_to_broker=False,
        )
        pact.start_service()

        yield pact

        pact.stop_service()

    def test_get_lawyer_profile(self, pact):
        """测试获取律师信息"""
        (
            pact
            .given("Lawyer with ID lawyer-123 exists")
            .upon_receiving("a request for lawyer profile")
            .with_request(
                method="GET",
                path="/api/v1/legal/lawyers/lawyer-123",
                headers={
                    "Accept": "application/json",
                    "Authorization": "Bearer test-token"
                }
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body={
                    "lawyer_id": "lawyer-123",
                    "name": "Test Lawyer",
                    "firm_id": "firm-456",
                    "title": "Senior Partner",
                    "expertise": ["criminal", "civil"],
                    "rating": 4.5,
                    "consultation_count": 100,
                    "price_per_hour": 50000
                }
            )
        )

        import requests

        with pact:
            response = requests.get(
                f"{pact.uri}/api/v1/legal/lawyers/lawyer-123",
                headers={
                    "Accept": "application/json",
                    "Authorization": "Bearer test-token"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["lawyer_id"] == "lawyer-123"
            assert data["name"] == "Test Lawyer"

    def test_get_lawyer_schedule(self, pact):
        """测试获取律师日程"""
        (
            pact
            .given("Lawyer lawyer-123 has available slots on 2024-03-25")
            .upon_receiving("a request for lawyer schedule")
            .with_request(
                method="GET",
                path="/api/v1/legal/lawyers/lawyer-123/schedule",
                query={"date": "2024-03-25"},
                headers={
                    "Accept": "application/json",
                    "Authorization": "Bearer test-token"
                }
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body={
                    "lawyer_id": "lawyer-123",
                    "available_slots": [
                        {
                            "slot_id": "slot-1",
                            "start_time": "2024-03-25T09:00:00Z",
                            "end_time": "2024-03-25T10:00:00Z",
                            "is_available": True
                        },
                        {
                            "slot_id": "slot-2",
                            "start_time": "2024-03-25T10:00:00Z",
                            "end_time": "2024-03-25T11:00:00Z",
                            "is_available": True
                        }
                    ]
                }
            )
        )

        import requests

        with pact:
            response = requests.get(
                f"{pact.uri}/api/v1/legal/lawyers/lawyer-123/schedule",
                params={"date": "2024-03-25"},
                headers={
                    "Accept": "application/json",
                    "Authorization": "Bearer test-token"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["lawyer_id"] == "lawyer-123"
            assert len(data["available_slots"]) == 2

    def test_create_consultation(self, pact):
        """测试创建咨询"""
        (
            pact
            .given("User user-123 wants to book a consultation with lawyer-123")
            .upon_receiving("a request to create consultation")
            .with_request(
                method="POST",
                path="/api/v1/legal/consultations",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": "Bearer test-token"
                },
                body={
                    "user_id": "user-123",
                    "lawyer_id": "lawyer-123",
                    "type": "video",
                    "scheduled_at": "2024-03-25T10:00:00Z",
                    "description": "I need legal advice"
                }
            )
            .will_respond_with(
                status=201,
                headers={"Content-Type": "application/json"},
                body={
                    "consultation_id": "consultation-789",
                    "user_id": "user-123",
                    "lawyer_id": "lawyer-123",
                    "type": "video",
                    "status": "pending",
                    "scheduled_at": "2024-03-25T10:00:00Z"
                }
            )
        )

        import requests

        with pact:
            response = requests.post(
                f"{pact.uri}/api/v1/legal/consultations",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": "Bearer test-token"
                },
                json={
                    "user_id": "user-123",
                    "lawyer_id": "lawyer-123",
                    "type": "video",
                    "scheduled_at": "2024-03-25T10:00:00Z",
                    "description": "I need legal advice"
                }
            )

            assert response.status_code == 201
            data = response.json()
            assert data["consultation_id"] == "consultation-789"
            assert data["status"] == "pending"


class TestPaymentUserContract:
    """Payment Service 作为消费者，User Service 作为提供者的契约测试"""

    @pytest.fixture
    def pact(self, tmp_path):
        log_dir = tmp_path / "logs"
        log_dir.mkdir(exist_ok=True)

        pact_dir = tmp_path / "pacts"
        pact_dir.mkdir(exist_ok=True)

        consumer = Consumer("PaymentService", version="1.0.0")
        provider = Provider("UserService")

        pact = consumer.has_pact_with(
            provider,
            pact_dir=str(pact_dir),
            log_dir=str(log_dir),
            publish_to_broker=False,
        )
        pact.start_service()

        yield pact

        pact.stop_service()

    def test_get_user_quota(self, pact):
        """测试获取用户配额"""
        (
            pact
            .given("User user-123 exists")
            .upon_receiving("a request for user quota")
            .with_request(
                method="GET",
                path="/api/v1/users/user-123/quota",
                headers={
                    "Accept": "application/json",
                    "Authorization": "Bearer test-token"
                }
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body={
                    "user_id": "user-123",
                    "consultation_quota": 10,
                    "consultation_used": 3,
                    "document_quota": 5,
                    "document_used": 1
                }
            )
        )

        import requests

        with pact:
            response = requests.get(
                f"{pact.uri}/api/v1/users/user-123/quota",
                headers={
                    "Accept": "application/json",
                    "Authorization": "Bearer test-token"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == "user-123"
            assert data["consultation_quota"] == 10

    def test_deduct_quota(self, pact):
        """测试扣减用户配额"""
        (
            pact
            .given("User user-123 has remaining quota")
            .upon_receiving("a request to deduct quota")
            .with_request(
                method="POST",
                path="/api/v1/users/user-123/quota/deduct",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": "Bearer test-token"
                },
                body={
                    "quota_type": "consultation",
                    "amount": 1
                }
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body={
                    "success": True,
                    "remaining_quota": 9
                }
            )
        )

        import requests

        with pact:
            response = requests.post(
                f"{pact.uri}/api/v1/users/user-123/quota/deduct",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": "Bearer test-token"
                },
                json={
                    "quota_type": "consultation",
                    "amount": 1
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
