from __future__ import annotations

import pytest
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock
from app.utils.structured_logger import (
    get_request_id,
    set_request_id,
    get_user_id,
    set_user_id,
    get_trace_id,
    set_trace_id,
    StructuredLogFormatter,
    JSONLogFormatter,
    StructuredLogger,
    get_logger,
)


class TestContextVars:
    """测试上下文变量"""

    def test_request_id_operations(self):
        """测试请求ID操作"""
        assert get_request_id() is None
        set_request_id("test-request-123")
        assert get_request_id() == "test-request-123"
        set_request_id(None)
        assert get_request_id() is None

    def test_user_id_operations(self):
        """测试用户ID操作"""
        assert get_user_id() is None
        set_user_id(123)
        assert get_user_id() == 123
        set_user_id(None)
        assert get_user_id() is None

    def test_trace_id_operations(self):
        """测试追踪ID操作"""
        assert get_trace_id() is None
        set_trace_id("trace-abc")
        assert get_trace_id() == "trace-abc"
        set_trace_id(None)
        assert get_trace_id() is None


class TestStructuredLogFormatter:
    """测试结构化日志格式化器"""

    def setup_method(self):
        """每个测试前初始化"""
        self.formatter = StructuredLogFormatter()

    def test_format_basic(self):
        """测试基础日志格式化"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="test message",
            args=(),
            exc_info=None,
        )
        result = self.formatter.format(record)
        data = json.loads(result)
        assert data["message"] == "test message"
        assert data["level"] == "INFO"

    def test_format_with_request_id(self):
        """测试带请求ID的日志格式化"""
        set_request_id("req-123")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="test message",
            args=(),
            exc_info=None,
        )
        result = self.formatter.format(record)
        data = json.loads(result)
        assert data["request_id"] == "req-123"
        set_request_id(None)

    def test_format_with_user_id(self):
        """测试带用户ID的日志格式化"""
        set_user_id(456)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="test message",
            args=(),
            exc_info=None,
        )
        result = self.formatter.format(record)
        data = json.loads(result)
        assert data["user_id"] == 456
        set_user_id(None)

    def test_format_with_trace_id(self):
        """测试带追踪ID的日志格式化"""
        set_trace_id("trace-xyz")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="test message",
            args=(),
            exc_info=None,
        )
        result = self.formatter.format(record)
        data = json.loads(result)
        assert data["trace_id"] == "trace-xyz"
        set_trace_id(None)

    def test_format_with_extra_fields(self):
        """测试带额外字段的日志格式化"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="test message",
            args=(),
            exc_info=None,
        )
        record.custom_field = "custom_value"
        result = self.formatter.format(record)
        data = json.loads(result)
        assert data["custom_field"] == "custom_value"


class TestJSONLogFormatter:
    """测试JSON日志格式化器"""

    def setup_method(self):
        """每个测试前初始化"""
        self.formatter = JSONLogFormatter()

    def test_format_basic(self):
        """测试基础日志格式化"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="test message",
            args=(),
            exc_info=None,
        )
        result = self.formatter.format(record)
        data = json.loads(result)
        assert data["message"] == "test message"
        assert data["level"] == "INFO"

    def test_format_with_context_ids(self):
        """测试带上下文ID的日志格式化"""
        set_request_id("req-abc")
        set_user_id(789)
        set_trace_id("trace-123")

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="test message",
            args=(),
            exc_info=None,
        )
        result = self.formatter.format(record)
        data = json.loads(result)
        assert data["request_id"] == "req-abc"
        assert data["user_id"] == 789
        assert data["trace_id"] == "trace-123"

        set_request_id(None)
        set_user_id(None)
        set_trace_id(None)

    def test_format_with_location(self):
        """测试带位置信息的日志格式化"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="test message",
            args=(),
            exc_info=None,
        )
        result = self.formatter.format(record)
        data = json.loads(result)
        assert "location" in data
        assert "module" in data["location"]


