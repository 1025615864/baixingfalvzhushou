"""Tests for AI metrics service."""
from __future__ import annotations

import pytest
import time
import threading
from collections import deque

from app.services.ai_metrics import (
    AiRecentError,
    AiMetrics,
    ai_metrics,
)


class TestAiRecentError:
    """Test AiRecentError dataclass."""

    def test_ai_recent_error_creation(self) -> None:
        """Test creating AiRecentError."""
        error = AiRecentError(
            ts=time.time(),
            request_id="req-123",
            endpoint="chat",
            error_code="TIMEOUT",
            status_code=500,
            message="Request timed out"
        )
        assert error.ts > 0
        assert error.request_id == "req-123"
        assert error.endpoint == "chat"
        assert error.error_code == "TIMEOUT"
        assert error.status_code == 500
        assert error.message == "Request timed out"

    def test_ai_recent_error_optional_fields(self) -> None:
        """Test creating AiRecentError with optional fields as None."""
        error = AiRecentError(
            ts=time.time(),
            request_id="req-456",
            endpoint="chat_stream",
            error_code="RATE_LIMIT",
            status_code=None,
            message=None
        )
        assert error.status_code is None
        assert error.message is None

    def test_ai_recent_error_to_dict(self) -> None:
        """Test to_dict method."""
        ts = time.time()
        error = AiRecentError(
            ts=ts,
            request_id="req-789",
            endpoint="chat",
            error_code="AUTH_ERROR",
            status_code=401,
            message="Unauthorized"
        )
        result = error.to_dict()
        assert result["ts"] == ts
        assert result["request_id"] == "req-789"
        assert result["endpoint"] == "chat"
        assert result["error_code"] == "AUTH_ERROR"
        assert result["status_code"] == 401
        assert result["message"] == "Unauthorized"
        assert "at" in result

    def test_ai_recent_error_to_dict_with_none_fields(self) -> None:
        """Test to_dict with None optional fields."""
        error = AiRecentError(
            ts=time.time(),
            request_id="req-000",
            endpoint="chat",
            error_code="UNKNOWN",
            status_code=None,
            message=None
        )
        result = error.to_dict()
        assert result["status_code"] is None
        assert result["message"] is None


