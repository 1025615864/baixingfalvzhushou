"""Re-export module for openapi_exporter - allows test patching via app.utils.openapi_exporter."""
from __future__ import annotations

from pathlib import Path
from typing import Any
from datetime import datetime
import json
import logging

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi as _get_openapi

get_openapi = _get_openapi

logger = logging.getLogger(__name__)

DOCS_DIR = Path(__file__).parent.parent.parent / "docs" / "api"
OPENAPI_FILE = DOCS_DIR / "openapi.json"
REDOC_FILE = DOCS_DIR / "redoc.html"


def export_openapi_schema(
    app: FastAPI,
    output_path: str | None = None,
    format: str = "json",
) -> dict[str, Any]:
    schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        routes=app.routes,
        servers=app.servers,
    )

    schema.setdefault("info", {})
    schema["info"]["description"] = schema["info"].get(
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

    schema["x-generated-at"] = datetime.now().isoformat()

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

        logger.info("OpenAPI schema exported to %s", path)

    return schema


def generate_redoc_html(
    openapi_url: str = "/openapi.json",
    title: str = "API Documentation",
    output_path: str | None = None,
) -> str:
    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <style>body {{ margin: 0; padding: 0; }}</style>
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
        logger.info("ReDoc HTML generated to %s", path)

    return html


def generate_swagger_ui_html(
    openapi_url: str = "/openapi.json",
    title: str = "API Documentation",
    output_path: str | None = None,
) -> str:
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
        logger.info("Swagger UI HTML generated to %s", path)

    return html


def export_api_docs(app: FastAPI) -> dict[str, Any]:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    schema = export_openapi_schema(app, str(OPENAPI_FILE), format="json")

    generate_redoc_html(
        openapi_url="/openapi.json",
        title=f"{app.title} - API Documentation",
        output_path=str(REDOC_FILE),
    )

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

    methods = ["get", "post", "put", "delete", "patch", "options", "head"]
    for details in paths.values():
        tag = "default"
        for method in methods:
            if method in details:
                op = details[method]
                tags = op.get("tags", ["default"])
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

    summary["tags"] = list(summary["endpoints"].keys())

    return summary


def print_api_summary() -> None:
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
        methods_str = ", ".join([f"{k}: {v}" for k, v in data["methods"].items()])
        print(f"  {tag}: {data['total']} endpoints ({methods_str})")

    print("-" * 40)
    print(f"Total tags: {len(summary['tags'])}")
    print("=" * 60)