class TestStructuredLogger:
    """测试结构化日志记录器"""

    def setup_method(self):
        """每个测试前初始化"""
        self.logger = StructuredLogger("test")

    def test_init(self):
        """测试初始化"""
        logger = StructuredLogger("myapp")
        assert logger.name == "myapp"
        assert logger.logger.name == "myapp"

    def test_info(self):
        """测试INFO级别日志"""
        with patch.object(self.logger.logger, 'log') as mock_log:
            self.logger.info("test message", key="value")
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][0] == logging.INFO
            assert "test message" in str(call_args[0][1])

    def test_debug(self):
        """测试DEBUG级别日志"""
        with patch.object(self.logger.logger, 'log') as mock_log:
            self.logger.debug("debug message")
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][0] == logging.DEBUG

    def test_warning(self):
        """测试WARNING级别日志"""
        with patch.object(self.logger.logger, 'log') as mock_log:
            self.logger.warning("warning message")
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][0] == logging.WARNING

    def test_error(self):
        """测试ERROR级别日志"""
        with patch.object(self.logger.logger, 'log') as mock_log:
            self.logger.error("error message")
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][0] == logging.ERROR

    def test_critical(self):
        """测试CRITICAL级别日志"""
        with patch.object(self.logger.logger, 'log') as mock_log:
            self.logger.critical("critical message")
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][0] == logging.CRITICAL

    def test_exception(self):
        """测试异常日志"""
        with patch.object(self.logger.logger, 'log') as mock_log:
            self.logger.exception("error occurred")
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[1]["exc_info"] is True


class TestGetLogger:
    """测试获取日志记录器"""

    def test_get_default_logger(self):
        """测试获取默认日志记录器"""
        logger = get_logger()
        assert isinstance(logger, StructuredLogger)
        assert logger.name == "app"

    def test_get_named_logger(self):
        """测试获取命名日志记录器"""
        logger = get_logger("custom")
        assert isinstance(logger, StructuredLogger)
        assert logger.name == "custom"


