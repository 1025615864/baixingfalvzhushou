import os
import pytest
import httpx

BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:8000")
SERVICES = {
    "bff": os.getenv("E2E_BFF_URL", "http://localhost:8000"),
    "user": os.getenv("E2E_USER_URL", "http://localhost:8001"),
    "payment-channel": os.getenv("E2E_PAYMENT_URL", "http://localhost:8002"),
    "embedding": os.getenv("E2E_EMBEDDING_URL", "http://localhost:8003"),
    "order": os.getenv("E2E_ORDER_URL", "http://localhost:8004"),
    "ai": os.getenv("E2E_AI_URL", "http://localhost:8005"),
    "news": os.getenv("E2E_NEWS_URL", "http://localhost:8006"),
    "community": os.getenv("E2E_COMMUNITY_URL", "http://localhost:8007"),
    "legal": os.getenv("E2E_LEGAL_URL", "http://localhost:8008"),
    "search": os.getenv("E2E_SEARCH_URL", "http://localhost:8009"),
    "recommendation": os.getenv("E2E_RECOMMENDATION_URL", "http://localhost:8010"),
    "notification": os.getenv("E2E_NOTIFICATION_URL", "http://localhost:8011"),
    "points": os.getenv("E2E_POINTS_URL", "http://localhost:8012"),
    "archive": os.getenv("E2E_ARCHIVE_URL", "http://localhost:8013"),
    "knowledge": os.getenv("E2E_KNOWLEDGE_URL", "http://localhost:8081"),
}


@pytest.fixture(scope="session")
def http_client():
    with httpx.Client(timeout=30.0) as client:
        yield client


@pytest.fixture(scope="session")
def auth_token(http_client):
    login_url = f"{SERVICES['user']}/api/v1/auth/login"
    resp = http_client.post(login_url, json={
        "phone": os.getenv("E2E_TEST_PHONE", "13800138000"),
        "password": os.getenv("E2E_TEST_PASSWORD", "Test1234"),
    })
    if resp.status_code == 200:
        data = resp.json()
        return data.get("access_token") or data.get("data", {}).get("access_token", "")
    return ""


@pytest.fixture(scope="session")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"} if auth_token else {}


class TestServiceHealth:
    @pytest.mark.parametrize("service_name,url", list(SERVICES.items()))
    def test_service_health(self, http_client, service_name, url):
        resp = http_client.get(f"{url}/health", timeout=10)
        assert resp.status_code == 200, f"{service_name} health check failed: {resp.status_code}"


class TestUserFlow:
    def test_register_and_login(self, http_client):
        phone = "13900001111"
        password = "E2eTest123!"

        resp = http_client.post(f"{SERVICES['user']}/api/v1/auth/register", json={
            "phone": phone,
            "password": password,
            "username": "e2e_test_user",
        })
        assert resp.status_code in (200, 201, 409), f"Register failed: {resp.status_code}"

        resp = http_client.post(f"{SERVICES['user']}/api/v1/auth/login", json={
            "phone": phone,
            "password": password,
        })
        assert resp.status_code == 200, f"Login failed: {resp.status_code}"
        data = resp.json()
        token = data.get("access_token") or data.get("data", {}).get("access_token", "")
        assert token, "No access token returned"

    def test_get_profile(self, http_client, auth_headers):
        if not auth_headers:
            pytest.skip("No auth token available")
        resp = http_client.get(f"{SERVICES['user']}/api/v1/users/me", headers=auth_headers)
        assert resp.status_code in (200, 401), f"Get profile failed: {resp.status_code}"


class TestSearchFlow:
    def test_search_endpoint(self, http_client):
        resp = http_client.get(f"{SERVICES['search']}/api/v1/search", params={"q": "法律咨询"})
        assert resp.status_code == 200, f"Search failed: {resp.status_code}"


class TestPointsFlow:
    def test_get_balance(self, http_client, auth_headers):
        if not auth_headers:
            pytest.skip("No auth token available")
        resp = http_client.get(f"{SERVICES['points']}/api/v1/points/balance", headers=auth_headers)
        assert resp.status_code in (200, 401), f"Points balance failed: {resp.status_code}"


class TestNotificationFlow:
    def test_list_notifications(self, http_client, auth_headers):
        if not auth_headers:
            pytest.skip("No auth token available")
        resp = http_client.get(f"{SERVICES['notification']}/api/v1/notifications", headers=auth_headers)
        assert resp.status_code in (200, 401), f"List notifications failed: {resp.status_code}"


class TestBFFRouting:
    def test_bff_health(self, http_client):
        resp = http_client.get(f"{SERVICES['bff']}/health")
        assert resp.status_code == 200, f"BFF health failed: {resp.status_code}"

    def test_bff_api_docs(self, http_client):
        resp = http_client.get(f"{SERVICES['bff']}/docs")
        assert resp.status_code == 200, f"BFF docs failed: {resp.status_code}"
