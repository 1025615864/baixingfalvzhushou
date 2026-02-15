"""Tests for AI models."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add backend directory to path for cross-platform import
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.ai.models import AIModelConfig


class TestAIModelConfig:
    """Test AIModelConfig class."""

    def test_init_with_required_params(self) -> None:
        """Test initialization with required parameters only."""
        config = AIModelConfig(model_id="gpt-4o-mini")
        assert config.model_id == "gpt-4o-mini"
        assert config.api_key is None
        assert config.base_url is None
        assert config.max_tokens is None
        assert config.temperature is None
        assert config.weight == 1

    def test_init_with_all_params(self) -> None:
        """Test initialization with all parameters."""
        config = AIModelConfig(
            model_id="gpt-4o",
            api_key="sk-xxx",
            base_url="https://api.example.com",
            max_tokens=4096,
            temperature=0.7,
            weight=2,
        )
        assert config.model_id == "gpt-4o"
        assert config.api_key == "sk-xxx"
        assert config.base_url == "https://api.example.com"
        assert config.max_tokens == 4096
        assert config.temperature == 0.7
        assert config.weight == 2

    def test_default_weight(self) -> None:
        """Test that default weight is 1."""
        config = AIModelConfig(model_id="test")
        assert config.weight == 1

    def test_custom_weight(self) -> None:
        """Test custom weight value."""
        config = AIModelConfig(model_id="test", weight=3)
        assert config.weight == 3

    def test_optional_api_key(self) -> None:
        """Test that api_key can be None."""
        config = AIModelConfig(model_id="test", api_key=None)
        assert config.api_key is None

    def test_optional_base_url(self) -> None:
        """Test that base_url can be None."""
        config = AIModelConfig(model_id="test", base_url=None)
        assert config.base_url is None

    def test_optional_max_tokens(self) -> None:
        """Test that max_tokens can be None."""
        config = AIModelConfig(model_id="test", max_tokens=None)
        assert config.max_tokens is None

    def test_optional_temperature(self) -> None:
        """Test that temperature can be None."""
        config = AIModelConfig(model_id="test", temperature=None)
        assert config.temperature is None

    def test_attributes_are_modifiable(self) -> None:
        """Test that attributes can be modified."""
        config = AIModelConfig(model_id="test")
        config.api_key = "new-key"  # Should not raise
        assert config.api_key == "new-key"
