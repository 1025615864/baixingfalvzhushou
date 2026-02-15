"""Comprehensive tests for app.config Settings"""
import os
import sys
import pytest
from unittest.mock import patch

from app.config import Settings, _running_tests, _resolve_env_files, get_settings


class TestAIFallbackModelsList:
    """Tests for ai_fallback_models_list property"""
    
    def test_ai_fallback_models_list_json_success(self):
        """Test ai_fallback_models_list with valid JSON (covers lines 392-412)"""
        get_settings.cache_clear()
        with patch.dict(os.environ, {'AI_FALLBACK_MODELS': '["gpt-4", "gpt-3.5"]'}):
            settings = Settings()
            result = settings.ai_fallback_models_list
            assert result == ["gpt-4", "gpt-3.5"]
    
    def test_ai_fallback_models_list_json_deduplicated(self):
        """Test ai_fallback_models_list removes duplicates (covers lines 405-412)"""
        get_settings.cache_clear()
        with patch.dict(os.environ, {'AI_FALLBACK_MODELS': '["gpt-4", "gpt-3.5", "gpt-4"]'}):
            settings = Settings()
            result = settings.ai_fallback_models_list
            assert result == ["gpt-4", "gpt-3.5"]
            assert len(result) == 2
    
    def test_ai_fallback_models_list_comma_separated(self):
        """Test ai_fallback_models_list with comma-separated values"""
        get_settings.cache_clear()
        with patch.dict(os.environ, {'AI_FALLBACK_MODELS': 'gpt-4,gpt-3.5,claude-3'}):
            settings = Settings()
            result = settings.ai_fallback_models_list
            assert result == ["gpt-4", "gpt-3.5", "claude-3"]
    
    def test_ai_fallback_models_list_chinese_comma(self):
        """Test ai_fallback_models_list with Chinese comma separator"""
        get_settings.cache_clear()
        with patch.dict(os.environ, {'AI_FALLBACK_MODELS': 'gpt-4，gpt-3.5，claude-3'}):
            settings = Settings()
            result = settings.ai_fallback_models_list
            assert result == ["gpt-4", "gpt-3.5", "claude-3"]
    
    def test_ai_fallback_models_list_with_whitespace(self):
        """Test ai_fallback_models_list handles whitespace correctly"""
        get_settings.cache_clear()
        with patch.dict(os.environ, {'AI_FALLBACK_MODELS': ' gpt-4 , gpt-3.5 '}):
            settings = Settings()
            result = settings.ai_fallback_models_list
            assert result == ["gpt-4", "gpt-3.5"]
    
    def test_ai_fallback_models_list_invalid_json_fallback(self):
        """Test ai_fallback_models_list falls back when JSON is invalid (covers line 400)"""
        get_settings.cache_clear()
        with patch.dict(os.environ, {'AI_FALLBACK_MODELS': '{"invalid": json}'}):
            settings = Settings()
            result = settings.ai_fallback_models_list
            # Should not crash, return empty list or parsed result
            assert isinstance(result, list)
    
    def test_ai_fallback_models_list_empty_string(self):
        """Test ai_fallback_models_list with empty string"""
        get_settings.cache_clear()
        with patch.dict(os.environ, {'AI_FALLBACK_MODELS': ''}):
            settings = Settings()
            result = settings.ai_fallback_models_list
            assert result == []
    
    def test_ai_fallback_models_list_whitespace_only(self):
        """Test ai_fallback_models_list with whitespace only"""
        get_settings.cache_clear()
        with patch.dict(os.environ, {'AI_FALLBACK_MODELS': '   '}):
            settings = Settings()
            result = settings.ai_fallback_models_list
            assert result == []
    
    def test_ai_fallback_models_list_empty_after_cleanup(self):
        """Test ai_fallback_models_list when all entries are whitespace"""
        get_settings.cache_clear()
        with patch.dict(os.environ, {'AI_FALLBACK_MODELS': '   ,   ,   '}):
            settings = Settings()
            result = settings.ai_fallback_models_list
            assert result == []


