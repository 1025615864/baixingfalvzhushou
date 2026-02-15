"""JSON字段解析工具

提供安全的JSON字段解析功能。
"""
from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def parse_json_field(
    field_value: str | None,
    field_name: str = "field"
) -> list[Any] | dict[str, Any] | None:
    """安全解析JSON字段

    Args:
        field_value: JSON字符串
        field_name: 字段名称（用于日志）

    Returns:
        解析后的JSON对象，解析失败返回None
    """
    if not field_value:
        return None

    try:
        return json.loads(field_value)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse {field_name}: {str(e)}")
        return None


def parse_images_field(images_json: str | None) -> list[str]:
    """解析图片字段

    Args:
        images_json: JSON字符串

    Returns:
        图片URL列表
    """
    if not images_json:
        return []

    raw_images = parse_json_field(images_json, "images")
    if not isinstance(raw_images, list):
        return []

    images = []
    for elem in raw_images:
        if elem is None:
            continue
        if isinstance(elem, str):
            if elem:
                images.append(elem)
            continue
        images.append(str(elem))

    return images


def parse_attachments_field(
    attachments_json: str | None
) -> list[dict[str, str]]:
    """解析附件字段

    Args:
        attachments_json: JSON字符串

    Returns:
        附件列表，每个附件包含 name 和 url
    """
    if not attachments_json:
        return []

    raw_attachments = parse_json_field(attachments_json, "attachments")
    if not isinstance(raw_attachments, list):
        return []

    normalized = []
    for item in raw_attachments:
        if not isinstance(item, dict):
            continue

        item_dict = item
        name = item_dict.get("name")
        url = item_dict.get("url")

        if not isinstance(name, str) or not isinstance(url, str) or not name or not url:
            continue

        normalized.append({"name": name, "url": url})

    return normalized
