"""Tests for system metrics endpoints"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from fastapi.responses import PlainTextResponse
from fastapi.testclient import TestClient


class TestMetricsEndpoints:
    """Test system metrics API endpoints"""

    @pytest.fixture
    def mock_prometheus_metrics(self):
        """Create mock prometheus metrics"""
        mock = MagicMock()
        mock.render_prometheus.return_value = "# HELP test\n# TYPE test counter\ntest_total 1"
        mock.snapshot_http.return_value = {}
        mock.snapshot_jobs.return_value = {}
        return mock

    @pytest.fixture
    def mock_system_monitor(self):
        """Create mock system monitor"""
        mock = MagicMock()
        mock.get_health_status.return_value = {
            "status": "healthy",
            "components": {}
        }
        mock.get_recent_alerts.return_value = []
        return mock

    @pytest.mark.asyncio
    async def test_get_prometheus_metrics_returns_plain_text(self):
        """Test that prometheus metrics endpoint returns plain text"""
        mock_metrics = MagicMock()
        mock_metrics.render_prometheus.return_value = "# HELP test\n# TYPE test counter\ntest_total 1"

        with patch("app.routers.system_admin.metrics.prometheus_metrics", mock_metrics):
            from app.routers.system_admin.metrics import get_prometheus_metrics

            response = await get_prometheus_metrics()
            assert isinstance(response, PlainTextResponse)
            assert "text/plain" in response.media_type
            # Mock 返回值 - body 是 bytes
            assert b"test_total" in response.body

    @pytest.mark.asyncio
    async def test_get_metrics_summary_empty(self, mock_prometheus_metrics, mock_system_monitor):
        """Test metrics summary with no data"""
        mock_prometheus_metrics.snapshot_http.return_value = {}
        mock_prometheus_metrics.snapshot_jobs.return_value = {}

        with patch("app.routers.system_admin.metrics.prometheus_metrics", mock_prometheus_metrics):
            with patch("app.routers.system_admin.metrics.get_system_monitor", return_value=mock_system_monitor):
                from app.routers.system_admin.metrics import router
                from app.main import app

                app.include_router(router)
                from httpx import AsyncClient, ASGITransport
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get("/metrics/summary?hours=1")
                    assert response.status_code == 200
                    data = response.json()
                    assert "generated_at" in data
                    assert data["period_hours"] == 1
                    assert data["api"]["total_requests"] == 0

    @pytest.mark.asyncio
    async def test_get_health_check(self, mock_system_monitor):
        """Test health check endpoint"""
        with patch("app.routers.system_admin.metrics.get_system_monitor", return_value=mock_system_monitor):
            from app.routers.system_admin.metrics import router
            from app.main import app

            app.include_router(router)
            from httpx import AsyncClient, ASGITransport
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/metrics/health")
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_get_alerts_empty(self, mock_system_monitor):
        """Test alerts endpoint with no alerts"""
        mock_system_monitor.get_recent_alerts.return_value = []

        with patch("app.routers.system_admin.metrics.get_system_monitor", return_value=mock_system_monitor):
            from app.routers.system_admin.metrics import router
            from app.main import app

            app.include_router(router)
            from httpx import AsyncClient, ASGITransport
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/metrics/alerts?hours=24")
                assert response.status_code == 200
                data = response.json()
                assert data["alerts"] == []
                assert data["total"] == 0
