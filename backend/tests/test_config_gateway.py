"""Tests for config_gateway module."""
from __future__ import annotations

import pytest
import base64
import json

from app.services.system.config_gateway import (
    ConfigValueType,
    ConfigKeySpec,
    PrefixConfigSpec,
    _parse_bool,
    _parse_int,
    _parse_float,
    _validate_json,
    _validate_json_b64,
    ConfigGateway,
    config_gateway,
    _CONFIG_SPECS,
    _PREFIX_SPECS,
)


class TestConfigValueType:
    """Test ConfigValueType enum."""

    def test_value_types_exist(self) -> None:
        """Test all value types are defined."""
        assert ConfigValueType.STRING.value == "string"
        assert ConfigValueType.INT.value == "int"
        assert ConfigValueType.FLOAT.value == "float"
        assert ConfigValueType.BOOL.value == "bool"
        assert ConfigValueType.JSON.value == "json"
        assert ConfigValueType.JSON_B64.value == "json_b64"


class TestParseBool:
    """Test _parse_bool function."""

    def test_parse_bool_true_values(self) -> None:
        """Test parsing boolean true values."""
        assert _parse_bool("1") is True
        assert _parse_bool("true") is True
        assert _parse_bool("yes") is True
        assert _parse_bool("y") is True
        assert _parse_bool("on") is True

    def test_parse_bool_false_values(self) -> None:
        """Test parsing boolean false values."""
        assert _parse_bool("0") is False
        assert _parse_bool("false") is False
        assert _parse_bool("no") is False
        assert _parse_bool("n") is False
        assert _parse_bool("off") is False

    def test_parse_bool_case_insensitive(self) -> None:
        """Test parsing is case insensitive."""
        assert _parse_bool("TRUE") is True
        assert _parse_bool("False") is False
        assert _parse_bool("YES") is True

    def test_parse_bool_invalid(self) -> None:
        """Test parsing invalid boolean value."""
        with pytest.raises(ValueError, match="must be a boolean value"):
            _parse_bool("invalid")


class TestParseInt:
    """Test _parse_int function."""

    def test_parse_int_valid(self) -> None:
        """Test parsing valid integers."""
        assert _parse_int("42") == 42
        assert _parse_int("  42  ") == 42
        assert _parse_int("42.0") == 42

    def test_parse_int_invalid(self) -> None:
        """Test parsing invalid integers."""
        with pytest.raises(ValueError, match="must be an integer"):
            _parse_int("not_a_number")


class TestParseFloat:
    """Test _parse_float function."""

    def test_parse_float_valid(self) -> None:
        """Test parsing valid floats."""
        assert _parse_float("3.14") == 3.14
        assert _parse_float("  3.14  ") == 3.14
        assert _parse_float("42") == 42.0

    def test_parse_float_invalid(self) -> None:
        """Test parsing invalid floats."""
        with pytest.raises(ValueError, match="must be a number"):
            _parse_float("not_a_number")


class TestValidateJson:
    """Test _validate_json function."""

    def test_validate_json_valid(self) -> None:
        """Test validating valid JSON."""
        _validate_json('{"key": "value"}')
        _validate_json('["item1", "item2"]')
        _validate_json('42')
        _validate_json('"string"')

    def test_validate_json_invalid(self) -> None:
        """Test validating invalid JSON."""
        with pytest.raises(ValueError, match="must be valid JSON"):
            _validate_json('{"invalid": }')


class TestValidateJsonB64:
    """Test _validate_json_b64 function."""

    def test_validate_json_b64_valid(self) -> None:
        """Test validating valid base64-encoded JSON."""
        json_str = '{"key": "value"}'
        b64_str = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
        _validate_json_b64(b64_str)

    def test_validate_json_b64_invalid_b64(self) -> None:
        """Test validating invalid base64."""
        with pytest.raises(ValueError, match="must be base64-encoded JSON"):
            _validate_json_b64("not_base64!")

    def test_validate_json_b64_invalid_json(self) -> None:
        """Test validating base64-encoded invalid JSON."""
        invalid_json = '{"invalid": }'
        b64_str = base64.b64encode(invalid_json.encode("utf-8")).decode("utf-8")
        with pytest.raises(ValueError, match="must be valid JSON"):
            _validate_json_b64(b64_str)


class TestConfigKeySpec:
    """Test ConfigKeySpec dataclass."""

    def test_config_key_spec_creation(self) -> None:
        """Test creating ConfigKeySpec."""
        spec = ConfigKeySpec(
            key="TEST_KEY",
            domain="test",
            value_type=ConfigValueType.STRING,
            category="test_category",
            description="Test description",
        )
        assert spec.key == "TEST_KEY"
        assert spec.domain == "test"
        assert spec.value_type == ConfigValueType.STRING
        assert spec.category == "test_category"
        assert spec.description == "Test description"
        assert spec.allow_empty is True

    def test_config_key_spec_defaults(self) -> None:
        """Test ConfigKeySpec default values."""
        spec = ConfigKeySpec(
            key="TEST_KEY",
            domain="test",
            value_type=ConfigValueType.STRING,
            category="test_category",
        )
        assert spec.description == ""
        assert spec.allow_empty is True


