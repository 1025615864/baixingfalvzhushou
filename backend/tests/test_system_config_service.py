"""Tests for System Config Service"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.services.system.config import SystemConfigService, SystemSecretService, _mask_secret_value
from app.models.system import SystemConfig, SystemSecret


class TestMaskSecretValue:
    """Tests for _mask_secret_value helper function."""

    def test_mask_none(self) -> None:
        """Test masking None returns None."""
        assert _mask_secret_value(None) is None

    def test_mask_empty_string(self) -> None:
        """Test masking empty string returns None."""
        assert _mask_secret_value("") is None

    def test_mask_whitespace(self) -> None:
        """Test masking whitespace returns None."""
        assert _mask_secret_value("   ") is None

    def test_mask_value(self) -> None:
        """Test masking value returns masked value."""
        assert _mask_secret_value("secret123") == "***"


class TestSystemConfigServiceIsSecretKey:
    """Tests for is_secret_key method."""

    def test_is_secret_key_password(self) -> None:
        """Test detecting password key."""
        assert SystemConfigService.is_secret_key("db_password") is True

    def test_is_secret_key_secret(self) -> None:
        """Test detecting secret key."""
        assert SystemConfigService.is_secret_key("api_secret") is True

    def test_is_secret_key_token(self) -> None:
        """Test detecting token key."""
        assert SystemConfigService.is_secret_key("access_token") is True

    def test_is_secret_key_normal(self) -> None:
        """Test normal key is not secret."""
        assert SystemConfigService.is_secret_key("app_name") is False

    def test_is_secret_key_case_insensitive(self) -> None:
        """Test detection is case insensitive."""
        assert SystemConfigService.is_secret_key("API_KEY") is True


class TestSystemConfigServiceGetConfig:
    """Tests for get_config method."""

    @pytest.mark.asyncio
    async def test_get_config_found(self) -> None:
        """Test get_config returns config when found."""
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.key = "test_key"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_config
        mock_db.execute.return_value = mock_result

        config = await SystemConfigService.get_config(mock_db, "test_key")

        assert config is not None
        assert config.key == "test_key"

    @pytest.mark.asyncio
    async def test_get_config_not_found(self) -> None:
        """Test get_config returns None when not found."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        config = await SystemConfigService.get_config(mock_db, "nonexistent")

        assert config is None


class TestSystemConfigServiceGetAllConfigs:
    """Tests for get_all_configs method."""

    @pytest.mark.asyncio
    async def test_get_all_configs(self) -> None:
        """Test get_all_configs returns all configs."""
        mock_db = AsyncMock()
        mock_config1 = MagicMock()
        mock_config1.key = "key1"
        mock_config2 = MagicMock()
        mock_config2.key = "key2"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_config1, mock_config2]
        mock_db.execute.return_value = mock_result

        configs = await SystemConfigService.get_all_configs(mock_db)

        assert len(configs) == 2

    @pytest.mark.asyncio
    async def test_get_all_configs_with_category(self) -> None:
        """Test get_all_configs with category filter."""
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.key = "key1"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_config]
        mock_db.execute.return_value = mock_result

        configs = await SystemConfigService.get_all_configs(mock_db, category="general")

        assert len(configs) == 1


class TestSystemConfigServiceSetConfig:
    """Tests for set_config method."""

    @pytest.mark.asyncio
    async def test_set_config_update_existing(self) -> None:
        """Test set_config updates existing config."""
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.key = "test_key"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_config
        mock_db.execute.return_value = mock_result

        config = await SystemConfigService.set_config(
            mock_db,
            key="test_key",
            value="new_value",
            updated_by=1,
        )

        assert config is not None

    @pytest.mark.asyncio
    async def test_set_config_create_new(self) -> None:
        """Test set_config creates new config."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch.object(SystemConfig, '__init__', return_value=None):
            config = await SystemConfigService.set_config(
                mock_db,
                key="new_key",
                value="value",
                description="Test config",
                category="general",
                updated_by=1,
            )

            assert config is not None
            mock_db.add.assert_called_once()


class TestSystemConfigServiceDeleteConfig:
    """Tests for delete_config method."""

    @pytest.mark.asyncio
    async def test_delete_config_success(self) -> None:
        """Test delete_config returns True when successful."""
        mock_db = AsyncMock()
        mock_config = MagicMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_config
        mock_db.execute.return_value = mock_result

        result = await SystemConfigService.delete_config(mock_db, "test_key")

        assert result is True
        mock_db.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_config_not_found(self) -> None:
        """Test delete_config returns False when not found."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await SystemConfigService.delete_config(mock_db, "nonexistent")

        assert result is False