class TestStructuredLoggerEdgeCases:
    """测试结构化日志边界情况"""

    def setup_method(self):
        """每个测试前初始化"""
        self.logger = StructuredLogger("test_edge")
        self.formatter = StructuredLogFormatter()

    def test_format_with_exception_info(self):
        """测试带异常信息的日志格式化"""
        try:
            raise ValueError("test error")
        except ValueError:
            import sys
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=10,
                msg="error occurred",
                args=(),
                exc_info=sys.exc_info(),
            )
            result = self.formatter.format(record)
            data = json.loads(result)
            assert data["message"] == "error occurred"
            assert data["level"] == "ERROR"

    def test_format_with_empty_message(self):
        """测试空消息的日志格式化"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="",
            args=(),
            exc_info=None,
        )
        result = self.formatter.format(record)
        data = json.loads(result)
        assert "message" in data

    def test_format_with_special_characters(self):
        """测试带特殊字符的日志格式化"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="测试消息 <特殊字符> & \"引号\"",
            args=(),
            exc_info=None,
        )
        result = self.formatter.format(record)
        data = json.loads(result)
        assert data["message"] == "测试消息 <特殊字符> & \"引号\""

    def test_format_with_numeric_args(self):
        """测试带数字参数的日志格式化"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="User %s has %d items",
            args=("user123", 5),
            exc_info=None,
        )
        result = self.formatter.format(record)
        data = json.loads(result)
        assert "message" in data

    def test_context_vars_independence(self):
        """测试上下文变量的独立性"""
        set_request_id("req-1")
        set_user_id(100)
        set_trace_id("trace-1")

        # 验证每个上下文变量独立设置和获取
        assert get_request_id() == "req-1"
        assert get_user_id() == 100
        assert get_trace_id() == "trace-1"

        # 清理
        set_request_id(None)
        set_user_id(None)
        set_trace_id(None)

        # 验证清理后为None
        assert get_request_id() is None
        assert get_user_id() is None
        assert get_trace_id() is None

    def test_logger_with_extra_kwargs(self):
        """测试日志记录器传递额外关键字参数"""
        with patch.object(self.logger.logger, 'log') as mock_log:
            self.logger.info("message", user_id=123, action="login")
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][0] == logging.INFO


class TestStructuredLogFormatterDetailed:
    """测试StructuredLogFormatter详细功能"""

    def setup_method(self):
        """每个测试前初始化"""
        self.formatter = StructuredLogFormatter()

    def test_format_includes_timestamp(self):
        """测试日志格式化包含时间戳"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="test message",
            args=(),
            exc_info=None,
        )
        result = self.formatter.format(record)
        data = json.loads(result)
        assert "timestamp" in data or "time" in data

    def test_format_includes_logger_name(self):
        """测试日志格式化包含日志器名称"""
        record = logging.LogRecord(
            name="myapp.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="test message",
            args=(),
            exc_info=None,
        )
        result = self.formatter.format(record)
        data = json.loads(result)
        assert "logger" in data or "name" in data

    def test_format_with_different_log_levels(self):
        """测试不同日志级别的格式化"""
        levels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]
        level_names = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level, level_name in zip(levels, level_names):
            record = logging.LogRecord(
                name="test",
                level=level,
                pathname="test.py",
                lineno=10,
                msg="test message",
                args=(),
                exc_info=None,
            )
            result = self.formatter.format(record)
            data = json.loads(result)
            assert data["level"] == level_name

    def test_format_with_empty_extra_fields(self):
        """测试带空额外字段的日志格式化"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="test message",
            args=(),
            exc_info=None,
        )
        result = self.formatter.format(record)
        data = json.loads(result)
        assert data["message"] == "test message"
        assert data["level"] == "INFO"


class TestJSONLogFormatterDetailed:
    """测试JSONLogFormatter详细功能"""

    def setup_method(self):
        """每个测试前初始化"""
        self.formatter = JSONLogFormatter()

    def test_format_contains_all_standard_fields(self):
        """测试日志格式化包含所有标准字段"""
        record = logging.LogRecord(
            name="test.module",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="test message",
            args=(),
            exc_info=None,
        )
        result = self.formatter.format(record)
        data = json.loads(result)

        # 验证标准字段存在
        assert "message" in data
        assert "level" in data
        assert "timestamp" in data or "time" in data

    def test_format_with_context_clear(self):
        """测试清理上下文后的日志格式化"""
        # 设置上下文
        set_request_id("req-test")
        set_user_id(999)
        set_trace_id("trace-test")

        # 清理上下文
        set_request_id(None)
        set_user_id(None)
        set_trace_id(None)

        # 验证清理后不包含上下文信息
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="test message",
            args=(),
            exc_info=None,
        )
        result = self.formatter.format(record)
        data = json.loads(result)

        # 清理后不应包含上下文ID
        assert data["message"] == "test message"


class TestStructuredLoggerSetup:
    """测试StructuredLogger设置功能"""

    def test_logger_name_is_string(self):
        """测试日志记录器名称是字符串"""
        logger = StructuredLogger("test_logger")
        assert logger.name == "test_logger"

    def test_logger_has_logger_attribute(self):
        """测试日志记录器有logger属性"""
        logger = StructuredLogger("test")
        assert hasattr(logger, "logger")
        assert isinstance(logger.logger, logging.Logger)

    def test_logger_level_is_configurable(self):
        """测试日志记录器级别可配置"""
        logger = StructuredLogger("test")
        # 验证logger有level属性
        assert hasattr(logger.logger, "level")

    def test_logger_has_info_method(self):
        """测试日志记录器有info方法"""
        logger = StructuredLogger("test")
        assert hasattr(logger, "info")
        assert callable(logger.info)

    def test_logger_has_error_method(self):
        """测试日志记录器有error方法"""
        logger = StructuredLogger("test")
        assert hasattr(logger, "error")
        assert callable(logger.error)

    def test_logger_has_warning_method(self):
        """测试日志记录器有warning方法"""
        logger = StructuredLogger("test")
        assert hasattr(logger, "warning")
        assert callable(logger.warning)

    def test_logger_has_debug_method(self):
        """测试日志记录器有debug方法"""
        logger = StructuredLogger("test")
        assert hasattr(logger, "debug")
        assert callable(logger.debug)


class TestContextVariableEdgeCases:
    """测试上下文变量边界情况"""

    def test_request_id_with_special_characters(self):
        """测试请求ID包含特殊字符"""
        set_request_id("req-abc-123_xyz")
        result = get_request_id()
        assert result == "req-abc-123_xyz"
        set_request_id(None)

    def test_user_id_with_zero(self):
        """测试用户ID为零"""
        set_user_id(0)
        result = get_user_id()
        assert result == 0
        set_user_id(None)

    def test_trace_id_with_unicode(self):
        """测试追踪ID包含Unicode"""
        set_trace_id("trace-测试-123")
        result = get_trace_id()
        assert result == "trace-测试-123"
        set_trace_id(None)

    def test_multiple_context_operations(self):
        """测试多个上下文操作"""
        set_request_id("req-1")
        set_user_id(100)
        set_trace_id("trace-1")

        # 验证所有值
        assert get_request_id() == "req-1"
        assert get_user_id() == 100
        assert get_trace_id() == "trace-1"

        # 清理一个
        set_request_id(None)
        assert get_request_id() is None
        assert get_user_id() == 100
        assert get_trace_id() == "trace-1"

        # 清理全部
        set_user_id(None)
        set_trace_id(None)
        assert get_user_id() is None
        assert get_trace_id() is None


class TestStructuredLogFormatterEdgeCases:
    """测试StructuredLogFormatter边界情况"""

    def setup_method(self):
        """每个测试前初始化"""
        self.formatter = StructuredLogFormatter()

    def test_format_with_none_args(self):
        """测试带None参数的日志格式化"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="User %s logged in",
            args=(None,),
            exc_info=None,
        )
        result = self.formatter.format(record)
        data = json.loads(result)
        assert "message" in data

    def test_format_with_long_message(self):
        """测试长消息的日志格式化"""
        long_msg = "A" * 1000
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg=long_msg,
            args=(),
            exc_info=None,
        )
        result = self.formatter.format(record)
        data = json.loads(result)
        assert data["message"] == long_msg

    def test_format_with_unicode_message(self):
        """测试Unicode消息的日志格式化"""
        unicode_msg = "你好世界 🌍 αβγδ"
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg=unicode_msg,
            args=(),
            exc_info=None,
        )
        result = self.formatter.format(record)
        data = json.loads(result)
        assert data["message"] == unicode_msg

    def test_format_with_dict_args(self):
        """测试带字典参数的日志格式化"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Data: %s",
            args=({"key": "value"},),
            exc_info=None,
        )
        result = self.formatter.format(record)
        data = json.loads(result)
        assert "message" in data

    def test_format_with_list_args(self):
        """测试带列表参数的日志格式化"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Items: %s",
            args=(["a", "b", "c"],),
            exc_info=None,
        )
        result = self.formatter.format(record)
        data = json.loads(result)
        assert "message" in data