class TestAiMetrics:
    """Test AiMetrics class."""

    def test_ai_metrics_initialization(self) -> None:
        """Test AiMetrics initializes correctly."""
        metrics = AiMetrics()
        assert metrics.started_at > 0
        assert metrics.chat_requests_total == 0
        assert metrics.chat_stream_requests_total == 0
        assert metrics.errors_total == 0
        assert isinstance(metrics._error_code_counts, dict)
        assert isinstance(metrics._endpoint_error_counts, dict)
        assert isinstance(metrics._recent_errors, deque)
        assert isinstance(metrics._lock, type(threading.Lock()))

    def test_ai_metrics_singleton_exists(self) -> None:
        """Test that ai_metrics singleton exists."""
        assert ai_metrics is not None
        assert isinstance(ai_metrics, AiMetrics)

    def test_record_request_chat(self) -> None:
        """Test recording chat request."""
        metrics = AiMetrics()
        metrics.record_request("chat")
        assert metrics.chat_requests_total == 1

    def test_record_request_chat_stream(self) -> None:
        """Test recording chat stream request."""
        metrics = AiMetrics()
        metrics.record_request("chat_stream")
        assert metrics.chat_stream_requests_total == 1

    def test_record_request_multiple(self) -> None:
        """Test recording multiple requests."""
        metrics = AiMetrics()
        metrics.record_request("chat")
        metrics.record_request("chat")
        metrics.record_request("chat_stream")
        assert metrics.chat_requests_total == 2
        assert metrics.chat_stream_requests_total == 1

    def test_record_request_unknown_endpoint(self) -> None:
        """Test recording request for unknown endpoint doesn't count."""
        metrics = AiMetrics()
        metrics.record_request("unknown")
        assert metrics.chat_requests_total == 0
        assert metrics.chat_stream_requests_total == 0

    def test_record_error(self) -> None:
        """Test recording error."""
        metrics = AiMetrics()
        metrics.record_error(
            endpoint="chat",
            request_id="req-001",
            error_code="TIMEOUT",
            status_code=500,
            message="Timeout"
        )
        assert metrics.errors_total == 1
        assert metrics._error_code_counts["TIMEOUT"] == 1
        assert metrics._endpoint_error_counts["chat"] == 1

    def test_record_error_multiple(self) -> None:
        """Test recording multiple errors."""
        metrics = AiMetrics()
        metrics.record_error(
            endpoint="chat",
            request_id="req-001",
            error_code="TIMEOUT",
            status_code=500,
            message="Timeout"
        )
        metrics.record_error(
            endpoint="chat",
            request_id="req-002",
            error_code="TIMEOUT",
            status_code=500,
            message="Timeout"
        )
        metrics.record_error(
            endpoint="chat_stream",
            request_id="req-003",
            error_code="RATE_LIMIT",
            status_code=429,
            message="Rate limited"
        )
        assert metrics.errors_total == 3
        assert metrics._error_code_counts["TIMEOUT"] == 2
        assert metrics._error_code_counts["RATE_LIMIT"] == 1
        assert metrics._endpoint_error_counts["chat"] == 2
        assert metrics._endpoint_error_counts["chat_stream"] == 1

    def test_record_error_same_endpoint_different_codes(self) -> None:
        """Test recording errors with same endpoint different codes."""
        metrics = AiMetrics()
        metrics.record_error(
            endpoint="chat",
            request_id="req-001",
            error_code="AUTH_ERROR",
            status_code=401
        )
        metrics.record_error(
            endpoint="chat",
            request_id="req-002",
            error_code="TIMEOUT",
            status_code=500
        )
        assert metrics._endpoint_error_counts["chat"] == 2
        assert metrics._error_code_counts["AUTH_ERROR"] == 1
        assert metrics._error_code_counts["TIMEOUT"] == 1

    def test_snapshot_empty(self) -> None:
        """Test snapshot of empty metrics."""
        metrics = AiMetrics()
        snapshot = metrics.snapshot()
        assert snapshot["started_at"] > 0
        assert snapshot["chat_requests_total"] == 0
        assert snapshot["chat_stream_requests_total"] == 0
        assert snapshot["errors_total"] == 0
        assert snapshot["recent_errors"] == []
        assert snapshot["top_error_codes"] == []
        assert snapshot["top_endpoints"] == []

    def test_snapshot_with_data(self) -> None:
        """Test snapshot with some data."""
        metrics = AiMetrics()
        metrics.record_request("chat")
        metrics.record_request("chat_stream")
        metrics.record_error(
            endpoint="chat",
            request_id="req-001",
            error_code="TIMEOUT",
            status_code=500
        )
        
        snapshot = metrics.snapshot()
        assert snapshot["chat_requests_total"] == 1
        assert snapshot["chat_stream_requests_total"] == 1
        assert snapshot["errors_total"] == 1
        assert len(snapshot["recent_errors"]) == 1
        assert len(snapshot["top_error_codes"]) == 1
        assert snapshot["top_error_codes"][0]["error_code"] == "TIMEOUT"
        assert len(snapshot["top_endpoints"]) == 1
        assert snapshot["top_endpoints"][0]["endpoint"] == "chat"

    def test_recent_errors_limit(self) -> None:
        """Test that recent errors are limited to 50."""
        metrics = AiMetrics()
        for i in range(60):
            metrics.record_error(
                endpoint="chat",
                request_id=f"req-{i}",
                error_code="ERROR",
                status_code=500
            )
        
        assert len(metrics._recent_errors) == 50
        snapshot = metrics.snapshot()
        assert len(snapshot["recent_errors"]) == 50

    def test_thread_safety(self) -> None:
        """Test that metrics are thread-safe."""
        metrics = AiMetrics()
        errors_to_add = 100
        threads = []
        
        def add_errors():
            for i in range(errors_to_add):
                metrics.record_error(
                    endpoint="chat",
                    request_id=f"req-{i}",
                    error_code="ERROR",
                    status_code=500
                )
        
        for _ in range(4):
            t = threading.Thread(target=add_errors)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        assert metrics.errors_total == 400

    def test_snapshot_top_limit(self) -> None:
        """Test that top lists are limited to 10 items."""
        metrics = AiMetrics()
        for i in range(20):
            metrics.record_error(
                endpoint=f"endpoint-{i}",
                request_id=f"req-{i}",
                error_code=f"error-{i}",
                status_code=500
            )
        
        snapshot = metrics.snapshot()
        assert len(snapshot["top_error_codes"]) <= 10
        assert len(snapshot["top_endpoints"]) <= 10

    def test_started_at_format(self) -> None:
        """Test that started_at has correct format."""
        metrics = AiMetrics()
        snapshot = metrics.snapshot()
        assert "started_at" in snapshot
        assert "started_at_iso" in snapshot
        assert isinstance(snapshot["started_at_iso"], str)
        assert "T" in snapshot["started_at_iso"]  # ISO format


class TestAiMetricsEdgeCases:
    """Test edge cases for AiMetrics."""

    def test_record_request_with_empty_string(self) -> None:
        """Test recording request with empty string."""
        metrics = AiMetrics()
        metrics.record_request("")
        assert metrics.chat_requests_total == 0
        assert metrics.chat_stream_requests_total == 0

    def test_record_request_with_none_like_value(self) -> None:
        """Test recording request with various string values."""
        metrics = AiMetrics()
        metrics.record_request("chat")
        metrics.record_request("Chat")
        metrics.record_request("CHAT")
        assert metrics.chat_requests_total == 1  # Only exact match

    def test_record_error_with_empty_strings(self) -> None:
        """Test recording error with empty strings."""
        metrics = AiMetrics()
        metrics.record_error(
            endpoint="",
            request_id="",
            error_code="",
            status_code=None,
            message=""
        )
        assert metrics.errors_total == 1
        # Empty strings are converted to ""
        assert metrics._error_code_counts[""] == 1
