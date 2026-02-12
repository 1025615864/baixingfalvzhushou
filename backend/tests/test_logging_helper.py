"""Tests for logging helper utilities."""
import logging
import pytest

from app.utils.logging_helper import (
    log_error_with_exc,
    log_exception_with_exc,
    log_warning_with_exc,
    get_request_id,
    add_request_id_to_context,
)


class TestLogErrorWithExc:
    """Tests for log_error_with_exc function."""

    def test_log_error_with_exception(self, caplog):
        """Test logging error with exception info."""
        logger = logging.getLogger("test_error")
        exc = ValueError("test error")

        with caplog.at_level(logging.ERROR):
            log_error_with_exc(logger, "Error occurred", exc=exc)

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "ERROR"
        assert "Error occurred" in caplog.records[0].message

    def test_log_error_without_exception(self, caplog):
        """Test logging error without exception."""
        logger = logging.getLogger("test_error_no_exc")

        with caplog.at_level(logging.ERROR):
            log_error_with_exc(logger, "Error without exception")

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "ERROR"

    def test_log_error_with_extra(self, caplog):
        """Test logging error with extra context."""
        logger = logging.getLogger("test_error_extra")
        exc = RuntimeError("test")
        extra = {"user_id": "123"}

        with caplog.at_level(logging.ERROR):
            log_error_with_exc(logger, "Error with extra", exc=exc, extra=extra)

        assert len(caplog.records) == 1


class TestLogExceptionWithExc:
    """Tests for log_exception_with_exc function."""

    def test_log_exception_with_exception(self, caplog):
        """Test logging exception with exception info."""
        logger = logging.getLogger("test_exc")
        exc = ValueError("test exception")

        with caplog.at_level(logging.ERROR):
            log_exception_with_exc(logger, "Exception occurred", exc=exc)

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "ERROR"

    def test_log_exception_without_exception(self, caplog):
        """Test logging exception without exception object."""
        logger = logging.getLogger("test_exc_no_obj")

        with caplog.at_level(logging.ERROR):
            log_exception_with_exc(logger, "Exception without object")

        assert len(caplog.records) == 1


class TestLogWarningWithExc:
    """Tests for log_warning_with_exc function."""

    def test_log_warning_with_exception(self, caplog):
        """Test logging warning with exception info."""
        logger = logging.getLogger("test_warning")
        exc = ValueError("test warning")

        with caplog.at_level(logging.WARNING):
            log_warning_with_exc(logger, "Warning occurred", exc=exc)

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "WARNING"

    def test_log_warning_without_exception(self, caplog):
        """Test logging warning without exception."""
        logger = logging.getLogger("test_warning_no_exc")

        with caplog.at_level(logging.WARNING):
            log_warning_with_exc(logger, "Warning without exception")

        assert len(caplog.records) == 1


class TestGetRequestId:
    """Tests for get_request_id function."""

    def test_get_request_id_returns_none(self):
        """Test that get_request_id returns None in test context."""
        result = get_request_id()
        # In test context without FastAPI request, should return None
        assert result is None


class TestAddRequestIdToContext:
    """Tests for add_request_id_to_context function."""

    def test_add_request_id_to_none_context(self):
        """Test adding request ID to None context."""
        result = add_request_id_to_context(None)
        assert isinstance(result, dict)

    def test_add_request_id_to_existing_context(self):
        """Test adding request ID to existing context."""
        context = {"user_id": "123"}
        result = add_request_id_to_context(context)
        assert "user_id" in result
        assert result["user_id"] == "123"

    def test_add_request_id_preserves_existing_data(self):
        """Test that existing context data is preserved."""
        context = {"key1": "value1", "key2": "value2"}
        result = add_request_id_to_context(context)
        assert result["key1"] == "value1"
        assert result["key2"] == "value2"
