"""Tests for AI Model Config Service"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import select, func, and_

import app.services.cache_service as cache_service_module

from app.services.system.ai_config import AIModelConfigService
from app.models.system import AIModelConfig


@pytest.fixture(autouse=True)
def _reset_service_singletons_state():
    # Ensure cache_service always uses memory fallback during tests.
    cache_service_module.cache_service._redis = None
    cache_service_module.cache_service._connected = False
    cache_service_module._memory_cache.clear()


class TestAIModelConfigServiceGetList:
    """Tests for get_list method."""

    @pytest.mark.asyncio
    async def test_get_list_all_configs(self) -> None:
        """Test get_list returns all configs."""
        mock_db = AsyncMock()
        mock_config1 = MagicMock()
        mock_config1.id = 1
        mock_config1.name = "Model 1"
        mock_config2 = MagicMock()
        mock_config2.id = 2
        mock_config2.name = "Model 2"

        mock_result1 = MagicMock()
        mock_result1.scalars.return_value.all.return_value = [mock_config1, mock_config2]

        mock_db.execute.return_value = mock_result1
        mock_db.scalar.return_value = 2

        configs, total = await AIModelConfigService.get_list(mock_db)

        assert len(configs) == 2
        assert total == 2

    @pytest.mark.asyncio
    async def test_get_list_enabled_only(self) -> None:
        """Test get_list with enabled_only filter."""
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.name = "Model 1"

        mock_result1 = MagicMock()
        mock_result1.scalars.return_value.all.return_value = [mock_config]

        mock_db.execute.return_value = mock_result1
        mock_db.scalar.return_value = 1

        configs, total = await AIModelConfigService.get_list(mock_db, enabled_only=True)

        assert len(configs) == 1
        assert total == 1

    @pytest.mark.asyncio
    async def test_get_list_empty(self) -> None:
        """Test get_list with no configs."""
        mock_db = AsyncMock()
        mock_result1 = MagicMock()
        mock_result1.scalars.return_value.all.return_value = []

        mock_db.execute.return_value = mock_result1
        mock_db.scalar.return_value = 0

        configs, total = await AIModelConfigService.get_list(mock_db)

        assert configs == []
        assert total == 0


class TestAIModelConfigServiceGetById:
    """Tests for get_by_id method."""

    @pytest.mark.asyncio
    async def test_get_by_id_found(self) -> None:
        """Test get_by_id returns config when found."""
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.name = "Model 1"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_config
        mock_db.execute.return_value = mock_result

        config = await AIModelConfigService.get_by_id(mock_db, 1)

        assert config is not None
        assert config.id == 1

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self) -> None:
        """Test get_by_id returns None when not found."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        config = await AIModelConfigService.get_by_id(mock_db, 999)

        assert config is None


class TestAIModelConfigServiceCreate:
    """Tests for create method."""

    @pytest.mark.asyncio
    async def test_create_success(self) -> None:
        """Test create successfully creates config."""
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.id = 1

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch('app.services.system.ai_config.encrypt_secret') as mock_encrypt:
            mock_encrypt.return_value = "encrypted_key"

            config = await AIModelConfigService.create(
                mock_db,
                name="Test Model",
                model_id="test-model",
                api_key="test-key",
                base_url="https://api.test.com",
                enabled=True,
                weight=10,
                max_tokens=2000,
                temperature=0.7,
                created_by=1,
            )

            assert config is not None
            mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_duplicate_model_id(self) -> None:
        """Test create raises error for duplicate model_id."""
        mock_db = AsyncMock()
        mock_existing = MagicMock()
        mock_existing.id = 1

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_existing
        mock_db.execute.return_value = mock_result

        with pytest.raises(Exception) as exc_info:
            await AIModelConfigService.create(
                mock_db,
                name="Test Model",
                model_id="test-model",
                api_key="test-key",
                base_url="https://api.test.com",
                enabled=True,
                weight=10,
                max_tokens=2000,
                temperature=0.7,
                created_by=1,
            )

        assert "模型ID已存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_without_api_key(self) -> None:
        """Test create without API key."""
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.id = 1

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        config = await AIModelConfigService.create(
            mock_db,
            name="Test Model",
            model_id="test-model",
            api_key=None,
            base_url="https://api.test.com",
            enabled=True,
            weight=10,
            max_tokens=2000,
            temperature=0.7,
            created_by=1,
        )

        assert config is not None


class TestAIModelConfigServiceUpdate:
    """Tests for update method."""

    @pytest.mark.asyncio
    async def test_update_success(self) -> None:
        """Test update successfully updates config."""
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.name = "Old Name"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_config
        mock_db.execute.return_value = mock_result

        with patch('app.services.system.ai_config.encrypt_secret') as mock_encrypt:
            mock_encrypt.return_value = "new_encrypted_key"

            config = await AIModelConfigService.update(
                mock_db,
                config_id=1,
                name="New Name",
                api_key="new-key",
                updated_by=1,
            )

            assert config is not None

    @pytest.mark.asyncio
    async def test_update_not_found(self) -> None:
        """Test update raises error when config not found."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(Exception) as exc_info:
            await AIModelConfigService.update(
                mock_db,
                config_id=999,
                name="New Name",
            )

        assert "配置不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_preserve_api_key(self) -> None:
        """Test update preserves API key when masked."""
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.api_key = "old_encrypted_key"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_config
        mock_db.execute.return_value = mock_result

        config = await AIModelConfigService.update(
            mock_db,
            config_id=1,
            api_key="***",
        )

        assert config is not None

    @pytest.mark.asyncio
    async def test_update_clear_api_key(self) -> None:
        """Test update clears API key when empty."""
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.api_key = "old_encrypted_key"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_config
        mock_db.execute.return_value = mock_result

        config = await AIModelConfigService.update(
            mock_db,
            config_id=1,
            api_key="",
        )

        assert config is not None

    @pytest.mark.asyncio
    async def test_update_duplicate_model_id(self) -> None:
        """Test update raises error for duplicate model_id."""
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.id = 1
        mock_config.model_id = "old-model"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_config
        mock_db.execute.return_value = mock_result

        with patch('app.services.system.ai_config.encrypt_secret'):
            with pytest.raises(Exception) as exc_info:
                await AIModelConfigService.update(
                    mock_db,
                    config_id=1,
                    model_id="existing-model",
                )

            assert "模型ID已被其他配置使用" in str(exc_info.value)


class TestAIModelConfigServiceDelete:
    """Tests for delete method."""

    @pytest.mark.asyncio
    async def test_delete_success(self) -> None:
        """Test delete successfully deletes config."""
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.id = 1

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_config
        mock_db.execute.return_value = mock_result

        result = await AIModelConfigService.delete(mock_db, 1)

        assert result is True
        mock_db.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self) -> None:
        """Test delete raises error when config not found."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(Exception) as exc_info:
            await AIModelConfigService.delete(mock_db, 999)

        assert "配置不存在" in str(exc_info.value)
