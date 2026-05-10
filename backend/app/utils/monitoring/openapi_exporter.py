"""OpenAPI 文档导出工具

提供接口文档自动生成、导出和预览功能。
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

logger = logging.getLogger(__name__)

# 文档输出目录
DOCS_DIR = Path(__file__).parent.parent.parent / "docs" / "api"
OPENAPI_FILE = DOCS_DIR / "openapi.json"
REDOC_FILE = DOCS_DIR / "redoc.html"


def export_openapi_schema(
    app: FastAPI,
    output_path: str | None = None,
    format: str = "json",
) -> dict[str, Any]:
    """导出 OpenAPI schema

    Args:
        app: FastAPI 应用实例
        output_path: 输出文件路径
        format: 输出格式（json/yaml）

    Returns:
        OpenAPI schema 字典
    """
    schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        routes=app.routes,
        servers=app.servers,
    )

    # 添加额外信息
    schema["info"]["description"] = schema.get("info", {}).get(
        "description",
        "百姓法律助手 API 文档"
    )
    schema["info"]["contact"] = {
        "name": "百姓助手开发团队",
        "email": "dev@baixing.example.com"
    }
    schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }

    # 添加生成时间
    schema["x-generated-at"] = datetime.now().isoformat()

    # 输出文件
    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            with open(path, "w", encoding="utf-8") as f:
                json.dump(schema, f, ensure_ascii=False, indent=2)
        elif format == "yaml":
            import yaml
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(
                    schema,
                    f,
                    allow_unicode=True,
                    default_flow_style=False)

        logger.info(f"OpenAPI schema exported to {path}")

    return schema


def generate_redoc_html(
    openapi_url: str = "/openapi.json",
    title: str = "API Documentation",
    output_path: str | None = None,
) -> str:
    """生成 ReDoc HTML 页面

    Args:
        openapi_url: OpenAPI JSON 的 URL
        title: 页面标题
        output_path: 输出文件路径

    Returns:
        HTML 内容
    """
    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js" />
</head>
<body>
  <redoc spec-url='{openapi_url}'></redoc>
  <script src="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"></script>
</body>
</html>
"""

    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info(f"ReDoc HTML generated to {path}")

    return html


def generate_swagger_ui_html(
    openapi_url: str = "/openapi.json",
    title: str = "API Documentation",
    output_path: str | None = None,
) -> str:
    """生成 Swagger UI HTML 页面

    Args:
        openapi_url: OpenAPI JSON 的 URL
        title: 页面标题
        output_path: 输出文件路径

    Returns:
        HTML 内容
    """
    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    window.onload = function() {{
      SwaggerUIBundle({{
        url: '{openapi_url}',
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIBundle.SwaggerUIStandalonePreset
        ],
        plugins: [
          SwaggerUIBundle.plugins.DownloadUrl
        ]
      }});
    }};
  </script>
</body>
</html>
"""

    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info(f"Swagger UI HTML generated to {path}")

    return html


def export_api_docs(app: FastAPI) -> dict[str, Any]:
    """导出所有 API 文档

    Args:
        app: FastAPI 应用实例

    Returns:
        导出信息
    """
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # 导出 OpenAPI JSON
    schema = export_openapi_schema(app, str(OPENAPI_FILE), format="json")

    # 生成 ReDoc HTML
    generate_redoc_html(
        openapi_url="/openapi.json",
        title=f"{app.title} - API Documentation",
        output_path=str(REDOC_FILE),
    )

    # 生成 Swagger UI HTML
    swagger_file = DOCS_DIR / "swagger.html"
    generate_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{app.title} - Swagger UI",
        output_path=str(swagger_file),
    )

    return {
        "openapi": str(OPENAPI_FILE),
        "redoc": str(REDOC_FILE),
        "swagger": str(swagger_file),
        "endpoints_count": len(schema.get("paths", {})),
        "tags_count": len(schema.get("tags", [])),
    }


def get_api_summary() -> dict[str, Any]:
    """获取 API 摘要信息

    Returns:
        API 摘要字典
    """
    if not OPENAPI_FILE.exists():
        return {"error": "OpenAPI file not found"}

    with open(OPENAPI_FILE, encoding="utf-8") as f:
        schema = json.load(f)

    paths = schema.get("paths", {})
    summary: dict[str, Any] = {
        "title": schema.get("info", {}).get("title", "Unknown"),
        "version": schema.get("info", {}).get("version", "Unknown"),
        "generated_at": schema.get("x-generated-at", "Unknown"),
        "endpoints": {},
        "tags": [],
    }

    # 统计各方法的端点数量
    methods = ["get", "post", "put", "delete", "patch", "options", "head"]
    for details in paths.values():
        tag = "default"
        for method in methods:
            if method in details:
                op = details[method]
                tags = op.get("tags", ["default"])
                # 防御性编程：确保tags非空，避免IndexError
                tag = tags[0] if tags else "default"
                break

        if tag not in summary["endpoints"]:
            summary["endpoints"][tag] = {"total": 0, "methods": {}}

        summary["endpoints"][tag]["total"] += 1
        for method in methods:
            if method in details:
                if method not in summary["endpoints"][tag]["methods"]:
                    summary["endpoints"][tag]["methods"][method] = 0
                summary["endpoints"][tag]["methods"][method] += 1

    # 统计标签
    summary["tags"] = list(summary["endpoints"].keys())

    return summary


def print_api_summary() -> None:
    """打印 API 摘要"""
    summary = get_api_summary()

    if "error" in summary:
        print(f"Error: {summary['error']}")
        return

    print("=" * 60)
    print(f"API: {summary['title']} v{summary['version']}")
    print(f"Generated: {summary['generated_at']}")
    print("=" * 60)
    print("\nEndpoints by Tag:")
    print("-" * 40)

    for tag, data in summary["endpoints"].items():
        methods = ", ".join([f"{k}: {v}" for k, v in data["methods"].items()])
        print(f"  {tag}: {data['total']} endpoints ({methods})")

    print("-" * 40)
    print(f"Total tags: {len(summary['tags'])}")
    print("=" * 60)