class TestJSONLogFormatterEdgeCases:
    """测试JSONLogFormatter边界情况"""

    def setup_method(self):
        """每个测试前初始化"""
        self.formatter = JSONLogFormatter()

    def test_format_with_nested_exception(self):
        """测试带嵌套异常的日志格式化"""
        try:
            raise ValueError("outer")
        except ValueError:
            try:
                raise TypeError("inner")
            except TypeError:
                record = logging.LogRecord(
                    name="test",
                    level=logging.ERROR,
                    pathname="test.py",
                    lineno=10,
                    msg="nested error",
                    args=(),
                    exc_info=sys.exc_info(),
                )
                result = self.formatter.format(record)
                data = json.loads(result)
                assert "error" in data
                assert data["level"] == "ERROR"

    def test_format_with_zero_level(self):
        """测试零级别的日志格式化"""
        record = logging.LogRecord(
            name="test",
            level=0,
            pathname="test.py",
            lineno=10,
            msg="zero level",
            args=(),
            exc_info=None,
        )
        result = self.formatter.format(record)
        data = json.loads(result)
        assert "message" in data

    def test_format_with_high_level(self):
        """测试高级别的日志格式化"""
        record = logging.LogRecord(
            name="test",
            level=logging.CRITICAL,
            pathname="test.py",
            lineno=10,
            msg="critical message",
            args=(),
            exc_info=None,
        )
        result = self.formatter.format(record)
        data = json.loads(result)
        assert data["level"] == "CRITICAL"

    def test_format_with_empty_path(self):
        """测试空路径的日志格式化"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="empty path",
            args=(),
            exc_info=None,
        )
        result = self.formatter.format(record)
        data = json.loads(result)
        assert "message" in data


class TestSetupStructuredLogging:
    """测试 setup_structured_logging 函数"""

    def test_setup_with_json_format(self, tmpdir, monkeypatch):
        """测试使用 JSON 格式配置日志"""
        from app.utils.structured_logger import setup_structured_logging
        import logging

        log_dir = Path(tmpdir) / "json_logs"
        log_dir.mkdir()

        monkeypatch.setattr("pathlib.Path.mkdir", lambda *args, **kwargs: None)

        setup_structured_logging(
            log_level="DEBUG",
            log_dir=str(log_dir),
            app_name="test_app",
            use_json=True
        )

        root_logger = logging.getLogger()
        assert root_logger.level <= logging.DEBUG
        logging.shutdown()

    def test_setup_with_plain_format(self, tmpdir, monkeypatch):
        """测试使用普通格式配置日志"""
        from app.utils.structured_logger import setup_structured_logging
        import logging

        log_dir = Path(tmpdir) / "plain_logs"
        log_dir.mkdir()

        monkeypatch.setattr("pathlib.Path.mkdir", lambda *args, **kwargs: None)

        setup_structured_logging(
            log_level="INFO",
            log_dir=str(log_dir),
            app_name="test_app",
            use_json=False
        )

        root_logger = logging.getLogger()
        assert root_logger.level <= logging.INFO
        logging.shutdown()

    def test_setup_creates_log_directory(self, tmpdir):
        """测试日志目录自动创建"""
        from app.utils.structured_logger import setup_structured_logging

        log_dir = Path(tmpdir) / "new_logs" / "nested"
        assert not log_dir.exists()

        log_dir.parent.mkdir(parents=True, exist_ok=True)

        setup_structured_logging(
            log_level="INFO",
            log_dir=str(log_dir),
            app_name="test_app",
            use_json=False
        )

        assert log_dir.exists()
        logging.shutdown()


class TestStructuredLogger:
    """测试 StructuredLogger 类"""

    def test_structured_logger_init(self):
        """测试 StructuredLogger 初始化"""
        from app.utils.structured_logger import StructuredLogger

        logger = StructuredLogger("test_logger")
        assert logger.name == "test_logger"

    def test_structured_logger_info(self):
        """测试 StructuredLogger info 方法"""
        from app.utils.structured_logger import StructuredLogger

        logger = StructuredLogger("test_info")
        logger.info("test message", key="value")

    def test_structured_logger_debug(self):
        """测试 StructuredLogger debug 方法"""
        from app.utils.structured_logger import StructuredLogger

        logger = StructuredLogger("test_debug")
        logger.debug("debug message", key="value")

    def test_structured_logger_warning(self):
        """测试 StructuredLogger warning 方法"""
        from app.utils.structured_logger import StructuredLogger

        logger = StructuredLogger("test_warning")
        logger.warning("warning message", key="value")

    def test_structured_logger_error(self):
        """测试 StructuredLogger error 方法"""
        from app.utils.structured_logger import StructuredLogger

        logger = StructuredLogger("test_error")
        logger.error("error message", key="value")

    def test_structured_logger_critical(self):
        """测试 StructuredLogger critical 方法"""
        from app.utils.structured_logger import StructuredLogger

        logger = StructuredLogger("test_critical")
        logger.critical("critical message", key="value")

    def test_structured_logger_exception(self):
        """测试 StructuredLogger exception 方法"""
        from app.utils.structured_logger import StructuredLogger

        logger = StructuredLogger("test_exception")
        try:
            raise ValueError("test exception")
        except ValueError:
            logger.exception("exception occurred")


class TestGetLogger:
    """测试 get_logger 函数"""

    def test_get_logger_default_name(self):
        """测试获取默认日志记录器"""
        from app.utils.structured_logger import get_logger

        logger = get_logger()
        assert isinstance(logger, StructuredLogger)

    def test_get_logger_custom_name(self):
        """测试获取自定义名称日志记录器"""
        from app.utils.structured_logger import get_logger

        logger = get_logger("custom_logger")
        assert logger.name == "custom_logger"
