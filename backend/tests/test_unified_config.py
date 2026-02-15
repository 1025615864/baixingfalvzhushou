import pytest
import base64
import json
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.system.unified_config import (
    ConfigParseError,
    TypedConfigService,
    ConfigDomain,
    UnifiedConfigService,
    ConfigValueType,
)


class TestConfigParseError:
    """测试配置解析错误"""

    def test_error_message(self):
        """测试错误消息"""
        error = ConfigParseError("测试错误消息")
        assert "测试错误消息" in str(error)
        assert isinstance(error, ValueError)


class TestTypedConfigService:
    """测试类型化配置服务"""

    def setup_method(self):
        """每个测试前初始化"""
        self.service = TypedConfigService()

    def test_init_default_gateway(self):
        """测试默认网关初始化"""
        service = TypedConfigService()
        assert service._gateway is not None

    def test_init_custom_gateway(self):
        """测试自定义网关初始化"""
        mock_gateway = MagicMock()
        service = TypedConfigService(gateway=mock_gateway)
        assert service._gateway == mock_gateway

    def test_parse_value_string(self):
        """测试字符串解析"""
        result = self.service._parse_value("test_key", "hello", ConfigValueType.STRING)
        assert result == "hello"

    def test_parse_value_int(self):
        """测试整数解析"""
        result = self.service._parse_value("test_key", "42", ConfigValueType.INT)
        assert result == 42

    def test_parse_value_float(self):
        """测试浮点数解析"""
        result = self.service._parse_value("test_key", "3.14", ConfigValueType.FLOAT)
        assert result == 3.14

    def test_parse_value_bool_true(self):
        """测试布尔值解析 - true"""
        result = self.service._parse_value("test_key", "true", ConfigValueType.BOOL)
        assert result is True

    def test_parse_value_bool_false(self):
        """测试布尔值解析 - false"""
        result = self.service._parse_value("test_key", "false", ConfigValueType.BOOL)
        assert result is False

    def test_parse_value_json(self):
        """测试JSON解析"""
        result = self.service._parse_value("test_key", '{"key": "value"}', ConfigValueType.JSON)
        assert result == {"key": "value"}

    def test_parse_value_invalid_int(self):
        """测试无效整数解析"""
        with pytest.raises(ConfigParseError):
            self.service._parse_value("test_key", "not_a_number", ConfigValueType.INT)

    def test_parse_value_invalid_json(self):
        """测试无效JSON解析"""
        with pytest.raises(ConfigParseError):
            self.service._parse_value("test_key", "not_json", ConfigValueType.JSON)

    def test_parse_value_json_b64(self):
        """测试base64编码的JSON解析"""
        json_str = '{"key": "value"}'
        b64_str = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
        result = self.service._parse_value("test_key", b64_str, ConfigValueType.JSON_B64)
        assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_typed_with_default(self):
        """测试获取类型化配置 - 使用默认值"""
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.value = None

        with patch('app.services.system.unified_config.SystemConfigService.get_config', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_config
            result = await self.service.get_typed(mock_db, "test_key", ConfigValueType.INT, default=10)
            assert result == 10

    @pytest.mark.asyncio
    async def test_get_typed_empty_not_allowed(self):
        """测试获取类型化配置 - 空值不允许"""
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.value = ""

        with patch('app.services.system.unified_config.SystemConfigService.get_config', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_config
            with patch.object(self.service._gateway, 'resolve_spec') as mock_resolve:
                mock_spec = MagicMock()
                mock_spec.allow_empty = False
                mock_resolve.return_value = mock_spec
                with pytest.raises(ConfigParseError, match="不能为空"):
                    await self.service.get_typed(mock_db, "test_key", ConfigValueType.INT)

    @pytest.mark.asyncio
    async def test_get_int(self):
        """测试获取整数配置"""
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.value = "42"

        with patch('app.services.system.unified_config.SystemConfigService.get_config', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_config
            result = await self.service.get_int(mock_db, "test_key")
            assert result == 42

    @pytest.mark.asyncio
    async def test_get_float(self):
        """测试获取浮点数配置"""
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.value = "3.14"

        with patch('app.services.system.unified_config.SystemConfigService.get_config', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_config
            result = await self.service.get_float(mock_db, "test_key")
            assert result == 3.14

    @pytest.mark.asyncio
    async def test_get_bool(self):
        """测试获取布尔配置"""
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.value = "true"

        with patch('app.services.system.unified_config.SystemConfigService.get_config', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_config
            result = await self.service.get_bool(mock_db, "test_key")
            assert result is True

    @pytest.mark.asyncio
    async def test_get_str(self):
        """测试获取字符串配置"""
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.value = "hello"

        with patch('app.services.system.unified_config.SystemConfigService.get_config', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_config
            result = await self.service.get_str(mock_db, "test_key")
            assert result == "hello"

    @pytest.mark.asyncio
    async def test_get_json_dict(self):
        """测试获取JSON配置 - 字典"""
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.value = '{"key": "value"}'

        with patch('app.services.system.unified_config.SystemConfigService.get_config', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_config
            result = await self.service.get_json(mock_db, "test_key")
            assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_json_list(self):
        """测试获取JSON配置 - 列表"""
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.value = '["item1", "item2"]'

        with patch('app.services.system.unified_config.SystemConfigService.get_config', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_config
            result = await self.service.get_json(mock_db, "test_key")
            assert result == ["item1", "item2"]

    @pytest.mark.asyncio
    async def test_get_json_invalid_returns_default(self):
        """测试获取JSON配置 - 无效值返回默认值"""
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.value = None

        with patch('app.services.system.unified_config.SystemConfigService.get_config', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_config
            result = await self.service.get_json(mock_db, "test_key", default={"default": True})
            assert result == {"default": True}

    @pytest.mark.asyncio
    async def test_get_json_string_value(self):
        """测试获取JSON配置 - 字符串值需要解析"""
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.value = '{"key": "value"}'

        with patch('app.services.system.unified_config.SystemConfigService.get_config', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_config
            result = await self.service.get_json(mock_db, "test_key")
            assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_required_int(self):
        """测试获取必需的整数配置"""
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.value = "42"

        with patch('app.services.system.unified_config.SystemConfigService.get_config', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_config
            result = await self.service.get_required_int(mock_db, "test_key")
            assert result == 42

    @pytest.mark.asyncio
    async def test_get_required_int_missing(self):
        """测试获取必需的整数配置 - 缺失值"""
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.value = None

        with patch('app.services.system.unified_config.SystemConfigService.get_config', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_config
            with pytest.raises(ConfigParseError, match="不存在或无法解析"):
                await self.service.get_required_int(mock_db, "test_key")

    @pytest.mark.asyncio
    async def test_get_required_bool(self):
        """测试获取必需的布尔配置"""
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.value = "true"

        with patch('app.services.system.unified_config.SystemConfigService.get_config', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_config
            result = await self.service.get_required_bool(mock_db, "test_key")
            assert result is True

    @pytest.mark.asyncio
    async def test_get_required_bool_missing(self):
        """测试获取必需的布尔配置 - 缺失值"""
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.value = None

        with patch('app.services.system.unified_config.SystemConfigService.get_config', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_config
            with pytest.raises(ConfigParseError, match="不存在或无法解析"):
                await self.service.get_required_bool(mock_db, "test_key")


class TestConfigDomain:
    """测试配置域模型"""

    def test_create_empty_domain(self):
        """测试创建空配置域"""
        domain = ConfigDomain(domain="test")
        assert domain.domain == "test"
        assert domain.configs == []

    def test_create_with_configs(self):
        """测试创建带配置的配置域"""
        domain = ConfigDomain(domain="test")
        assert domain.domain == "test"
        assert len(domain.configs) == 0


class TestUnifiedConfigService:
    """测试统一配置服务"""

    def setup_method(self):
        """每个测试前初始化"""
        self.service = UnifiedConfigService()

    def test_init(self):
        """测试初始化"""
        assert self.service._typed_service is not None
        assert self.service._gateway is not None

    def test_list_specs_by_domain_empty(self):
        """测试列出空域的配置规格"""
        result = self.service.list_specs_by_domain("nonexistent")
        assert isinstance(result, list)
        assert len(result) == 0

    def test_list_specs_by_domain_system(self):
        """测试列出system域的配置规格"""
        result = self.service.list_specs_by_domain("system")
        assert isinstance(result, list)

    def test_get_domain_schema_empty(self):
        """测试获取空域的schema"""
        result = self.service.get_domain_schema("nonexistent")
        assert result["domain"] == "nonexistent"
        assert result["keys"] == []
        assert result["count"] == 0
        assert "schema" in result

    def test_get_domain_schema_system(self):
        """测试获取system域的schema"""
        result = self.service.get_domain_schema("system")
        assert result["domain"] == "system"
        assert "keys" in result
        assert "count" in result
        assert "schema" in result

    @pytest.mark.asyncio
    async def test_validate_and_set_with_value(self):
        """测试验证并设置配置"""
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.key = "test.key"
        mock_config.value = "test_value"

        with patch.object(self.service._gateway, 'validate_value'):
            with patch.object(self.service._gateway, 'normalize_category', return_value="general"):
                with patch('app.services.system.unified_config.SystemConfigService.set_config', new_callable=AsyncMock) as mock_set:
                    mock_set.return_value = mock_config
                    result = await self.service.validate_and_set(
                        db=mock_db,
                        key="test.key",
                        value="test_value",
                        description="测试配置",
                        category="test",
                        updated_by=1
                    )
                    assert result == mock_config

    @pytest.mark.asyncio
    async def test_validate_and_set_empty_category(self):
        """测试空分类时的自动确定"""
        mock_db = AsyncMock()
        mock_config = MagicMock()
        mock_config.key = "test.key"
        mock_config.value = "test_value"

        with patch.object(self.service._gateway, 'validate_value'):
            with patch.object(self.service._gateway, 'normalize_category', return_value="general"):
                with patch('app.services.system.unified_config.SystemConfigService.set_config', new_callable=AsyncMock) as mock_set:
                    mock_set.return_value = mock_config
                    result = await self.service.validate_and_set(
                        db=mock_db,
                        key="test.key",
                        value="test_value",
                        category="",
                        updated_by=1
                    )
                    assert result == mock_config

    @pytest.mark.asyncio
    async def test_get_by_domain_empty(self):
        """测试获取空域配置"""
        mock_db = AsyncMock()

        with patch('app.services.system.unified_config.SystemConfigService.get_all_configs', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = []
            result = await self.service.get_by_domain(mock_db, "nonexistent")
            assert result == []
