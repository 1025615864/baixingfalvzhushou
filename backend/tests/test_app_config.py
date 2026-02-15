"""Tests for app.config module"""
import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch

# Add the backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import Settings, _running_tests, _resolve_env_files


class TestHelperFunctions:
    """Test helper functions"""

    def test_running_tests_true(self):
        """Test _running_tests when pytest is in sys.modules"""
        with patch.dict(sys.modules, {'pytest': True}):
            assert _running_tests() is True

    def test_running_tests_false(self):
        """Test _running_tests when pytest is not in sys.modules"""
        with patch.dict(sys.modules, {}, clear=True):
            assert _running_tests() is False

    def test_resolve_env_files_with_explicit(self):
        """Test _resolve_env_files with explicit ENV_FILE"""
        import app.config.settings as settings_module
        with patch.object(settings_module, '_running_tests', return_value=False):
            with patch.dict(settings_module.os.environ, {'ENV_FILE': '/path/to/.env'}):
                result = _resolve_env_files()
                assert result == ['/path/to/.env']

    def test_resolve_env_files_in_tests(self):
        """Test _resolve_env_files returns None during tests"""
        with patch('app.config._running_tests', return_value=True):
            result = _resolve_env_files()
            assert result is None


class TestSettings:
    """Test Settings class"""

    def test_settings_creation(self):
        """Test creating Settings instance"""
        settings = Settings()
        assert settings.app_name == "百姓法律助手"
        assert settings.algorithm == "HS256"
        assert settings.access_token_expire_minutes == 60

    def test_settings_with_debug(self):
        """Test Settings with debug mode"""
        with patch('app.config._running_tests', return_value=True):
            settings = Settings()
            assert settings.debug is True

    def test_settings_database_url_default(self):
        """Test default database URL"""
        # 清除环境变量以测试默认值
        import os
        env_backup = os.environ.get('DATABASE_URL')
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
        try:
            settings = Settings()
            assert "sqlite+aiosqlite" in settings.database_url
            assert "app.db" in settings.database_url
        finally:
            # 恢复环境变量
            if env_backup:
                os.environ['DATABASE_URL'] = env_backup

    def test_settings_secret_key_default(self):
        """Test default secret key"""
        # 清除环境变量以测试默认值
        import os
        env_backup = os.environ.get('SECRET_KEY')
        env_backup_jwt = os.environ.get('JWT_SECRET_KEY')
        if 'SECRET_KEY' in os.environ:
            del os.environ['SECRET_KEY']
        if 'JWT_SECRET_KEY' in os.environ:
            del os.environ['JWT_SECRET_KEY']
        try:
            settings = Settings()
            # 测试环境下会生成测试密钥
            assert settings.secret_key != ""
        finally:
            # 恢复环境变量
            if env_backup:
                os.environ['SECRET_KEY'] = env_backup
            if env_backup_jwt:
                os.environ['JWT_SECRET_KEY'] = env_backup_jwt

    def test_settings_alipay_defaults(self):
        """Test Alipay default values"""
        settings = Settings()
        assert settings.alipay_app_id == ""
        assert settings.alipay_private_key == ""
        assert settings.alipay_public_key == ""
        assert settings.alipay_gateway_url == "https://openapi.alipay.com/gateway.do"

    def test_settings_validation_alias_database_url(self):
        """Test DATABASE_URL validation alias"""
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test'}):
            settings = Settings()
            assert settings.database_url == 'postgresql://test'

    def test_settings_validation_alias_db_url(self):
        """Test DB_URL validation alias"""
        # 清除所有数据库URL相关的环境变量
        import os
        env_backup = {
            'DATABASE_URL': os.environ.get('DATABASE_URL'),
            'DB_URL': os.environ.get('DB_URL'),
            'SQLALCHEMY_DATABASE_URL': os.environ.get('SQLALCHEMY_DATABASE_URL'),
        }
        for key in ['DATABASE_URL', 'DB_URL', 'SQLALCHEMY_DATABASE_URL']:
            if key in os.environ:
                del os.environ[key]
        try:
            with patch.dict(os.environ, {'DB_URL': 'postgresql://test'}, clear=False):
                settings = Settings()
                assert settings.database_url == 'postgresql://test'
        finally:
            # 恢复环境变量
            for key, value in env_backup.items():
                if value is not None:
                    os.environ[key] = value

    def test_settings_validation_alias_secret_key(self):
        """Test SECRET_KEY validation alias"""
        with patch.dict(os.environ, {'SECRET_KEY': 'test-secret'}):
            settings = Settings()
            assert settings.secret_key == 'test-secret'

    def test_settings_validation_alias_jwt_secret_key(self):
        """Test JWT_SECRET_KEY validation alias"""
        with patch.dict(os.environ, {'JWT_SECRET_KEY': 'test-secret'}):
            settings = Settings()
            assert settings.secret_key == 'test-secret'

    def test_settings_validation_alias_payment_webhook_secret(self):
        """Test PAYMENT_WEBHOOK_SECRET validation alias"""
        with patch.dict(os.environ, {'PAYMENT_WEBHOOK_SECRET': '0123456789abcdef'}):
            settings = Settings()
            assert settings.payment_webhook_secret == '0123456789abcdef'

    def test_settings_validation_alias_payment_callback_secret(self):
        """Test PAYMENT_CALLBACK_SECRET validation alias"""
        # Clear the Settings cache to avoid pollution from previous tests
        from app.config import get_settings
        get_settings.cache_clear()
        # Delete PAYMENT_WEBHOOK_SECRET to ensure PAYMENT_CALLBACK_SECRET is used
        with patch.dict(os.environ, {'PAYMENT_CALLBACK_SECRET': '0123456789abcdef'}, clear=False):
            # Remove PAYMENT_WEBHOOK_SECRET if it exists
            if 'PAYMENT_WEBHOOK_SECRET' in os.environ:
                del os.environ['PAYMENT_WEBHOOK_SECRET']
            settings = Settings()
            assert settings.payment_webhook_secret == '0123456789abcdef'

    def test_settings_validation_alias_alipay_app_id(self):
        """Test ALIPAY_APP_ID validation alias"""
        with patch.dict(os.environ, {'ALIPAY_APP_ID': 'test-app-id'}):
            settings = Settings()
            assert settings.alipay_app_id == 'test-app-id'

    def test_settings_validation_alias_pay_alipay_app_id(self):
        """Test PAY_ALIPAY_APP_ID validation alias"""
        with patch.dict(os.environ, {'PAY_ALIPAY_APP_ID': 'test-app-id'}):
            settings = Settings()
            assert settings.alipay_app_id == 'test-app-id'

    def test_settings_singleton(self):
        """Test Settings singleton behavior"""
        settings1 = Settings()
        settings2 = Settings()
        # Settings instances should be independent
        assert settings1 is not settings2
        # But should have same default values
        assert settings1.app_name == settings2.app_name

    def test_parse_cors_allow_origins_string(self):
        """Test _parse_cors_allow_origins with string"""
        settings = Settings()
        result = settings._parse_cors_allow_origins("http://localhost:3000,http://localhost:8080")
        assert result == ["http://localhost:3000", "http://localhost:8080"]

    def test_parse_cors_allow_origins_list(self):
        """Test _parse_cors_allow_origins with list"""
        settings = Settings()
        result = settings._parse_cors_allow_origins(["http://localhost:3000", "http://localhost:8080"])
        assert result == ["http://localhost:3000", "http://localhost:8080"]

    def test_parse_ai_fallback_models_none(self):
        """Test _parse_ai_fallback_models with None"""
        settings = Settings()
        result = settings._parse_ai_fallback_models(None)
        assert result == ""

    def test_parse_ai_fallback_models_string(self):
        """Test _parse_ai_fallback_models with string"""
        settings = Settings()
        result = settings._parse_ai_fallback_models("model1,model2")
        assert result == "model1,model2"

    def test_parse_ai_fallback_models_list(self):
        """Test _parse_ai_fallback_models with list"""
        settings = Settings()
        result = settings._parse_ai_fallback_models(["model1", "model2"])
        assert result == "model1,model2"

    def test_ai_fallback_models_list_empty(self):
        """Test ai_fallback_models_list with empty value"""
        settings = Settings()
        result = settings.ai_fallback_models_list
        assert result == []
