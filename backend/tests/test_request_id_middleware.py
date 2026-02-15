"""Tests for request_id_middleware module"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.middleware.request_id_middleware import (
    RequestIdMiddleware,
    TracingMiddleware,
)


class TestRequestIdMiddleware:
    """Test RequestIdMiddleware class"""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance"""
        app = MagicMock()
        return RequestIdMiddleware(app)

    @pytest.mark.asyncio
    async def test_dispatch_with_incoming_request_id(self, middleware):
        """Test dispatch with incoming X-Request-Id header"""
        request = MagicMock(spec=Request)
        request.headers.get.return_value = "test-request-id"
        request.state = MagicMock()

        call_next = AsyncMock(return_value=MagicMock(spec=Response))

        response = await middleware.dispatch(request, call_next)

        assert request.state.request_id == "test-request-id"
        assert response.headers.setdefault.called
        call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_dispatch_without_incoming_request_id(self, middleware):
        """Test dispatch without incoming X-Request-Id header"""
        request = MagicMock(spec=Request)
        request.headers.get.return_value = None
        request.state = MagicMock()

        call_next = AsyncMock(return_value=MagicMock(spec=Response))

        response = await middleware.dispatch(request, call_next)

        assert request.state.request_id is not None
        assert len(request.state.request_id) == 32  # UUID hex format
        assert response.headers.setdefault.called
        call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_dispatch_with_empty_request_id(self, middleware):
        """Test dispatch with empty X-Request-Id header"""
        request = MagicMock(spec=Request)
        request.headers.get.return_value = ""
        request.state = MagicMock()

        call_next = AsyncMock(return_value=MagicMock(spec=Response))

        response = await middleware.dispatch(request, call_next)

        assert request.state.request_id is not None
        assert len(request.state.request_id) == 32  # UUID hex format
        assert response.headers.setdefault.called


class TestTracingMiddleware:
    """Test TracingMiddleware class"""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance"""
        app = MagicMock()
        return TracingMiddleware(app)

    @pytest.mark.asyncio
    async def test_dispatch_with_incoming_trace_id(self, middleware):
        """Test dispatch with incoming X-Trace-Id header"""
        request = MagicMock(spec=Request)
        request.headers.get.return_value = "test-trace-id"
        request.state = MagicMock()
        request.state.user_id = None

        call_next = AsyncMock(return_value=MagicMock(spec=Response))

        response = await middleware.dispatch(request, call_next)

        assert request.state.trace_id == "test-trace-id"
        assert response.headers.setdefault.called
        call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_dispatch_without_incoming_trace_id(self, middleware):
        """Test dispatch without incoming X-Trace-Id header"""
        request = MagicMock(spec=Request)
        request.headers.get.return_value = None
        request.state = MagicMock()
        request.state.user_id = None

        call_next = AsyncMock(return_value=MagicMock(spec=Response))

        response = await middleware.dispatch(request, call_next)

        assert request.state.trace_id is not None
        assert len(request.state.trace_id) == 32  # UUID hex format
        assert response.headers.setdefault.called
        call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_dispatch_with_user_id(self, middleware):
        """Test dispatch with user_id in request state"""
        request = MagicMock(spec=Request)
        request.headers.get.return_value = None
        request.state = MagicMock()
        request.state.user_id = "test-user-id"

        call_next = AsyncMock(return_value=MagicMock(spec=Response))

        with patch('app.middleware.request_id_middleware.set_trace_id') as mock_set_trace_id, \
             patch('app.middleware.request_id_middleware.set_user_id') as mock_set_user_id:
            response = await middleware.dispatch(request, call_next)

            mock_set_trace_id.assert_called_once()
            mock_set_user_id.assert_called_once_with("test-user-id")

    @pytest.mark.asyncio
    async def test_dispatch_without_user_id(self, middleware):
        """Test dispatch without user_id in request state"""
        request = MagicMock(spec=Request)
        request.headers.get.return_value = None
        request.state = MagicMock()
        request.state.user_id = None

        call_next = AsyncMock(return_value=MagicMock(spec=Response))

        with patch('app.middleware.request_id_middleware.set_trace_id') as mock_set_trace_id, \
             patch('app.middleware.request_id_middleware.set_user_id') as mock_set_user_id:
            response = await middleware.dispatch(request, call_next)

            mock_set_trace_id.assert_called_once()
            mock_set_user_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_response_headers(self, middleware):
        """Test that trace_id is added to response headers"""
        request = MagicMock(spec=Request)
        request.headers.get.return_value = "test-trace-id"
        request.state = MagicMock()
        request.state.user_id = None

        call_next = AsyncMock(return_value=MagicMock(spec=Response))

        response = await middleware.dispatch(request, call_next)

        response.headers.setdefault.assert_called_once_with("X-Trace-Id", "test-trace-id")