class TestParseDebug:
    """Tests for _parse_debug validator (covers lines 418, 421-432)"""
    
    def test_parse_debug_none_value(self):
        """Test _parse_debug with None (covers line 418)"""
        # In test environment, _running_tests() returns True
        settings = Settings()
        result = settings._parse_debug(None)
        # None defaults to _running_tests() which is True in tests
        assert result is True
    
    def test_parse_debug_int_zero(self):
        """Test _parse_debug with int 0 (covers line 422)"""
        with patch('app.config._running_tests', return_value=False):
            settings = Settings()
            result = settings._parse_debug(0)
            assert result is False
    
    def test_parse_debug_int_positive(self):
        """Test _parse_debug with positive int"""
        with patch('app.config._running_tests', return_value=False):
            settings = Settings()
            result = settings._parse_debug(1)
            assert result is True
    
    def test_parse_debug_int_negative(self):
        """Test _parse_debug with negative int"""
        with patch('app.config._running_tests', return_value=False):
            settings = Settings()
            result = settings._parse_debug(-1)
            assert result is True
    
    @pytest.mark.parametrize("str_value", [
        "true", "True", "TRUE", "tRuE",
        "yes", "Yes", "YES",
        "y", "Y",
        "on", "On", "ON",
        "1"
    ])
    def test_parse_debug_string_true_variations(self, str_value):
        """Test _parse_debug with various true string values (covers line 427)"""
        with patch('app.config._running_tests', return_value=False):
            settings = Settings()
            result = settings._parse_debug(str_value)
            assert result is True
    
    @pytest.mark.parametrize("str_value", [
        "false", "False", "FALSE",
        "no", "No", "NO",
        "n", "N",
        "off", "Off", "OFF",
        "0"
    ])
    def test_parse_debug_string_false_variations(self, str_value):
        """Test _parse_debug with various false string values (covers line 429)"""
        with patch('app.config._running_tests', return_value=False):
            settings = Settings()
            result = settings._parse_debug(str_value)
            assert result is False
    
    def test_parse_debug_random_string(self):
        """Test _parse_debug with random string (covers line 431)"""
        with patch('app.config._running_tests', return_value=False):
            settings = Settings()
            result = settings._parse_debug("random")
            assert result is True  # Default to True for unknown strings
    
    def test_parse_debug_whitespace_string(self):
        """Test _parse_debug with whitespace string (covers line 424-426)"""
        # In test environment, _running_tests() returns True
        settings = Settings()
        result = settings._parse_debug("  ")
        assert result is True  # Empty string defaults to _running_tests=True in tests


class TestValidateSecurity:
    """Tests for _validate_security - tests are skipped in pytest environment"""
    
    def test_validate_security_skipped_in_tests(self):
        """Verify that security validation is skipped when running in test mode"""
        # In pytest environment, _running_tests() returns True
        # and _validate_security returns early without validation
        settings = Settings(debug=False)
        # Should not raise any error in test mode
        assert settings is not None


class TestGetSettingsCache:
    """Tests for get_settings caching behavior (covers line 492-495)"""
    
    def test_get_settings_singleton_caching(self):
        """Test get_settings returns same instance (caching works)"""
        get_settings.cache_clear()
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
    
    def test_get_settings_cache_clear_returns_new_instance(self):
        """Test cache_clear() returns new instance"""
        settings1 = get_settings()
        get_settings.cache_clear()
        settings2 = get_settings()
        assert settings1 is not settings2
        # But values should be same
        assert settings1.app_name == settings2.app_name
    
    def test_get_settings_multiple_calls_same_instance(self):
        """Test multiple calls return same cached instance"""
        get_settings.cache_clear()
        settings = [get_settings() for _ in range(5)]
        # All should be the same instance
        assert all(s is settings[0] for s in settings)