class TestPrefixConfigSpec:
    """Test PrefixConfigSpec dataclass."""

    def test_prefix_config_spec_creation(self) -> None:
        """Test creating PrefixConfigSpec."""
        spec = PrefixConfigSpec(
            prefix="TEST_PREFIX_",
            domain="test",
            value_type=ConfigValueType.STRING,
            category="test_category",
            description="Test description",
        )
        assert spec.prefix == "TEST_PREFIX_"
        assert spec.domain == "test"
        assert spec.value_type == ConfigValueType.STRING
        assert spec.category == "test_category"
        assert spec.description == "Test description"
        assert spec.allow_empty is True


class TestConfigGateway:
    """Test ConfigGateway class."""

    def test_config_gateway_singleton(self) -> None:
        """Test config_gateway is a singleton."""
        assert config_gateway is not None
        assert isinstance(config_gateway, ConfigGateway)

    def test_resolve_spec_known_key(self) -> None:
        """Test resolving spec for known key."""
        spec = config_gateway.resolve_spec("FREE_AI_CHAT_DAILY_LIMIT")
        assert spec is not None
        assert spec.key == "FREE_AI_CHAT_DAILY_LIMIT"
        assert spec.value_type == ConfigValueType.INT

    def test_resolve_spec_unknown_key(self) -> None:
        """Test resolving spec for unknown key."""
        spec = config_gateway.resolve_spec("UNKNOWN_KEY")
        assert spec is None

    def test_resolve_spec_empty_key(self) -> None:
        """Test resolving spec for empty key."""
        spec = config_gateway.resolve_spec("")
        assert spec is None

    def test_resolve_spec_prefix_match(self) -> None:
        """Test resolving spec with prefix match."""
        spec = config_gateway.resolve_spec("SHERPA_ONNX_CUSTOM_SETTING")
        assert spec is not None
        assert isinstance(spec, PrefixConfigSpec)
        assert spec.prefix == "SHERPA_ONNX_"

    def test_resolve_spec_prefix_case_sensitive(self) -> None:
        """Test prefix matching is case sensitive."""
        spec = config_gateway.resolve_spec("sherpa_onnx_custom_setting")
        # Should not match since prefix is uppercase
        assert spec is None

    def test_normalize_category_with_spec(self) -> None:
        """Test normalizing category when spec exists."""
        category = config_gateway.normalize_category("FREE_AI_CHAT_DAILY_LIMIT", "default")
        assert category == "quota"

    def test_normalize_category_without_spec(self) -> None:
        """Test normalizing category when spec doesn't exist."""
        category = config_gateway.normalize_category("UNKNOWN_KEY", "default")
        assert category == "default"

    def test_normalize_category_fallback_none(self) -> None:
        """Test normalizing category with None fallback."""
        category = config_gateway.normalize_category("UNKNOWN_KEY", None)
        assert category is None

    def test_validate_value_string_valid(self) -> None:
        """Test validating string value."""
        config_gateway.validate_value("AI_PROMPT_VERSION_DEFAULT", "v1.0")

    def test_validate_value_string_empty_allowed(self) -> None:
        """Test validating empty string when allowed."""
        config_gateway.validate_value("AI_PROMPT_VERSION_DEFAULT", "")

    def test_validate_value_int_valid(self) -> None:
        """Test validating int value."""
        config_gateway.validate_value("FREE_AI_CHAT_DAILY_LIMIT", "10")

    def test_validate_value_int_invalid(self) -> None:
        """Test validating invalid int value."""
        with pytest.raises(ValueError, match="must be an integer"):
            config_gateway.validate_value("FREE_AI_CHAT_DAILY_LIMIT", "not_a_number")

    def test_validate_value_float_valid(self) -> None:
        """Test validating float value."""
        config_gateway.validate_value("VIP_DEFAULT_PRICE", "99.99")

    def test_validate_value_float_invalid(self) -> None:
        """Test validating invalid float value."""
        with pytest.raises(ValueError, match="must be a number"):
            config_gateway.validate_value("VIP_DEFAULT_PRICE", "not_a_number")

    def test_validate_value_bool_valid(self) -> None:
        """Test validating bool value."""
        config_gateway.validate_value("enable_notifications", "true")
        config_gateway.validate_value("enable_notifications", "1")
        config_gateway.validate_value("enable_notifications", "yes")

    def test_validate_value_bool_invalid(self) -> None:
        """Test validating invalid bool value."""
        with pytest.raises(ValueError, match="must be a boolean value"):
            config_gateway.validate_value("enable_notifications", "invalid")

    def test_validate_value_json_valid(self) -> None:
        """Test validating JSON value."""
        config_gateway.validate_value("CONSULT_REVIEW_SLA_JSON", '{"key": "value"}')

    def test_validate_value_json_invalid(self) -> None:
        """Test validating invalid JSON value."""
        with pytest.raises(ValueError, match="must be valid JSON"):
            config_gateway.validate_value("CONSULT_REVIEW_SLA_JSON", '{"invalid": }')

    def test_validate_value_json_b64_valid(self) -> None:
        """Test validating base64-encoded JSON value."""
        json_str = '{"key": "value"}'
        b64_str = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
        config_gateway.validate_value("NEWS_AI_SUMMARY_LLM_PROVIDERS_B64", b64_str)

    def test_validate_value_json_b64_invalid(self) -> None:
        """Test validating invalid base64."""
        with pytest.raises(ValueError, match="must be base64-encoded JSON"):
            config_gateway.validate_value("NEWS_AI_SUMMARY_LLM_PROVIDERS_B64", "not_base64!")

    def test_validate_value_empty_not_allowed(self) -> None:
        """Test validating empty value when not allowed."""
        # Create a spec that doesn't allow empty values
        spec = ConfigKeySpec(
            key="TEST_KEY",
            domain="test",
            value_type=ConfigValueType.STRING,
            category="test",
            allow_empty=False,
        )
        gateway = ConfigGateway()
        gateway._spec_map = {"TEST_KEY": spec}
        with pytest.raises(ValueError, match="value cannot be empty"):
            gateway.validate_value("TEST_KEY", "")

    def test_validate_value_unknown_key(self) -> None:
        """Test validating value for unknown key (should pass)."""
        # Should not raise any error for unknown keys
        config_gateway.validate_value("UNKNOWN_KEY", "any_value")

    def test_iter_specs(self) -> None:
        """Test iterating over specs."""
        specs = list(config_gateway.iter_specs())
        assert len(specs) > 0
        assert all(isinstance(spec, ConfigKeySpec) for spec in specs)


