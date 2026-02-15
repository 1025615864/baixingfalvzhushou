"""OpenAPI 文档导出工具测试"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
import json
import tempfile
from pathlib import Path


@pytest.fixture
def mock_tmp_path(tmpdir):
    """提供临时路径（避免Windows权限问题）"""
    return Path(tmpdir)


class TestExportOpenAPISchema:
    """导出 OpenAPI Schema 测试"""

    @pytest.fixture
    def mock_app(self):
        """创建模拟 FastAPI 应用"""
        app = MagicMock()
        app.title = "Test API"
        app.version = "1.0.0"
        app.openapi_version = "3.0.0"
        app.servers = [{"url": "http://localhost:8000"}]
        app.routes = []
        return app

    def test_export_openapi_schema_basic(self, mock_app):
        """测试基础导出"""
        from app.utils.openapi_exporter import export_openapi_schema

        with patch('app.utils.openapi_exporter.get_openapi') as mock_get:
            mock_get.return_value = {
                "info": {"title": "Test", "version": "1.0"},
                "paths": {},
            }

            result = export_openapi_schema(mock_app)

            assert "info" in result
            assert result["info"]["title"] == "Test"

    def test_export_openapi_schema_with_contact(self, mock_app):
        """测试导出包含联系信息"""
        from app.utils.openapi_exporter import export_openapi_schema

        with patch('app.utils.openapi_exporter.get_openapi') as mock_get:
            mock_get.return_value = {
                "info": {"title": "Test", "version": "1.0"},
                "paths": {},
            }

            result = export_openapi_schema(mock_app)

            assert "contact" in result["info"]
            assert result["info"]["contact"]["name"] == "百姓助手开发团队"

    def test_export_openapi_schema_with_license(self, mock_app):
        """测试导出包含许可证"""
        from app.utils.openapi_exporter import export_openapi_schema

        with patch('app.utils.openapi_exporter.get_openapi') as mock_get:
            mock_get.return_value = {
                "info": {"title": "Test", "version": "1.0"},
                "paths": {},
            }

            result = export_openapi_schema(mock_app)

            assert "license" in result["info"]
            assert result["info"]["license"]["name"] == "MIT"

    def test_export_openapi_schema_generated_at(self, mock_app):
        """测试生成时间戳"""
        from app.utils.openapi_exporter import export_openapi_schema

        with patch('app.utils.openapi_exporter.get_openapi') as mock_get:
            mock_get.return_value = {
                "info": {"title": "Test", "version": "1.0"},
                "paths": {},
            }

            result = export_openapi_schema(mock_app)

            assert "x-generated-at" in result

    def test_export_openapi_schema_to_file_json(self, mock_app, tmpdir, monkeypatch):
        """测试导出到 JSON 文件"""
        from app.utils.openapi_exporter import export_openapi_schema

        monkeypatch.setattr("pathlib.Path.mkdir", lambda *args, **kwargs: None)
        output_path = Path(tmpdir) / "openapi.json"

        with patch('app.utils.openapi_exporter.get_openapi') as mock_get:
            mock_get.return_value = {
                "info": {"title": "Test", "version": "1.0"},
                "paths": {},
            }

            export_openapi_schema(mock_app, str(output_path), format="json")

            assert output_path.exists()
            content = json.loads(output_path.read_text(encoding='utf-8'))
            assert content["info"]["title"] == "Test"

    def test_export_openapi_schema_to_file_yaml(self, mock_app, tmpdir, monkeypatch):
        """测试导出到 YAML 文件"""
        from app.utils.openapi_exporter import export_openapi_schema

        monkeypatch.setattr("pathlib.Path.mkdir", lambda *args, **kwargs: None)
        output_path = Path(tmpdir) / "openapi.yaml"

        with patch('app.utils.openapi_exporter.get_openapi') as mock_get:
            mock_get.return_value = {
                "info": {"title": "Test", "version": "1.0"},
                "paths": {},
            }

            export_openapi_schema(mock_app, str(output_path), format="yaml")

            assert output_path.exists()

    def test_export_openapi_schema_to_file_json_safe(self, mock_app, tmpdir, monkeypatch):
        """测试导出到 JSON 文件（安全版本）"""
        from app.utils.openapi_exporter import export_openapi_schema
        import os

        output_path = Path(tmpdir) / "openapi.json"
        export_openapi_schema(mock_app, str(output_path), format="json")

        assert output_path.exists()
        content = json.loads(output_path.read_text(encoding='utf-8'))
        assert content["info"]["title"] == "Test API"

    def test_export_openapi_schema_to_file_yaml_safe(self, mock_app, tmpdir, monkeypatch):
        """测试导出到 YAML 文件（安全版本）"""
        from app.utils.openapi_exporter import export_openapi_schema

        monkeypatch.setattr("pathlib.Path.mkdir", lambda *args, **kwargs: None)
        output_path = Path(tmpdir) / "openapi.yaml"
        export_openapi_schema(mock_app, str(output_path), format="yaml")

        assert output_path.exists()


class TestGenerateReDocHTML:
    """生成 ReDoc HTML 测试"""

    def test_generate_redoc_html_basic(self):
        """测试基础生成"""
        from app.utils.openapi_exporter import generate_redoc_html

        html = generate_redoc_html(
            openapi_url="/openapi.json",
            title="API Documentation",
        )

        assert "<!DOCTYPE html>" in html
        assert "redoc" in html
        assert "/openapi.json" in html

    def test_generate_redoc_html_custom_title(self):
        """测试自定义标题"""
        from app.utils.openapi_exporter import generate_redoc_html

        html = generate_redoc_html(
            openapi_url="/openapi.json",
            title="Custom Title",
        )

        assert "Custom Title" in html

    def test_generate_redoc_html_to_file(self, tmpdir, monkeypatch):
        """测试生成到文件"""
        from app.utils.openapi_exporter import generate_redoc_html

        monkeypatch.setattr("pathlib.Path.mkdir", lambda *args, **kwargs: None)
        output_path = Path(tmpdir) / "redoc.html"

        generate_redoc_html(
            openapi_url="/openapi.json",
            title="API Docs",
            output_path=str(output_path),
        )

        assert output_path.exists()
        content = output_path.read_text()
        assert "redoc" in content


class TestGenerateSwaggerUIHTML:
    """生成 Swagger UI HTML 测试"""

    def test_generate_swagger_ui_html_basic(self):
        """测试基础生成"""
        from app.utils.openapi_exporter import generate_swagger_ui_html

        html = generate_swagger_ui_html(
            openapi_url="/openapi.json",
            title="API Documentation",
        )

        assert "<!DOCTYPE html>" in html
        assert "swagger-ui" in html
        assert "/openapi.json" in html

    def test_generate_swagger_ui_html_to_file(self, tmpdir, monkeypatch):
        """测试生成到文件"""
        from app.utils.openapi_exporter import generate_swagger_ui_html

        monkeypatch.setattr("pathlib.Path.mkdir", lambda *args, **kwargs: None)
        output_path = Path(tmpdir) / "swagger.html"

        generate_swagger_ui_html(
            openapi_url="/openapi.json",
            title="Swagger UI",
            output_path=str(output_path),
        )

        assert output_path.exists()
        content = output_path.read_text()
        assert "swagger" in content


class TestExportAPIDocs:
    """导出 API 文档测试"""

    @pytest.fixture
    def mock_app(self):
        """创建模拟 FastAPI 应用"""
        app = MagicMock()
        app.title = "Test API"
        app.version = "1.0.0"
        app.openapi_version = "3.0.0"
        app.servers = [{"url": "http://localhost:8000"}]
        app.routes = []
        return app

    def test_export_api_docs(self, mock_app, tmpdir, monkeypatch):
        """测试导出所有 API 文档"""
        from app.utils.openapi_exporter import export_api_docs

        monkeypatch.setattr("pathlib.Path.mkdir", lambda *args, **kwargs: None)
        with patch('app.utils.openapi_exporter.export_openapi_schema') as mock_export, \
             patch('app.utils.openapi_exporter.generate_redoc_html') as mock_redoc, \
             patch('app.utils.openapi_exporter.generate_swagger_ui_html') as mock_swagger, \
             patch('app.utils.openapi_exporter.DOCS_DIR', Path(tmpdir)):
            mock_export.return_value = {"paths": {"/test": {"get": {}}}}
            mock_redoc.return_value = "<html>redoc</html>"
            mock_swagger.return_value = "<html>swagger</html>"

            result = export_api_docs(mock_app)

            assert "openapi" in result
            assert "redoc" in result
            assert "swagger" in result
            assert "endpoints_count" in result
            assert "tags_count" in result


class TestGetAPISummary:
    """获取 API 摘要测试"""

    def test_get_api_summary_file_not_found(self):
        """测试文件不存在"""
        from app.utils.openapi_exporter import get_api_summary

        with patch('app.utils.openapi_exporter.OPENAPI_FILE') as mock_file:
            mock_file.exists.return_value = False

            result = get_api_summary()

            assert "error" in result

    def test_get_api_summary_success(self, tmpdir, monkeypatch):
        """测试获取 API 摘要成功"""
        from app.utils.openapi_exporter import get_api_summary

        monkeypatch.setattr("pathlib.Path.mkdir", lambda *args, **kwargs: None)
        openapi_file = Path(tmpdir) / "openapi.json"
        openapi_file.write_text(json.dumps({
            "info": {"title": "Test API", "version": "1.0"},
            "x-generated-at": "2024-01-01T00:00:00",
            "paths": {
                "/users": {"get": {"tags": ["users"]}},
                "/users/{id}": {"get": {"tags": ["users"]}, "put": {"tags": ["users"]}},
                "/orders": {"post": {"tags": ["orders"]}},
            },
        }))

        with patch('app.utils.openapi_exporter.OPENAPI_FILE', openapi_file):
            result = get_api_summary()

            assert result["title"] == "Test API"
            assert result["version"] == "1.0"
            assert "users" in result["endpoints"]
            assert "orders" in result["endpoints"]


class TestPrintAPISummary:
    """打印 API 摘要测试"""

    def test_print_api_summary_error(self, capsys):
        """测试打印错误"""
        from app.utils.openapi_exporter import print_api_summary

        with patch('app.utils.openapi_exporter.get_api_summary') as mock:
            mock.return_value = {"error": "File not found"}

            print_api_summary()

            captured = capsys.readouterr()
            assert "Error" in captured.out

    def test_print_api_summary_success(self, capsys):
        """测试成功打印"""
        from app.utils.openapi_exporter import print_api_summary

        with patch('app.utils.openapi_exporter.get_api_summary') as mock:
            mock.return_value = {
                "title": "Test API",
                "version": "1.0",
                "generated_at": "2024-01-01",
                "endpoints": {
                    "users": {"total": 2, "methods": {"get": 1, "post": 1}},
                },
                "tags": ["users"],
            }

            print_api_summary()

            captured = capsys.readouterr()
            assert "Test API" in captured.out
            assert "users" in captured.out


class TestOpenAPIExporterEdgeCases:
    """测试 OpenAPI Exporter 边界情况"""

    @pytest.fixture
    def mock_app(self):
        """创建模拟 FastAPI 应用"""
        app = MagicMock()
        app.title = "Test API"
        app.version = "1.0.0"
        app.openapi_version = "3.0.0"
        app.servers = [{"url": "http://localhost:8000"}]
        app.routes = []
        return app

    def test_export_with_empty_paths(self, mock_app, tmpdir, monkeypatch):
        """测试导出空路径"""
        from app.utils.openapi_exporter import export_openapi_schema

        monkeypatch.setattr("pathlib.Path.mkdir", lambda *args, **kwargs: None)
        output_path = Path(tmpdir) / "empty.json"

        with patch('app.utils.openapi_exporter.get_openapi') as mock_get:
            mock_get.return_value = {
                "info": {"title": "Empty API", "version": "1.0"},
                "paths": {},
            }

            result = export_openapi_schema(mock_app, str(output_path), format="json")

            assert result["info"]["title"] == "Empty API"
            assert output_path.exists()

    def test_export_with_complex_paths(self, mock_app, tmpdir, monkeypatch):
        """测试导出复杂路径"""
        from app.utils.openapi_exporter import export_openapi_schema

        monkeypatch.setattr("pathlib.Path.mkdir", lambda *args, **kwargs: None)
        output_path = Path(tmpdir) / "complex.json"

        with patch('app.utils.openapi_exporter.get_openapi') as mock_get:
            mock_get.return_value = {
                "info": {"title": "Complex API", "version": "2.0"},
                "paths": {
                    "/users/{id}/posts/{post_id}": {
                        "get": {
                            "tags": ["users", "posts"],
                            "summary": "Get user post",
                            "parameters": [
                                {"name": "id", "in": "path", "required": True},
                                {"name": "post_id", "in": "path", "required": True},
                            ],
                        }
                    }
                },
            }

            result = export_openapi_schema(mock_app, str(output_path), format="json")

            assert result["info"]["title"] == "Complex API"
            assert "/users/{id}/posts/{post_id}" in result["paths"]

    def test_generate_redoc_html_with_theme(self):
        """测试生成 ReDoc HTML（带主题）"""
        from app.utils.openapi_exporter import generate_redoc_html

        html = generate_redoc_html(
            openapi_url="/openapi.json",
            title="Themed API Docs",
        )

        assert "<!DOCTYPE html>" in html
        assert "redoc" in html
        assert "Themed API Docs" in html

    def test_generate_swagger_ui_html_with_options(self):
        """测试生成 Swagger UI HTML（带选项）"""
        from app.utils.openapi_exporter import generate_swagger_ui_html

        html = generate_swagger_ui_html(
            openapi_url="/openapi.json",
            title="Options API Docs",
        )

        assert "<!DOCTYPE html>" in html
        assert "swagger-ui" in html
        assert "Options API Docs" in html

    def test_export_api_docs_with_no_endpoints(self, mock_app, tmpdir, monkeypatch):
        """测试导出无端点 API 文档"""
        from app.utils.openapi_exporter import export_api_docs

        monkeypatch.setattr("pathlib.Path.mkdir", lambda *args, **kwargs: None)
        with patch('app.utils.openapi_exporter.export_openapi_schema') as mock_export, \
             patch('app.utils.openapi_exporter.generate_redoc_html') as mock_redoc, \
             patch('app.utils.openapi_exporter.generate_swagger_ui_html') as mock_swagger, \
             patch('app.utils.openapi_exporter.DOCS_DIR', Path(tmpdir)):

            mock_export.return_value = {"paths": {}}
            mock_redoc.return_value = "<html>redoc</html>"
            mock_swagger.return_value = "<html>swagger</html>"

            result = export_api_docs(mock_app)

            assert result["endpoints_count"] == 0
            assert "openapi" in result
            assert "redoc" in result
            assert "swagger" in result

    def test_get_api_summary_with_tags(self, tmpdir, monkeypatch):
        """测试获取带标签的 API 摘要"""
        from app.utils.openapi_exporter import get_api_summary

        monkeypatch.setattr("pathlib.Path.mkdir", lambda *args, **kwargs: None)
        openapi_file = Path(tmpdir) / "openapi.json"
        openapi_file.write_text(json.dumps({
            "info": {"title": "Tagged API", "version": "3.0"},
            "x-generated-at": "2024-06-01T00:00:00",
            "paths": {
                "/users": {"get": {"tags": ["users", "admin"]}},
                "/posts": {"post": {"tags": ["content"]}},
            },
            "tags": [
                {"name": "users", "description": "User operations"},
                {"name": "admin", "description": "Admin operations"},
            ],
        }))

        with patch('app.utils.openapi_exporter.OPENAPI_FILE', openapi_file):
            result = get_api_summary()

            assert result["title"] == "Tagged API"
            assert result["version"] == "3.0"
            assert len(result["tags"]) == 2

    def test_print_api_summary_empty(self, capsys):
        """测试打印空摘要"""
        from app.utils.openapi_exporter import print_api_summary

        with patch('app.utils.openapi_exporter.get_api_summary') as mock:
            mock.return_value = {
                "title": "Empty API",
                "version": "1.0",
                "generated_at": "2024-01-01",
                "endpoints": {},
                "tags": [],
            }

            print_api_summary()

            captured = capsys.readouterr()
            assert "Empty API" in captured.out


class TestOpenAPIExporterDetail:
    """测试 OpenAPI Exporter 详细功能"""

    @pytest.fixture
    def mock_app(self):
        """创建模拟 FastAPI 应用"""
        app = MagicMock()
        app.title = "Test API"
        app.version = "1.0.0"
        app.openapi_version = "3.0.0"
        app.servers = [{"url": "http://localhost:8000"}]
        app.routes = []
        return app

    def test_export_preserves_all_fields(self, mock_app, tmpdir):
        """测试导出保留所有字段"""
        from app.utils.openapi_exporter import export_openapi_schema

        output_path = Path(tmpdir) / "full.json"

        with patch('app.utils.openapi_exporter.get_openapi') as mock_get:
            mock_get.return_value = {
                "info": {
                    "title": "Full API",
                    "version": "1.0.0",
                    "description": "A complete API",
                    "contact": {"name": "Team", "email": "team@example.com"},
                    "license": {"name": "MIT"},
                },
                "paths": {
                    "/test": {
                        "get": {
                            "summary": "Test endpoint",
                            "description": "A test endpoint",
                            "operationId": "getTest",
                            "tags": ["test"],
                        }
                    }
                },
                "components": {
                    "schemas": {
                        "Test": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "name": {"type": "string"},
                            }
                        }
                    }
                },
            }

            result = export_openapi_schema(mock_app, str(output_path), format="json")

            assert result["info"]["title"] == "Full API"
            assert result["info"]["version"] == "1.0.0"
            assert "/test" in result["paths"]
            assert "components" in result

    def test_generate_redoc_html_includes_css(self):
        """测试 ReDoc HTML 包含 CSS"""
        from app.utils.openapi_exporter import generate_redoc_html

        html = generate_redoc_html(
            openapi_url="/openapi.json",
            title="CSS Test",
        )

        assert "<!DOCTYPE html>" in html
        assert "redoc" in html
        assert "css" in html.lower() or "style" in html.lower()

    def test_generate_swagger_ui_html_includes_js(self):
        """测试 Swagger UI HTML 包含 JS"""
        from app.utils.openapi_exporter import generate_swagger_ui_html

        html = generate_swagger_ui_html(
            openapi_url="/openapi.json",
            title="JS Test",
        )

        assert "<!DOCTYPE html>" in html
        assert "swagger" in html
        assert "javascript" in html.lower() or "js" in html.lower()