class TestSystemConfigServiceBatchUpdate:
    """Tests for batch_update method."""

    @pytest.mark.asyncio
    async def test_batch_update(self) -> None:
        """Test batch_update updates multiple configs."""
        mock_db = AsyncMock()

        configs = [
            {"key": "key1", "value": "value1"},
            {"key": "key2", "value": "value2"},
        ]

        with patch.object(SystemConfigService, 'set_config', new_callable=AsyncMock) as mock_set_config:
            mock_config1 = MagicMock()
            mock_config2 = MagicMock()
            mock_set_config.side_effect = [mock_config1, mock_config2]

            results = await SystemConfigService.batch_update(mock_db, configs, updated_by=1)

            assert len(results) == 2


class TestSystemSecretServiceGetAll:
    """Tests for SystemSecretService.get_all method."""

    @pytest.mark.asyncio
    async def test_get_all_secrets(self) -> None:
        """Test get_all returns all secrets."""
        mock_db = AsyncMock()
        mock_secret1 = MagicMock()
        mock_secret1.key = "secret1"
        mock_secret2 = MagicMock()
        mock_secret2.key = "secret2"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_secret1, mock_secret2]
        mock_db.execute.return_value = mock_result

        secrets = await SystemSecretService.get_all(mock_db)

        assert len(secrets) == 2


class TestSystemSecretServiceGet:
    """Tests for SystemSecretService.get method."""

    @pytest.mark.asyncio
    async def test_get_secret_found(self) -> None:
        """Test get returns secret when found."""
        mock_db = AsyncMock()
        mock_secret = MagicMock()
        mock_secret.key = "secret_key"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_secret
        mock_db.execute.return_value = mock_result

        secret = await SystemSecretService.get(mock_db, "secret_key")

        assert secret is not None

    @pytest.mark.asyncio
    async def test_get_secret_not_found(self) -> None:
        """Test get returns None when not found."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        secret = await SystemSecretService.get(mock_db, "nonexistent")

        assert secret is None


class TestSystemSecretServiceSet:
    """Tests for SystemSecretService.set method."""

    @pytest.mark.asyncio
    async def test_set_secret_update_existing(self) -> None:
        """Test set updates existing secret."""
        mock_db = AsyncMock()
        mock_secret = MagicMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_secret
        mock_db.execute.return_value = mock_result

        secret = await SystemSecretService.set(
            mock_db,
            key="secret_key",
            value="new_value",
            updated_by=1,
        )

        assert secret is not None

    @pytest.mark.asyncio
    async def test_set_secret_create_new(self) -> None:
        """Test set creates new secret."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch.object(SystemSecret, '__init__', return_value=None):
            secret = await SystemSecretService.set(
                mock_db,
                key="new_secret",
                value="value",
                description="Test secret",
                updated_by=1,
            )

            assert secret is not None
            mock_db.add.assert_called_once()


class TestSystemSecretServiceDelete:
    """Tests for SystemSecretService.delete method."""

    @pytest.mark.asyncio
    async def test_delete_secret_success(self) -> None:
        """Test delete returns True when successful."""
        mock_db = AsyncMock()
        mock_secret = MagicMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_secret
        mock_db.execute.return_value = mock_result

        result = await SystemSecretService.delete(mock_db, "secret_key")

        assert result is True
        mock_db.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_secret_not_found(self) -> None:
        """Test delete returns False when not found."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await SystemSecretService.delete(mock_db, "nonexistent")

        assert result is False


class TestSystemSecretServiceExists:
    """Tests for SystemSecretService.exists method."""

    @pytest.mark.asyncio
    async def test_exists_true(self) -> None:
        """Test exists returns True when secret exists."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = "secret_key"
        mock_db.execute.return_value = mock_result

        result = await SystemSecretService.exists(mock_db, "secret_key")

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(self) -> None:
        """Test exists returns False when secret doesn't exist."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await SystemSecretService.exists(mock_db, "nonexistent")

        assert result is False