class TestConfigSpecs:
    """Test _CONFIG_SPECS tuple."""

    def test_config_specs_not_empty(self) -> None:
        """Test _CONFIG_SPECS is not empty."""
        assert len(_CONFIG_SPECS) > 0

    def test_config_specs_have_required_fields(self) -> None:
        """Test all specs have required fields."""
        for spec in _CONFIG_SPECS:
            assert spec.key
            assert spec.domain
            assert spec.value_type
            assert spec.category


class TestPrefixSpecs:
    """Test _PREFIX_SPECS tuple."""

    def test_prefix_specs_not_empty(self) -> None:
        """Test _PREFIX_SPECS is not empty."""
        assert len(_PREFIX_SPECS) > 0

    def test_prefix_specs_have_required_fields(self) -> None:
        """Test all prefix specs have required fields."""
        for spec in _PREFIX_SPECS:
            assert spec.prefix
            assert spec.domain
            assert spec.value_type
            assert spec.category


class TestIntegration:
    """Test integration scenarios."""

    def test_resolve_and_validate_workflow(self) -> None:
        """Test resolve spec and validate value workflow."""
        # Resolve spec
        spec = config_gateway.resolve_spec("FREE_AI_CHAT_DAILY_LIMIT")
        assert spec is not None

        # Validate value
        config_gateway.validate_value("FREE_AI_CHAT_DAILY_LIMIT", "10")

        # Get category
        category = config_gateway.normalize_category("FREE_AI_CHAT_DAILY_LIMIT", "default")
        assert category == "quota"

    def test_workflow_with_prefix_spec(self) -> None:
        """Test workflow with prefix spec."""
        # Resolve spec with prefix
        spec = config_gateway.resolve_spec("SHERPA_ONNX_CUSTOM_SETTING")
        assert spec is not None
        assert isinstance(spec, PrefixConfigSpec)

        # Validate value (string type)
        config_gateway.validate_value("SHERPA_ONNX_CUSTOM_SETTING", "custom_value")

        # Get category
        category = config_gateway.normalize_category("SHERPA_ONNX_CUSTOM_SETTING", "default")
        assert category == "voice"

    def test_all_config_keys_are_resolvable(self) -> None:
        """Test all config keys in _CONFIG_SPECS can be resolved."""
        for spec in _CONFIG_SPECS:
            resolved = config_gateway.resolve_spec(spec.key)
            assert resolved is not None
            assert resolved.key == spec.key
